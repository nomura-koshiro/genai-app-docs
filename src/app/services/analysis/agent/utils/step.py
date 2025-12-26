from copy import deepcopy

import numpy as np
import pandas as pd

from .chart import draw_graph

# ---------------------------
# Step
# ---------------------------


# def init_step(name, step_type):
#     base_step = {
#         "name": name,
#         "type": step_type,  # 'filter', 'aggregate', 'calculate'
#         "data_source": "original",
#         "result_data": None,
#         "result_table": None,
#         "result_chart": None,
#     }

#     if step_type == "filter":
#         # データ絞り込み専用
#         base_step.update(
#             {
#                 "category_filter": {},
#                 "numeric_filter": {
#                     "column": "値",
#                     "filter_type": "range",  # 'range', 'topk', 'percentage'
#                     # rangeタイプ用
#                     "enable_min": False,
#                     "min_value": 0.0,
#                     "include_min": True,
#                     "enable_max": False,
#                     "max_value": 100.0,
#                     "include_max": True,
#                     # topkタイプ用
#                     "k_value": 10,
#                     "ascending": False,  # False=上位K件, True=下位K件
#                     # percentageタイプ用
#                     "min_percentile": 0.0,  # 0-100
#                     "max_percentile": 100.0,  # 0-100
#                 },
#                 "table_filter": {
#                     "table_df": None,
#                     "key_columns": [],
#                     "exclude_mode": True,
#                     "enable": False,  # テーブルフィルタの有効/無効
#                 },
#             }
#         )

#     elif step_type == "summary":
#         # サマリー・可視化専用
#         base_step.update(
#             {
#                 "formulas": [],
#             }
#         )

#     elif step_type == "aggregate":
#         # 集計専用
#         base_step.update({"group_by_axis": [], "aggregation_config": []})

#     return base_step


# def apply_configs(source_data, step_data):
#     if step_data['type'] == 'filter':
#         # フィルタステップの場合、フィルタを適用
#         apply_filters(source_data, step_data)
#         return
#     elif step_data['type'] == 'summary':
#         # サマリーステップの場合、計算式を適用
#         apply_formula(source_data, step_data)
#         apply_chart(source_data, step_data)
#         return
#     elif step_data['type'] == 'aggregate':
#         # 集計ステップの場合、集計を適用
#         apply_aggregation(source_data, step_data)
#         return
#     else:
#         raise ValueError(f"Unknown step type: {step_data['type']}")

# ---------------------------
# Formulas
# ---------------------------


def init_formula():
    # 新しい計算式の初期化（nameフィールドを削除、単位フィールドを追加）
    return {
        "type": "sum",
        "target_subject": None,
        "unit": "円",  # 単位フィールドを追加
        "portion": 1.0,  # 重み、値が掛ける係数を追加
        "result_value": None,
        "formula_text": "計算式未設定",
    }


