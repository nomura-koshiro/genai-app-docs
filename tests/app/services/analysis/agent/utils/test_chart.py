"""チャートユーティリティのテスト。

このテストファイルは、チャート関連のユーティリティ関数をテストします。

対応関数:
    - check_data_and_config: データと設定のチェック
    - draw_graph: グラフ描画
    - check_scatter/draw_scatter: 散布図
    - check_bar/draw_bar: 棒グラフ
    - check_line/draw_line: 折れ線グラフ
    - check_pie/draw_pie: 円グラフ
    - check_waterfall/draw_waterfall: ウォーターフォール図
    - check_stacked_bar/draw_stacked_bar: 積み上げ棒グラフ
"""

import pandas as pd
import pytest
from plotly import graph_objects as go

from app.services.analysis.agent.utils.chart import (
    check_bar,
    check_data_and_config,
    check_horizontal_bar,
    check_line,
    check_line_and_bar,
    check_pie,
    check_scatter,
    check_stacked_bar,
    check_waterfall,
    draw_bar,
    draw_graph,
    draw_horizontal_bar,
    draw_line,
    draw_line_and_bar,
    draw_pie,
    draw_scatter,
    draw_stacked_bar,
    draw_waterfall,
)

# ================================================================================
# テストデータ準備
# ================================================================================


def create_scatter_data() -> pd.DataFrame:
    """散布図用のテストデータを作成します。"""
    return pd.DataFrame(
        {
            "地域": ["日本", "日本", "アメリカ", "アメリカ", "中国", "中国"],
            "部門": ["営業", "開発", "営業", "開発", "営業", "開発"],
            "科目": ["売上", "利益", "売上", "利益", "売上", "利益"],
            "値": [1000, 100, 1500, 150, 2000, 200],
        }
    )


def create_bar_data() -> pd.DataFrame:
    """棒グラフ用のテストデータを作成します。"""
    return pd.DataFrame(
        {
            "地域": ["日本", "アメリカ", "中国"],
            "部門": ["営業", "営業", "営業"],
            "科目": ["売上", "売上", "売上"],
            "値": [1000, 1500, 2000],
        }
    )


def create_line_data() -> pd.DataFrame:
    """折れ線グラフ用のテストデータを作成します。"""
    return pd.DataFrame(
        {
            "年度": ["2021", "2022", "2023", "2024"],
            "地域": ["日本", "日本", "日本", "日本"],
            "科目": ["売上", "売上", "売上", "売上"],
            "値": [1000, 1200, 1500, 1800],
        }
    )


def create_pie_data() -> pd.DataFrame:
    """円グラフ用のテストデータを作成します。"""
    return pd.DataFrame(
        {
            "地域": ["日本", "アメリカ", "中国"],
            "科目": ["売上", "売上", "売上"],
            "値": [1000, 1500, 2000],
        }
    )


def create_waterfall_data() -> pd.DataFrame:
    """ウォーターフォール図用のテストデータを作成します。"""
    return pd.DataFrame(
        {
            "項目": ["売上", "原価", "営業費", "その他"],
            "科目": ["収益", "費用", "費用", "費用"],
            "値": [1000, -600, -200, -50],
        }
    )


def create_stacked_bar_data() -> pd.DataFrame:
    """積み上げ棒グラフ用のテストデータを作成します。"""
    return pd.DataFrame(
        {
            "年度": ["2023", "2023", "2024", "2024"],
            "部門": ["営業", "開発", "営業", "開発"],
            "科目": ["売上", "売上", "売上", "売上"],
            "値": [1000, 500, 1200, 600],
        }
    )


# ================================================================================
# check_data_and_config テスト
# ================================================================================


def test_check_data_and_config_empty_data():
    """[test_chart-001] 空データでチェック失敗。"""
    # Arrange
    df = pd.DataFrame()
    config = {"graph_type": "bar"}

    # Act
    success, msg = check_data_and_config(df, config)

    # Assert
    assert success is False
    assert "データが空" in msg


def test_check_data_and_config_invalid_config_type():
    """[test_chart-002] 不正な設定型でチェック失敗。"""
    # Arrange
    df = create_bar_data()
    config = "invalid_config"

    # Act
    success, msg = check_data_and_config(df, config)

    # Assert
    assert success is False
    assert "辞書形式" in msg


