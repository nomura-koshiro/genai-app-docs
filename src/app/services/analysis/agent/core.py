"""分析エージェントのLangChain AgentExecutor実装。

このモジュールはLangChainのAgentExecutorを使用して、
データ分析タスクを自然言語で実行できるAIエージェントを提供します。

元ファイル:
    C:/developments/camp-backend-code-analysis/app/agents/analysis/agent.py

主な変更点:
    - メモリベースAnalysisState → DB永続化版AnalysisState
    - 同期chat() → 非同期chat()
    - db: AsyncSession と session_id: uuid.UUID を受け取る
    - Azure OpenAI via LangChain
    - ConversationBufferMemory + DB永続化
    - Google-style docstrings追加
    - 完全な型ヒント
    - structlogによるロギング
    - @measure_performance デコレータ

主な機能:
    - LangChain AgentExecutorによるツール実行
    - 13個のツール統合（フィルタ、集計、変換、サマリー等）
    - Azure OpenAI GPT-4による自然言語理解
    - 会話履歴のDB永続化
    - エラーハンドリングとリトライ機構

使用例:
    >>> from app.services.analysis.agent.core import AnalysisAgent
    >>> import uuid
    >>>
    >>> async with get_db() as db:
    ...     session_id = uuid.uuid4()
    ...     agent = AnalysisAgent(db, session_id)
    ...     await agent.initialize()
    ...     response = await agent.chat("データの概要を教えてください")
    ...     print(response)
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from langchain.agents import AgentExecutor, AgentType, initialize_agent
from langchain.callbacks.base import BaseCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.repositories.analysis import AnalysisSessionRepository
from app.schemas.analysis import ChatMessage, ToolUsage
from app.services.analysis.agent.state import AnalysisState
from app.services.analysis.agent.utils.tools import (
    AddStepTool,
    DeleteStepTool,
    GetAggregationTool,
    GetDataOverviewTool,
    GetDataValueTool,
    GetFilterTool,
    GetStepOverviewTool,
    GetSummaryTool,
    GetTransformTool,
    SetAggregationTool,
    SetFilterTool,
    SetSummaryTool,
    SetTransformTool,
)

logger = get_logger(__name__)


class ToolTrackingHandler(BaseCallbackHandler):
    """ツール使用履歴を追跡するコールバックハンドラー。

    LangChain AgentExecutorによるツール呼び出しを記録し、
    ユーザーに内部処理の詳細を表示するために使用します。

    Attributes:
        tool_usage (list[ToolUsage]): ツール使用履歴のリスト

    Example:
        >>> handler = ToolTrackingHandler()
        >>> response = await agent.invoke({"input": "データの概要を教えて"}, callbacks=[handler])
        >>> for usage in handler.tool_usage:
        ...     print(f"Tool: {usage.tool}, Output: {usage.output}")
    """

    def __init__(self) -> None:
        """初期化。"""
        super().__init__()
        self.tool_usage: list[ToolUsage] = []

    def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """ツール開始時のコールバック。

        Args:
            serialized (dict[str, Any]): ツールのシリアライズ情報
            input_str (str): ツールへの入力
            **kwargs: 追加パラメータ
        """
        tool_name = serialized.get("name", "unknown")
        self.tool_usage.append(ToolUsage(tool=tool_name, input=input_str, output=None))

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """ツール終了時のコールバック。

        Args:
            output (str): ツールからの出力
            **kwargs: 追加パラメータ
        """
        if self.tool_usage:
            self.tool_usage[-1].output = output


class AnalysisAgent:
    """データ分析エージェント。

    LangChainのAgentExecutorを使用して、自然言語での
    データ分析タスク実行を可能にします。

    主な機能:
        - データ概要の取得
        - 分析ステップの追加・削除
        - フィルタリング、集計、変換、サマリーの設定
        - 会話履歴の管理
        - Azure OpenAI GPT-4による対話

    Attributes:
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): 分析セッションID
        state (AnalysisState): 分析状態管理インスタンス
        session_repository (AnalysisSessionRepository): セッションリポジトリ
        agent_executor (AgentExecutor | None): LangChain AgentExecutor
        memory (ConversationBufferMemory | None): 会話履歴メモリ

    使用例:
        >>> async with get_db() as db:
        ...     agent = AnalysisAgent(db, session_id)
        ...     await agent.initialize()
        ...     response = await agent.chat("データの概要を教えてください")
        ...     print(response)
    """

    def __init__(self, db: AsyncSession, session_id: uuid.UUID):
        """初期化。

        Args:
            db (AsyncSession): データベースセッション
            session_id (uuid.UUID): 分析セッションID
        """
        self.db = db
        self.session_id = session_id
        self.state = AnalysisState(db, session_id)
        self.session_repository = AnalysisSessionRepository(db)
        self.agent_executor: AgentExecutor | None = None
        self.memory: ConversationBufferMemory | None = None

        logger.info(
            "分析エージェントを初期化しました",
            session_id=str(session_id),
        )

    async def initialize(self) -> None:
        """エージェントの初期化。

        LangChain AgentExecutorとツール、メモリを設定します。

        処理内容:
            1. 13個のツールを初期化
            2. Azure OpenAI GPT-4接続を設定
            3. ConversationBufferMemoryを初期化
            4. DBから会話履歴を読み込み
            5. AgentExecutorを初期化

        Raises:
            ValidationError: 初期化に失敗した場合
        """
        try:
            logger.info(
                "分析エージェントを初期化中",
                session_id=str(self.session_id),
                action="initialize_agent",
            )

            # Initialize all 13 tools
            tools = [
                GetDataOverviewTool(self.db, self.session_id),
                GetStepOverviewTool(self.db, self.session_id),
                GetDataValueTool(self.db, self.session_id),
                AddStepTool(self.db, self.session_id),
                DeleteStepTool(self.db, self.session_id),
                GetFilterTool(self.db, self.session_id),
                GetAggregationTool(self.db, self.session_id),
                GetTransformTool(self.db, self.session_id),
                GetSummaryTool(self.db, self.session_id),
                SetFilterTool(self.db, self.session_id),
                SetAggregationTool(self.db, self.session_id),
                SetTransformTool(self.db, self.session_id),
                SetSummaryTool(self.db, self.session_id),
            ]

            # Initialize Azure OpenAI via LangChain
            llm = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=(SecretStr(settings.AZURE_OPENAI_API_KEY) if settings.AZURE_OPENAI_API_KEY else None),
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                temperature=0.7,  # type: ignore[call-arg]
            )

            # Initialize conversation memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
            )

            # Load chat history from DB if exists
            await self._load_chat_history()

            # Get system prompt (camp-backend compatible)
            system_message = self._get_system_prompt()

            # Initialize agent with system prompt
            self.agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=25,
                agent_kwargs={"system_message": system_message},
            )

            logger.info(
                "分析エージェント初期化が完了しました",
                session_id=str(self.session_id),
                tools_count=len(tools),
            )

        except Exception as e:
            logger.error(
                "エージェント初期化に失敗しました",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            raise ValidationError(f"エージェントの初期化に失敗しました: {e}") from e

    def _get_system_prompt(self) -> str:
        """システムプロンプトを取得。

        camp-backend-code-analysisのプロンプトを使用します。

        Returns:
            str: システムプロンプト文字列
        """
        return """
