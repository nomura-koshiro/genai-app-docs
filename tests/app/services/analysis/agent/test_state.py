"""AnalysisStateのテスト。

このテストファイルは、AnalysisStateクラスの各メソッドをテストします。

対応メソッド:
    - set_source_data: データソース設定
    - get_source_data: データソース取得
    - apply: ステップ適用
    - add_step: ステップ追加
    - delete_step: ステップ削除
    - get_summary/set_summary: サマリ設定
    - get_aggregation/set_aggregation: 集計設定
    - get_filter/set_filter: フィルタ設定
    - get_transform/set_transform: 変換設定
    - get_data_overview: データ概要取得
    - get_step_overview: ステップ概要取得
"""

import pandas as pd
import pytest

from app.services.analysis.agent.state import AnalysisState

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
                "category_filter": {"地域": ["日本"]},
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
    return AnalysisState(df, steps, [])


# ================================================================================
# 初期化テスト
# ================================================================================


def test_analysis_state_init_success():
    """[test_state-001] AnalysisStateの初期化成功ケース。"""
    # Arrange
    df = create_test_dataframe()
    steps = []
    chat = []

    # Act
    state = AnalysisState(df, steps, chat)

    # Assert
    assert state.original_df is not None
    assert len(state.original_df) == 6
    assert state.all_steps == []
    assert state.chat_history == []


def test_analysis_state_init_with_steps():
    """[test_state-002] ステップ付きの初期化。"""
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
    chat = [("user", "テストメッセージ")]

    # Act
    state = AnalysisState(df, steps, chat)

    # Assert
    assert len(state.all_steps) == 1
    assert state.all_steps[0]["name"] == "テストフィルタ"
    assert state.chat_history == [("user", "テストメッセージ")]


def test_analysis_state_init_with_invalid_step_type():
    """[test_state-003] 不正なステップタイプでの初期化でエラー。"""
    # Arrange
    df = create_test_dataframe()
    steps = [
        {
            "name": "不正ステップ",
            "type": "invalid_type",
            "data_source": "original",
            "config": {},
        }
    ]

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        AnalysisState(df, steps, [])
    assert "不明なステップタイプ" in str(exc_info.value)


# ================================================================================
# set_source_data / get_source_data テスト
# ================================================================================


def test_set_source_data_success():
    """[test_state-004] set_source_dataの成功ケース。"""
    # Arrange
    state = create_empty_state()
    new_df = pd.DataFrame({"地域": ["中国"], "部門": ["営業"], "科目": ["売上"], "値": [3000]})

    # Act
    state.set_source_data(new_df)

    # Assert
    assert len(state.original_df) == 1
    assert state.original_df.iloc[0]["地域"] == "中国"


def test_set_source_data_invalid_type():
    """[test_state-005] 不正なデータ型でset_source_dataするとエラー。"""
    # Arrange
    state = create_empty_state()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.set_source_data([{"地域": "日本"}])
    assert "pandas DataFrame" in str(exc_info.value)


def test_get_source_data_original():
    """[test_state-006] get_source_dataでオリジナルデータを取得。"""
    # Arrange
    state = create_empty_state()

    # Act
    data = state.get_source_data(None)

    # Assert
    assert len(data) == 6


def test_get_source_data_from_step():
    """[test_state-007] get_source_dataでステップ結果を取得。"""
    # Arrange
    state = create_state_with_filter_step()
    state.apply(0)

    # Act
    state.add_step("ステップ2", "filter", "step_0")

    # ステップ1のデータソースを取得
    data = state.get_source_data(1)

    # Assert
    # ステップ0の結果（日本のみ）がデータソースになる
    assert all(data["地域"] == "日本")


def test_get_source_data_invalid_step_index():
    """[test_state-008] 無効なステップインデックスでエラー。"""
    # Arrange
    state = create_state_with_filter_step()
    state.add_step("ステップ2", "filter", "step_5")  # 存在しないステップ

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.get_source_data(1)
    assert "無効なデータソースインデックス" in str(exc_info.value)


# ================================================================================
# add_step / delete_step テスト
# ================================================================================