def apply_formula(source_data, step_data):
    """
    計算式を適用してDataFrameに新しい列を追加または既存の値を集計
    """
    formula_config = step_data["config"].get("formulas", [])
    if not formula_config:
        return
    tmp_fc = deepcopy(formula_config)
    for fc in tmp_fc:
        try:
            formula_type = fc.get("type", "sum")
            target_subject = fc.get("target_subject")
            portion = fc.get("portion", 1.0)  # portionを追加
            if not target_subject or formula_type not in ["sum", "mean", "count", "max", "min", "+", "-", "*", "/"]:
                fc["result_value"] = None
            else:
                if formula_type not in ["+", "-", "*", "/"]:
                    subject_df = source_data[source_data["科目"] == target_subject].copy()
                    if subject_df.empty:
                        pass
                    else:
                        numeric_values = pd.to_numeric(subject_df["値"], errors="coerce")
                        if formula_type == "sum":
                            result = numeric_values.sum()
                        elif formula_type == "mean":
                            result = numeric_values.mean()
                        elif formula_type == "count":
                            result = len(numeric_values.dropna())
                        elif formula_type == "max":
                            result = numeric_values.max()
                        elif formula_type == "min":
                            result = numeric_values.min()
                else:
                    operand_values = []
                    for t in target_subject:
                        for f in formula_config:
                            if f["formula_text"] == t:
                                operand_values.append(f["result_value"])
                    if formula_type == "+":
                        result = sum(operand_values)
                    elif formula_type == "-":
                        result = operand_values[0] - operand_values[1]
                    elif formula_type == "*":
                        result = operand_values[0] * operand_values[1]
                    elif formula_type == "/":
                        result = operand_values[0] / operand_values[1]

                # portionを掛ける, 結果を更新
                fc["result_value"] = result * portion

        except Exception:
            fc["result_value"] = None
            # fc['formula_text'] = f'計算エラー: {str(e)}'

    # 更新された計算式をresult_formulaに反映、config抜き、name,value,unitのみ
    step_data["result_formula"] = [
        {
            "unit": fc["unit"],
            "value": fc["result_value"],
            "name": fc["formula_text"],
        }
        for fc in tmp_fc
    ]
    return


def apply_chart(source_data, step_data):
    """
    チャートを描画する関数
    """
    chart_config = step_data["config"].get("chart_config", {})

    if not chart_config:
        return

    # チャートの描画
    fig = draw_graph(source_data, chart_config)
    step_data["result_chart"] = fig
    return


def apply_table(source_data, step_data):
    """
    テーブルを生成する関数
    """
    table_config = step_data.get("table_config", {})
    show_table = table_config.get("show_source_data", False)
    if not show_table:
        step_data["result_table"] = None
        return

    # テーブルの生成
    # ここでは単純にDataFrameをそのまま返す
    step_data["result_table"] = source_data.copy()
    return


# ---------------------------
# Aggregation
# ---------------------------