あなたはデータ分析のエキスパートアシスタントです。
ユーザーの自然言語による分析要求を理解し、適切な分析ステップを生成・設定して、望ましい分析結果を提供します。
ステップは、データの集計、データのフィルタリング、データの変換、データからの結果グラフと計算式の設定などをすることができます。
ユーザが望む分析結果を得るために必要なステップを自動的に追加・更新・削除をしてください。


## 一般的なデータ構造:
- データはDataFrameでレコード型式です。以下のようなコラムを持つことが想定されます:
    - '軸1', '軸2', ... (データ識別子: 地域、セグメント、製品など)
    - '科目': 科目名 (データ属性: 売り上げ高、利益率など)
    - '値': 数値データ (軸と科目に対応する数値: 売り上げ高の金額、利益率のパーセンテージなど)



## 利用可能なステップの4つのタイプ:
1. **フィルタ**: データを特定の条件で絞り込みます。その結果が新しい中間データセットを生成します。
   以下のフィルタを設定できます (3つのフィルタを同時に設定することも可能です):
2. **集計**: データをグループ化してデータの集計粒度を変えるステップです。
   その結果が新しい中間データセットを生成します。
3. **変換**: データの軸や科目を追加・変更してデータ構造を変更するステップです。
   その結果が新しい中間データセットを生成します。
4. **サマリ**: 計算式、チャート、出力テーブルを設定し、結果を表記します。
   新しい中間データセットを生成することはありません、数値、チャート、テーブルを表示するだけです。


## 利用可能なツール:
- `add_step`: 新しい分析ステップを追加します。
    - add_stepのステップの名前 'step_name' は何のステップかわかるように日本語で入力してください。
      さらに重複しないようにしてください。
    - add_stepのデータソース 'data_source' は元データの'original'または
      ステップでの結果'step_1'などで指定されたステップの結果を入力とします。