@pytest.mark.parametrize(
    "step_name,step_type,expected_config_keys",
    [
        ("フィルタステップ", "filter", ["category_filter", "numeric_filter"]),
        ("集計ステップ", "aggregate", ["group_by_axis", "aggregation_config"]),
        ("サマリステップ", "summary", ["formulas", "chart_config"]),
        ("変換ステップ", "transform", ["transform_config"]),
    ],
    ids=["filter", "aggregate", "summary", "transform"],
)
def test_add_step_success(step_name: str, step_type: str, expected_config_keys: list):
    """[test_state-009] ステップ追加の成功ケース。"""
    # Arrange
    state = create_empty_state()

    # Act
    state.add_step(step_name, step_type, "original")

    # Assert
    assert len(state.all_steps) == 1
    assert state.all_steps[0]["type"] == step_type
    for key in expected_config_keys:
        assert key in state.all_steps[0]["config"]


@pytest.mark.parametrize(
    "step_name,step_type,data_source,expected_error",
    [
        ("不正ステップ", "invalid", "original", "不明なステップタイプ"),
        ("テストステップ", "filter", "invalid_source", "無効なデータソース形式"),
    ],
    ids=["invalid_type", "invalid_data_source"],
)
def test_add_step_error(step_name: str, step_type: str, data_source: str, expected_error: str):
    """[test_state-013] ステップ追加のエラーケース。"""
    # Arrange
    state = create_empty_state()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.add_step(step_name, step_type, data_source)
    assert expected_error in str(exc_info.value)


def test_delete_step_success():
    """[test_state-015] ステップ削除の成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("ステップ1", "filter", "original")
    state.add_step("ステップ2", "filter", "original")

    # Act
    state.delete_step(0)

    # Assert
    assert len(state.all_steps) == 1
    assert state.all_steps[0]["name"] == "ステップ2"


def test_delete_step_invalid_index():
    """[test_state-016] 不正なインデックスでステップ削除するとエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("ステップ1", "filter", "original")

    # Act & Assert
    with pytest.raises(IndexError) as exc_info:
        state.delete_step(5)
    assert "範囲外" in str(exc_info.value)


# ================================================================================
# apply テスト
# ================================================================================


def test_apply_filter_step():
    """[test_state-017] filterステップの適用。"""
    # Arrange
    state = create_state_with_filter_step()

    # Act
    state.apply(0)

    # Assert
    result_data = state.all_steps[0]["result_data"]
    assert result_data is not None
    assert all(result_data["地域"] == "日本")


def test_apply_aggregate_step():
    """[test_state-018] aggregateステップの適用。"""
    # Arrange
    state = create_empty_state()
    state.add_step("集計ステップ", "aggregate", "original")
    state.set_aggregation(
        0,
        {
            "group_by_axis": ["地域"],
            "aggregation_config": [{"name": "売上合計", "subject": "売上", "method": "sum"}],
        },
    )

    # Assert
    result_data = state.all_steps[0]["result_data"]
    assert result_data is not None
    assert len(result_data) == 2  # 日本、アメリカの2グループ


def test_apply_invalid_step_type():
    """[test_state-019] 不正なステップタイプでapplyするとエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("テストステップ", "filter", "original")
    state.all_steps[0]["type"] = "invalid"

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.apply(0)
    assert "不明なステップタイプ" in str(exc_info.value)


# ================================================================================
# get_filter / set_filter テスト
# ================================================================================


def test_get_filter_success():
    """[test_state-020] get_filterの成功ケース。"""
    # Arrange
    state = create_state_with_filter_step()

    # Act
    filter_config = state.get_filter(0)

    # Assert
    assert "category_filter" in filter_config
    assert "numeric_filter" in filter_config
    assert "table_filter" in filter_config


@pytest.mark.parametrize(
    "filter_config,assertion_fn",
    [
        (
            {
                "category_filter": {"地域": ["日本"]},
                "numeric_filter": {},
                "table_filter": {},
            },
            lambda data: all(data["地域"] == "日本"),
        ),
        (
            {
                "category_filter": {},
                "numeric_filter": {
                    "column": "値",
                    "filter_type": "range",
                    "enable_min": True,
                    "min_value": 1000,
                    "include_min": True,
                    "enable_max": False,
                    "max_value": 0,
                    "include_max": True,
                },
                "table_filter": {},
            },
            lambda data: all(data["値"] >= 1000),
        ),
        (
            {
                "category_filter": {},
                "numeric_filter": {
                    "column": "値",
                    "filter_type": "topk",
                    "k_value": 3,
                    "ascending": False,
                },
                "table_filter": {},
            },
            lambda data: len(data) == 3,
        ),
    ],
    ids=["category", "numeric_range", "numeric_topk"],
)
def test_set_filter_success(filter_config: dict, assertion_fn):
    """[test_state-021] フィルタ設定の成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("フィルタステップ", "filter", "original")

    # Act
    state.set_filter(0, filter_config)

    # Assert
    result_data = state.all_steps[0]["result_data"]
    assert assertion_fn(result_data)