def apply_aggregation(source_data, step_data):
    """
    集計設定に基づいてデータを集約する関数（四則演算対応版）
    Args:
        source_data (DataFrame): 元データ
        step_data (dict): 集計ステップの設定データ
    Returns:
        DataFrame: 集計済みのデータ
    """
    if source_data is None or source_data.empty:
        step_data["result_data"] = None
        return

    group_by_axis = step_data["config"].get("group_by_axis", [])
    aggregation_config = step_data["config"].get("aggregation_config", [])

    # 集計軸が指定されていない場合はエラー
    if not group_by_axis:
        raise ValueError("集計軸が指定されていません。'group_by_axis'を設定してください。")

    # 集計設定が指定されていない場合はエラー
    if not aggregation_config:
        raise ValueError("集計設定が指定されていません。'aggregation_config'を設定してください。")

    try:
        # 集計軸が存在するかチェック
        missing_columns = [col for col in group_by_axis if col not in source_data.columns]
        if missing_columns:
            raise ValueError(f"集計軸に指定された列がデータフレームに存在しません: {missing_columns}")

        # 元の順序を保持するため、group_by_axisの組み合わせの順序を記録
        original_combinations = source_data[group_by_axis].drop_duplicates().reset_index(drop=True)
        original_combinations["_original_order"] = range(len(original_combinations))

        # 集計結果を格納するリスト
        aggregated_results = []
        # 四則演算用の中間結果を格納する辞書
        intermediate_results = {}

        # 各科目・集計方法の組み合わせごとに処理
        for config in aggregation_config:
            subject = config.get("subject")
            method = config.get("method", "sum")
            name = config.get("name", "")

            # nameが指定されていない場合はスキップ
            if not name:
                continue

            # 基本集計処理（sum, mean, count, max, min）
            if method in ["sum", "mean", "count", "max", "min"]:
                # 科目が指定されていない場合はスキップ
                if not subject:
                    continue

                # 指定科目のデータを抽出
                subject_data = source_data[source_data["科目"] == subject].copy()

                if subject_data.empty:
                    continue

                # 数値列を数値型に変換
                subject_data["値"] = pd.to_numeric(subject_data["値"], errors="coerce")

                # NaNを除外
                subject_data = subject_data.dropna(subset=["値"])

                if subject_data.empty:
                    continue

                # 集計軸でグループ化して集計実行（sort=Falseで元の順序を保持）
                if method == "sum":
                    agg_result = subject_data.groupby(group_by_axis, sort=False)["値"].sum()
                elif method == "mean":
                    agg_result = subject_data.groupby(group_by_axis, sort=False)["値"].mean()
                elif method == "count":
                    agg_result = subject_data.groupby(group_by_axis, sort=False)["値"].count()
                elif method == "max":
                    agg_result = subject_data.groupby(group_by_axis, sort=False)["値"].max()
                elif method == "min":
                    agg_result = subject_data.groupby(group_by_axis, sort=False)["値"].min()

                # インデックスをリセットして通常の列に変換
                agg_result = agg_result.reset_index()
                agg_result["科目"] = name

                # 元の順序を保持するためにマージ
                agg_result = agg_result.merge(original_combinations, on=group_by_axis, how="left")

                # 結果リストに追加
                aggregated_results.append(agg_result)

                # 中間結果として保存（四則演算で使用）
                intermediate_results[name] = agg_result

            # 四則演算処理（+, -, *, /）
            elif method in ["+", "-", "*", "/"]:
                if not isinstance(subject, list) or len(subject) != 2:
                    continue

                left_name, right_name = subject

                # 左右のオペランドが中間結果に存在するかチェック
                if left_name not in intermediate_results or right_name not in intermediate_results:
                    continue

                left_df = intermediate_results[left_name].copy()
                right_df = intermediate_results[right_name].copy()

                # 集計軸でマージ
                merged_df = left_df.merge(right_df, on=group_by_axis, suffixes=("_left", "_right"))

                if merged_df.empty:
                    continue

                # 四則演算を実行
                if method == "+":
                    merged_df["値"] = merged_df["値_left"] + merged_df["値_right"]
                elif method == "-":
                    merged_df["値"] = merged_df["値_left"] - merged_df["値_right"]
                elif method == "*":
                    merged_df["値"] = merged_df["値_left"] * merged_df["値_right"]
                elif method == "/":
                    # ゼロ除算を防ぐ
                    # 分子分母両方が0の場合は0、分子が0でないが分母が0の場合のみNaN
                    condition = (merged_df["値_left"] == 0) & (merged_df["値_right"] == 0)
                    merged_df["値"] = merged_df["値_left"] / merged_df["値_right"].replace(0, float("nan"))
                    merged_df.loc[condition, "値"] = 0

                # _original_order列が存在するかチェックしてから選択
                required_columns = group_by_axis + ["値", "科目"]
                available_columns = required_columns.copy()

                # _original_orderが両方のDataFrameに存在する場合のみ追加
                if "_original_order_left" in merged_df.columns and "_original_order_right" in merged_df.columns:
                    # 左側の順序を優先して使用
                    merged_df["_original_order"] = merged_df["_original_order_left"]
                    available_columns.append("_original_order")
                elif "_original_order_left" in merged_df.columns:
                    merged_df["_original_order"] = merged_df["_original_order_left"]
                    available_columns.append("_original_order")
                elif "_original_order_right" in merged_df.columns:
                    merged_df["_original_order"] = merged_df["_original_order_right"]
                    available_columns.append("_original_order")

                # 科目を設定
                merged_df["科目"] = name

                # 利用可能な列のみを選択
                result_df = merged_df[available_columns].copy()

                # 結果リストに追加
                aggregated_results.append(result_df)

                # 中間結果として保存（他の四則演算で使用される可能性がある）
                intermediate_results[name] = result_df

        # 結果が空の場合
        if not aggregated_results:
            step_data["result_data"] = pd.DataFrame(columns=group_by_axis + ["科目", "値"])
            return

        # 全ての集計結果を結合
        final_result = pd.concat(aggregated_results, ignore_index=True)

        # _original_order列が存在する場合のみソート
        if "_original_order" in final_result.columns:
            # 元の順序に基づいてソート（_original_order、次に科目名でソート）
            final_result = final_result.sort_values(["_original_order", "科目"]).reset_index(drop=True)
            # 順序管理用の列を削除
            final_result = final_result.drop(columns=["_original_order"])
        else:
            # _original_order列がない場合は科目名のみでソート
            final_result = final_result.sort_values(["科目"]).reset_index(drop=True)

        # 列の順序を調整（集計軸 + 科目 + 値）
        column_order = group_by_axis + ["科目", "値"]
        final_result = final_result[column_order]

        step_data["result_data"] = final_result
        return

    except Exception as e:
        raise ValueError(f"集計処理中にエラーが発生しました: {str(e)}") from e


