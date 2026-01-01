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
# 散布図テスト
# ================================================================================


def test_check_scatter_success():
    """[test_chart-008] 散布図チェックの成功ケース。"""
    # Arrange
    df = create_scatter_data()

    # Act
    success, msg = check_scatter(df, "売上", "利益", None)

    # Assert
    assert success is True


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


def test_draw_scatter_success():
    """[test_chart-011] 散布図描画の成功ケース。"""
    # Arrange
    df = create_scatter_data()

    # Act
    fig = draw_scatter(df, "売上", "利益", None, "散布図テスト")

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


def test_draw_scatter_with_legend():
    """[test_chart-012] 凡例付き散布図描画の成功ケース。"""
    # Arrange
    df = create_scatter_data()

    # Act
    fig = draw_scatter(df, "売上", "利益", "地域", "散布図テスト")

    # Assert
    assert fig is not None


# ================================================================================
# 棒グラフテスト
# ================================================================================


def test_check_bar_success():
    """[test_chart-013] 棒グラフチェックの成功ケース。"""
    # Arrange
    df = create_bar_data()

    # Act
    success, msg = check_bar(df, "地域", "値", None)

    # Assert
    assert success is True


def test_check_bar_missing_column():
    """[test_chart-014] 存在しない列を指定した場合のエラー。"""
    # Arrange
    df = create_bar_data()

    # Act
    success, msg = check_bar(df, "存在しない列", "値", None)

    # Assert
    assert success is False
    assert "存在しません" in msg


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


def test_draw_bar_success():
    """[test_chart-016] 棒グラフ描画の成功ケース。"""
    # Arrange
    df = create_bar_data()

    # Act
    fig = draw_bar(df, "地域", "値", None, "棒グラフテスト")

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


def test_draw_bar_with_legend():
    """[test_chart-017] 凡例付き棒グラフ描画の成功ケース。"""
    # Arrange
    df = pd.DataFrame(
        {
            "地域": ["日本", "日本", "アメリカ", "アメリカ"],
            "部門": ["営業", "開発", "営業", "開発"],
            "値": [1000, 500, 1500, 700],
        }
    )

    # Act
    fig = draw_bar(df, "地域", "値", "部門", "棒グラフテスト")

    # Assert
    assert fig is not None


# ================================================================================
# 横棒グラフテスト
# ================================================================================


def test_check_horizontal_bar_success():
    """[test_chart-018] 横棒グラフチェックの成功ケース。"""
    # Arrange
    df = create_bar_data()

    # Act
    success, msg = check_horizontal_bar(df, "値", "地域", None)

    # Assert
    assert success is True


def test_draw_horizontal_bar_success():
    """[test_chart-019] 横棒グラフ描画の成功ケース。"""
    # Arrange
    df = create_bar_data()

    # Act
    fig = draw_horizontal_bar(df, "値", "地域", None, "横棒グラフテスト")

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


# ================================================================================
# 折れ線グラフテスト
# ================================================================================


def test_check_line_success():
    """[test_chart-020] 折れ線グラフチェックの成功ケース。"""
    # Arrange
    df = create_line_data()

    # Act
    success, msg = check_line(df, "年度", "値", None)

    # Assert
    assert success is True


def test_check_line_single_point():
    """[test_chart-021] データポイントが1個の場合のエラー。"""
    # Arrange
    df = pd.DataFrame(
        {
            "年度": ["2023"],
            "値": [1000],
        }
    )

    # Act
    success, msg = check_line(df, "年度", "値", None)

    # Assert
    assert success is False
    assert "2個以上" in msg


def test_draw_line_success():
    """[test_chart-022] 折れ線グラフ描画の成功ケース。"""
    # Arrange
    df = create_line_data()

    # Act
    fig = draw_line(df, "年度", "値", None, "折れ線グラフテスト")

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


def test_draw_line_with_legend():
    """[test_chart-023] 凡例付き折れ線グラフ描画の成功ケース。"""
    # Arrange
    df = pd.DataFrame(
        {
            "年度": ["2022", "2023", "2022", "2023"],
            "地域": ["日本", "日本", "アメリカ", "アメリカ"],
            "値": [1000, 1200, 1500, 1800],
        }
    )

    # Act
    fig = draw_line(df, "年度", "値", "地域", "折れ線グラフテスト")

    # Assert
    assert fig is not None