def test_set_filter_on_non_filter_step():
    """[test_state-024] filter以外のステップにフィルタ設定するとエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("集計ステップ", "aggregate", "original")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.set_filter(0, {"category_filter": {}, "numeric_filter": {}, "table_filter": {}})
    assert "filterタイプ" in str(exc_info.value)


def test_set_filter_invalid_column():
    """[test_state-025] 存在しないカラムでフィルタ設定するとエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("フィルタステップ", "filter", "original")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.set_filter(
            0,
            {
                "category_filter": {"存在しないカラム": ["値"]},
                "numeric_filter": {},
                "table_filter": {},
            },
        )
    assert "見つかりません" in str(exc_info.value)


# ================================================================================
# get_aggregation / set_aggregation テスト
# ================================================================================


def test_get_aggregation_success():
    """[test_state-026] get_aggregationの成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("集計ステップ", "aggregate", "original")

    # Act
    agg_config = state.get_aggregation(0)

    # Assert
    assert "group_by_axis" in agg_config
    assert "aggregation_config" in agg_config


def test_set_aggregation_sum_success():
    """[test_state-027] sum集計の成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("集計ステップ", "aggregate", "original")

    # Act
    state.set_aggregation(
        0,
        {
            "group_by_axis": ["地域"],
            "aggregation_config": [{"name": "売上合計", "subject": "売上", "method": "sum"}],
        },
    )

    # Assert
    result_data = state.all_steps[0]["result_data"]
    assert result_data is not None
    assert "売上合計" in result_data["科目"].values


def test_set_aggregation_arithmetic_operation():
    """[test_state-028] 四則演算を含む集計の成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("集計ステップ", "aggregate", "original")

    # Act
    state.set_aggregation(
        0,
        {
            "group_by_axis": ["地域"],
            "aggregation_config": [
                {"name": "売上合計", "subject": "売上", "method": "sum"},
                {"name": "コスト合計", "subject": "コスト", "method": "sum"},
                {"name": "利益", "subject": ["売上合計", "コスト合計"], "method": "-"},
            ],
        },
    )

    # Assert
    result_data = state.all_steps[0]["result_data"]
    assert "利益" in result_data["科目"].values


def test_set_aggregation_on_non_aggregate_step():
    """[test_state-029] aggregate以外のステップに集計設定するとエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("フィルタステップ", "filter", "original")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.set_aggregation(0, {"group_by_axis": [], "aggregation_config": []})
    assert "aggregateタイプ" in str(exc_info.value)


def test_set_aggregation_invalid_subject():
    """[test_state-030] 存在しない科目で集計するとエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("集計ステップ", "aggregate", "original")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.set_aggregation(
            0,
            {
                "group_by_axis": ["地域"],
                "aggregation_config": [{"name": "不正集計", "subject": "存在しない科目", "method": "sum"}],
            },
        )
    assert "見つかりません" in str(exc_info.value)


# ================================================================================
# get_transform / set_transform テスト
# ================================================================================


def test_get_transform_success():
    """[test_state-031] get_transformの成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("変換ステップ", "transform", "original")

    # Act
    transform_config = state.get_transform(0)

    # Assert
    assert "operations" in transform_config