- `delete_step`: 指定したインデックスの分析ステップを削除します。間違ったステップを削除するために使用します。
- `get_aggregation`: 指定したインデックスの分析ステップの集計設定を取得します。
- `get_filter`: 指定したインデックスの分析ステップのフィルタ設定を取得します。
- `get_summary`: 指定したインデックスの分析ステップのサマリ設定を取得します。
- `get_transform`: 指定したインデックスの分析ステップの変換設定を取得します。
- `set_aggregation`: 指定したインデックスの分析ステップの集計設定を上書きします。
- `set_filter`: 指定したインデックスの分析ステップのフィルタ設定を上書きします。
- `set_summary`: 指定したインデックスの分析ステップのサマリ設定を上書きします。
- `set_transform`: 指定したインデックスの分析ステップの変換設定を上書きします。
- `get_data_overview`: 現在のデータセットの概要を取得します。
- `get_step_overview`: 現在の分析ステップの概要を取得します。
    - 現在のステップはどこまで進んでいるか、どのステップのデータが必要なのかを確認するために使用します。
- `get_data_value`: 指定したステップの入力データから特定の軸・科目の組み合わせに対応する値を取得します。
    - 特定の軸、科目が対応する値を確認したい場合に使用します。


## 注意事項:
- 返答は常に日本語で行ってください。ユーザーの要求が不明確な場合は、曖昧さを解消するために追加の質問をしてください
- ツール呼び出し時はJSON形式を避け、自然言語で説明してください
- ステップの更新内容は箇条書きで説明してください
- ツール使用時にエラーが発生した場合はエラーメッセージ及び利用可能な軸・科目を確認してから
  再設定してください。必ず成功するまで修正してから、Final Answerを出力してください
- 要求されていない計算式をサマリステップに勝手に追加しないでください

"""

    async def _load_chat_history(self) -> None:
        """DBから会話履歴をロード。

        AnalysisSession.chat_historyから会話履歴を読み込み、
        ConversationBufferMemoryに設定します。

        Note:
            - system, user, assistantのロールをそれぞれSystemMessage, HumanMessage, AIMessageに変換
            - 会話履歴が存在しない場合はスキップ
        """
        try:
            if not self.memory:
                return

            # Get session from DB
            session = await self.session_repository.get(self.session_id)
            if session and session.chat_history:
                # Load into memory (dict → ChatMessage変換)
                for message_dict in session.chat_history:
                    message = ChatMessage.model_validate(message_dict)
                    role = message.role
                    content = message.content

                    if role == "user":
                        self.memory.chat_memory.messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        self.memory.chat_memory.messages.append(AIMessage(content=content))

                logger.info(
                    "会話履歴をロードしました",
                    session_id=str(self.session_id),
                    message_count=len(session.chat_history),
                )
        except Exception as e:
            logger.warning(
                "会話履歴のロードに失敗しました",
                session_id=str(self.session_id),
                error=str(e),
            )

    def _get_current_context(self) -> str:
        """現在のデータとステップの状況を取得。

        camp-backend互換のメソッド。
        データ概要とステップ概要を組み合わせたコンテキスト文字列を返します。

        Returns:
            str: 現在のコンテキスト（データ概要 + ステップ概要）
        """
        # Note: This is synchronous in camp-backend but we'll need to call it async
        # We'll handle this in the chat method
        context = """
=== 現在のデータ状況 ===
{data_overview}

=== 現在のステップ状況 ===
{step_overview}
"""
        return context

    @measure_performance
    async def chat(self, user_input: str, max_retry: int = 3) -> str:
        """ユーザーメッセージを処理。

        camp-backend-code-analysisのchat()メソッドを非同期版に変換。

        処理フロー:
            1. スナップショットIDをインクリメント
            2. 会話履歴をクリアしてDBから再ロード
            3. 現在のコンテキスト（データ・ステップ概要）を追加
            4. AgentExecutorを実行
            5. ツール使用履歴を整形して応答に追加
            6. 会話履歴をDBに保存

        Args:
            user_input (str): ユーザーからのメッセージ
            max_retry (int): 最大リトライ回数（デフォルト: 3）

        Returns:
            str: エージェントからの応答（ツール使用履歴を含む）

        Raises:
            ValidationError: エージェントが初期化されていない場合

        Example:
            >>> response = await agent.chat("データの概要を教えてください")
            >>> print(response)
            現在のデータセットは...

            ---
            *内部処理（ツール使用履歴）:*
              - **ツール名**: `get_data_overview`
                - **入力**: ``
                - **出力**: `データの概要:...`
        """
        if not self.agent_executor:
            raise ValidationError("エージェントが初期化されていません。initialize()を呼び出してください。")

        # Type narrowing for Pylance
        assert self.memory is not None
        assert self.agent_executor is not None

        logger.info(
            "チャット要求を受信しました",
            session_id=str(self.session_id),
            message=user_input[:100],  # Log first 100 chars
        )

        # Get current snapshot ID and increment for new conversation
        snapshot_id = await self.state.get_snapshot_id()
        snapshot_id += 1

        for attempt in range(max_retry):
            try:
                # Clear memory and reload from DB (camp-backend pattern)
                self.memory.chat_memory.clear()
                await self._load_chat_history()

                # Add current context as system message
                data_overview = await self.state.get_data_overview()
                step_overview = await self.state.get_step_overview()
                current_context = f"""