# ---------------------------
# Filters
# ---------------------------


def apply_filters(source_data, step_data, table_filter_df=None):
    """
    フィルタを適用する共通関数
    """
    filtered_data = source_data.copy()

    # カテゴリフィルタ
    if step_data["config"]["category_filter"]:
        filtered_data = filter_data(filtered_data, category_filter=step_data["config"]["category_filter"])

    # 数値フィルタ
    numeric_filter = step_data["config"].get("numeric_filter", {})
    filter_type = numeric_filter.get("filter_type", "range")

    # フィルタタイプに応じて適用条件を判定
    should_apply_numeric_filter = False
    if filter_type == "range":
        should_apply_numeric_filter = numeric_filter.get("enable_min", False) or numeric_filter.get("enable_max", False)
    elif filter_type == "topk":
        should_apply_numeric_filter = numeric_filter.get("k_value", 0) > 0
    elif filter_type == "percentage":
        min_pct = numeric_filter.get("min_percentile", 0)
        max_pct = numeric_filter.get("max_percentile", 100)
        should_apply_numeric_filter = min_pct > 0 or max_pct < 100

    if should_apply_numeric_filter:
        filtered_data = filter_data(filtered_data, numeric_filter=numeric_filter)

    # テーブルフィルタ
    if (
        step_data["config"]["table_filter"].get("enable")
        and table_filter_df is not None
        and step_data["config"]["table_filter"].get("key_columns")
    ):
        filtered_data = filter_data(filtered_data, table_filter=[step_data["config"]["table_filter"], table_filter_df])

    step_data["result_data"] = filtered_data