def test_check_data_and_config_invalid_graph_type():
    """[test_chart-003] 不正なグラフタイプでチェック失敗。"""
    # Arrange
    df = create_bar_data()
    config = {"graph_type": "invalid_type"}

    # Act
    success, msg = check_data_and_config(df, config)

    # Assert
    assert success is False
    assert "graph_type" in msg


def test_check_data_and_config_bar_success():
    """[test_chart-004] 棒グラフの設定チェック成功。"""
    # Arrange
    df = create_bar_data()
    config = {
        "graph_type": "bar",
        "x_axis": "地域",
        "y_axis": "値",
    }

    # Act
    success, msg = check_data_and_config(df, config)

    # Assert
    assert success is True


def test_check_data_and_config_scatter_success():
    """[test_chart-005] 散布図の設定チェック成功。"""
    # Arrange
    df = create_scatter_data()
    config = {
        "graph_type": "scatter",
        "x_subject": "売上",
        "y_subject": "利益",
    }

    # Act
    success, msg = check_data_and_config(df, config)

    # Assert
    assert success is True


# ================================================================================
# draw_graph テスト
# ================================================================================


def test_draw_graph_bar_success():
    """[test_chart-006] 棒グラフ描画の成功ケース。"""
    # Arrange
    df = create_bar_data()
    config = {
        "graph_type": "bar",
        "x_axis": "地域",
        "y_axis": "値",
        "title": "売上グラフ",
    }

    # Act
    fig = draw_graph(df, config)

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


def test_draw_graph_invalid_type():
    """[test_chart-007] 不正なグラフタイプで描画失敗。"""
    # Arrange
    df = create_bar_data()
    config = {
        "graph_type": "invalid",
        "x_axis": "地域",
        "y_axis": "値",
    }

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        draw_graph(df, config)
    assert "存在しないチャートタイプ" in str(exc_info.value)


# ================================================================================
# チェック関数の成功テスト（パラメトライズ）
# ================================================================================


@pytest.mark.parametrize(
    "chart_type,check_func,data_factory,params",
    [
        ("scatter", check_scatter, create_scatter_data, {"x_subject": "売上", "y_subject": "利益", "legend": None}),
        ("bar", check_bar, create_bar_data, {"x_axis": "地域", "y_axis": "値", "legend": None}),
        ("horizontal_bar", check_horizontal_bar, create_bar_data, {"x_axis": "値", "y_axis": "地域", "legend": None}),
        ("line", check_line, create_line_data, {"x_axis": "年度", "y_axis": "値", "legend": None}),
        ("pie", check_pie, create_pie_data, {"values": "値", "names": "地域"}),
        (
            "waterfall",
            check_waterfall,
            lambda: pd.DataFrame({"項目": ["売上", "原価", "営業費"], "値": [1000, 600, 200]}),
            {"x_axis": "項目", "y_axis": "値", "measure_type": "relative", "base_value": 0, "legend": None},
        ),
        ("stacked_bar", check_stacked_bar, create_stacked_bar_data, {"x_axis": "年度", "y_axis": "値", "stack_by": "部門"}),
    ],
    ids=["scatter", "bar", "horizontal_bar", "line", "pie", "waterfall", "stacked_bar"],
)
def test_check_chart_success(chart_type, check_func, data_factory, params):
    """[test_chart-008,013,018,020,024,028,032] 各チャートタイプのチェック成功ケース。"""
    # Arrange
    df = data_factory()

    # Act
    success, msg = check_func(df, **params)

    # Assert
    assert success is True


# ================================================================================
# 散布図テスト
# ================================================================================


def test_check_scatter_same_subjects():
    """[test_chart-009] 同じ科目を指定した場合のエラー。"""
    # Arrange
    df = create_scatter_data()

    # Act
    success, msg = check_scatter(df, "売上", "売上", None)

    # Assert
    assert success is False
    assert "同じ科目" in msg


def test_check_scatter_missing_subject():
    """[test_chart-010] 存在しない科目を指定した場合のエラー。"""
    # Arrange
    df = create_scatter_data()

    # Act
    success, msg = check_scatter(df, "売上", "存在しない科目", None)

    # Assert
    assert success is False
    assert "存在しません" in msg


