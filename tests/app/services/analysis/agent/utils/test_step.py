"""ステップユーティリティのテスト。

このテストファイルは、ステップ関連のユーティリティ関数をテストします。

対応関数:
    - apply_formula: 計算式適用
    - apply_aggregation: 集計適用
    - apply_filters: フィルタ適用
    - apply_transform: 変換適用
    - filter_data: データフィルタリング
"""

import numpy as np
import pandas as pd
import pytest

from app.services.analysis.agent.utils.step import (
    apply_aggregation,
    apply_filters,
    apply_formula,
    apply_transform,
    filter_data,
    init_category_filter,
    init_formula,
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


def create_step_data_for_filter() -> dict:
    """フィルタステップ用のステップデータを作成します。"""
    return {
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
        "result_data": None,
    }


def create_step_data_for_aggregation() -> dict:
    """集計ステップ用のステップデータを作成します。"""
    return {
        "config": {
            "group_by_axis": ["地域"],
            "aggregation_config": [],
        },
        "result_data": None,
    }


def create_step_data_for_summary() -> dict:
    """サマリステップ用のステップデータを作成します。"""
    return {
        "config": {
            "formulas": [],
            "chart_config": {},
        },
        "result_data": None,
        "result_formula": None,
    }


def create_step_data_for_transform() -> dict:
    """変換ステップ用のステップデータを作成します。"""
    return {
        "config": {
            "transform_config": {
                "operations": [],
            },
        },
        "result_data": None,
    }


# ================================================================================
# init_formula テスト
# ================================================================================


def test_init_formula_default_values():
    """[test_step-001] init_formulaのデフォルト値。"""
    # Act
    formula = init_formula()

    # Assert
    assert formula["type"] == "sum"
    assert formula["target_subject"] is None
    assert formula["unit"] == "円"
    assert formula["portion"] == 1.0
    assert formula["result_value"] is None
    assert formula["formula_text"] == "計算式未設定"


# ================================================================================
# apply_formula テスト
# ================================================================================


def test_apply_formula_sum_success():
    """[test_step-002] sum計算式の適用成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_summary()
    step_data["config"]["formulas"] = [
        {
            "type": "sum",
            "target_subject": "売上",
            "formula_text": "売上合計",
            "unit": "円",
            "portion": 1.0,
        }
    ]

    # Act
    apply_formula(df, step_data)

    # Assert
    assert step_data["result_formula"] is not None
    assert len(step_data["result_formula"]) == 1
    assert step_data["result_formula"][0]["name"] == "売上合計"
    assert step_data["result_formula"][0]["value"] == 7000  # 1000+2000+1500+2500


def test_apply_formula_mean_success():
    """[test_step-003] mean計算式の適用成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_summary()
    step_data["config"]["formulas"] = [
        {
            "type": "mean",
            "target_subject": "売上",
            "formula_text": "売上平均",
            "unit": "円",
            "portion": 1.0,
        }
    ]

    # Act
    apply_formula(df, step_data)

    # Assert
    assert step_data["result_formula"] is not None
    assert step_data["result_formula"][0]["value"] == 1750  # (1000+2000+1500+2500)/4


def test_apply_formula_with_portion():
    """[test_step-004] portion係数付き計算式の適用成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_summary()
    step_data["config"]["formulas"] = [
        {
            "type": "sum",
            "target_subject": "売上",
            "formula_text": "売上合計(半分)",
            "unit": "円",
            "portion": 0.5,
        }
    ]

    # Act
    apply_formula(df, step_data)

    # Assert
    assert step_data["result_formula"][0]["value"] == 3500  # 7000 * 0.5


def test_apply_formula_arithmetic_operation():
    """[test_step-005] 四則演算の適用成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_summary()
    step_data["config"]["formulas"] = [
        {
            "type": "sum",
            "target_subject": "売上",
            "formula_text": "売上合計",
            "unit": "円",
            "portion": 1.0,
            "result_value": 7000,
        },
        {
            "type": "sum",
            "target_subject": "コスト",
            "formula_text": "コスト合計",
            "unit": "円",
            "portion": 1.0,
            "result_value": 1300,
        },
        {
            "type": "-",
            "target_subject": ["売上合計", "コスト合計"],
            "formula_text": "利益",
            "unit": "円",
            "portion": 1.0,
        },
    ]

    # Act
    apply_formula(df, step_data)

    # Assert
    assert len(step_data["result_formula"]) == 3
    assert step_data["result_formula"][2]["name"] == "利益"
    assert step_data["result_formula"][2]["value"] == 5700  # 7000 - 1300


def test_apply_formula_empty_config():
    """[test_step-006] 空の計算式設定での処理。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_summary()
    step_data["config"]["formulas"] = []

    # Act
    apply_formula(df, step_data)

    # Assert
    assert step_data.get("result_formula") is None


# ================================================================================
# apply_aggregation テスト
# ================================================================================


def test_apply_aggregation_sum_success():
    """[test_step-007] sum集計の適用成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_aggregation()
    step_data["config"]["aggregation_config"] = [{"name": "売上合計", "subject": "売上", "method": "sum"}]

    # Act
    apply_aggregation(df, step_data)

    # Assert
    assert step_data["result_data"] is not None
    assert "売上合計" in step_data["result_data"]["科目"].values
    assert len(step_data["result_data"]) == 2  # 日本とアメリカ


def test_apply_aggregation_mean_success():
    """[test_step-008] mean集計の適用成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_aggregation()
    step_data["config"]["aggregation_config"] = [{"name": "売上平均", "subject": "売上", "method": "mean"}]

    # Act
    apply_aggregation(df, step_data)

    # Assert
    result_df = step_data["result_data"]
    japan_mean = result_df[result_df["地域"] == "日本"]["値"].values[0]
    assert japan_mean == 1500  # (1000+2000)/2


def test_apply_aggregation_arithmetic():
    """[test_step-009] 四則演算を含む集計の成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_aggregation()
    step_data["config"]["aggregation_config"] = [
        {"name": "売上合計", "subject": "売上", "method": "sum"},
        {"name": "コスト合計", "subject": "コスト", "method": "sum"},
        {"name": "利益", "subject": ["売上合計", "コスト合計"], "method": "-"},
    ]

    # Act
    apply_aggregation(df, step_data)

    # Assert
    result_df = step_data["result_data"]
    assert "利益" in result_df["科目"].values


def test_apply_aggregation_empty_group_by():
    """[test_step-010] 集計軸なしでエラー。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_aggregation()
    step_data["config"]["group_by_axis"] = []
    step_data["config"]["aggregation_config"] = [{"name": "売上合計", "subject": "売上", "method": "sum"}]

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        apply_aggregation(df, step_data)
    assert "集計軸が指定されていません" in str(exc_info.value)


def test_apply_aggregation_empty_config():
    """[test_step-011] 集計設定なしでエラー。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_aggregation()
    step_data["config"]["aggregation_config"] = []

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        apply_aggregation(df, step_data)
    assert "集計設定が指定されていません" in str(exc_info.value)


def test_apply_aggregation_missing_column():
    """[test_step-012] 存在しない列でエラー。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_aggregation()
    step_data["config"]["group_by_axis"] = ["存在しない列"]
    step_data["config"]["aggregation_config"] = [{"name": "売上合計", "subject": "売上", "method": "sum"}]

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        apply_aggregation(df, step_data)
    assert "存在しません" in str(exc_info.value)


# ================================================================================
# apply_filters テスト
# ================================================================================


def test_apply_filters_category_success():
    """[test_step-013] カテゴリフィルタの適用成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_filter()
    step_data["config"]["category_filter"] = {"地域": ["日本"]}

    # Act
    apply_filters(df, step_data)

    # Assert
    assert all(step_data["result_data"]["地域"] == "日本")


def test_apply_filters_numeric_range_success():
    """[test_step-014] 数値範囲フィルタの適用成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_filter()
    step_data["config"]["numeric_filter"] = {
        "column": "値",
        "filter_type": "range",
        "enable_min": True,
        "min_value": 1000,
        "include_min": True,
        "enable_max": False,
        "max_value": 0,
        "include_max": True,
    }

    # Act
    apply_filters(df, step_data)

    # Assert
    assert all(step_data["result_data"]["値"] >= 1000)


def test_apply_filters_numeric_topk_success():
    """[test_step-015] TopKフィルタの適用成功。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_filter()
    step_data["config"]["numeric_filter"] = {
        "column": "値",
        "filter_type": "topk",
        "k_value": 3,
        "ascending": False,
    }

    # Act
    apply_filters(df, step_data)

    # Assert
    assert len(step_data["result_data"]) == 3


def test_apply_filters_combined():
    """[test_step-016] カテゴリと数値フィルタの組み合わせ。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_filter()
    step_data["config"]["category_filter"] = {"科目": ["売上"]}
    step_data["config"]["numeric_filter"] = {
        "column": "値",
        "filter_type": "range",
        "enable_min": True,
        "min_value": 1500,
        "include_min": True,
        "enable_max": False,
        "max_value": 0,
        "include_max": True,
    }

    # Act
    apply_filters(df, step_data)

    # Assert
    result = step_data["result_data"]
    assert all(result["科目"] == "売上")
    assert all(result["値"] >= 1500)


# ================================================================================
# filter_data テスト
# ================================================================================


def test_filter_data_category_single_value():
    """[test_step-017] 単一値でのカテゴリフィルタ。"""
    # Arrange
    df = create_test_dataframe()

    # Act
    result = filter_data(df, category_filter={"地域": "日本"})

    # Assert
    assert all(result["地域"] == "日本")


def test_filter_data_category_multiple_values():
    """[test_step-018] 複数値でのカテゴリフィルタ。"""
    # Arrange
    df = create_test_dataframe()

    # Act
    result = filter_data(df, category_filter={"地域": ["日本", "アメリカ"]})

    # Assert
    assert len(result) == 6  # 全データ


def test_filter_data_invalid_column():
    """[test_step-019] 存在しない列でエラー。"""
    # Arrange
    df = create_test_dataframe()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        filter_data(df, category_filter={"存在しない列": ["値"]})
    assert "見つかりません" in str(exc_info.value)


def test_filter_data_numeric_range():
    """[test_step-020] 数値範囲フィルタ。"""
    # Arrange
    df = create_test_dataframe()
    numeric_filter = {
        "column": "値",
        "filter_type": "range",
        "enable_min": True,
        "min_value": 1000,
        "include_min": True,
        "enable_max": True,
        "max_value": 2000,
        "include_max": True,
    }

    # Act
    result = filter_data(df, numeric_filter=numeric_filter)

    # Assert
    assert all((result["値"] >= 1000) & (result["値"] <= 2000))


def test_filter_data_numeric_topk():
    """[test_step-021] TopKフィルタ。"""
    # Arrange
    df = create_test_dataframe()
    numeric_filter = {
        "column": "値",
        "filter_type": "topk",
        "k_value": 2,
        "ascending": False,
    }

    # Act
    result = filter_data(df, numeric_filter=numeric_filter)

    # Assert
    assert len(result) == 2


def test_filter_data_numeric_percentage():
    """[test_step-022] パーセンテージフィルタ。"""
    # Arrange
    df = create_test_dataframe()
    numeric_filter = {
        "column": "値",
        "filter_type": "percentage",
        "min_percentile": 25,
        "max_percentile": 75,
    }

    # Act
    result = filter_data(df, numeric_filter=numeric_filter)

    # Assert
    assert len(result) > 0


def test_filter_data_table_filter_exclude():
    """[test_step-023] テーブルフィルタ(除外モード)。"""
    # Arrange
    df = create_test_dataframe()
    exclude_df = pd.DataFrame({"地域": ["日本"]})
    table_filter = [
        {"key_columns": ["地域"], "exclude_mode": True},
        exclude_df,
    ]

    # Act
    result = filter_data(df, table_filter=table_filter)

    # Assert
    assert all(result["地域"] != "日本")


def test_filter_data_table_filter_include():
    """[test_step-024] テーブルフィルタ(包含モード)。"""
    # Arrange
    df = create_test_dataframe()
    include_df = pd.DataFrame({"地域": ["日本"]})
    table_filter = [
        {"key_columns": ["地域"], "exclude_mode": False},
        include_df,
    ]

    # Act
    result = filter_data(df, table_filter=table_filter)

    # Assert
    assert all(result["地域"] == "日本")


# ================================================================================
# apply_transform テスト
# ================================================================================


def test_apply_transform_add_axis_constant():
    """[test_step-025] 定数値で軸追加。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_transform()
    step_data["config"]["transform_config"]["operations"] = [
        {
            "operation_type": "add_axis",
            "target_name": "新しい軸",
            "calculation": {"type": "constant", "constant_value": 100},
        }
    ]

    # Act
    apply_transform(df, step_data)

    # Assert
    assert "新しい軸" in step_data["result_data"].columns
    assert all(step_data["result_data"]["新しい軸"] == 100)


def test_apply_transform_add_axis_copy():
    """[test_step-026] コピーで軸追加。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_transform()
    step_data["config"]["transform_config"]["operations"] = [
        {
            "operation_type": "add_axis",
            "target_name": "地域コピー",
            "calculation": {"type": "copy", "copy_from": "地域"},
        }
    ]

    # Act
    apply_transform(df, step_data)

    # Assert
    assert "地域コピー" in step_data["result_data"].columns
    assert all(step_data["result_data"]["地域コピー"] == step_data["result_data"]["地域"])


def test_apply_transform_add_axis_formula():
    """[test_step-027] 計算式で軸追加。"""
    # Arrange
    df = pd.DataFrame(
        {
            "数値A": [10, 20, 30],
            "数値B": [1, 2, 3],
            "科目": ["売上", "売上", "売上"],
            "値": [100, 200, 300],
        }
    )
    step_data = create_step_data_for_transform()
    step_data["config"]["transform_config"]["operations"] = [
        {
            "operation_type": "add_axis",
            "target_name": "計算結果",
            "calculation": {
                "type": "formula",
                "formula_type": "+",
                "operands": ["数値A", "数値B"],
            },
        }
    ]

    # Act
    apply_transform(df, step_data)

    # Assert
    assert "計算結果" in step_data["result_data"].columns
    assert step_data["result_data"].iloc[0]["計算結果"] == 11  # 10 + 1


def test_apply_transform_modify_axis():
    """[test_step-028] 既存軸の変更。"""
    # Arrange
    df = pd.DataFrame(
        {
            "数値": [10, 20, 30],
            "科目": ["売上", "売上", "売上"],
            "値": [100, 200, 300],
        }
    )
    step_data = create_step_data_for_transform()
    step_data["config"]["transform_config"]["operations"] = [
        {
            "operation_type": "modify_axis",
            "target_name": "数値",
            "calculation": {"type": "constant", "constant_value": 999},
        }
    ]

    # Act
    apply_transform(df, step_data)

    # Assert
    assert all(step_data["result_data"]["数値"] == 999)


def test_apply_transform_empty_operations():
    """[test_step-029] 空のoperationsの場合。"""
    # Arrange
    df = create_test_dataframe()
    step_data = create_step_data_for_transform()
    step_data["config"]["transform_config"]["operations"] = []

    # Act
    apply_transform(df, step_data)

    # Assert
    assert step_data["result_data"] is not None
    assert len(step_data["result_data"]) == len(df)


def test_apply_transform_empty_data():
    """[test_step-030] 空データの場合。"""
    # Arrange
    df = pd.DataFrame()
    step_data = create_step_data_for_transform()
    step_data["config"]["transform_config"]["operations"] = [
        {
            "operation_type": "add_axis",
            "target_name": "新しい軸",
            "calculation": {"type": "constant", "constant_value": 100},
        }
    ]

    # Act
    apply_transform(df, step_data)

    # Assert
    assert step_data["result_data"] is None or step_data["result_data"].empty


# ================================================================================
# init_category_filter テスト
# ================================================================================


def test_init_category_filter_success():
    """[test_step-031] カテゴリフィルタ初期化の成功。"""
    # Arrange
    input_axis = [
        ("地域", ["日本", "アメリカ"]),
        ("部門", ["営業", "開発"]),
    ]

    # Act
    result = init_category_filter(input_axis)

    # Assert
    assert "地域" in result
    assert "部門" in result
    assert result["地域"] == ["日本", "アメリカ"]
    assert result["部門"] == ["営業", "開発"]


def test_init_category_filter_numpy_types():
    """[test_step-032] numpy型の変換。"""
    # Arrange
    input_axis = [
        ("数値列", [np.int64(1), np.int64(2), np.int64(3)]),
    ]

    # Act
    result = init_category_filter(input_axis)

    # Assert
    assert all(isinstance(v, int) for v in result["数値列"])