def filter_data(df, category_filter=None, numeric_filter=None, table_filter=None):
    """
    DataFrameを指定された条件でフィルタリングする関数（TopK・パーセンテージ対応版）
    Args:
        df (DataFrame): フィルタ対象のDataFrame
        filters (dict): カテゴリフィルタ条件
        numeric_filter (dict): 数値フィルタ条件 {
            'column': '値',  # 対象列名
            'filter_type': 'range',  # 'range', 'topk', 'percentage'

            # rangeタイプの場合
            'min_value': float,  # 下限値
            'max_value': float,  # 上限値
            'include_min': bool,  # 下限値を含むかどうか
            'include_max': bool,  # 上限値を含むかどうか
            'enable_min': bool,  # 下限フィルタを有効にするかどうか
            'enable_max': bool,  # 上限フィルタを有効にするかどうか

            # topkタイプの場合
            'k_value': int,  # 上位K件
            'ascending': bool,  # True=下位K件, False=上位K件

            # percentageタイプの場合
            'min_percentile': float,  # 下位パーセンタイル (0-100)
            'max_percentile': float,  # 上位パーセンタイル (0-100)
        }
        table_filter (list): テーブルフィルタ設定
    Returns:
        DataFrame: フィルタリング済みのDataFrame
    """
    filtered_df = df.copy()

    # カテゴリフィルタの適用
    if category_filter is not None and len(category_filter) > 0:
        for column, condition in category_filter.items():
            if column not in filtered_df.columns:
                raise ValueError(f"カラム '{column}' がDataFrameに見つかりません")

            # 条件が単一値の場合はリストに変換
            if not isinstance(condition, (list, tuple, set)):
                condition = [condition]

            # フィルタリング実行
            filtered_df = filtered_df[filtered_df[column].isin(condition)]

    # 数値フィルタの適用
    if numeric_filter is not None and len(numeric_filter) > 0:
        column = numeric_filter.get("column")
        filter_type = numeric_filter.get("filter_type", "range")

        if column and column in filtered_df.columns:
            try:
                numeric_series = pd.to_numeric(filtered_df[column], errors="coerce")
                # NaNでない値のみを対象とする
                valid_mask = ~numeric_series.isna()
                valid_df = filtered_df[valid_mask].copy()
                valid_numeric = numeric_series[valid_mask]

                if valid_df.empty:
                    # 有効な数値データがない場合は元のデータを返す
                    pass
                elif filter_type == "range":
                    # 既存の範囲フィルタ処理
                    # 下限フィルタ
                    if numeric_filter.get("enable_min", False):
                        min_value = numeric_filter.get("min_value")
                        if min_value is not None:
                            include_min = numeric_filter.get("include_min", True)
                            if include_min:
                                min_mask = numeric_series >= min_value
                            else:
                                min_mask = numeric_series > min_value
                            min_mask = min_mask | ~valid_mask
                            filtered_df = filtered_df[min_mask]
                            numeric_series = pd.to_numeric(filtered_df[column], errors="coerce")
                            valid_mask = ~numeric_series.isna()

                    # 上限フィルタ
                    if numeric_filter.get("enable_max", False):
                        max_value = numeric_filter.get("max_value")
                        if max_value is not None:
                            include_max = numeric_filter.get("include_max", True)
                            if include_max:
                                max_mask = numeric_series <= max_value
                            else:
                                max_mask = numeric_series < max_value
                            max_mask = max_mask | ~valid_mask
                            filtered_df = filtered_df[max_mask]

                elif filter_type == "topk":
                    # TopKフィルタ処理
                    k_value = numeric_filter.get("k_value", 10)
                    ascending = numeric_filter.get("ascending", False)  # False=上位K件

                    if k_value > 0:
                        # 数値でソートしてTopK件を取得
                        sorted_valid_df = valid_df.sort_values(by=column, ascending=ascending)
                        topk_df = sorted_valid_df.head(k_value)

                        # NaNの行も含めて結果を構築
                        nan_df = filtered_df[~valid_mask]
                        filtered_df = pd.concat([topk_df, nan_df]).sort_index()

                elif filter_type == "percentage":
                    # パーセンテージフィルタ処理
                    min_percentile = numeric_filter.get("min_percentile", 0)  # 0-100
                    max_percentile = numeric_filter.get("max_percentile", 100)  # 0-100

                    # パーセンタイル値を計算
                    min_threshold = valid_numeric.quantile(min_percentile / 100.0)
                    max_threshold = valid_numeric.quantile(max_percentile / 100.0)

                    # パーセンタイル範囲内の値をフィルタ
                    percentile_mask = (numeric_series >= min_threshold) & (numeric_series <= max_threshold)
                    percentile_mask = percentile_mask | ~valid_mask  # NaNの行は保持
                    filtered_df = filtered_df[percentile_mask]

                else:
                    raise ValueError(f"サポートされていないfilter_type: {filter_type}")

            except Exception as e:
                raise ValueError(f"カラム '{column}' への数値フィルタ適用中にエラーが発生しました: {str(e)}") from e

    # 除外テーブルフィルタの適用
    if table_filter is not None and len(table_filter) == 2:
        table_df = table_filter[1]
        key_columns = table_filter[0].get("key_columns", [])
        exclude_mode = table_filter[0].get("exclude_mode", True)

        if table_df is not None and not table_df.empty and key_columns:
            # キー列が存在するかチェック
            missing_cols = [col for col in key_columns if col not in filtered_df.columns]
            if missing_cols:
                raise ValueError(f"キーカラムがDataFrameに見つかりません: {missing_cols}")

            # 除外対象の組み合わせを取得
            table_combinations = table_df[key_columns].drop_duplicates()

            # マージして除外/包含を実行
            merge_indicator = "_merge_indicator"
            merged_df = filtered_df.merge(table_combinations, on=key_columns, how="left", indicator=merge_indicator)

            if exclude_mode:
                # 除外モード：マッチしないレコードのみ残す
                filtered_df = merged_df[merged_df[merge_indicator] == "left_only"].drop(columns=[merge_indicator])
            else:
                # 包含モード：マッチするレコードのみ残す
                filtered_df = merged_df[merged_df[merge_indicator] == "both"].drop(columns=[merge_indicator])

    return filtered_df


