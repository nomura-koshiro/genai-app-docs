import json
import os
from collections.abc import Callable
from typing import Any, cast

import numpy as np
import pandas as pd
import plotly.express as px
from plotly import graph_objects as go

# import matplotlib.pyplot as plt
# import matplotlib_fontja


# ------------------------------
# interface
# 全てのグラフタイプに対応するチェックと描画関数
# ------------------------------
def check_data_and_config(input_record: pd.DataFrame, graph_config):
    """
    チャートの描画が可能かどうかをチェックする関数
    Args:
        input_record (DataFrame): 入力データ
        graph_config (dict): チャートの設定
    Returns:
        tuple: (bool, str) - チャートが描画可能かどうかのフラグとエラーメッセージ
    """
    # 基本的な入力チェック
    if input_record is None or input_record.empty:
        return False, "データが空です。利用可能な列: なし. データを確認し、有効なデータを提供してください。"
    if not isinstance(graph_config, dict):
        return False, f"グラフ設定が辞書形式ではありません。正しいJSON形式で設定を提供してください。現在の型: {type(graph_config)}"

    # データの列情報を取得
    available_columns = list(input_record.columns)
    if "科目" in available_columns:
        available_subjects = sorted(input_record["科目"].unique())
    else:
        available_subjects = []
    # graph情報
    graph_type = graph_config.get("graph_type")
    x_subject = graph_config.get("x_subject")
    y_subject = graph_config.get("y_subject")
    x_axis = graph_config.get("x_axis")
    y_axis = graph_config.get("y_axis")
    y_left_subject = graph_config.get("y_left_subject")
    y_left_type = graph_config.get("y_left_type")
    y_right_subject = graph_config.get("y_right_subject")
    y_right_type = graph_config.get("y_right_type")
    legend_axis = graph_config.get("legend_axis")
    stack_axis = graph_config.get("stack_axis")
    value_axis = graph_config.get("value_axis")
    measure_type = graph_config.get("measure_type")
    base_value = graph_config.get("base_value")

    # ルーティング辞書
    routing = {
        "scatter": {
            "input_func": check_scatter_input,
            "input_args": (graph_config, available_columns, available_subjects),
            "check_func": check_scatter,
            "check_args": (input_record, x_subject, y_subject, legend_axis),
        },
        "bar": {
            "input_func": check_bar_input,
            "input_args": (graph_config, available_columns),
            "check_func": check_bar,
            "check_args": (input_record, x_axis, y_axis, legend_axis),
        },
        "horizontal bar": {
            "input_func": check_horizontal_bar_input,
            "input_args": (graph_config, available_columns),
            "check_func": check_horizontal_bar,
            "check_args": (input_record, x_axis, y_axis, legend_axis),
        },
        "stacked bar": {
            "input_func": check_stacked_bar_input,
            "input_args": (graph_config, available_columns),
            "check_func": check_stacked_bar,
            "check_args": (input_record, x_axis, y_axis, stack_axis),
        },
        "line": {
            "input_func": check_line_input,
            "input_args": (graph_config, available_columns),
            "check_func": check_line,
            "check_args": (input_record, x_axis, y_axis, legend_axis),
        },
        "line&bar": {
            "input_func": check_line_and_bar_input,
            "input_args": (graph_config, available_columns, available_subjects),
            "check_func": check_line_and_bar,
            "check_args": (input_record, x_axis, y_left_subject, y_left_type, y_right_subject, y_right_type, legend_axis),
        },
        "waterfall": {
            "input_func": check_waterfall_input,
            "input_args": (graph_config, available_columns),
            "check_func": check_waterfall,
            "check_args": (input_record, x_axis, y_axis, measure_type, base_value, legend_axis),
        },
        "pie": {
            "input_func": check_pie_input,
            "input_args": (graph_config, available_columns),
            "check_func": check_pie,
            "check_args": (input_record, value_axis, legend_axis),
        },
    }

    if not graph_type or graph_type not in routing:
        available_types = list(routing.keys())
        return (
            False,
            (
                f"グラフタイプを必ず選択可能のものから指定してください: '{graph_type}'. "
                f"'graph_type'パラメータは以下から選択してください: {', '.join(available_types)}"
            ),
        )
    else:
        route = routing[graph_type]
        input_func = cast(Callable[..., tuple[bool, str]], route["input_func"])
        check_func = cast(Callable[..., tuple[bool, str]], route["check_func"])
        input_args = cast(tuple[Any, ...], route["input_args"])
        check_args = cast(tuple[Any, ...], route["check_args"])
        success, msg = input_func(*input_args)
        if not success:
            return False, msg
        else:
            success, msg = check_func(*check_args)
            return success, msg


def draw_graph(input_record: pd.DataFrame, graph_config: dict):
    """
    チャートを描画する関数
    Args:
        input_record (DataFrame): 入力データ
        graph_config (dict): チャートの設定
    Returns:
        plotly.graph_objects.Figure: 描画されたグラフのfigureオブジェクト
    """
    # タイトルとグラフタイプを取得
    title = graph_config.get("title")
    graph_type = graph_config.get("graph_type")

    # データの列情報を取得
    available_columns = list(input_record.columns)
    if "科目" in available_columns:
        sorted(input_record["科目"].unique())
    else:
        pass

    # graph情報を取得
    x_subject = graph_config.get("x_subject")
    y_subject = graph_config.get("y_subject")
    x_axis = graph_config.get("x_axis")
    y_axis = graph_config.get("y_axis")
    y_left_subject = graph_config.get("y_left_subject")
    y_left_type = graph_config.get("y_left_type")
    y_right_subject = graph_config.get("y_right_subject")
    y_right_type = graph_config.get("y_right_type")
    legend_axis = graph_config.get("legend_axis")
    stack_axis = graph_config.get("stack_axis")
    value_axis = graph_config.get("value_axis")
    measure_type = graph_config.get("measure_type")
    base_value = graph_config.get("base_value")
    show_total = graph_config.get("show_total")
    total_label = graph_config.get("total_label")

    # 描画ルーティング辞書
    draw_routing = {
        "scatter": {"draw_func": draw_scatter, "draw_args": (input_record, x_subject, y_subject, legend_axis, title)},
        "bar": {"draw_func": draw_bar, "draw_args": (input_record, x_axis, y_axis, legend_axis, title)},
        "horizontal bar": {"draw_func": draw_horizontal_bar, "draw_args": (input_record, x_axis, y_axis, legend_axis, title)},
        "stacked bar": {"draw_func": draw_stacked_bar, "draw_args": (input_record, x_axis, y_axis, stack_axis, title)},
        "line": {"draw_func": draw_line, "draw_args": (input_record, x_axis, y_axis, legend_axis, title)},
        "line&bar": {
            "draw_func": draw_line_and_bar,
            "draw_args": (input_record, x_axis, y_left_subject, y_left_type, y_right_subject, y_right_type, legend_axis, title),
        },
        "waterfall": {
            "draw_func": draw_waterfall,
            "draw_args": (input_record, x_axis, y_axis, measure_type, base_value, legend_axis, show_total, total_label, title),
        },
        "pie": {"draw_func": draw_pie, "draw_args": (input_record, value_axis, legend_axis, title)},
    }

    # グラフタイプの妥当性チェック
    if not graph_type or graph_type not in draw_routing:
        available_types = list(draw_routing.keys())
        raise ValueError(
            f"存在しないチャートタイプです: '{graph_type}'. 'graph_type'パラメータは以下から選択してください: {', '.join(available_types)}"
        )

    # 対応する描画関数を実行
    route = draw_routing[graph_type]
    draw_func = cast(Callable[..., Any], route["draw_func"])
    draw_args = cast(tuple[Any, ...], route["draw_args"])

    return draw_func(*draw_args)