@pytest.mark.parametrize(
    "df_factory,transform_config,expected_column,expected_value",
    [
        (
            create_test_dataframe,
            {
                "operations": [
                    {
                        "operation_type": "add_axis",
                        "target_name": "新しい軸",
                        "calculation": {
                            "type": "constant",
                            "constant_value": 100,
                        },
                    }
                ]
            },
            "新しい軸",
            None,
        ),
        (
            lambda: pd.DataFrame(
                {
                    "数値A": [10, 20, 30],
                    "数値B": [1, 2, 3],
                    "科目": ["売上", "売上", "売上"],
                    "値": [100, 200, 300],
                }
            ),
            {
                "operations": [
                    {
                        "operation_type": "add_axis",
                        "target_name": "計算結果",
                        "calculation": {
                            "type": "formula",
                            "formula_type": "+",
                            "operands": ["数値A", "数値B"],
                            "constant_value": None,
                        },
                    }
                ]
            },
            "計算結果",
            11,
        ),
    ],
    ids=["constant", "formula"],
)
def test_set_transform_add_axis(df_factory, transform_config: dict, expected_column: str, expected_value):
    """[test_state-032] 軸追加（定数/計算式）の成功ケース。"""
    # Arrange
    df = df_factory()
    state = AnalysisState(df, [], [])
    state.add_step("変換ステップ", "transform", "original")

    # Act
    state.set_transform(0, transform_config)

    # Assert
    result_data = state.all_steps[0]["result_data"]
    assert expected_column in result_data.columns
    if expected_value is not None:
        assert result_data.iloc[0][expected_column] == expected_value


def test_set_transform_on_non_transform_step():
    """[test_state-034] transform以外のステップに変換設定するとエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("フィルタステップ", "filter", "original")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.set_transform(0, {"operations": []})
    assert "transformタイプ" in str(exc_info.value)


# ================================================================================
# get_summary / set_summary テスト
# ================================================================================


def test_get_summary_success():
    """[test_state-035] get_summaryの成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("サマリステップ", "summary", "original")

    # Act
    summary_config = state.get_summary(0)

    # Assert
    assert "formulas" in summary_config
    assert "chart_config" in summary_config
    assert "table_config" in summary_config


def test_set_summary_formula_success():
    """[test_state-036] サマリ設定（計算式）の成功ケース。"""
    # Arrange
    state = create_empty_state()
    state.add_step("サマリステップ", "summary", "original")

    # Act
    state.set_summary(
        0,
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
        },
    )

    # Assert
    result_formula = state.all_steps[0].get("result_formula")
    assert result_formula is not None
    assert len(result_formula) == 1
    assert result_formula[0]["name"] == "売上合計"


def test_set_summary_on_non_summary_step():
    """[test_state-037] summary以外のステップにサマリ設定するとエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("フィルタステップ", "filter", "original")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.set_summary(0, {"formulas": [], "chart_config": {}, "table_config": {}})
    assert "summaryタイプ" in str(exc_info.value)


def test_set_summary_invalid_formula_type():
    """[test_state-038] 不正な計算式タイプでエラー。"""
    # Arrange
    state = create_empty_state()
    state.add_step("サマリステップ", "summary", "original")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        state.set_summary(
            0,
            {
                "formulas": [
                    {
                        "target_subject": "売上",
                        "type": "invalid_type",
                        "formula_text": "テスト",
                        "unit": "円",
                        "portion": 1.0,
                    }
                ],
                "chart_config": {},
                "table_config": {},
            },
        )
    assert "サポートされていない計算式タイプ" in str(exc_info.value)


# ================================================================================
# get_data_overview / get_step_overview テスト
# ================================================================================


@pytest.mark.parametrize(
    "state_factory,expected_content",
    [
        (create_empty_state, ["データの概要", "original", "6件"]),
        (lambda: (lambda s: (s.apply(0), s)[1])(create_state_with_filter_step()), ["step_1"]),
    ],
    ids=["empty_state", "with_steps"],
)
def test_get_data_overview(state_factory, expected_content: list):
    """[test_state-039] データ概要取得のテスト。"""
    # Arrange
    state = state_factory()

    # Act
    overview = state.get_data_overview()

    # Assert
    for content in expected_content:
        assert content in overview


def test_get_step_overview_empty():
    """[test_state-041] ステップがない場合の概要。"""
    # Arrange
    state = create_empty_state()

    # Act
    overview = state.get_step_overview()

    # Assert
    assert "作成されていません" in overview


def test_get_step_overview_with_steps():
    """[test_state-042] ステップ概要の取得。"""
    # Arrange
    state = create_state_with_filter_step()

    # Act
    overview = state.get_step_overview()

    # Assert
    assert "Step 0" in overview
    assert "フィルタステップ" in overview
    assert "filter" in overview