# ---------------------------
# Transform
# ---------------------------


def apply_transform(source_data, step_data):
    """
    変換設定に基づいてデータを変換する関数
    Args:
        source_data (DataFrame): 元データ
        step_data (dict): 変換ステップの設定データ
    Returns:
        DataFrame: 変換済みのデータ
    """
    if source_data is None or source_data.empty:
        step_data["result_data"] = source_data
        return

    transform_config = step_data["config"].get("transform_config", {})
    operations = transform_config.get("operations", [])

    if not operations:
        step_data["result_data"] = source_data.copy()
        return

    try:
        result_data = source_data.copy()

        # 各operationを順次実行し、結果を次のoperationに渡す
        for operation in operations:
            operation_type = operation.get("operation_type")
            target_name = operation.get("target_name")
            calculation = operation.get("calculation", {})

            if not target_name:
                continue

            if operation_type in ["add_axis", "modify_axis"]:
                # 軸（列）の追加または変更
                calculated_values = _calculate_axis_values(result_data, calculation)

                if operation_type == "modify_axis":
                    # 既存の軸を変更
                    if target_name in result_data.columns:
                        result_data[target_name] = calculated_values
                else:
                    # 新しい軸を追加
                    result_data[target_name] = calculated_values

            elif operation_type in ["add_subject", "modify_subject"]:
                # 科目の追加または変更
                if operation_type == "modify_subject":
                    # 既存の科目を変更
                    subject_mask = result_data["科目"] == target_name
                    if subject_mask.any():
                        # 該当する科目の各組み合わせで値を再計算
                        unique_combinations = result_data[subject_mask].drop(["科目", "値"], axis=1).drop_duplicates()

                        for _, combo in unique_combinations.iterrows():
                            mask = subject_mask.copy()
                            for col in combo.index:
                                mask = mask & (result_data[col] == combo[col])

                            new_value = _calculate_subject_value(result_data, calculation, mask, combo)
                            result_data.loc[mask, "値"] = new_value
                else:
                    # 新しい科目を追加
                    new_rows = []
                    unique_combinations = result_data.drop(["科目", "値"], axis=1).drop_duplicates()

                    for _, combo in unique_combinations.iterrows():
                        new_row = combo.to_dict()
                        new_row["科目"] = target_name

                        # この組み合わせに対する計算値を取得
                        mask = True
                        for col in combo.index:
                            mask = mask & (result_data[col] == combo[col])

                        new_row["値"] = _calculate_subject_value(result_data, calculation, mask, combo)
                        new_rows.append(new_row)

                    if new_rows:
                        new_df = pd.DataFrame(new_rows)
                        result_data = pd.concat([result_data, new_df], ignore_index=True)

        step_data["result_data"] = result_data

    except Exception as e:
        raise ValueError(f"変換操作に失敗しました: {str(e)}") from e


