"""分析チャット管理サービス。

このモジュールは、AIエージェントとのチャット機能、チャット履歴管理などの
チャット関連のビジネスロジックを提供します。

主な機能:
    - AIエージェントとのチャット
    - チャット履歴の取得・管理
    - チャット履歴のクリア
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import async_timeout, measure_performance
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.repositories.analysis import AnalysisSessionRepository
from app.schemas.analysis import ChatMessage
from app.schemas.analysis.session import ChatRequest, ChatResponse

logger = get_logger(__name__)


class AnalysisChatService:
    """分析チャット管理サービスクラス。

    このサービスは、AIエージェントとのチャット、履歴管理などの
    チャット関連の操作を提供します。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
        session_repository: AnalysisSessionRepositoryインスタンス
    """

    def __init__(self, db: AsyncSession):
        """分析チャットサービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.session_repository = AnalysisSessionRepository(db)

    @measure_performance
    @async_timeout(seconds=600)  # 10分タイムアウト
    async def execute_chat(
        self,
        session_id: uuid.UUID,
        chat_request: ChatRequest,
    ) -> ChatResponse:
        """AIエージェントとチャットを実行します（準備中）。

        このメソッドは、ユーザーのメッセージを受け取り、AIエージェントに処理を依頼します。
        Phase 3.1で完全実装予定です。

        Args:
            session_id (uuid.UUID): セッションのUUID
            chat_request (ChatRequest): チャットリクエスト
                - message: ユーザーメッセージ

        Returns:
            ChatResponse: チャットレスポンス
                - message: アシスタントの応答メッセージ
                - snapshot_id: スナップショットID

        Raises:
            NotFoundError: セッションが存在しない場合
            ValidationError: チャット処理でエラーが発生した場合

        Example:
            >>> chat_request = ChatRequest(
            ...     message="東京と大阪の売上を表示してください"
            ... )
            >>> response = await chat_service.execute_chat(
            ...     session_id=session_id,
            ...     chat_request=chat_request
            ... )
            >>> print(f"Assistant: {response.message}")
            Assistant: 東京と大阪の売上データをフィルタリングしました

        Note:
            - Phase 3.1でAIエージェント統合予定
            - @async_timeoutデコレータにより10分でタイムアウトします
            - 現在はプレースホルダー実装です
        """
        logger.info(
            "チャット実行中",
            session_id=str(session_id),
            message_length=len(chat_request.message),
            action="execute_chat",
        )

        try:
            # セッションの存在確認
            session = await self.session_repository.get(session_id)
            if not session:
                logger.warning(
                    "セッションが見つかりません",
                    session_id=str(session_id),
                )
                raise NotFoundError(
                    "セッションが見つかりません",
                    details={"session_id": str(session_id)},
                )

            # TODO: Phase 3.1でAIエージェント統合
            # 現在はプレースホルダー実装
            response_message = "AIエージェント機能は現在準備中です。Phase 3.1で実装予定です。"

            # チャット履歴を更新
            snapshot_id = len(session.chat_history) // 2  # 仮のスナップショットID
            chat_entry = ChatMessage(
                role="assistant",
                content=response_message,
                timestamp=datetime.now(UTC).isoformat(),
            )

            await self.session_repository.update_chat_history(session_id, chat_entry)

            logger.info(
                "チャット実行完了",
                session_id=str(session_id),
                snapshot_id=snapshot_id,
            )

            return ChatResponse(
                message=response_message,
                snapshot_id=snapshot_id,
                steps_added=0,
                steps_modified=0,
                analysis_result=None,
            )

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(
                "チャット実行中に予期しないエラーが発生しました",
                session_id=str(session_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def chat(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        message: str,
    ) -> str:
        """分析エージェントとチャット。

        このメソッドは、ユーザーのメッセージを受け取り、AIエージェントに処理を依頼します。
        エージェントは自然言語でデータ分析タスクを実行し、適切な応答を返します。

        処理フロー:
            1. セッションの存在確認
            2. ユーザーのアクセス権限確認
            3. AnalysisAgentの初期化
            4. メッセージ処理と応答生成
            5. 結果のロギング

        Args:
            session_id (uuid.UUID): 分析セッションのUUID
            user_id (uuid.UUID): ユーザーのUUID
            message (str): ユーザーからのメッセージ
                例: "データの概要を教えてください"
                例: "東京と大阪の売上を表示してください"

        Returns:
            str: エージェントからの応答（ツール使用履歴を含む）
                - AI生成された応答メッセージ
                - 内部で使用されたツールの履歴（オプション）

        Raises:
            NotFoundError: 以下の場合に発生
                - セッションが存在しない
            AuthorizationError: 以下の場合に発生
                - ユーザーがこのセッションにアクセスする権限がない
            ValidationError: 以下の場合に発生
                - チャット処理中にエラーが発生した
                - エージェントの初期化に失敗した

        Example:
            >>> response = await chat_service.chat(
            ...     session_id=session_id,
            ...     user_id=user_id,
            ...     message="データの概要を教えてください"
            ... )
            >>> print(response)
            現在のデータセットは...

            ---
            *内部処理（ツール使用履歴）:*
              - **ツール名**: `get_data_overview`
                - **入力**: ``
                - **出力**: `データの概要:...`

        Note:
            - Phase 3.4で完全実装されました
            - エージェントはLangChainのAgentExecutorを使用します
            - 会話履歴は自動的にDBに保存されます
            - @measure_performanceデコレータによりパフォーマンスが記録されます
        """
        logger.info(
            "チャット要求を受信しました",
            session_id=str(session_id),
            user_id=str(user_id),
            message=message[:100],  # Log first 100 chars
            action="chat",
        )

        try:
            # 1. Verify session exists
            session = await self.session_repository.get(session_id)
            if not session:
                logger.warning(
                    "セッションが見つかりません",
                    session_id=str(session_id),
                )
                raise NotFoundError(
                    f"セッション {session_id} が見つかりません",
                    details={"session_id": str(session_id)},
                )

            # 2. Verify user has access
            if session.created_by != user_id:
                logger.warning(
                    "ユーザーがセッションにアクセスする権限がありません",
                    session_id=str(session_id),
                    user_id=str(user_id),
                    session_creator=str(session.created_by),
                )
                raise AuthorizationError(
                    "このセッションにアクセスする権限がありません",
                    details={
                        "session_id": str(session_id),
                        "user_id": str(user_id),
                    },
                )

            # 3. Initialize agent
            from app.services.analysis.agent.core import AnalysisAgent

            agent = AnalysisAgent(self.db, session_id)
            await agent.initialize()

            # 4. Process chat
            response = await agent.chat(message)

            logger.info(
                "チャット応答を生成しました",
                session_id=str(session_id),
                response_length=len(response),
            )

            return response

        except (NotFoundError, AuthorizationError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "チャット処理中に予期しないエラーが発生しました",
                session_id=str(session_id),
                error=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"チャット処理に失敗しました: {e}",
                details={"session_id": str(session_id), "error": str(e)},
            ) from e

    @measure_performance
    async def get_chat_history(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ChatMessage]:
        """チャット履歴を取得。

        このメソッドは、指定されたセッションのチャット履歴を取得します。
        セッションの存在とユーザーのアクセス権限を確認した後、
        chat_historyフィールドから履歴を返します。

        Args:
            session_id (uuid.UUID): 分析セッションのUUID
            user_id (uuid.UUID): ユーザーのUUID

        Returns:
            list[ChatMessage]: チャット履歴のリスト
                各要素は ChatMessage スキーマ:
                - role: Literal["user", "assistant"] - メッセージの送信者
                - content: str - メッセージ本文
                - timestamp: str - タイムスタンプ（ISO 8601形式）

        Raises:
            NotFoundError: 以下の場合に発生
                - セッションが存在しない
            AuthorizationError: 以下の場合に発生
                - ユーザーがこのセッションにアクセスする権限がない

        Example:
            >>> history = await chat_service.get_chat_history(
            ...     session_id=session_id,
            ...     user_id=user_id
            ... )
            >>> for entry in history:
            ...     print(f"{entry.role}: {entry.content}")
            user: データの概要を教えてください
            assistant: 現在のデータセットは...

        Note:
            - 履歴が空の場合は空リストを返します
            - @measure_performanceデコレータによりパフォーマンスが記録されます
            - DB保存形式（dict）から ChatMessage スキーマに変換して返します
        """
        logger.info(
            "チャット履歴を取得中",
            session_id=str(session_id),
            user_id=str(user_id),
            action="get_chat_history",
        )

        # Verify session exists
        session = await self.session_repository.get(session_id)
        if not session:
            logger.warning(
                "セッションが見つかりません",
                session_id=str(session_id),
            )
            raise NotFoundError(
                f"セッション {session_id} が見つかりません",
                details={"session_id": str(session_id)},
            )

        # Verify user has access
        if session.created_by != user_id:
            logger.warning(
                "ユーザーがセッションにアクセスする権限がありません",
                session_id=str(session_id),
                user_id=str(user_id),
                session_creator=str(session.created_by),
            )
            raise AuthorizationError(
                "このセッションにアクセスする権限がありません",
                details={
                    "session_id": str(session_id),
                    "user_id": str(user_id),
                },
            )

        # Return chat history (dict → ChatMessage変換)
        chat_history_dicts = session.chat_history or []
        chat_history = [ChatMessage.model_validate(entry) for entry in chat_history_dicts]

        logger.info(
            "チャット履歴を正常に取得しました",
            session_id=str(session_id),
            history_count=len(chat_history),
        )

        return chat_history

    @measure_performance
    async def clear_chat_history(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """チャット履歴をクリア。

        このメソッドは、指定されたセッションのチャット履歴を完全にクリアします。
        セッションの存在とユーザーのアクセス権限を確認した後、
        AnalysisAgentを使用して履歴を削除します。

        処理内容:
            1. セッションの存在確認
            2. ユーザーのアクセス権限確認
            3. AnalysisAgentの初期化
            4. エージェント経由で履歴をクリア
            5. クリア完了のロギング

        Args:
            session_id (uuid.UUID): 分析セッションのUUID
            user_id (uuid.UUID): ユーザーのUUID

        Raises:
            NotFoundError: 以下の場合に発生
                - セッションが存在しない
            AuthorizationError: 以下の場合に発生
                - ユーザーがこのセッションにアクセスする権限がない

        Example:
            >>> await chat_service.clear_chat_history(
            ...     session_id=session_id,
            ...     user_id=user_id
            ... )
            >>> print("Chat history cleared")
            Chat history cleared

        Note:
            - この操作は元に戻せません
            - ConversationBufferMemoryとDBの両方から履歴が削除されます
            - @measure_performanceデコレータによりパフォーマンスが記録されます
        """
        logger.info(
            "チャット履歴をクリア中",
            session_id=str(session_id),
            user_id=str(user_id),
            action="clear_chat_history",
        )

        # Verify session exists
        session = await self.session_repository.get(session_id)
        if not session:
            logger.warning(
                "セッションが見つかりません",
                session_id=str(session_id),
            )
            raise NotFoundError(
                f"セッション {session_id} が見つかりません",
                details={"session_id": str(session_id)},
            )

        # Verify user has access
        if session.created_by != user_id:
            logger.warning(
                "ユーザーがセッションにアクセスする権限がありません",
                session_id=str(session_id),
                user_id=str(user_id),
                session_creator=str(session.created_by),
            )
            raise AuthorizationError(
                "このセッションにアクセスする権限がありません",
                details={
                    "session_id": str(session_id),
                    "user_id": str(user_id),
                },
            )

        # Clear chat history via agent
        from app.services.analysis.agent.core import AnalysisAgent

        agent = AnalysisAgent(self.db, session_id)
        await agent.initialize()
        await agent.clear_history()

        logger.info(
            "チャット履歴を正常にクリアしました",
            session_id=str(session_id),
        )