# ================================================================================
# 円グラフテスト
# ================================================================================


def test_check_pie_success():
    """[test_chart-024] 円グラフチェックの成功ケース。"""
    # Arrange
    df = create_pie_data()

    # Act
    success, msg = check_pie(df, "値", "地域")

    # Assert
    assert success is True


def test_check_pie_negative_values():
    """[test_chart-025] 負の値がある場合のエラー。"""
    # Arrange
    df = pd.DataFrame(
        {
            "地域": ["日本", "アメリカ", "中国"],
            "値": [1000, -500, 2000],
        }
    )

    # Act
    success, msg = check_pie(df, "値", "地域")

    # Assert
    assert success is False
    assert "負の値" in msg


def test_check_pie_single_category():
    """[test_chart-026] カテゴリが1つの場合のエラー。"""
    # Arrange
    df = pd.DataFrame(
        {
            "地域": ["日本"],
            "値": [1000],
        }
    )

    # Act
    success, msg = check_pie(df, "値", "地域")

    # Assert
    assert success is False
    assert "2つ以上" in msg


def test_draw_pie_success():
    """[test_chart-027] 円グラフ描画の成功ケース。"""
    # Arrange
    df = create_pie_data()

    # Act
    fig = draw_pie(df, "値", "地域", "円グラフテスト")

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


# ================================================================================
# ウォーターフォール図テスト
# ================================================================================


def test_check_waterfall_success():
    """[test_chart-028] ウォーターフォール図チェックの成功ケース。"""
    # Arrange
    df = pd.DataFrame(
        {
            "項目": ["売上", "原価", "営業費"],
            "値": [1000, 600, 200],
        }
    )

    # Act
    success, msg = check_waterfall(df, "項目", "値", "relative", 0, None)

    # Assert
    assert success is True


def test_check_waterfall_invalid_measure_type():
    """[test_chart-029] 不正な測定タイプでエラー。"""
    # Arrange
    df = create_waterfall_data()

    # Act
    success, msg = check_waterfall(df, "項目", "値", "invalid", 0, None)

    # Assert
    assert success is False
    assert "測定タイプ" in msg


def test_draw_waterfall_success():
    """[test_chart-030] ウォーターフォール図描画の成功ケース。"""
    # Arrange
    df = pd.DataFrame(
        {
            "項目": ["売上", "原価", "営業費"],
            "値": [1000, 600, 200],
        }
    )

    # Act
    fig = draw_waterfall(df, "項目", "値", "relative", 0, None, False, None, "ウォーターフォールテスト")

    # Assert
    assert fig is not None
    assert isinstance(fig, go.Figure)


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


# ================================================================================
# 積み上げ棒グラフテスト
# ================================================================================


def test_check_stacked_bar_success():
    """[test_chart-032] 積み上げ棒グラフチェックの成功ケース。"""
    # Arrange
    df = create_stacked_bar_data()

    # Act
    success, msg = check_stacked_bar(df, "年度", "値", "部門")

    # Assert
    assert success is True


def test_check_stacked_bar_single_stack():
    """[test_chart-033] スタック要素が1つの場合のエラー。"""
    # Arrange
    df = pd.DataFrame(
        {
            "年度": ["2023", "2024"],
            "部門": ["営業", "営業"],
            "値": [1000, 1200],
        }
    )

    # Act
    success, msg = check_stacked_bar(df, "年度", "値", "部門")

    # Assert
    assert success is False
    assert "2つ以上" in msg


def test_check_stacked_bar_negative_values():
    """[test_chart-034] 負の値がある場合のエラー。"""
    # Arrange
    df = pd.DataFrame(
        {
            "年度": ["2023", "2023"],
            "部門": ["営業", "開発"],
            "値": [1000, -500],
        }
    )

    # Act
    success, msg = check_stacked_bar(df, "年度", "値", "部門")

    # Assert
    assert success is False
    assert "負の値" in msg


def test_draw_stacked_bar_success():
    """[test_chart-035] 積み上げ棒グラフ描画の成功ケース。"""
    # Arrange
    df = create_stacked_bar_data()

    # Act
    fig = draw_stacked_bar(df, "年度", "値", "部門", "積み上げ棒グラフテスト")

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