# ------------------------------
# save & load json
# ------------------------------
def save_plotly_json(fig, path):
    """
    PlotlyのfigオブジェクトをJSON形式で保存する

    Args:
        fig: plotly.graph_objects.Figure オブジェクト
        path: 保存先のファイルパス（.json拡張子）

    Returns:
        bool: 保存成功時True、失敗時False
    """
    try:
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # figオブジェクトを辞書形式に変換してJSON保存
        with open(path, "w", encoding="utf-8") as f:
            json.dump(fig.to_dict(), f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"保存エラー: {e}")
        return False


def load_plotly_json(path):
    """
    JSON形式で保存されたPlotlyグラフを読み込む

    Args:
        path: 読み込み元のファイルパス（.json拡張子）

    Returns:
        plotly.graph_objects.Figure: 読み込まれたfigオブジェクト、失敗時None
    """
    try:
        # JSONファイルを読み込み
        with open(path, encoding="utf-8") as f:
            fig_dict = json.load(f)

        # 辞書からfigオブジェクトを復元
        fig = go.Figure(fig_dict)

        return fig
    except Exception as e:
        print(f"読み込みエラー: {e}")
        return None


# ------------------------------
# 散布グラフのチェックと描画関数
# ------------------------------


def check_scatter_input(graph_config: dict, available_columns: list, available_subjects: list) -> tuple[bool, str]:
    """散布図の入力パラメータチェック"""
    x_subject = graph_config.get("x_subject")
    y_subject = graph_config.get("y_subject")
    graph_config.get("legend_axis")

    # 科目列の存在チェック
    if not available_subjects:
        return False, f"散布図には '科目' 列が必要です。利用可能な列: {available_columns}. データに '科目' 列を追加してください。"

    if not x_subject:
        return (
            False,
            (
                f"X軸の科目が指定されていません。利用可能な科目: {available_subjects}. "
                "'x_subject', 'y_subject' パラメータを設定してください。(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    if not y_subject:
        return (
            False,
            (
                f"Y軸の科目が指定されていません。利用可能な科目: {available_subjects}. "
                "'x_subject', 'y_subject' パラメータを設定してください。(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    for k in graph_config.keys():
        if "legend" in k and k != "legend_axis":
            return (
                False,
                f"存在しないパラメータ '{k}' が指定されています。legendを設定する場合は、'legend_axis' パラメータを設定してください。",
            )
    return True, "OK"


def check_scatter(df, x_subject, y_subject, legend_axis):
    """
    散布図が描画可能かどうかをチェックする関数（科目ピボット版）
    Args:
        df (DataFrame): データフレーム [会社, セグメント, 科目, 値] 形式
        x_subject (str): X軸に使用する科目名
        y_subject (str): Y軸に使用する科目名
        legend_axis (str, optional): 色分け軸の列名（会社、セグメント等）
    Returns:
        tuple: (bool, str) - (チェック結果, エラーメッセージ)
    """

    # 基本的な入力チェック
    if df is None or df.empty:
        return False, "データが空です。"
    if x_subject is None:
        return False, "X軸の科目が選択されていません。"
    if y_subject is None:
        return False, "Y軸の科目が選択されていません。"
    if x_subject == y_subject:
        return False, "X軸とY軸に同じ科目が選択されています。異なる科目を選択してください。"

    # 必要な列の存在チェック
    required_columns = ["科目", "値"]
    for col in required_columns:
        if col not in df.columns:
            return False, f"必要な列 '{col}' がデータに存在しません。"

    if legend_axis and legend_axis not in df.columns:
        return False, f"色分け軸に指定された列 '{legend_axis}' がデータに存在しません。"

    # 指定された科目がデータに存在するかチェック
    available_subjects = df["科目"].unique()
    if x_subject not in available_subjects:
        return False, f"X軸の科目 '{x_subject}' がデータに存在しません。"
    if y_subject not in available_subjects:
        return False, f"Y軸の科目 '{y_subject}' がデータに存在しません。"

    # 値列が数値データかチェック
    try:
        pd.to_numeric(df["値"], errors="raise")
    except (ValueError, TypeError):
        return False, "値列のデータが数値ではありません。散布図には数値データが必要です。"

    # ピボット変換を試行してデータの整合性をチェック
    try:
        if legend_axis:
            grouping_cols = [col for col in df.columns if col not in ["科目", "値"]]
            if legend_axis not in grouping_cols:
                return False, f"色分け軸 '{legend_axis}' はグループ化可能な列ではありません。"

            pivot_df = df.pivot_table(index=list(grouping_cols), columns="科目", values="値", aggfunc="first").reset_index()
        else:
            grouping_cols = [col for col in df.columns if col not in ["科目", "値"]]
            pivot_df = df.pivot_table(index=grouping_cols, columns="科目", values="値", aggfunc="first").reset_index()

        # ピボット後のデータで必要な科目列が存在するかチェック
        if x_subject not in pivot_df.columns or y_subject not in pivot_df.columns:
            return False, "ピボット変換後に必要な科目列が見つかりません。"

        # 有効なデータポイントの数をチェック
        valid_data = pivot_df.dropna(subset=[x_subject, y_subject])
        if len(valid_data) == 0:
            return False, f"X軸の科目 '{x_subject}' とY軸の科目 '{y_subject}' の両方に値があるデータが見つかりません。"

        if len(valid_data) == 1:
            return False, "データポイントが1個しかありません。散布図には2個以上のデータポイントが必要です。"

    except Exception as e:
        return False, f"データのピボット変換でエラーが発生しました: {str(e)}"

    return True, "散布図の描画が可能です。"


def draw_scatter(df, x_subject, y_subject, legend_axis, title):
    """
    散布図を描画する関数（科目ピボット版）
    Args:
        df (DataFrame): データフレーム [会社, セグメント, 科目, 値] 形式
        x_subject (str): X軸に使用する科目名
        y_subject (str): Y軸に使用する科目名
        legend_axis (str, optional): 色分け軸の列名（会社、セグメント等）
        title (str): グラフタイトル
    Returns:
        plotly.graph_objects.Figure: 散布図のfigureオブジェクト
    """

    # データをピボット変換
    grouping_cols = [col for col in df.columns if col not in ["科目", "値"]]
    pivot_df = df.pivot_table(index=grouping_cols, columns="科目", values="値", aggfunc="first").reset_index()

    # NaNを除去
    plot_df = pivot_df.dropna(subset=[x_subject, y_subject])

    if legend_axis:
        # 色分け軸のユニークな値を取得
        unique_values = plot_df[legend_axis].unique()

        # 各カテゴリにランダムな色を割り当て
        np.random.seed(42)  # 再現性のために固定シード
        colors = [
            f"rgb({np.random.randint(50, 256)},{np.random.randint(50, 256)},{np.random.randint(50, 256)})"
            for _ in range(len(unique_values))
        ]

        # カテゴリと色のマッピングを作成
        color_discrete_map = dict(zip(unique_values, colors, strict=False))

        fig = px.scatter(plot_df, x=x_subject, y=y_subject, color=legend_axis, color_discrete_map=color_discrete_map, title=title)
    else:
        fig = px.scatter(plot_df, x=x_subject, y=y_subject, title=title)

    # レイアウトの調整
    fig.update_layout(xaxis_title=x_subject, yaxis_title=y_subject, showlegend=True if legend_axis else False)

    return fig


# ------------------------------
# 棒グラフのチェックと描画関数
# ------------------------------


def check_bar_input(graph_config: dict, available_columns: list) -> tuple[bool, str]:
    """棒グラフの入力パラメータチェック"""
    x_axis = graph_config.get("x_axis")
    y_axis = graph_config.get("y_axis")

    data_info = f"利用可能な列: {available_columns}"
    if not x_axis:
        return (
            False,
            (
                f"X軸が指定されていません。{data_info}. 'x_axis', 'y_axis' パラメータを設定してください。"
                "(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    if not y_axis:
        return (
            False,
            (
                f"Y軸が指定されていません。{data_info}. 'x_axis', 'y_axis' パラメータを設定してください。"
                "(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    for k in graph_config.keys():
        if "legend" in k and k != "legend_axis":
            return (
                False,
                f"存在しないパラメータ '{k}' が指定されています。legendを設定する場合は、'legend_axis' パラメータを設定してください。",
            )
    return True, "OK"


def check_bar(df, x_axis, y_axis, legend_axis):
    """
    棒グラフが描画可能かどうかをチェックする関数
    Args:
        df (DataFrame): データフレーム
        x_axis (str): X軸の列名（カテゴリ軸）
        y_axis (str): Y軸の列名（値軸）
        legend_axis (str, optional): 色分け軸の列名
    Returns:
        tuple: (bool, str) - (チェック結果, エラーメッセージ)
    """

    # 基本的な入力チェック
    if df is None or df.empty:
        return False, "データが空です。"
    if x_axis is None:
        return False, "X軸が選択されていません。"
    if y_axis is None:
        return False, "Y軸が選択されていません。"

    # 列の存在チェック
    if x_axis not in df.columns:
        return False, f"X軸に指定された列 '{x_axis}' がデータに存在しません。"
    if y_axis not in df.columns:
        return False, f"Y軸に指定された列 '{y_axis}' がコラムではありません。Y軸は'値'コラムだけ指定できです。"
    if legend_axis and legend_axis not in df.columns:
        return False, f"色分け軸に指定された列 '{legend_axis}' がデータに存在しません。"

    # Y軸は数値データである必要がある
    df[x_axis]
    y_values = df[y_axis]
    try:
        pd.to_numeric(y_values, errors="raise")
    except (ValueError, TypeError):
        return False, f"Y軸 '{y_axis}' のデータが数値ではありません。棒グラフのY軸には数値データが必要です。"

    # データポイントの数チェック
    valid_data = df.dropna(subset=[x_axis, y_axis])
    if len(valid_data) == 0:
        return False, "有効なデータポイントがありません。X軸とY軸の両方に値があるデータが必要です。"

    # 重複チェック（同じカテゴリの組み合わせ）
    if legend_axis:
        # 色分けがある場合：(x, color)が同じ場合は集計が必要
        duplicate_check_cols = [x_axis, legend_axis]
        duplicates = valid_data.duplicated(subset=duplicate_check_cols)
        if duplicates.any():
            duplicate_count = duplicates.sum()
            return False, f"同じカテゴリ・同じ色分けの組み合わせが{duplicate_count}個重複しています。データの集計が必要です。"
    else:
        # 色分けがない場合：xが同じ場合は集計が必要
        duplicates = valid_data.duplicated(subset=[x_axis])
        if duplicates.any():
            duplicate_count = duplicates.sum()
            return False, f"同じカテゴリ '{x_axis}' が{duplicate_count}個重複しています。データの集計が必要です。"

    return True, "棒グラフの描画が可能です。"


def draw_bar(df, x_axis, y_axis, legend_axis, title):
    """
    棒グラフを描画する関数
    Args:
        df (DataFrame): データフレーム
        chart_config (dict): グラフ設定
    Returns:
        plotly.graph_objects.Figure: 棒グラフのfigureオブジェクト
    """

    if legend_axis:
        # 色分け軸のユニークな値を取得
        unique_values = df[legend_axis].unique()

        # 各カテゴリにランダムな色を割り当て
        np.random.seed(42)  # 再現性のために固定シード
        colors = [
            f"rgb({np.random.randint(50, 256)},{np.random.randint(50, 256)},{np.random.randint(50, 256)})"
            for _ in range(len(unique_values))
        ]

        # カテゴリと色のマッピングを作成
        color_discrete_map = dict(zip(unique_values, colors, strict=False))

        fig = px.bar(
            df,
            x=x_axis,
            y=y_axis,
            color=legend_axis,
            color_discrete_map=color_discrete_map,  # カスタム色マッピング
            title=title,
        )
    else:
        fig = px.bar(df, x=x_axis, y=y_axis, title=title)

    # レイアウトの調整
    fig.update_layout(xaxis_title=x_axis, yaxis_title=y_axis, showlegend=False if legend_axis is None else True)

    return fig


# ------------------------------
# 横棒グラフのチェックと描画関数
# ------------------------------


def check_horizontal_bar_input(graph_config: dict, available_columns: list) -> tuple[bool, str]:
    """横棒グラフの入力パラメータチェック"""
    return check_bar_input(graph_config, available_columns)  # 同じチェック


def check_horizontal_bar(df, x_axis, y_axis, legend_axis):
    """
    横棒グラフが描画可能かどうかをチェックする関数
    Args:
        df (DataFrame): データフレーム
        x_axis (str): X軸の列名（値軸）
        y_axis (str): Y軸の列名（カテゴリ軸）
        legend_axis (str, optional): 色分け軸の列名
    Returns:
        tuple: (bool, str) - (チェック結果, エラーメッセージ)
    """

    # 基本的な入力チェック
    if df is None or df.empty:
        return False, "データが空です。"
    if x_axis is None:
        return False, "X軸が選択されていません。"
    if y_axis is None:
        return False, "Y軸が選択されていません。"

    # 列の存在チェック
    if x_axis not in df.columns:
        return False, f"X軸に指定された列 '{x_axis}' がコラムではありません。X軸は'値'コラムだけ指定できです。"
    if y_axis not in df.columns:
        return False, f"Y軸に指定された列 '{y_axis}' がデータに存在しません。"
    if legend_axis and legend_axis not in df.columns:
        return False, f"色分け軸に指定された列 '{legend_axis}' がデータに存在しません。"

    # X軸は数値データである必要がある（横棒グラフでは値軸がX軸）
    x_values = df[x_axis]
    df[y_axis]
    try:
        pd.to_numeric(x_values, errors="raise")
    except (ValueError, TypeError):
        return False, f"X軸 '{x_axis}' のデータが数値ではありません。横棒グラフのX軸には数値データが必要です。"

    # データポイントの数チェック
    valid_data = df.dropna(subset=[x_axis, y_axis])
    if len(valid_data) == 0:
        return False, "有効なデータポイントがありません。X軸とY軸の両方に値があるデータが必要です。"

    # 重複チェック（同じカテゴリの組み合わせ）
    if legend_axis:
        # 色分けがある場合：(y, color)が同じ場合は集計が必要
        duplicate_check_cols = [y_axis, legend_axis]
        duplicates = valid_data.duplicated(subset=duplicate_check_cols)
        if duplicates.any():
            duplicate_count = duplicates.sum()
            return False, f"同じカテゴリ・同じ色分けの組み合わせが{duplicate_count}個重複しています。データの集計が必要です。"
    else:
        # 色分けがない場合：yが同じ場合は集計が必要
        duplicates = valid_data.duplicated(subset=[y_axis])
        if duplicates.any():
            duplicate_count = duplicates.sum()
            return False, f"同じカテゴリ '{y_axis}' が{duplicate_count}個重複しています。データの集計が必要です。"

    return True, "横棒グラフの描画が可能です。"


def draw_horizontal_bar(df, x_axis, y_axis, legend_axis, title):
    """
    横棒グラフを描画する関数
    Args:
        df (DataFrame): データフレーム
        x_axis (str): X軸の列名（値軸）
        y_axis (str): Y軸の列名（カテゴリ軸）
        legend_axis (str, optional): 色分け軸の列名
        title (str): グラフタイトル
    Returns:
        plotly.graph_objects.Figure: 横棒グラフのfigureオブジェクト
    """

    if legend_axis:
        # 色分け軸のユニークな値を取得
        unique_values = df[legend_axis].unique()

        # 各カテゴリにランダムな色を割り当て
        np.random.seed(42)  # 再現性のために固定シード
        colors = [
            f"rgb({np.random.randint(50, 256)},{np.random.randint(50, 256)},{np.random.randint(50, 256)})"
            for _ in range(len(unique_values))
        ]

        # カテゴリと色のマッピングを作成
        color_discrete_map = dict(zip(unique_values, colors, strict=False))

        fig = px.bar(
            df,
            x=x_axis,
            y=y_axis,
            color=legend_axis,
            color_discrete_map=color_discrete_map,  # カスタム色マッピング
            orientation="h",  # 横棒グラフ指定
            title=title,
        )
    else:
        fig = px.bar(
            df,
            x=x_axis,
            y=y_axis,
            orientation="h",  # 横棒グラフ指定
            title=title,
        )

    # レイアウトの調整
    fig.update_layout(xaxis_title=x_axis, yaxis_title=y_axis, showlegend=False if legend_axis is None else True)

    return fig


# ------------------------------
# 折れ線グラフのチェックと描画関数
# ------------------------------


def check_line_input(graph_config: dict, available_columns: list) -> tuple[bool, str]:
    """折れ線グラフの入力パラメータチェック"""
    return check_bar_input(graph_config, available_columns)  # 同じチェック


def check_line(df, x_axis, y_axis, legend_axis):
    """
    折れ線グラフが描画可能かどうかをチェックする関数
    Args:
        df (DataFrame): データフレーム
        x_axis (str): X軸の列名
        y_axis (str): Y軸の列名
        legend_axis (str, optional): 色分け軸の列名
    Returns:
        tuple: (bool, str) - (チェック結果, エラーメッセージ)
    """

    # 基本的な入力チェック
    if df is None or df.empty:
        return False, "データが空です。"
    if x_axis is None:
        return False, "X軸が選択されていません。"
    if y_axis is None:
        return False, "Y軸が選択されていません。"

    # 列の存在チェック
    if x_axis not in df.columns:
        return False, f"X軸に指定された列 '{x_axis}' がデータに存在しません。"
    if y_axis not in df.columns:
        return False, f"Y軸に指定された列 '{y_axis}' がコラムではありません。Y軸は'値'コラムだけ指定できです。"
    if legend_axis and legend_axis not in df.columns:
        return False, f"色分け軸に指定された列 '{legend_axis}' がデータに存在しません。"

    # Y軸は数値データである必要がある
    y_values = df[y_axis]
    try:
        pd.to_numeric(y_values, errors="raise")
    except (ValueError, TypeError):
        return False, f"Y軸 '{y_axis}' のデータが数値ではありません。折れ線グラフには数値データが必要です。"

    # データポイントの数チェック
    valid_data = df.dropna(subset=[x_axis, y_axis])
    if len(valid_data) == 0:
        return False, "有効なデータポイントがありません。X軸とY軸の両方に値があるデータが必要です。"
    if len(valid_data) == 1:
        return False, "データポイントが1個しかありません。折れ線グラフには2個以上のデータポイントが必要です。"

    # 重複チェック
    if legend_axis:
        duplicate_check_cols = [x_axis, y_axis, legend_axis]
    else:
        duplicate_check_cols = [x_axis, y_axis]
    duplicates = valid_data.duplicated(subset=duplicate_check_cols)
    if duplicates.any():
        duplicate_count = duplicates.sum()
        return (
            False,
            f"重複するデータポイントが{duplicate_count}個見つかりました。折れ線グラフでは重複データは適切に描画されない可能性があります。",
        )

    return True, "折れ線グラフの描画が可能です。"


def draw_line(df, x_axis, y_axis, legend_axis, title):
    """
    折れ線グラフを描画する関数
    Args:
        df (DataFrame): データフレーム
        x_axis (str): X軸の列名
        y_axis (str): Y軸の列名
        legend_axis (str, optional): 色分け軸の列名
        title (str): グラフタイトル
    Returns:
        plotly.graph_objects.Figure: 折れ線グラフのfigureオブジェクト
    """

    if legend_axis:
        # 色分け軸のユニークな値を取得
        unique_values = df[legend_axis].unique()

        # 各カテゴリにランダムな色を割り当て
        np.random.seed(42)  # 再現性のために固定シード
        colors = [
            f"rgb({np.random.randint(50, 256)},{np.random.randint(50, 256)},{np.random.randint(50, 256)})"
            for _ in range(len(unique_values))
        ]

        # カテゴリと色のマッピングを作成
        color_discrete_map = dict(zip(unique_values, colors, strict=False))

        fig = px.line(
            df,
            x=x_axis,
            y=y_axis,
            color=legend_axis,
            color_discrete_map=color_discrete_map,  # カスタム色マッピング
            title=title,
        )
    else:
        fig = px.line(df, x=x_axis, y=y_axis, title=title)

    # レイアウトの調整
    fig.update_layout(xaxis_title=x_axis, yaxis_title=y_axis, showlegend=False if legend_axis is None else True)

    return fig


# ------------------------------
# 折れ線+棒グラフのチェックと描画関数
# ------------------------------


def check_line_and_bar_input(graph_config: dict, available_columns: list, available_subjects: list) -> tuple[bool, str]:
    """line&barグラフの入力パラメータチェック"""
    x_axis = graph_config.get("x_axis")
    y_left_subject = graph_config.get("y_left_subject")
    y_right_subject = graph_config.get("y_right_subject")

    # 科目列の存在チェック
    if not available_subjects:
        return False, f"line&barグラフには '科目' 列が必要です。利用可能な列: {available_columns}. データに '科目' 列を追加してください。"

    if not x_axis:
        grouping_columns = [col for col in available_columns if col not in ["科目", "値"]]
        return (
            False,
            (
                f"X軸が指定されていません。利用可能な軸: {grouping_columns}. "
                "'x_axis', 'y_left_subject', 'y_left_type', 'y_right_subject', 'y_right_type' パラメータを設定してください。"
                "(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    if not y_left_subject:
        return (
            False,
            (
                f"左Y軸の科目が指定されていません。利用可能な科目: {available_subjects}. "
                "'x_axis', 'y_left_subject', 'y_left_type', 'y_right_subject', 'y_right_type' パラメータを設定してください。"
                "(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    if not y_right_subject:
        return (
            False,
            (
                f"右Y軸の科目が指定されていません。利用可能な科目: {available_subjects}. "
                "'x_axis', 'y_left_subject', 'y_left_type', 'y_right_subject', 'y_right_type' パラメータを設定してください。"
                "(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    for k in graph_config.keys():
        if "legend" in k and k != "legend_axis":
            return (
                False,
                f"存在しないパラメータ '{k}' が指定されています。legendを設定する場合は、'legend_axis' パラメータを設定してください。",
            )
    return True, "OK"


def check_line_and_bar(df, x_axis, y_left_subject, y_left_type, y_right_subject, y_right_type, legend_axis):
    """
    混合グラフ（line&bar）が描画可能かどうかをチェックする関数
    Args:
        df (DataFrame): データフレーム [会社, セグメント, 科目, 値] 形式
        x_axis (str): X軸の列名（科目以外）
        y_left_subject (str): 左Y軸に使用する科目名
        y_left_type (str): 左Y軸のグラフタイプ（'bar' or 'line'）
        y_right_subject (str): 右Y軸に使用する科目名
        y_right_type (str): 右Y軸のグラフタイプ（'bar' or 'line'）
        legend_axis (str, optional): 色分け軸の列名
    Returns:
        tuple: (bool, str) - (チェック結果, エラーメッセージ)
    """

    # 基本的な入力チェック
    if df is None or df.empty:
        return False, "データが空です。"
    if x_axis is None:
        return False, "X軸が選択されていません。"
    if y_left_subject is None:
        return False, "左Y軸の科目が選択されていません。"
    if y_right_subject is None:
        return False, "右Y軸の科目が選択されていません。"
    if y_left_subject == y_right_subject:
        return False, "左Y軸と右Y軸に同じ科目が選択されています。異なる科目を選択してください。"

    # 必要な列の存在チェック
    required_columns = ["科目", "値"]
    for col in required_columns:
        if col not in df.columns:
            return False, f"必要な列 '{col}' がデータに存在しません。"

    if x_axis not in df.columns:
        return False, f"X軸に指定された列 '{x_axis}' がデータに存在しません。"
    if legend_axis and legend_axis not in df.columns:
        return False, f"色分け軸に指定された列 '{legend_axis}' がデータに存在しません。"

    # 指定された科目がデータに存在するかチェック
    available_subjects = df["科目"].unique()
    if y_left_subject not in available_subjects:
        return False, f"左Y軸の科目 '{y_left_subject}' がデータに存在しません。"
    if y_right_subject not in available_subjects:
        return False, f"右Y軸の科目 '{y_right_subject}' がデータに存在しません。"

    # 値列が数値データかチェック
    try:
        pd.to_numeric(df["値"], errors="raise")
    except (ValueError, TypeError):
        return False, "値列のデータが数値ではありません。混合グラフには数値データが必要です。"

    # グラフタイプの妥当性チェック
    valid_types = ["bar", "line"]
    if y_left_type not in valid_types:
        return False, f"左Y軸のグラフタイプ '{y_left_type}' が無効です。'bar' または 'line' を選択してください。"
    if y_right_type not in valid_types:
        return False, f"右Y軸のグラフタイプ '{y_right_type}' が無効です。'bar' または 'line' を選択してください。"

    # ピボット変換を試行してデータの整合性をチェック
    try:
        grouping_cols = [col for col in df.columns if col not in ["科目", "値"]]
        pivot_df = df.pivot_table(index=grouping_cols, columns="科目", values="値", aggfunc="first").reset_index()

        # ピボット後のデータで必要な科目列が存在するかチェック
        if y_left_subject not in pivot_df.columns or y_right_subject not in pivot_df.columns:
            return False, "ピボット変換後に必要な科目列が見つかりません。"

        # 有効なデータポイントの数をチェック
        valid_data = pivot_df.dropna(subset=[x_axis, y_left_subject, y_right_subject])
        if len(valid_data) == 0:
            return (
                False,
                f"X軸 '{x_axis}'、左Y軸の科目 '{y_left_subject}'、右Y軸の科目 '{y_right_subject}' の全てに値があるデータが見つかりません。",
            )

        if len(valid_data) == 1:
            return False, "データポイントが1個しかありません。混合グラフには2個以上のデータポイントが必要です。"

    except Exception as e:
        return False, f"データのピボット変換でエラーが発生しました: {str(e)}"

    return True, "混合グラフ（line&bar）の描画が可能です。"


def draw_line_and_bar(df, x_axis, y_left_subject, y_left_type, y_right_subject, y_right_type, legend_axis, title):
    """
    混合グラフ（line&bar）を描画する関数
    Args:
        df (DataFrame): データフレーム [会社, セグメント, 科目, 値] 形式
        x_axis (str): X軸の列名（科目以外）
        y_left_subject (str): 左Y軸に使用する科目名
        y_left_type (str): 左Y軸のグラフタイプ（'bar' or 'line'）
        y_right_subject (str): 右Y軸に使用する科目名
        y_right_type (str): 右Y軸のグラフタイプ（'bar' or 'line'）
        legend_axis (str, optional): 色分け軸の列名
        title (str): グラフタイトル
    Returns:
        plotly.graph_objects.Figure: 混合グラフのfigureオブジェクト
    """

    # データをピボット変換
    grouping_cols = [col for col in df.columns if col not in ["科目", "値"]]
    pivot_df = df.pivot_table(index=grouping_cols, columns="科目", values="値", aggfunc="first").reset_index()

    # NaNを除去
    plot_df = pivot_df.dropna(subset=[x_axis, y_left_subject, y_right_subject])

    # 図を作成
    fig = go.Figure()

    # 色の設定
    np.random.seed(42)

    if legend_axis:
        # 凡例軸がある場合
        unique_values = plot_df[legend_axis].unique()
        colors = [
            f"rgb({np.random.randint(50, 256)},{np.random.randint(50, 256)},{np.random.randint(50, 256)})"
            for _ in range(len(unique_values))
        ]
        color_map = dict(zip(unique_values, colors, strict=False))

        for _i, group_value in enumerate(unique_values):
            group_data = plot_df[plot_df[legend_axis] == group_value]
            color = color_map[group_value]

            # 左Y軸のトレースを追加
            if y_left_type == "bar":
                fig.add_trace(
                    go.Bar(
                        x=group_data[x_axis],
                        y=group_data[y_left_subject],
                        name=f"{group_value} ({y_left_subject})",
                        marker_color=color,
                        yaxis="y",
                        offsetgroup=1,
                    )
                )
            else:  # line
                fig.add_trace(
                    go.Scatter(
                        x=group_data[x_axis],
                        y=group_data[y_left_subject],
                        mode="lines+markers",
                        name=f"{group_value} ({y_left_subject})",
                        line={"color": color, "width": 2},
                        marker={"color": color, "size": 6},
                        yaxis="y",
                    )
                )

            # 右Y軸のトレースを追加（色を少し変える）
            darker_color = (
                f"rgb({max(0, int(color.split('(')[1].split(',')[0]) - 30)},"
                f"{max(0, int(color.split(',')[1]) - 30)},{max(0, int(color.split(',')[2].split(')')[0]) - 30)})"
            )

            if y_right_type == "bar":
                fig.add_trace(
                    go.Bar(
                        x=group_data[x_axis],
                        y=group_data[y_right_subject],
                        name=f"{group_value} ({y_right_subject})",
                        marker_color=darker_color,
                        yaxis="y2",
                        offsetgroup=2,
                    )
                )
            else:  # line
                fig.add_trace(
                    go.Scatter(
                        x=group_data[x_axis],
                        y=group_data[y_right_subject],
                        mode="lines+markers",
                        name=f"{group_value} ({y_right_subject})",
                        line={"color": darker_color, "width": 2, "dash": "dash"},
                        marker={"color": darker_color, "size": 6},
                        yaxis="y2",
                    )
                )
    else:
        # 凡例軸がない場合
        # 左Y軸のトレースを追加
        if y_left_type == "bar":
            fig.add_trace(go.Bar(x=plot_df[x_axis], y=plot_df[y_left_subject], name=y_left_subject, marker_color="blue", yaxis="y"))
        else:  # line
            fig.add_trace(
                go.Scatter(
                    x=plot_df[x_axis],
                    y=plot_df[y_left_subject],
                    mode="lines+markers",
                    name=y_left_subject,
                    line={"color": "blue", "width": 2},
                    marker={"color": "blue", "size": 6},
                    yaxis="y",
                )
            )

        # 右Y軸のトレースを追加
        if y_right_type == "bar":
            fig.add_trace(go.Bar(x=plot_df[x_axis], y=plot_df[y_right_subject], name=y_right_subject, marker_color="red", yaxis="y2"))
        else:  # line
            fig.add_trace(
                go.Scatter(
                    x=plot_df[x_axis],
                    y=plot_df[y_right_subject],
                    mode="lines+markers",
                    name=y_right_subject,
                    line={"color": "red", "width": 2},
                    marker={"color": "red", "size": 6},
                    yaxis="y2",
                )
            )

    # レイアウトの設定（二重Y軸）
    fig.update_layout(
        title=title,
        xaxis_title=x_axis,
        yaxis={"title": y_left_subject, "side": "left"},
        yaxis2={"title": y_right_subject, "side": "right", "overlaying": "y"},
        showlegend=True,
        hovermode="x unified",
    )

    return fig


# ------------------------------
# 積み上げ棒グラフのチェックと描画関数
# ------------------------------


def check_stacked_bar_input(graph_config: dict, available_columns: list) -> tuple[bool, str]:
    """積み上げ棒グラフの入力パラメータチェック"""
    x_axis = graph_config.get("x_axis")
    y_axis = graph_config.get("y_axis")
    stack_axis = graph_config.get("stack_axis")

    data_info = f"利用可能な列: {available_columns}"
    if not x_axis:
        return False, f"X軸が指定されていません。{data_info}. 'x_axis', 'y_axis', 'stack_axis' パラメータを設定してください。"
    if not y_axis:
        return False, f"Y軸が指定されていません。{data_info}. 'x_axis', 'y_axis', 'stack_axis' パラメータを設定してください。"
    if not stack_axis:
        return False, f"積み上げ軸が指定されていません。{data_info}. 'x_axis', 'y_axis', 'stack_axis' パラメータを設定してください。"
    return True, "OK"


def check_stacked_bar(df, x_axis, y_axis, stack_axis):
    """
    積み上げ棒グラフが描画可能かどうかをチェックする関数
    Args:
        df (DataFrame): データフレーム
        x_axis (str): X軸の列名（カテゴリ軸）
        y_axis (str): Y軸の列名（値軸）
        stack_axis (str): 積み上げ軸の列名（スタック要素）
    Returns:
        tuple: (bool, str) - (チェック結果, エラーメッセージ)
    """

    # 基本的な入力チェック
    if df is None or df.empty:
        return False, "データが空です。"
    if x_axis is None:
        return False, "X軸が選択されていません。"
    if y_axis is None:
        return False, "Y軸が選択されていません。"
    if stack_axis is None:
        return False, "積み上げ軸が選択されていません。"

    # 列の存在チェック
    if x_axis not in df.columns:
        return False, f"X軸に指定された列 '{x_axis}' がデータに存在しません。"
    if y_axis not in df.columns:
        return False, f"Y軸に指定された列 '{y_axis}' がコラムではありません。Y軸は'値'コラムだけ指定できです。"
    if stack_axis not in df.columns:
        return False, f"積み上げ軸に指定された列 '{stack_axis}' がデータに存在しません。"

    # 同じ列を指定していないかチェック
    if x_axis == y_axis:
        return False, "X軸とY軸に同じ列が選択されています。異なる列を選択してください。"
    if x_axis == stack_axis:
        return False, "X軸と積み上げ軸に同じ列が選択されています。異なる列を選択してください。"
    if y_axis == stack_axis:
        return False, "Y軸と積み上げ軸に同じ列が選択されています。異なる列を選択してください。"

    # Y軸は数値データである必要がある
    y_values = df[y_axis]
    try:
        pd.to_numeric(y_values, errors="raise")
    except (ValueError, TypeError):
        return False, f"Y軸 '{y_axis}' のデータが数値ではありません。積み上げ棒グラフのY軸には数値データが必要です。"

    # データポイントの数チェック
    valid_data = df.dropna(subset=[x_axis, y_axis, stack_axis])
    if len(valid_data) == 0:
        return False, "有効なデータポイントがありません。X軸、Y軸、積み上げ軸の全てに値があるデータが必要です。"

    # 積み上げ軸のユニークな値が1つだけの場合は警告
    unique_stack_values = valid_data[stack_axis].nunique()
    if unique_stack_values == 1:
        return False, f"積み上げ軸 '{stack_axis}' のユニークな値が1つしかありません。積み上げ棒グラフには2つ以上のカテゴリが必要です。"

    # 重複チェック（同じX軸・同じ積み上げ軸の組み合わせ）
    duplicate_check_cols = [x_axis, stack_axis]
    duplicates = valid_data.duplicated(subset=duplicate_check_cols)
    if duplicates.any():
        duplicate_count = duplicates.sum()
        return False, f"同じX軸・同じ積み上げ軸の組み合わせが{duplicate_count}個重複しています。データの集計が必要です。"

    # 負の値チェック（積み上げ棒グラフでは負の値は推奨されない）
    negative_values = valid_data[y_axis] < 0
    if negative_values.any():
        negative_count = negative_values.sum()
        return (
            False,
            f"Y軸のデータに負の値が{negative_count}個含まれています。積み上げ棒グラフでは負の値は適切に表示されない可能性があります。",
        )

    return True, "積み上げ棒グラフの描画が可能です。"


def draw_stacked_bar(df, x_axis, y_axis, stack_axis, title):
    """
    積み上げ棒グラフを描画する関数
    Args:
        df (DataFrame): データフレーム
        x_axis (str): X軸の列名（カテゴリ軸）
        y_axis (str): Y軸の列名（値軸）
        stack_axis (str): 積み上げ軸の列名（スタック要素）
        title (str): グラフタイトル
    Returns:
        plotly.graph_objects.Figure: 積み上げ棒グラフのfigureオブジェクト
    """

    # 有効なデータのみを使用
    plot_df = df.dropna(subset=[x_axis, y_axis, stack_axis])

    # 積み上げ軸のユニークな値を取得
    unique_stack_values = plot_df[stack_axis].unique()

    # 各カテゴリにランダムな色を割り当て
    np.random.seed(42)  # 再現性のために固定シード
    colors = [
        f"rgb({np.random.randint(50, 256)},{np.random.randint(50, 256)},{np.random.randint(50, 256)})"
        for _ in range(len(unique_stack_values))
    ]

    # カテゴリと色のマッピングを作成
    color_discrete_map = dict(zip(unique_stack_values, colors, strict=False))

    # plotly expressで積み上げ棒グラフを作成
    fig = px.bar(plot_df, x=x_axis, y=y_axis, color=stack_axis, color_discrete_map=color_discrete_map, title=title)

    # 積み上げモードに設定
    fig.update_layout(barmode="stack", xaxis_title=x_axis, yaxis_title=y_axis, showlegend=True, legend_title=stack_axis)

    return fig


# ------------------------------
# Waterfall図のチェックと描画関数
# ------------------------------


def check_waterfall_input(graph_config: dict, available_columns: list) -> tuple[bool, str]:
    """Waterfallグラフの入力パラメータチェック"""
    x_axis = graph_config.get("x_axis")
    y_axis = graph_config.get("y_axis")
    measure_type = graph_config.get("measure_type")

    data_info = f"利用可能な列: {available_columns}"
    if not x_axis:
        return (
            False,
            (
                f"X軸が指定されていません。{data_info}. "
                "'x_axis', 'y_axis', 'measure_type', 'base_value' パラメータを設定してください。"
                "(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    if not y_axis:
        return (
            False,
            (
                f"Y軸が指定されていません。{data_info}. "
                "'x_axis', 'y_axis', 'measure_type', 'base_value' パラメータを設定してください。"
                "(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    if not measure_type:
        return (
            False,
            (
                "測定タイプが指定されていません。'relative' または 'absolute' を 'measure_type' パラメータに設定してください。"
                "(オプション: 'legend_axis' パラメータも設定可能)"
            ),
        )
    for k in graph_config.keys():
        if ("legend" in k or "series" in k) and k != "legend_axis":
            return (
                False,
                (f"存在しないパラメータ '{k}' が指定されています。legendを設定する場合は、'legend_axis' パラメータを設定してください。"),
            )
    return True, "OK"


def check_waterfall(df, x_axis, y_axis, measure_type, base_value, legend_axis):
    """
    Waterfall図が描画可能かどうかをチェックする関数
    Args:
        df (DataFrame): データフレーム
        x_axis (str): X軸の列名（カテゴリ軸）
        y_axis (str): Y軸の列名（値軸）
        measure_type (str): 測定タイプ（'relative' または 'absolute'）
        base_value (float): 開始値
        legend_axis (str, optional): 色分け軸の列名
    Returns:
        tuple: (bool, str) - (チェック結果, エラーメッセージ)
    """

    # 基本的な入力チェック
    if df is None or df.empty:
        return False, "データが空です。"
    if x_axis is None:
        return False, "X軸が選択されていません。"
    if y_axis is None:
        return False, "Y軸が選択されていません。"
    if measure_type is None:
        return False, "測定タイプが選択されていません。"

    # 列の存在チェック
    if x_axis not in df.columns:
        return False, f"X軸に指定された列 '{x_axis}' がデータに存在しません。"
    if y_axis not in df.columns:
        return False, f"Y軸に指定された列 '{y_axis}' がコラムではありません。Y軸は'値'コラムだけ指定できです。"
    if legend_axis and legend_axis not in df.columns:
        return False, f"色分け軸に指定された列 '{legend_axis}' がデータに存在しません。"

    # 同じ列を指定していないかチェック
    if x_axis == y_axis:
        return False, "X軸とY軸に同じ列が選択されています。異なる列を選択してください。"
    if legend_axis and x_axis == legend_axis:
        return False, "X軸と色分け軸に同じ列が選択されています。異なる列を選択してください。"
    if legend_axis and y_axis == legend_axis:
        return False, "Y軸と色分け軸に同じ列が選択されています。異なる列を選択してください。"

    # Y軸は数値データである必要がある
    y_values = df[y_axis]
    try:
        pd.to_numeric(y_values, errors="raise")
    except (ValueError, TypeError):
        return False, f"Y軸 '{y_axis}' のデータが数値ではありません。Waterfall図のY軸には数値データが必要です。"

    # 測定タイプの妥当性チェック
    valid_measure_types = ["relative", "absolute"]
    if measure_type not in valid_measure_types:
        return False, f"測定タイプ '{measure_type}' が無効です。'relative' または 'absolute' を選択してください。"

    # 開始値の妥当性チェック
    if base_value is not None:
        try:
            float(base_value)
        except (ValueError, TypeError):
            return False, f"開始値 '{base_value}' が数値ではありません。数値を入力してください。"

    # データポイントの数チェック
    valid_data = df.dropna(subset=[x_axis, y_axis])
    if len(valid_data) == 0:
        return False, "有効なデータポイントがありません。X軸とY軸の両方に値があるデータが必要です。"

    if len(valid_data) == 1:
        return False, "データポイントが1個しかありません。Waterfall図には2個以上のデータポイントが必要です。"

    # 重複チェック
    if legend_axis:
        duplicate_check_cols = [x_axis, legend_axis]
        duplicates = valid_data.duplicated(subset=duplicate_check_cols)
        if duplicates.any():
            duplicate_count = duplicates.sum()
            return False, f"同じX軸・同じ色分け軸の組み合わせが{duplicate_count}個重複しています。データの集計が必要です。"
    else:
        duplicates = valid_data.duplicated(subset=[x_axis])
        if duplicates.any():
            duplicate_count = duplicates.sum()
            return False, f"同じX軸の値が{duplicate_count}個重複しています。データの集計が必要です。"

    return True, "Waterfall図の描画が可能です。"


def draw_waterfall(df, x_axis, y_axis, measure_type, base_value, legend_axis, show_total, total_label, title):
    """
    Waterfall図を描画する関数
    Args:
        df (DataFrame): データフレーム
        x_axis (str): X軸の列名（カテゴリ軸）
        y_axis (str): Y軸の列名（値軸）
        measure_type (str): 測定タイプ（'relative' または 'absolute'）
        base_value (float): 開始値
        legend_axis (str, optional): 色分け軸の列名
        show_total (bool): 合計を表示するかどうか
        total_label (str): 合計のラベル名
        title (str): グラフタイトル
    Returns:
        plotly.graph_objects.Figure: Waterfall図のfigureオブジェクト
    """

    # 有効なデータのみを使用
    plot_df = df.dropna(subset=[x_axis, y_axis]).copy()

    if legend_axis is None:
        # 単一のWaterfall図
        # データをX軸でソート
        # plot_df = plot_df.sort_values(x_axis)

        # 開始値を設定
        if base_value is None:
            base_value = 0

        # Waterfall図用のデータを準備
        x_values = plot_df[x_axis].tolist()
        y_values = plot_df[y_axis].tolist()

        if measure_type == "relative":
            # 相対値の場合：各値は前の値からの増減
            measures = ["relative"] * len(y_values)

            # 開始値がある場合は追加
            if base_value != 0:
                x_values = ["開始値"] + x_values
                y_values = [base_value] + y_values
                measures = ["absolute"] + measures

            # 合計を表示する場合
            if show_total:
                x_values.append(total_label if total_label else "合計")
                y_values.append(None)  # Plotlyが自動計算
                measures.append("total")
        else:
            # 絶対値の場合：各値は絶対値（Plotlyが差分を自動計算）
            measures = ["absolute"] * len(y_values)

        # Waterfall図を作成
        fig = go.Figure(
            go.Waterfall(
                name="",
                orientation="v",
                measure=measures,
                x=x_values,
                y=y_values,
                textposition="outside",
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": "green"}},
                decreasing={"marker": {"color": "red"}},
                totals={"marker": {"color": "blue"}},
            )
        )

    else:
        # 複数のWaterfall図（グループ別）
        unique_groups = plot_df[legend_axis].unique()
        fig = go.Figure()

        # 色の設定
        np.random.seed(42)
        colors = [
            f"rgb({np.random.randint(50, 256)},{np.random.randint(50, 256)},{np.random.randint(50, 256)})"
            for _ in range(len(unique_groups))
        ]

        for i, group in enumerate(unique_groups):
            group_data = plot_df[plot_df[legend_axis] == group].copy()
            # group_data = group_data.sort_values(x_axis)

            # 開始値を設定
            if base_value is None:
                base_value = 0

            x_values = group_data[x_axis].tolist()
            y_values = group_data[y_axis].tolist()

            if measure_type == "relative":
                measures = ["relative"] * len(y_values)

                if base_value != 0:
                    x_values = ["開始値"] + x_values
                    y_values = [base_value] + y_values
                    measures = ["absolute"] + measures

                if show_total:
                    x_values.append(total_label if total_label else "合計")
                    y_values.append(None)
                    measures.append("total")
            else:
                measures = ["absolute"] * len(y_values)

            # 各グループのWaterfall図を追加
            fig.add_trace(
                go.Waterfall(
                    name=str(group),
                    orientation="v",
                    measure=measures,
                    x=x_values,
                    y=y_values,
                    textposition="outside",
                    connector={"line": {"color": colors[i]}},
                    increasing={"marker": {"color": colors[i]}},
                    decreasing={
                        "marker": {
                            "color": (
                                f"rgb({max(0, int(colors[i].split('(')[1].split(',')[0]) - 50)},"
                                f"{max(0, int(colors[i].split(',')[1]) - 50)},"
                                f"{max(0, int(colors[i].split(',')[2].split(')')[0]) - 50)})"
                            )
                        }
                    },
                )
            )

    # レイアウトの設定
    fig.update_layout(title=title, xaxis_title=x_axis, yaxis_title=y_axis, showlegend=True if legend_axis else False, waterfallgap=0.3)

    return fig


# ------------------------------
# 円グラフのチェックと描画関数
# ------------------------------


def check_pie_input(graph_config: dict, available_columns: list) -> tuple[bool, str]:
    """円グラフの入力パラメータチェック"""
    value_axis = graph_config.get("value_axis")
    legend_axis = graph_config.get("legend_axis")

    data_info = f"利用可能な列: {available_columns}"
    if not legend_axis:
        return False, f"凡例軸が指定されていません。{data_info}. 'value_axis', 'legend_axis' パラメータを設定してください。"
    if not value_axis:
        return False, f"値軸が指定されていません。{data_info}. 'value_axis', 'legend_axis' パラメータを設定してください。"
    return True, "OK"


def check_pie(df, value_axis, legend_axis):
    """
    円グラフが描画可能かどうかをチェックする関数
    Args:
        df (DataFrame): データフレーム
        value_axis (str): 値軸の列名（数値データ）
        legend_axis (str): 凡例軸の列名（カテゴリ軸）
    Returns:
        tuple: (bool, str) - (チェック結果, エラーメッセージ)
    """

    # 基本的な入力チェック
    if df is None or df.empty:
        return False, "データが空です。"
    if value_axis is None:
        return False, "値軸が選択されていません。"
    if legend_axis is None:
        return False, "凡例軸が選択されていません。"

    # 列の存在チェック
    if value_axis not in df.columns:
        return False, f"値軸に指定された列 '{value_axis}' がコラムではありません。値軸は'値'コラムだけ指定できです。"
    if legend_axis not in df.columns:
        return False, f"凡例軸に指定された列 '{legend_axis}' がデータに存在しません。"

    # 同じ列を指定していないかチェック
    if value_axis == legend_axis:
        return False, "値軸と凡例軸に同じ列が選択されています。異なる列を選択してください。"

    # 値軸は数値データである必要がある
    value_values = df[value_axis]
    try:
        pd.to_numeric(value_values, errors="raise")
    except (ValueError, TypeError):
        return False, f"値軸 '{value_axis}' のデータが数値ではありません。円グラフの値軸には数値データが必要です。"

    # データポイントの数チェック
    valid_data = df.dropna(subset=[value_axis, legend_axis])
    if len(valid_data) == 0:
        return False, "有効なデータポイントがありません。値軸と凡例軸の両方に値があるデータが必要です。"

    # 凡例軸のユニークな値が1つだけの場合は警告
    unique_legend_values = valid_data[legend_axis].nunique()
    if unique_legend_values == 1:
        return False, f"凡例軸 '{legend_axis}' のユニークな値が1つしかありません。円グラフには2つ以上のカテゴリが必要です。"

    # 重複チェック（同じ凡例軸の値）
    duplicates = valid_data.duplicated(subset=[legend_axis])
    if duplicates.any():
        duplicate_count = duplicates.sum()
        return False, f"同じ凡例軸 '{legend_axis}' が{duplicate_count}個重複しています。データの集計が必要です。"

    # 負の値チェック（円グラフでは負の値は適切に表示されない）
    negative_values = valid_data[value_axis] < 0
    if negative_values.any():
        negative_count = negative_values.sum()
        return False, f"値軸のデータに負の値が{negative_count}個含まれています。円グラフでは負の値は適切に表示されません。"

    # ゼロ値チェック（すべてがゼロの場合は意味がない）
    zero_values = valid_data[value_axis] == 0
    if zero_values.all():
        return False, "すべての値がゼロです。円グラフには正の値が必要です。"

    return True, "円グラフの描画が可能です。"


def draw_pie(df, value_axis, legend_axis, title):
    """
    円グラフを描画する関数
    Args:
        df (DataFrame): データフレーム
        value_axis (str): 値軸の列名（数値データ）
        legend_axis (str): 凡例軸の列名（カテゴリ軸）
        title (str): グラフタイトル
    Returns:
        plotly.graph_objects.Figure: 円グラフのfigureオブジェクト
    """

    # 有効なデータのみを使用
    plot_df = df.dropna(subset=[value_axis, legend_axis]).copy()

    # 負の値を除外（円グラフでは表示できないため）
    plot_df = plot_df[plot_df[value_axis] > 0]

    # 凡例軸のユニークな値を取得
    unique_legend_values = plot_df[legend_axis].unique()

    # 各カテゴリにランダムな色を割り当て
    np.random.seed(42)  # 再現性のために固定シード
    colors = [
        f"rgb({np.random.randint(50, 256)},{np.random.randint(50, 256)},{np.random.randint(50, 256)})"
        for _ in range(len(unique_legend_values))
    ]

    # カテゴリと色のマッピングを作成
    color_discrete_map = dict(zip(unique_legend_values, colors, strict=False))

    # plotly expressで円グラフを作成
    fig = px.pie(plot_df, values=value_axis, names=legend_axis, color=legend_axis, color_discrete_map=color_discrete_map, title=title)

    # レイアウトの調整
    fig.update_traces(
        textposition="inside", textinfo="percent+label", hovertemplate="<b>%{label}</b><br>値: %{value}<br>割合: %{percent}<extra></extra>"
    )

    fig.update_layout(showlegend=True, legend={"orientation": "v", "yanchor": "middle", "y": 0.5, "xanchor": "left", "x": 1.01})

    return fig
