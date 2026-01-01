import time
from pathlib import Path

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.integrations.llm import get_llm

from .state import AnalysisState
from .utils.tools import (
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
    ToolTrackingHandler,
)

# システムプロンプトファイルのパス（このファイルからの相対パス）
SYSTEM_PROMPT_PATH = Path(__file__).parent / "utils" / "system_prompt.txt"


class AnalysisAgent:
    def __init__(self, state: AnalysisState, custom_system_prompt: str | None = None):
        """分析エージェントを初期化します。

        Args:
            state: 分析状態オブジェクト
            custom_system_prompt: カスタムシステムプロンプト（デフォルトプロンプトに追加）
        """
        self.state = state
        self.custom_system_prompt = custom_system_prompt
        self.tools = [
            GetDataOverviewTool(state),
            GetStepOverviewTool(state),
            GetDataValueTool(state),
            AddStepTool(state),
            DeleteStepTool(state),
            GetAggregationTool(state),
            GetFilterTool(state),
            GetTransformTool(state),
            GetSummaryTool(state),
            SetAggregationTool(state),
            SetFilterTool(state),
            SetTransformTool(state),
            SetSummaryTool(state),
        ]

        # メモリの初期化
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # システムプロンプトの設定
        with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
            system_message = f.read()

        # カスタムシステムプロンプトがある場合は追加
        if custom_system_prompt:
            system_message = f"{system_message}\n\n## 追加の指示\n{custom_system_prompt}"

        # プロンプトテンプレートを直接定義
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # 新しいAPIでエージェントを作成
        agent = create_tool_calling_agent(get_llm(), self.tools, prompt)
        self.agent = AgentExecutor(agent=agent, tools=self.tools, memory=self.memory, verbose=True)

    def get_current_context(self):
        """現在のデータとステップの状況を取得"""
        data_overview = self.state.get_data_overview()
        step_overview = self.state.get_step_overview()
        context = f"""
=== 現在のデータ状況 ===
{data_overview}

=== 現在のステップ状況 ===
{step_overview}
"""
        return context

    def chat(self, user_input: str, max_retry=3) -> str | None:
        """ユーザーからの入力を処理し、エージェントに応答を求める"""
        for t in range(max_retry):
            try:
                # チャット履歴の初期化（session_stateから)
                self.memory.chat_memory.clear()
                chat_history = self.state.chat_history  # デフォルト値を追加

                # chat_historyがNoneまたは空でない場合のみ処理
                if chat_history:
                    for role, message_content in chat_history:
                        if role == "system":
                            self.memory.chat_memory.messages.append(SystemMessage(content=message_content))
                        elif role == "user":
                            self.memory.chat_memory.messages.append(HumanMessage(content=message_content))
                        elif role == "assistant":
                            self.memory.chat_memory.messages.append(AIMessage(content=message_content))

                handler = ToolTrackingHandler()
                current_context = self.get_current_context()
                self.memory.chat_memory.messages.append(
                    SystemMessage(content=current_context)
                )  # 現在のデータとステップの状況をシステムメッセージとして追加

                response = self.agent.invoke({"input": user_input}, callbacks=[handler])

                # ツール使用履歴を整形
                tool_usage_text = ""
                if handler.tool_usage:
                    tool_usage_text = "\n\n---\n*内部処理（ツール使用履歴）:*\n"
                    for usage in handler.tool_usage:
                        tool_name = usage.get("tool", "unknown")
                        tool_input = usage.get("input", "")
                        tool_output = usage.get("output", "出力なし")

                        if len(str(tool_output)) > 200:
                            tool_output = str(tool_output)[:200] + "..."

                        tool_usage_text += f"  - **ツール名**: `{tool_name}`\n"
                        tool_usage_text += f"    - **入力**: `{tool_input}`\n"
                        tool_usage_text += f"    - **出力**: `{tool_output}`\n"

                # チャット履歴を更新
                output = response.get("output", "応答がありませんでした")

                # chat_historyがNoneの場合は空リストで初期化
                if user_input != "":
                    chat_history.append(("user", user_input))
                response_to_store = output + tool_usage_text if tool_usage_text else output
                chat_history.append(("assistant", response_to_store))

                # session_stateに保存
                self.state.chat_history = chat_history

                return response_to_store
            except Exception as e:
                # if 400 error
                if "400" in str(e) and t < max_retry - 1:
                    time.sleep(2)
                    error_chat_history = self.state.chat_history
                    error_chat_history.append(
                        ("assistant", f"⚠️ 実行中にエラーが発生しました: {str(e)}。再開します。(試行 {t + 1}/{max_retry})")
                    )
                    self.state.chat_history = error_chat_history
                    t += 1
                    continue
                else:
                    error_chat_history = self.state.chat_history
                    if user_input != "":
                        # ユーザー入力が空でない場合のみ追加
                        error_chat_history.append(("user", user_input))
                    error_chat_history.append(("assistant", f"申し訳ありません。エラーが発生しました: {str(e)}"))
                    self.state.chat_history = error_chat_history
                    return f"申し訳ありません。エラーが発生しました: {str(e)}"
        return None