def _calculate_axis_values(data, calculation):
    """
    計算設定に基づいて値を計算する補助関数
    """
    calc_type = calculation.get("type", "constant")

    if calc_type == "constant":
        return calculation.get("constant_value", 0)

    elif calc_type == "copy":
        copy_from = calculation.get("copy_from")
        if copy_from and copy_from in data.columns:
            return data[copy_from]
        else:
            return 0

    elif calc_type == "mapping":
        mapping_dict = calculation.get("mapping_dict", {})
        source_col = calculation.get("operands", [None])[0]
        if source_col and source_col in data.columns:
            return data[source_col].map(mapping_dict).fillna(data[source_col])
        else:
            return 0

    elif calc_type == "formula":
        formula_type = calculation.get("formula_type", "+")
        operands = calculation.get("operands", [])

        if len(operands) >= 2 and all(op in data.columns for op in operands):
            if formula_type == "+":
                return data[operands[0]] + data[operands[1]]
            elif formula_type == "-":
                return data[operands[0]] - data[operands[1]]
            elif formula_type == "*":
                return data[operands[0]] * data[operands[1]]
            elif formula_type == "/":
                return data[operands[0]] / data[operands[1]].replace(0, 1)  # ゼロ除算回避

        constant_value = calculation.get("constant_value")
        if constant_value is not None and len(operands) >= 1 and operands[0] in data.columns:
            if formula_type == "+":
                return data[operands[0]] + constant_value
            elif formula_type == "-":
                return data[operands[0]] - constant_value
            elif formula_type == "*":
                return data[operands[0]] * constant_value
            elif formula_type == "/":
                return data[operands[0]] / constant_value if constant_value != 0 else data[operands[0]]

    return 0


def _calculate_subject_value(data, calculation, mask, combo):
    """
    科目の値を計算する補助関数
    """
    if calculation["type"] == "formula" and calculation["formula_type"] in ["+", "-", "*", "/"]:
        # 四則演算の場合、該当する科目の値を取得
        operand_values = []
        for operand in calculation["operands"]:
            operand_mask = mask & (data["科目"] == operand)
            if operand_mask.any():
                operand_values.append(data.loc[operand_mask, "値"].iloc[0])
            else:
                operand_values.append(0)

        if len(operand_values) >= 2:
            if calculation["formula_type"] == "+":
                return operand_values[0] + operand_values[1]
            elif calculation["formula_type"] == "-":
                return operand_values[0] - operand_values[1]
            elif calculation["formula_type"] == "*":
                return operand_values[0] * operand_values[1]
            elif calculation["formula_type"] == "/":
                return operand_values[0] / operand_values[1] if operand_values[1] != 0 else 0
        elif len(operand_values) == 1 and calculation.get("constant_value") is not None:
            # 定数との計算
            constant_value = calculation["constant_value"]
            if calculation["formula_type"] == "+":
                return operand_values[0] + constant_value
            elif calculation["formula_type"] == "-":
                return operand_values[0] - constant_value
            elif calculation["formula_type"] == "*":
                return operand_values[0] * constant_value
            elif calculation["formula_type"] == "/":
                return operand_values[0] / constant_value if constant_value != 0 else operand_values[0]

        return 0

    elif calculation["type"] == "constant":
        return calculation.get("constant_value", 0)

    elif calculation["type"] == "copy":
        copy_from = calculation.get("copy_from")
        if copy_from:
            copy_mask = mask & (data["科目"] == copy_from)
            if copy_mask.any():
                return data.loc[copy_mask, "値"].iloc[0]
        return 0

    else:
        return 0


def init_category_filter(input_axis):
    # 入力軸の初期化
    filter = {}
    for axis_name, axis_values in input_axis:
        for i, v in enumerate(axis_values):
            # numpyの型を標準型に変換
            if isinstance(v, (np.generic,)):
                axis_values[i] = v.item()
        filter[axis_name] = list(axis_values)  # 各軸の値をリストに変換
    return filter
