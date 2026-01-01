"""分析ツールクラスのテスト。

このテストファイルは、各Toolクラスをテストします。

対応クラス:
    - ToolTrackingHandler: ツール使用追跡
    - GetDataOverviewTool: データ概要取得
    - GetStepOverviewTool: ステップ概要取得
    - AddStepTool: ステップ追加
    - DeleteStepTool: ステップ削除
    - GetFilterTool / SetFilterTool: フィルタ取得・設定
    - GetAggregationTool / SetAggregationTool: 集計取得・設定
    - GetTransformTool / SetTransformTool: 変換取得・設定
    - GetSummaryTool / SetSummaryTool: サマリ取得・設定
    - GetDataValueTool: データ値取得
"""

import json

import pandas as pd

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
    ToolTrackingHandler,
)

# ================================================================================
# テストデータ準備
# ================================================================================


def create_test_dataframe() -> pd.DataFrame:
    """テスト用のDataFrameを作成します。"""
    return pd.DataFrame(
        {
            "地域": ["日本", "日本", "アメリカ", "アメリカ", "日本", "アメリカ"],
            "部門": ["営業", "開発", "営業", "開発", "営業", "開発"],
            "科目": ["売上", "売上", "売上", "売上", "コスト", "コスト"],
            "値": [1000, 2000, 1500, 2500, 500, 800],
        }
    )


def create_empty_state() -> AnalysisState:
    """空のAnalysisStateを作成します。"""
    return AnalysisState(create_test_dataframe(), [], [])