# ================================================================================
# 描画関数の成功テスト（パラメトライズ）
# ================================================================================


@pytest.mark.parametrize(
    "chart_type,draw_func,data_factory,params,title",
    [
        (
            "scatter",
            draw_scatter,
            create_scatter_data,
            {"x_subject": "売上", "y_subject": "利益", "legend": None},
            "散布図テスト",
        ),
        ("bar", draw_bar, create_bar_data, {"x_axis": "地域", "y_axis": "値", "legend": None}, "棒グラフテスト"),
        (
            "horizontal_bar",
            draw_horizontal_bar,
            create_bar_data,
            {"x_axis": "値", "y_axis": "地域", "legend": None},
            "横棒グラフテスト",
        ),
        ("line", draw_line, create_line_data, {"x_axis": "年度", "y_axis": "値", "legend": None}, "折れ線グラフテスト"),
        ("pie", draw_pie, create_pie_data, {"values": "値", "names": "地域"}, "円グラフテスト"),
        (
            "waterfall",
            draw_waterfall,
            lambda: pd.DataFrame({"項目": ["売上", "原価", "営業費"], "値": [1000, 600, 200]}),
            {
                "x_axis": "項目",
                "y_axis": "値",
                "measure_type": "relative",
                "base_value": 0,
                "legend": None,
                "show_total": False,
                "total_label": None,
            },
            "ウォーターフォールテスト",
        ),
        (
            "stacked_bar",
            draw_stacked_bar,
            create_stacked_bar_data,
            {"x_axis": "年度", "y_axis": "値", "stack_by": "部門"},
            "積み上げ棒グラフテスト",
        ),
    ],
    ids=["scatter", "bar", "horizontal_bar", "line", "pie", "waterfall", "stacked_bar"],
)
def test_draw_chart_success(chart_type, draw_func, data_factory, params, title):
    """[test_chart-011,016,019,022,027,030,035] 各チャートタイプの描画成功ケース。"""
    # Arrange
    df = data_factory()

    # Act
    fig = draw_func(df, **params, title=title)

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


# ================================================================================
# 凡例付き描画テスト（パラメトライズ）
# ================================================================================


@pytest.mark.parametrize(
    "chart_type,draw_func,data_factory,legend_column,title",
    [
        ("scatter", draw_scatter, create_scatter_data, "地域", "散布図テスト"),
        (
            "bar",
            draw_bar,
            lambda: pd.DataFrame(
                {
                    "地域": ["日本", "日本", "アメリカ", "アメリカ"],
                    "部門": ["営業", "開発", "営業", "開発"],
                    "値": [1000, 500, 1500, 700],
                }
            ),
            "部門",
            "棒グラフテスト",
        ),
        (
            "line",
            draw_line,
            lambda: pd.DataFrame(
                {
                    "年度": ["2022", "2023", "2022", "2023"],
                    "地域": ["日本", "日本", "アメリカ", "アメリカ"],
                    "値": [1000, 1200, 1500, 1800],
                }
            ),
            "地域",
            "折れ線グラフテスト",
        ),
    ],
    ids=["scatter", "bar", "line"],
)
def test_draw_chart_with_legend(chart_type, draw_func, data_factory, legend_column, title):
    """[test_chart-012,017,023] 凡例付き描画の成功ケース。"""
    # Arrange
    df = data_factory()

    # Act
    if chart_type == "scatter":
        fig = draw_func(df, "売上", "利益", legend_column, title)
    else:  # bar or line
        fig = draw_func(df, df.columns[0], "値", legend_column, title)

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


# ================================================================================
# エラーケーステスト（パラメトライズ）
# ================================================================================