=== 現在のデータ状況 ===
{data_overview}

=== 現在のステップ状況 ===
{step_overview}
"""
                self.memory.chat_memory.messages.append(SystemMessage(content=current_context))

                # Execute agent with tool tracking
                handler = ToolTrackingHandler()
                response = await self.agent_executor.ainvoke({"input": user_input}, callbacks=[handler])

                # Format tool usage history
                tool_usage_text = ""
                if handler.tool_usage:
                    tool_usage_text = "\n\n---\n*内部処理（ツール使用履歴）:*\n"
                    for usage in handler.tool_usage:
                        tool_name = usage.tool
                        tool_input = usage.input
                        tool_output = usage.output if usage.output is not None else "出力なし"

                        # Truncate long outputs
                        if len(str(tool_output)) > 200:
                            tool_output = str(tool_output)[:200] + "..."

                        tool_usage_text += f"  - **ツール名**: `{tool_name}`\n"
                        tool_usage_text += f"    - **入力**: `{tool_input}`\n"
                        tool_usage_text += f"    - **出力**: `{tool_output}`\n"

                # Get output
                output = response.get("output", "応答がありませんでした")

                # Update chat history in DB
                session = await self.session_repository.get(self.session_id)
                if not session:
                    raise ValidationError("セッションが見つかりません")
                chat_history = session.chat_history or []

                # ChatMessageスキーマを使用してuser入力を追加
                if user_input != "":
                    user_msg = ChatMessage(
                        role="user",
                        content=user_input,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
                    chat_history.append(user_msg.model_dump())

                response_to_store = output + tool_usage_text if tool_usage_text else output

                # ChatMessageスキーマを使用してchat_historyに追加
                chat_msg = ChatMessage(
                    role="assistant",
                    content=response_to_store,
                    timestamp=datetime.now(UTC).isoformat(),
                )
                chat_history.append(chat_msg.model_dump())

                # Save to DB
                await self.session_repository.update(session, chat_history=chat_history)

                logger.info(
                    "チャット応答を生成しました",
                    session_id=str(self.session_id),
                    response_length=len(response_to_store),
                )

                return response_to_store

            except Exception as e:
                # Retry logic (camp-backend pattern)
                if "400" in str(e) and attempt < max_retry - 1:
                    logger.warning(
                        "エラーが発生しました。リトライします",
                        session_id=str(self.session_id),
                        attempt=attempt + 1,
                        max_retry=max_retry,
                        error=str(e),
                    )

                    # Add error message to chat history
                    session = await self.session_repository.get(self.session_id)
                    if not session:
                        raise ValidationError("セッションが見つかりません") from None
                    error_chat_history = session.chat_history or []

                    # ChatMessageスキーマを使用
                    error_msg = ChatMessage(
                        role="assistant",
                        content=f"⚠️ 実行中にエラーが発生しました: {str(e)}。再開します。(試行 {attempt + 1}/{max_retry})",
                        timestamp=datetime.now(UTC).isoformat(),
                    )
                    error_chat_history.append(error_msg.model_dump())
                    await self.session_repository.update(session, chat_history=error_chat_history)

                    continue
                else:
                    # Final failure
                    logger.error(
                        "チャット実行に失敗しました",
                        session_id=str(self.session_id),
                        error=str(e),
                        exc_info=True,
                    )

                    session = await self.session_repository.get(self.session_id)
                    if not session:
                        raise ValidationError("セッションが見つかりません") from None
                    error_chat_history = session.chat_history or []

                    # ChatMessageスキーマを使用
                    if user_input != "":
                        user_msg = ChatMessage(
                            role="user",
                            content=user_input,
                            timestamp=datetime.now(UTC).isoformat(),
                        )
                        error_chat_history.append(user_msg.model_dump())

                    error_msg = ChatMessage(
                        role="assistant",
                        content=f"申し訳ありません。エラーが発生しました: {str(e)}",
                        timestamp=datetime.now(UTC).isoformat(),
                    )
                    error_chat_history.append(error_msg.model_dump())

                    await self.session_repository.update(session, chat_history=error_chat_history)

                    return f"申し訳ありません。エラーが発生しました: {str(e)}"

        # Should not reach here
        return "申し訳ありません。最大リトライ回数に達しました。"

    async def clear_history(self) -> None:
        """会話履歴をクリア。

        ConversationBufferMemoryとDBの両方から会話履歴を削除します。

        Example:
            >>> await agent.clear_history()
        """
        if self.memory:
            self.memory.clear()

        session = await self.session_repository.get(self.session_id)
        if session:
            await self.session_repository.update(session, chat_history=[])

        logger.info("会話履歴をクリアしました", session_id=str(self.session_id))