def create_state_with_filter_step() -> AnalysisState:
    """フィルタステップを持つAnalysisStateを作成します。"""
    df = create_test_dataframe()
    steps = [
        {
            "name": "フィルタステップ",
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
    state.apply(0)
    return state


def create_state_with_aggregate_step() -> AnalysisState:
    """集計ステップを持つAnalysisStateを作成します。"""
    df = create_test_dataframe()
    steps = [
        {
            "name": "集計ステップ",
            "type": "aggregate",
            "data_source": "original",
            "config": {
                "group_by_axis": ["地域"],
                "aggregation_config": [{"name": "売上合計", "subject": "売上", "method": "sum"}],
            },
        }
    ]
    state = AnalysisState(df, steps, [])
    state.apply(0)
    return state


def create_state_with_summary_step() -> AnalysisState:
    """サマリステップを持つAnalysisStateを作成します。"""
    df = create_test_dataframe()
    steps = [
        {
            "name": "サマリステップ",
            "type": "summary",
            "data_source": "original",
            "config": {
                "formulas": [],
                "chart_config": {},
                "table_config": {},
            },
        }
    ]
    state = AnalysisState(df, steps, [])
    state.apply(0)
    return state


def create_state_with_transform_step() -> AnalysisState:
    """変換ステップを持つAnalysisStateを作成します。"""
    df = create_test_dataframe()
    steps = [
        {
            "name": "変換ステップ",
            "type": "transform",
            "data_source": "original",
            "config": {
                "transform_config": {},
                "operations": [],
            },
        }
    ]
    state = AnalysisState(df, steps, [])
    state.apply(0)
    return state


# ================================================================================
# ToolTrackingHandler テスト
# ================================================================================


def test_tool_tracking_handler_on_tool_start():
    """[test_tools-001] ツール開始時の追跡。"""
    # Arrange
    handler = ToolTrackingHandler()

    # Act
    handler.on_tool_start(
        serialized={"name": "test_tool"},
        input_str="test input",
    )

    # Assert
    assert len(handler.tool_usage) == 1
    assert handler.tool_usage[0]["tool"] == "test_tool"
    assert handler.tool_usage[0]["input"] == "test input"


def test_tool_tracking_handler_on_tool_end():
    """[test_tools-002] ツール終了時の追跡。"""
    # Arrange
    handler = ToolTrackingHandler()
    handler.on_tool_start(serialized={"name": "test_tool"}, input_str="input")

    # Act
    handler.on_tool_end(output="test output")

    # Assert
    assert handler.tool_usage[0]["output"] == "test output"


def test_tool_tracking_handler_on_tool_end_empty():
    """[test_tools-003] ツールが開始されていない状態での終了。"""
    # Arrange
    handler = ToolTrackingHandler()

    # Act
    handler.on_tool_end(output="test output")

    # Assert
    assert len(handler.tool_usage) == 0


# ================================================================================
# GetDataOverviewTool テスト
# ================================================================================


def test_get_data_overview_tool_success():
    """[test_tools-004] データ概要取得の成功ケース。"""
    # Arrange
    state = create_empty_state()
    tool = GetDataOverviewTool(analysis_state=state)

    # Act
    result = tool._run()

    # Assert
    assert "データの概要" in result
    assert "original" in result


def test_get_data_overview_tool_with_steps():
    """[test_tools-005] ステップ付きでのデータ概要取得。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetDataOverviewTool(analysis_state=state)

    # Act
    result = tool._run()

    # Assert
    assert "step_1" in result


# ================================================================================
# GetStepOverviewTool テスト
# ================================================================================


def test_get_step_overview_tool_success():
    """[test_tools-006] ステップ概要取得の成功ケース。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetStepOverviewTool(analysis_state=state)

    # Act
    result = tool._run()

    # Assert
    assert "Step 0" in result
    assert "フィルタステップ" in result


def test_get_step_overview_tool_no_steps():
    """[test_tools-007] ステップがない場合の概要取得。"""
    # Arrange
    state = create_empty_state()
    tool = GetStepOverviewTool(analysis_state=state)

    # Act
    result = tool._run()

    # Assert
    assert "作成されていません" in result


# ================================================================================
# AddStepTool テスト
# ================================================================================


def test_add_step_tool_filter_success():
    """[test_tools-008] filterステップ追加の成功ケース。"""
    # Arrange
    state = create_empty_state()
    tool = AddStepTool(analysis_state=state)

    # Act
    result = tool._run("テストフィルタ, filter, original")

    # Assert
    assert "追加しました" in result
    assert len(state.all_steps) == 1


def test_add_step_tool_aggregate_success():
    """[test_tools-009] aggregateステップ追加の成功ケース。"""
    # Arrange
    state = create_empty_state()
    tool = AddStepTool(analysis_state=state)

    # Act
    result = tool._run("集計, aggregate, original")

    # Assert
    assert "追加しました" in result
    assert state.all_steps[0]["type"] == "aggregate"


def test_add_step_tool_summary_success():
    """[test_tools-010] summaryステップ追加の成功ケース。"""
    # Arrange
    state = create_empty_state()
    tool = AddStepTool(analysis_state=state)

    # Act
    result = tool._run("サマリ, summary, original")

    # Assert
    assert "追加しました" in result
    assert state.all_steps[0]["type"] == "summary"


def test_add_step_tool_transform_success():
    """[test_tools-011] transformステップ追加の成功ケース。"""
    # Arrange
    state = create_empty_state()
    tool = AddStepTool(analysis_state=state)

    # Act
    result = tool._run("変換, transform, original")

    # Assert
    assert "追加しました" in result
    assert state.all_steps[0]["type"] == "transform"


def test_add_step_tool_invalid_type():
    """[test_tools-012] 不正なステップタイプでエラー。"""
    # Arrange
    state = create_empty_state()
    tool = AddStepTool(analysis_state=state)

    # Act
    result = tool._run("テスト, invalid, original")

    # Assert
    assert "実行失敗" in result
    assert "不正です" in result


def test_add_step_tool_invalid_format():
    """[test_tools-013] 不正な入力形式でエラー。"""
    # Arrange
    state = create_empty_state()
    tool = AddStepTool(analysis_state=state)

    # Act
    result = tool._run("テスト")

    # Assert
    assert "実行失敗" in result
    assert "入力形式" in result


# ================================================================================
# DeleteStepTool テスト
# ================================================================================


def test_delete_step_tool_success():
    """[test_tools-014] ステップ削除の成功ケース。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = DeleteStepTool(analysis_state=state)

    # Act
    result = tool._run("0")

    # Assert
    assert "削除しました" in result
    assert len(state.all_steps) == 0


def test_delete_step_tool_invalid_index():
    """[test_tools-015] 不正なインデックスでエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = DeleteStepTool(analysis_state=state)

    # Act
    result = tool._run("99")

    # Assert
    assert "実行失敗" in result
    assert "範囲外" in result


def test_delete_step_tool_non_numeric():
    """[test_tools-016] 非数値入力でエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = DeleteStepTool(analysis_state=state)

    # Act
    result = tool._run("abc")

    # Assert
    assert "実行失敗" in result
    assert "数値" in result


def test_delete_step_tool_empty_input():
    """[test_tools-017] 空入力でエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = DeleteStepTool(analysis_state=state)

    # Act
    result = tool._run("")

    # Assert
    assert "実行失敗" in result


# ================================================================================
# GetFilterTool / SetFilterTool テスト
# ================================================================================


def test_get_filter_tool_success():
    """[test_tools-018] フィルタ取得の成功ケース。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetFilterTool(analysis_state=state)

    # Act
    result = tool._run("0")

    # Assert
    assert "フィルタ設定" in result


def test_get_filter_tool_invalid_step_type():
    """[test_tools-019] filter以外のステップでエラー。"""
    # Arrange
    state = create_state_with_aggregate_step()
    tool = GetFilterTool(analysis_state=state)

    # Act
    result = tool._run("0")

    # Assert
    assert "実行失敗" in result
    assert "フィルタステップではありません" in result


def test_set_filter_tool_success():
    """[test_tools-020] フィルタ設定の成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("フィルタ", "filter", "original")
    tool = SetFilterTool(analysis_state=state)

    filter_config = json.dumps(
        {
            "category_filter": {"地域": ["日本"]},
            "numeric_filter": {},
            "table_filter": {},
        }
    )

    # Act
    result = tool._run(f"0, {filter_config}")

    # Assert
    assert "適用しました" in result


def test_set_filter_tool_invalid_json():
    """[test_tools-021] 不正なJSONでエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("フィルタ", "filter", "original")
    tool = SetFilterTool(analysis_state=state)

    # Act
    result = tool._run("0, {invalid json}")

    # Assert
    assert "JSON形式が不正" in result


def test_set_filter_tool_invalid_step_type():
    """[test_tools-022] filter以外のステップへのフィルタ設定でエラー。"""
    # Arrange
    state = create_state_with_aggregate_step()
    tool = SetFilterTool(analysis_state=state)

    # Act
    result = tool._run('0, {"category_filter": {}}')

    # Assert
    assert "実行失敗" in result


# ================================================================================
# GetAggregationTool / SetAggregationTool テスト
# ================================================================================


def test_get_aggregation_tool_success():
    """[test_tools-023] 集計設定取得の成功ケース。"""
    # Arrange
    state = create_state_with_aggregate_step()
    tool = GetAggregationTool(analysis_state=state)

    # Act
    result = tool._run("0")

    # Assert
    assert "集計設定" in result


def test_get_aggregation_tool_invalid_step_type():
    """[test_tools-024] aggregate以外のステップでエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetAggregationTool(analysis_state=state)

    # Act
    result = tool._run("0")

    # Assert
    assert "実行失敗" in result
    assert "集計ステップではありません" in result


def test_set_aggregation_tool_success():
    """[test_tools-025] 集計設定の成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("集計", "aggregate", "original")
    tool = SetAggregationTool(analysis_state=state)

    agg_config = json.dumps(
        {
            "group_by_axis": ["地域"],
            "aggregation_config": [{"name": "売上合計", "subject": "売上", "method": "sum"}],
        }
    )

    # Act
    result = tool._run(f"0, {agg_config}")

    # Assert
    assert "適用しました" in result


def test_set_aggregation_tool_invalid_json():
    """[test_tools-026] 不正なJSONでエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("集計", "aggregate", "original")
    tool = SetAggregationTool(analysis_state=state)

    # Act
    result = tool._run("0, {invalid}")

    # Assert
    assert "JSON形式が不正" in result


# ================================================================================
# GetTransformTool / SetTransformTool テスト
# ================================================================================


def test_get_transform_tool_success():
    """[test_tools-027] 変換設定取得の成功ケース。"""
    # Arrange
    state = create_state_with_transform_step()
    tool = GetTransformTool(analysis_state=state)

    # Act
    result = tool._run("0")

    # Assert
    assert "変換設定" in result


def test_get_transform_tool_invalid_step_type():
    """[test_tools-028] transform以外のステップでエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetTransformTool(analysis_state=state)

    # Act
    result = tool._run("0")

    # Assert
    assert "実行失敗" in result
    assert "変換ステップではありません" in result


def test_set_transform_tool_success():
    """[test_tools-029] 変換設定の成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("変換", "transform", "original")
    tool = SetTransformTool(analysis_state=state)

    transform_config = json.dumps(
        {
            "operations": [
                {
                    "operation_type": "add_axis",
                    "target_name": "新しい軸",
                    "calculation": {"type": "constant", "constant_value": 100},
                }
            ]
        }
    )

    # Act
    result = tool._run(f"0, {transform_config}")

    # Assert
    assert "適用しました" in result


def test_set_transform_tool_invalid_step_type():
    """[test_tools-030] transform以外のステップへの変換設定でエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = SetTransformTool(analysis_state=state)

    # Act
    result = tool._run('0, {"operations": []}')

    # Assert
    assert "実行失敗" in result


# ================================================================================
# GetSummaryTool / SetSummaryTool テスト
# ================================================================================


def test_get_summary_tool_success():
    """[test_tools-031] サマリ設定取得の成功ケース。"""
    # Arrange
    state = create_state_with_summary_step()
    tool = GetSummaryTool(analysis_state=state)

    # Act
    result = tool._run("0")

    # Assert
    assert "サマリ設定" in result


def test_get_summary_tool_invalid_step_type():
    """[test_tools-032] summary以外のステップでエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetSummaryTool(analysis_state=state)

    # Act
    result = tool._run("0")

    # Assert
    assert "実行失敗" in result


def test_set_summary_tool_success():
    """[test_tools-033] サマリ設定の成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("サマリ", "summary", "original")
    tool = SetSummaryTool(analysis_state=state)

    summary_config = json.dumps(
        {
            "formulas": [
                {
                    "target_subject": "売上",
                    "type": "sum",
                    "formula_text": "売上合計",
                    "unit": "円",
                    "portion": 1.0,
                }
            ],
            "chart_config": {},
            "table_config": {},
        }
    )

    # Act
    result = tool._run(f"0, {summary_config}")

    # Assert
    assert "サマリ設定" in result or "計算式" in result


def test_set_summary_tool_invalid_step_type():
    """[test_tools-034] summary以外のステップへのサマリ設定でエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = SetSummaryTool(analysis_state=state)

    # Act
    result = tool._run('0, {"formulas": []}')

    # Assert
    assert "実行失敗" in result


# ================================================================================
# GetDataValueTool テスト
# ================================================================================


def test_get_data_value_tool_success():
    """[test_tools-035] データ値取得の成功ケース。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetDataValueTool(analysis_state=state)

    filter_json = json.dumps({"科目": "売上", "地域": "日本", "部門": "営業"})

    # Act
    result = tool._run(f"0, {filter_json}")

    # Assert
    assert "ステップ0" in result


def test_get_data_value_tool_invalid_column():
    """[test_tools-036] 存在しないカラムでエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetDataValueTool(analysis_state=state)

    filter_json = json.dumps({"存在しないカラム": "値"})

    # Act
    result = tool._run(f"0, {filter_json}")

    # Assert
    assert "存在しません" in result


def test_get_data_value_tool_invalid_value():
    """[test_tools-037] 存在しない値でエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetDataValueTool(analysis_state=state)

    filter_json = json.dumps({"地域": "存在しない値"})

    # Act
    result = tool._run(f"0, {filter_json}")

    # Assert
    assert "実行失敗" in result


def test_get_data_value_tool_invalid_json():
    """[test_tools-038] 不正なJSONでエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetDataValueTool(analysis_state=state)

    # Act
    result = tool._run("0, {invalid}")

    # Assert
    assert "JSON形式が不正" in result


def test_get_data_value_tool_invalid_index():
    """[test_tools-039] 不正なステップインデックスでエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetDataValueTool(analysis_state=state)

    filter_json = json.dumps({"地域": "日本"})

    # Act
    result = tool._run(f"99, {filter_json}")

    # Assert
    assert "実行失敗" in result
    assert "範囲外" in result


def test_get_data_value_tool_multiple_results():
    """[test_tools-040] 複数結果がある場合。"""
    # Arrange
    state = create_state_with_filter_step()
    tool = GetDataValueTool(analysis_state=state)

    filter_json = json.dumps({"地域": "日本"})

    # Act
    result = tool._run(f"0, {filter_json}")

    # Assert
    # 複数結果または該当する値が見つかることを確認
    assert "ステップ0" in result