@pytest.mark.parametrize(
    "test_id,check_func,data_factory,params,expected_error_msg",
    [
        (
            "014",
            check_bar,
            create_bar_data,
            {"x_axis": "存在しない列", "y_axis": "値", "legend": None},
            "存在しません",
        ),
        (
            "021",
            check_line,
            lambda: pd.DataFrame({"年度": ["2023"], "値": [1000]}),
            {"x_axis": "年度", "y_axis": "値", "legend": None},
            "2個以上",
        ),
        (
            "025",
            check_pie,
            lambda: pd.DataFrame({"地域": ["日本", "アメリカ", "中国"], "値": [1000, -500, 2000]}),
            {"values": "値", "names": "地域"},
            "負の値",
        ),
        (
            "026",
            check_pie,
            lambda: pd.DataFrame({"地域": ["日本"], "値": [1000]}),
            {"values": "値", "names": "地域"},
            "2つ以上",
        ),
        (
            "033",
            check_stacked_bar,
            lambda: pd.DataFrame({"年度": ["2023", "2024"], "部門": ["営業", "営業"], "値": [1000, 1200]}),
            {"x_axis": "年度", "y_axis": "値", "stack_by": "部門"},
            "2つ以上",
        ),
        (
            "034",
            check_stacked_bar,
            lambda: pd.DataFrame({"年度": ["2023", "2023"], "部門": ["営業", "開発"], "値": [1000, -500]}),
            {"x_axis": "年度", "y_axis": "値", "stack_by": "部門"},
            "負の値",
        ),
    ],
    ids=["bar_missing_column", "line_single_point", "pie_negative", "pie_single_category", "stacked_single_stack", "stacked_negative"],
)
def test_check_chart_errors(test_id, check_func, data_factory, params, expected_error_msg):
    """[test_chart-014,021,025,026,033,034] 各チャートタイプのエラーケース。"""
    # Arrange
    df = data_factory()

    # Act
    success, msg = check_func(df, **params)

    # Assert
    assert success is False
    assert expected_error_msg in msg


# ================================================================================
# 棒グラフ個別テスト
# ================================================================================


def test_check_bar_non_numeric_y():
    """[test_chart-015] Y軸が数値でない場合のエラー。"""
    # Arrange
    df = pd.DataFrame(
        {
            "地域": ["日本", "アメリカ"],
            "値": ["数値じゃない", "abc"],
        }
    )

    # Act
    success, msg = check_bar(df, "地域", "値", None)

    # Assert
    assert success is False
    assert "数値" in msg


# ================================================================================
# ウォーターフォール図個別テスト
# ================================================================================


def test_check_waterfall_invalid_measure_type():
    """[test_chart-029] 不正な測定タイプでエラー。"""
    # Arrange
    df = create_waterfall_data()

    # Act
    success, msg = check_waterfall(df, "項目", "値", "invalid", 0, None)

    # Assert
    assert success is False
    assert "測定タイプ" in msg


def test_draw_waterfall_with_total():
    """[test_chart-031] 合計付きウォーターフォール図描画の成功ケース。"""
    # Arrange
    df = pd.DataFrame(
        {
            "項目": ["売上", "原価"],
            "値": [1000, -600],
        }
    )

    # Act
    fig = draw_waterfall(df, "項目", "値", "relative", 0, None, True, "合計", "ウォーターフォールテスト")

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


# ================================================================================
# 折れ線+棒グラフテスト
# ================================================================================


def test_check_line_and_bar_success():
    """[test_chart-036] 折れ線+棒グラフチェックの成功ケース。"""
    # Arrange
    df = pd.DataFrame(
        {
            "年度": ["2022", "2022", "2023", "2023"],
            "科目": ["売上", "利益", "売上", "利益"],
            "値": [1000, 100, 1200, 120],
        }
    )

    # Act
    success, msg = check_line_and_bar(df, "年度", "売上", "bar", "利益", "line", None)

    # Assert
    assert success is True


def test_check_line_and_bar_same_subjects():
    """[test_chart-037] 同じ科目を指定した場合のエラー。"""
    # Arrange
    df = create_scatter_data()

    # Act
    success, msg = check_line_and_bar(df, "地域", "売上", "bar", "売上", "line", None)

    # Assert
    assert success is False
    assert "同じ科目" in msg


def test_draw_line_and_bar_success():
    """[test_chart-038] 折れ線+棒グラフ描画の成功ケース。"""
    # Arrange
    df = pd.DataFrame(
        {
            "年度": ["2022", "2022", "2023", "2023"],
            "科目": ["売上", "利益", "売上", "利益"],
            "値": [1000, 100, 1200, 120],
        }
    )

    # Act
    fig = draw_line_and_bar(df, "年度", "売上", "bar", "利益", "line", None, "混合グラフテスト")

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)
