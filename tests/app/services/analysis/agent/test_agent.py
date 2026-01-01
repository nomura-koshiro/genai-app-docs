"""AnalysisAgentのテスト。

このテストファイルは、AnalysisAgentクラスの各メソッドをテストします。

対応メソッド:
    - chat: チャット実行
    - _initialize_llm: LLM初期化
    - _create_agent: エージェント作成
"""

from unittest.mock import MagicMock, patch

import pandas as pd

from app.services.analysis.agent.agent import AnalysisAgent
from app.services.analysis.agent.state import AnalysisState

# ================================================================================
# テストデータ準備
# ================================================================================


def create_test_dataframe() -> pd.DataFrame:
    """テスト用のDataFrameを作成します。"""
    return pd.DataFrame(
        {
            "地域": ["日本", "日本", "アメリカ", "アメリカ"],
            "部門": ["営業", "開発", "営業", "開発"],
            "科目": ["売上", "売上", "売上", "売上"],
            "値": [1000, 2000, 1500, 2500],
        }
    )


def create_test_state() -> AnalysisState:
    """テスト用のAnalysisStateを作成します。"""
    return AnalysisState(create_test_dataframe(), [], [])


# ================================================================================
# 初期化テスト
# ================================================================================


def test_analysis_agent_init_success():
    """[test_agent-001] AnalysisAgentの初期化成功ケース。"""
    # Arrange
    state = create_test_state()

    # Act
    agent = AnalysisAgent(state)

    # Assert
    assert agent.state is not None
    assert agent.state == state


def test_analysis_agent_init_with_state_containing_steps():
    """[test_agent-002] ステップを持つ状態での初期化。"""
    # Arrange
    df = create_test_dataframe()
    steps = [
        {
            "name": "テストフィルタ",
            "type": "filter",
            "data_source": "original",
            "config": {
                "category_filter": {},
                "numeric_filter": {
                    "column": "値",
                    "filter_type": "range",
                    "enable_min": False,
                    "min_value": 0.0,
                    "include_min": True,
                    "enable_max": False,
                    "max_value": 100.0,
                    "include_max": True,
                },
                "table_filter": {
                    "table_df": None,
                    "key_columns": [],
                    "exclude_mode": True,
                    "enable": False,
                },
            },
        }
    ]
    state = AnalysisState(df, steps, [])

    # Act
    agent = AnalysisAgent(state)

    # Assert
    assert len(agent.state.all_steps) == 1


# ================================================================================
# チャット実行テスト
# ================================================================================


@patch("app.services.analysis.agent.agent.AzureChatOpenAI")
def test_chat_success(mock_azure_chat):
    """[test_agent-003] チャット実行の成功ケース。"""
    # Arrange
    state = create_test_state()
    agent = AnalysisAgent(state)

    # LLMのモック設定
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value=MagicMock(content="テスト応答"))
    mock_azure_chat.return_value = mock_llm

    # Act
    with patch.object(agent, "_create_agent", return_value=MagicMock(invoke=MagicMock(return_value={"output": "テスト応答"}))):
        result = agent.chat("テストメッセージ")

    # Assert
    assert result is not None


@patch("app.services.analysis.agent.agent.AzureChatOpenAI")
def test_chat_updates_history(mock_azure_chat):
    """[test_agent-004] チャット実行で履歴が更新される。"""
    # Arrange
    state = create_test_state()
    agent = AnalysisAgent(state)

    # LLMのモック設定
    mock_llm = MagicMock()
    mock_azure_chat.return_value = mock_llm

    # Act
    with patch.object(agent, "_create_agent") as mock_create_agent:
        mock_agent = MagicMock()
        mock_agent.invoke = MagicMock(return_value={"output": "応答メッセージ"})
        mock_create_agent.return_value = mock_agent

        agent.chat("ユーザーメッセージ")

    # Assert
    # チャット履歴が更新されていることを確認
    assert len(agent.state.chat_history) >= 1


@patch("app.services.analysis.agent.agent.AzureChatOpenAI")
def test_chat_with_empty_message(mock_azure_chat):
    """[test_agent-005] 空メッセージでのチャット。"""
    # Arrange
    state = create_test_state()
    agent = AnalysisAgent(state)

    mock_llm = MagicMock()
    mock_azure_chat.return_value = mock_llm

    # Act
    with patch.object(agent, "_create_agent") as mock_create_agent:
        mock_agent = MagicMock()
        mock_agent.invoke = MagicMock(return_value={"output": "応答"})
        mock_create_agent.return_value = mock_agent

        result = agent.chat("")

    # Assert
    assert result is not None


# ================================================================================
# 状態管理テスト
# ================================================================================


def test_agent_state_modification():
    """[test_agent-008] エージェント経由での状態変更。"""
    # Arrange
    state = create_test_state()
    agent = AnalysisAgent(state)

    # Act
    agent.state.add_step("新しいステップ", "filter", "original")

    # Assert
    assert len(agent.state.all_steps) == 1
    assert agent.state.all_steps[0]["name"] == "新しいステップ"


def test_agent_preserves_original_data():
    """[test_agent-009] エージェントがオリジナルデータを保持。"""
    # Arrange
    original_df = create_test_dataframe()
    state = AnalysisState(original_df.copy(), [], [])
    agent = AnalysisAgent(state)

    # Act
    agent.state.add_step("フィルタ", "filter", "original")
    agent.state.set_filter(
        0,
        {
            "category_filter": {"地域": ["日本"]},
            "numeric_filter": {},
            "table_filter": {},
        },
    )

    # Assert
    # オリジナルデータは変更されていないこと
    assert len(agent.state.original_df) == 4
