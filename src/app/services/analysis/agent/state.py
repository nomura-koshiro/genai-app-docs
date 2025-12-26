import pandas as pd

from .utils.chart import (
    check_data_and_config,
)
from .utils.step import (
    apply_aggregation,
    apply_chart,
    apply_filters,
    apply_formula,
    apply_table,
    apply_transform,
    init_category_filter,
)


class AnalysisState:
    def __init__(self, input, step, chat):
        self.original_df = input
        self.chat_history = chat
        self.all_steps = []
        for s_i, s in enumerate(step):
            self.add_step(s["name"], s["type"], s["data_source"])
            if s["type"] == "filter":
                self.set_filter(s_i, s["config"])
            elif s["type"] == "summary":
                self.set_summary(s_i, s["config"])
            elif s["type"] == "aggregate":
                self.set_aggregation(s_i, s["config"])
            elif s["type"] == "transform":
                self.set_transform(s_i, s["config"])
            else:
                raise ValueError(f"不明なステップタイプ: {s['type']}")

    def set_source_data(self, data):
        """
        アップロードされたデータを元に、元のデータフレームを設定する
        Args:
            data (pd.DataFrame): 元のデータフレーム
        Returns:
            None
        """
        if isinstance(data, pd.DataFrame):
            self.original_df = data
        else:
            raise ValueError("データはpandas DataFrameである必要があります。")

    def get_source_data(self, step_index=None):
        """
        ステップのデータソースを取得する共通関数
        """
        all_steps_data = self.all_steps
        if step_index is None or all_steps_data[step_index]["data_source"] == "original":
            return self.original_df
        else:
            source_step_index = int(all_steps_data[step_index]["data_source"].split("_")[1])
            if source_step_index < len(all_steps_data) and all_steps_data[source_step_index]["result_data"] is not None:
                return all_steps_data[source_step_index]["result_data"]
            else:
                raise ValueError(
                    f"無効なデータソースインデックス: ステップ{step_index}に対する{source_step_index}。結果データがありません。"
                )

    def apply(self, step_index: int, include_following=True):
        """
        指定したステップの設定を適用し、結果を更新する
        Args:
            step_index (int): 設定を適用するステップのインデックス
        Returns:
            None
        """
        step_data = self.all_steps[step_index]
        source_data = self.get_source_data(step_index)
        if step_data["type"] == "filter":
            if step_data.get("table_filter") and step_data["table_filter"].get("enable") and step_data["table_filter"]["enable"]:
                # テーブルフィルタが有効な場合、テーブルフィルタを適用
                if "table_df" in step_data["table_filter"].keys() and step_data["table_filter"]["table_df"] is not None:
                    # テーブルフィルタのDataFrameを取得
                    table_df_index = int(step_data["table_filter"]["table_df"].split("_")[1])
                    table_filter_df = self.all_steps[table_df_index]["result_data"]
                else:
                    table_filter_df = None
            else:
                table_filter_df = None
            apply_filters(source_data, step_data, table_filter_df)
        elif step_data["type"] == "summary":
            # サマリーステップの場合、計算式を適用
            apply_formula(source_data, step_data)
            apply_chart(source_data, step_data)
            apply_table(source_data, step_data)
        elif step_data["type"] == "aggregate":
            # 集計ステップの場合、集計を適用
            apply_aggregation(source_data, step_data)
        elif step_data["type"] == "transform":
            # 変換ステップの場合、変換を適用
            apply_transform(source_data, step_data)
        else:
            raise ValueError(f"不明なステップタイプ: {step_data['type']}")

        # 指定したステップ以降のステップを再適用
        if include_following:
            for i in range(step_index + 1, len(self.all_steps)):
                self.apply(i, include_following=False)

    def add_step(self, name, type, data="original"):
        """
        新しいステップを追加する
        Args:
            name (str): ステップの名前
            type (str): ステップのタイプ ('filter', 'aggregate', 'calculate')
            data (str): 使うデータの名前
        Returns:
            None
        """
        base_step = {
            "name": name,
            "type": type,  # 'filter', 'aggregate', 'calculate'
            "data_source": data,
            "config": {},
            "result_data": None,
            "result_table": None,
            "result_chart": None,
            "result_formula": None,
        }
        # データソースが 'original' 以外の場合、インデックスを確認
        if data != "original":
            if not data.startswith("step_"):
                raise ValueError(f"無効なデータソース形式: {data}。'original'または'step_1', 'step_2', ...の形式を指定してください。")
            data_index = int(data.split("_")[1])
            if data_index < 0 or data_index >= len(self.all_steps) or self.all_steps[data_index]["result_data"] is None:
                raise ValueError(f"無効なデータソースインデックス: {data}")
        # ステップタイプに応じて初期設定を追加
        if type == "filter":
            source_data = self.get_source_data(None)
            assert isinstance(source_data, pd.DataFrame)
            input_axis = [(col, list(source_data[col].dropna().unique())) for col in source_data.columns if col != "値"]
            base_step["config"].update(
                {
                    "category_filter": init_category_filter(input_axis),
                    "numeric_filter": {
                        "column": "値",
                        "filter_type": "range",  # 'range', 'topk', 'percentage'
                        # rangeタイプ用
                        "enable_min": False,
                        "min_value": 0.0,
                        "include_min": True,
                        "enable_max": False,
                        "max_value": 100.0,
                        "include_max": True,
                        # topkタイプ用
                        "k_value": 10,
                        "ascending": False,  # False=上位K件, True=下位K件
                        # percentageタイプ用
                        "min_percentile": 0.0,  # 0-100
                        "max_percentile": 100.0,  # 0-100
                    },
                    "table_filter": {"table_df": None, "key_columns": [], "exclude_mode": True, "enable": False},
                }
            )
        elif type == "summary":
            base_step["config"].update({"formulas": [], "chart_config": {}, "table_config": {}})
        elif type == "aggregate":
            base_step["config"].update({"group_by_axis": [], "aggregation_config": []})
        elif type == "transform":
            base_step["config"].update({"transform_config": {"operations": []}})
        else:
            raise ValueError(f"不明なステップタイプ: {type}")

        self.all_steps.append(base_step)

    def delete_step(self, step_index):
        """
        指定したステップを削除する
        Args:
            step_index (int): 削除するステップのインデックス
        Returns:
            None
        """
        if 0 <= step_index < len(self.all_steps):
            self.all_steps.pop(step_index)
        else:
            raise IndexError("ステップインデックスが範囲外です")

    def get_summary(self, step_index):
        """
        指定したステップのサマリ設定（計算式とチャート設定）を取得する
        """
        assert self.all_steps[step_index]["type"] == "summary"
        return {
            "formulas": self.all_steps[step_index]["config"]["formulas"],
            "chart_config": self.all_steps[step_index]["config"]["chart_config"],
            "table_config": self.all_steps[step_index]["config"]["table_config"],
        }

    def set_summary(self, step_index, summary_config):
        """
        指定したステップにサマリ設定（計算式とチャート設定）を設定する
        Args:
            summary_config (dict): サマリ設定, 以下の形式
                {
                    "formulas": [
                        {"target_subject": "科目1", "type": "sum", "formula_text": "0.5倍科目1の合計", "unit": "円", "portion": 0.5},
                        {"target_subject": "科目2", "type": "mean", "formula_text": "科目2の平均", "unit": "%", "portion": 1.0},
                    ],
                    "chart_config": {
                        "graph_type": "bar",
                        "x_axis": "科目",
                        "y_axis": ["科目1", "科目2"],
                        "title": "科目ごとの集計"
                    },
                    "table_config": {
                        "show_source_data": true,  # ソースデータを表示するかどうか
                        "table_name": "出力テーブル名",
                    }
                }
        """
        example_formula = (
            '[{"target_subject": "科目1", "type": "sum", '
            '"formula_text": "0.5倍の科目1の合計", "unit": "円", "portion": 0.5}, '
            '{"target_subject": "科目1", "type": "count", '
            '"formula_text": "科目1の個数", "unit": "個", "portion": 1.0}, '
            '{"target_subject": ["0.5倍の科目1の合計", "科目1の個数"], "type": "/", '
            '"formula_text": "0.5倍の科目1の平均", "unit": "円", "portion": 1.0}]'
        )
        example_table = '{"show_source_data": true, "table_name": "出力テーブル名"}'

        if self.all_steps[step_index]["type"] != "summary":
            raise ValueError("サマリはsummaryタイプのステップにのみ設定できます。")

        if not isinstance(summary_config, dict):
            raise ValueError("サマリ設定は辞書型である必要があります。")
        if "formulas" not in summary_config or not isinstance(summary_config["formulas"], list):
            raise ValueError(
                "サマリ設定には'formulas'をリストとして含める必要があります。" + "空のリストを設定すると、計算式の計算が無効になります。"
            )
        if "chart_config" not in summary_config or not isinstance(summary_config["chart_config"], dict):
            raise ValueError(
                "サマリ設定には'chart_config'を辞書として含める必要があります。" + "空の辞書を設定すると、チャート表示が無効になります。"
            )
        if "table_config" not in summary_config or not isinstance(summary_config["table_config"], dict):
            raise ValueError(
                "サマリ設定には'table_config'を辞書として含める必要があります。" + "空の辞書を設定すると、テーブル出力が無効になります。"
            )

        formula = summary_config["formulas"]
        if not all(isinstance(f, dict) for f in formula):
            raise ValueError("各計算式は辞書型である必要があります。")
        source_data = self.get_source_data(step_index)
        assert isinstance(source_data, pd.DataFrame)
        available_subjects = set(source_data["科目"].values)
        for f in formula:
            if f.keys() != {"target_subject", "type", "formula_text", "unit", "portion"}:
                raise ValueError(
                    "各計算式には'target_subject', 'type', 'formula_text', 'unit', 'portion'が必要です。" + "例: " + example_formula
                )
            if f["type"] not in ["sum", "mean", "count", "max", "min", "+", "-", "*", "/"]:
                raise ValueError(
                    f"サポートされていない計算式タイプ: {f['type']}。'sum', 'mean', 'count', 'max', 'min'のいずれかを指定してください。"
                    + "例: "
                    + example_formula
                )
            if f["unit"] not in ["円", "%", "個"]:
                raise ValueError(
                    f"サポートされていない単位: {f['unit']}。'円', '%', '個'のいずれかを指定してください。" + "例: " + example_formula
                )
            if f["type"] in ["sum", "mean", "count", "max", "min"] and not isinstance(f["target_subject"], str):
                raise ValueError(f"'{f['type']}'のtarget_subjectは科目名を表す文字列である必要があります。" + "例: " + example_formula)
            if f["type"] in ["sum", "mean", "count", "max", "min"] and f["target_subject"] not in available_subjects:
                raise ValueError(f"target_subject '{f['target_subject']}' が利用可能な科目に見つかりません: {available_subjects}。")
            if f["type"] in ["+", "-", "*", "/"] and not isinstance(f["target_subject"], list):
                raise ValueError(
                    f"'{f['type']}'のtarget_subjectは他のformula_textのリストである必要があります。" + "例: " + example_formula
                )
            if f["type"] in ["+", "-", "*", "/"] and len(f["target_subject"]) != 2:
                raise ValueError(f"'{f['type']}'のtarget_subjectには2つのformula_textが必要です。" + "例: " + example_formula)
            if not isinstance(f["portion"], float):
                raise ValueError(
                    f"portionは浮動小数点数である必要があります。{type(f['portion'])}が指定されました。" + "例: " + example_formula
                )

        chart_config = summary_config["chart_config"]
        if chart_config != {}:
            chart_check, chart_msg = check_data_and_config(source_data, chart_config)
            if not chart_check:
                raise ValueError(f"チャート コンフィグ エラー: {chart_msg}")
            else:
                self.all_steps[step_index]["chart_config"] = chart_config

        table_config = summary_config["table_config"]
        if table_config != {}:
            if "show_source_data" not in table_config.keys():
                raise ValueError("テーブル設定には'show_source_data'が必要です。" + " 例: " + example_table)
            if not isinstance(table_config["show_source_data"], bool):
                raise ValueError("'show_source_data'はブール値である必要があります。" + " 例: " + example_table)
            if "table_name" not in table_config.keys():
                raise ValueError("テーブル設定には'table_name'が必要です。" + " 例: " + example_table)
            self.all_steps[step_index]["table_config"] = table_config

        # ステップの設定を更新
        self.all_steps[step_index]["config"]["formulas"] = summary_config["formulas"]
        self.all_steps[step_index]["config"]["chart_config"] = summary_config["chart_config"]
        self.all_steps[step_index]["config"]["table_config"] = summary_config["table_config"]

        self.apply(step_index)

    def get_aggregation(self, step_index):
        """
        指定したステップの集計設定を取得する
        Args:
            step_index (int): 集計設定を取得するステップのインデックス
        Returns:
            list: 集計設定のリスト
        """
        assert self.all_steps[step_index]["type"] == "aggregate"
        result = {
            "group_by_axis": self.all_steps[step_index]["config"]["group_by_axis"],
            "aggregation_config": self.all_steps[step_index]["config"]["aggregation_config"],
        }
        return result

    def set_aggregation(self, step_index, config):
        """
        指定したステップに集計設定を追加する（四則演算対応版）
        Args:
            step_index (int): 集計設定を追加するステップのインデックス
            config (dict): 集計設定の内容, 必ず以下の形式で指定
                {
                    "group_by_axis": [
                        "軸1",
                        "軸2"
                    ],
                    "aggregation_config":[
                        {"name": "科目1合計", "subject": "科目1", "method": "sum"},
                        {"name": "科目2平均", "subject": "科目2", "method": "mean"},
                        {"name": "新しい値名", "subject": ["科目1合計", "科目2平均"], "method": "/"}
                    ]
                }
        Returns:
            None
        """
        example_config = (
            '{"group_by_axis": ["軸1", "軸2"],'
            '"aggregation_config":'
            '[{"name": "科目1合計", "subject": "科目1", "method": "sum"}, '
            '{"name": "科目2平均", "subject": "科目2", "method": "mean"}, '
            '{"name": "新しい値名", "subject": ["科目1合計", "科目2平均"], "method": "/"}]}'
        )

        # 内容をチェックする
        if self.all_steps[step_index]["type"] != "aggregate":
            raise ValueError("集計はaggregateタイプのステップにのみ設定できます。")
        if not isinstance(config, dict):
            raise ValueError("集計設定は辞書型である必要があります。" + "例: " + example_config)
        if "group_by_axis" not in config or not isinstance(config["group_by_axis"], list):
            raise ValueError("集計設定には'group_by_axis'をリストとして含める必要があります。" + "例: " + example_config)
        if "aggregation_config" not in config or not isinstance(config["aggregation_config"], list):
            raise ValueError("集計設定には'aggregation_config'をリストとして含める必要があります。" + "例: " + example_config)

        source_data = self.get_source_data(step_index)
        assert isinstance(source_data, pd.DataFrame)
        available_subjects = set(source_data["科目"].values)
        available_columns = set(source_data.columns) - {"値", "科目"}

        for col in config["group_by_axis"]:
            if col not in available_columns:
                raise ValueError(f"group_by_axis '{col}' が利用可能な軸に見つかりません: {available_columns}。")

        # 集計設定名を追跡（四則演算の参照チェック用）
        config_names = []

        for agg in config["aggregation_config"]:
            if "name" not in agg or "subject" not in agg or "method" not in agg:
                raise ValueError("各集計設定には'name', 'subject', 'method'が必要です。" + "例: " + example_config)

            # nameの重複チェック
            if agg["name"] in config_names:
                raise ValueError(f"重複した集計名 '{agg['name']}' が見つかりました。各集計には一意の名前が必要です。")
            config_names.append(agg["name"])

            # 基本集計のチェック
            if agg["method"] in ["sum", "mean", "count", "max", "min"]:
                if not isinstance(agg["subject"], str):
                    raise ValueError(
                        f"'{agg['method']}'メソッドの場合、subjectは科目名を表す文字列である必要があります。" + "例: " + example_config
                    )
                if agg["subject"] not in available_subjects:
                    raise ValueError(f"集計対象の科目 '{agg['subject']}' が利用可能な科目に見つかりません: {available_subjects}。")

            # 四則演算のチェック
            elif agg["method"] in ["+", "-", "*", "/"]:
                if not isinstance(agg["subject"], list) or len(agg["subject"]) != 2:
                    raise ValueError(
                        f"'{agg['method']}'メソッドの場合、subjectは2つの集計名のリストである必要があります。" + "例: " + example_config
                    )
                # 参照する集計名が既に定義されているかチェック（順序依存）
                for ref_name in agg["subject"]:
                    if ref_name not in config_names:
                        raise ValueError(
                            f"'{agg['method']}'メソッドで参照している集計名 '{ref_name}' は、"
                            + "この集計より前に定義されている必要があります。"
                        )

            else:
                raise ValueError(
                    f"サポートされていない集計メソッド: {agg['method']}。"
                    + "'sum', 'mean', 'count', 'max', 'min', '+', '-', '*', '/'のいずれかを指定してください。"
                )

        # ステップの集計設定を更新
        self.all_steps[step_index]["config"]["group_by_axis"] = config["group_by_axis"]
        self.all_steps[step_index]["config"]["aggregation_config"] = config["aggregation_config"]

        self.apply(step_index)  # Apply the step to ensure data is processed
        data = self.all_steps[step_index]["result_data"]
        overview = "結果データの概要:\n"
        overview += f"  データ: {len(data)}件\n  コラム:\n"
        for col in data.columns:
            if col == "値":
                continue
            unique_values = data[col].unique()
            overview += f"    {col}: {', '.join(map(str, unique_values))}\n"
        return overview

    def get_filter(self, step_index):
        """
        指定したステップのフィルタ設定を取得する
        Args:
            step_index (int): フィルタ設定を取得するステップのインデックス
        Returns:
            dict: フィルタ設定
        """
        assert self.all_steps[step_index]["type"] == "filter"
        return {
            "category_filter": self.all_steps[step_index]["config"]["category_filter"],
            "numeric_filter": self.all_steps[step_index]["config"]["numeric_filter"],
            "table_filter": self.all_steps[step_index]["config"]["table_filter"],
        }

    def set_filter(self, step_index, filters):
        """
        指定したステップにフィルタ設定を追加する
        Args:
            step_index (int): フィルタ設定を追加するステップのインデックス
            filters (dict): フィルタ設定の内容, 必ず以下の形式で指定
                {
                    "category_filter": {
                        "コラム1": ["日本", "アメリカ"],
                        "コラム2": ["化学材料", "自動車部品"]
                    },
                    "numeric_filter": {
                        "column": "値",
                        "filter_type": "range | topk | percentage",

                        // rangeタイプの場合
                        "enable_min": false,
                        "min_value": 0.0,
                        "include_min": true,
                        "enable_max": false,
                        "max_value": 100.0,
                        "include_max": true,

                        // topkタイプの場合
                        "k_value": 10,
                        "ascending": false,

                        // percentageタイプの場合
                        "min_percentile": 0.0,
                        "max_percentile": 100.0
                    },
                    "table_filter": {
                        "table_df": str,  # フィルタ対象のDataFrame
                        "key_columns": ["コラム1", "コラム2"],
                        "exclude_mode": true,
                        "enable": false
                    }
                }
        Returns:
            None
        """
        example_category_filter = '{"コラム1": ["日本", "アメリカ"], "コラム2": ["化学材料", "自動車部品"]}'
        example_numeric_filter_range = (
            '{"column": "値", "filter_type": "range", '
            '"enable_min": false, "min_value": 0.0, "include_min": true, '
            '"enable_max": false, "max_value": 100.0, "include_max": true}'
        )
        example_numeric_filter_topk = '{"column": "値", "filter_type": "topk", "k_value": 10, "ascending": false}'
        example_numeric_filter_percentage = '{"column": "値", "filter_type": "percentage", "min_percentile": 10.0, "max_percentile": 90.0}'
        example_table_filter = '{"table_df": "step_1", "key_columns": ["地域"], "exclude_mode": true, "enable": false}'

        # 内容をチェックする
        if self.all_steps[step_index]["type"] != "filter":
            raise ValueError("フィルタはfilterタイプのステップにのみ設定できます。")
        if not isinstance(filters, dict):
            raise ValueError("フィルタは辞書型である必要があります。")
        if "category_filter" not in filters or not isinstance(filters["category_filter"], dict):
            raise ValueError(
                "フィルタには'category_filter', 'numeric_filter', 'table_filter'の3つの辞書を含める必要があります。"
                + "空の辞書を設定するとそのフィルタは無効になります。"
            )
        if "numeric_filter" not in filters or not isinstance(filters["numeric_filter"], dict):
            raise ValueError(
                "フィルタには'category_filter', 'numeric_filter', 'table_filter'の3つの辞書を含める必要があります。"
                + "空の辞書を設定するとそのフィルタは無効になります。"
            )
        if "table_filter" not in filters or not isinstance(filters["table_filter"], dict):
            raise ValueError(
                "フィルタには'category_filter', 'numeric_filter', 'table_filter'の3つの辞書を含める必要があります。"
                + "空の辞書を設定するとそのフィルタは無効になります。"
            )

        source_data = self.get_source_data(step_index)
        assert isinstance(source_data, pd.DataFrame)
        available_columns = set(source_data.columns) - {"値"}

        # カテゴリフィルタのチェック
        if len(filters["category_filter"].keys()) != 0:
            for col, values in filters["category_filter"].items():
                if col not in available_columns:
                    raise ValueError(f"カテゴリフィルタのカラム '{col}' が利用可能なカラムに見つかりません: {available_columns}。")
                if not isinstance(values, list):
                    raise ValueError(f"カテゴリフィルタ '{col}' の値はリストである必要があります。" + "例: " + example_category_filter)
                unique_values = source_data[col].dropna().unique()
                # 日付型の値である場合
                if pd.api.types.is_datetime64_any_dtype(source_data[col]):
                    values = pd.to_datetime(values, errors="coerce")
                    filters["category_filter"][col] = [v for v in values if pd.notna(v)]
                for value in values:
                    if value not in unique_values:
                        raise ValueError(f"カテゴリ '{col}' の値 '{value}' がデータ内に見つかりません。")

        # 数値フィルタのチェック
        if len(filters["numeric_filter"].keys()) != 0:
            numeric_filter = filters["numeric_filter"]
            filter_type = numeric_filter.get("filter_type", "range")

            if filter_type not in ["range", "topk", "percentage"]:
                raise ValueError(f"無効なfilter_type: {filter_type}。'range', 'topk', 'percentage'のいずれかを指定してください。")

            if numeric_filter.get("column", "値") != "値":
                raise ValueError(
                    "数値フィルタは'値'カラムに適用する必要があります。"
                    + "特定の'科目'の値でフィルタリングしたい場合は、先にカテゴリフィルタでその'科目'を指定してください。"
                )

            if filter_type == "range":
                required_keys = {
                    "column",
                    "filter_type",
                    "enable_min",
                    "min_value",
                    "include_min",
                    "enable_max",
                    "max_value",
                    "include_max",
                }
                if not required_keys.issubset(set(numeric_filter.keys())):
                    raise ValueError(
                        "range型の数値フィルタには必須キーが含まれている必要があります。" + " 例: " + example_numeric_filter_range
                    )

            elif filter_type == "topk":
                required_keys = {"column", "filter_type", "k_value", "ascending"}
                if not required_keys.issubset(set(numeric_filter.keys())):
                    raise ValueError(
                        "topk型の数値フィルタには必須キーが含まれている必要があります。" + " 例: " + example_numeric_filter_topk
                    )
                if not isinstance(numeric_filter["k_value"], int) or numeric_filter["k_value"] <= 0:
                    raise ValueError("k_valueは正の整数である必要があります。" + " 例: " + example_numeric_filter_topk)
                if not isinstance(numeric_filter["ascending"], bool):
                    raise ValueError("ascendingはブール値である必要があります。" + " 例: " + example_numeric_filter_topk)

            elif filter_type == "percentage":
                required_keys = {"column", "filter_type", "min_percentile", "max_percentile"}
                if not required_keys.issubset(set(numeric_filter.keys())):
                    raise ValueError(
                        "percentage型の数値フィルタには必須キーが含まれている必要があります。" + " 例: " + example_numeric_filter_percentage
                    )
                min_pct = numeric_filter["min_percentile"]
                max_pct = numeric_filter["max_percentile"]
                if not (0 <= min_pct <= 100) or not (0 <= max_pct <= 100):
                    raise ValueError("パーセンタイル値は0から100の範囲である必要があります。" + " 例: " + example_numeric_filter_percentage)
                if min_pct > max_pct:
                    raise ValueError(
                        "min_percentileはmax_percentile以下である必要があります。" + " 例: " + example_numeric_filter_percentage
                    )

        # テーブルフィルタのチェック
        if len(filters["table_filter"].keys()) != 0:
            if filters["table_filter"]["enable"]:
                if filters["table_filter"]["table_df"] != "original" and not filters["table_filter"]["table_df"].startswith("step_"):
                    raise ValueError(
                        "テーブルフィルタの'table_df'は'step_'で始まるステップ名か'original'である必要があります。"
                        + "例: "
                        + example_table_filter
                    )
                if not isinstance(filters["table_filter"]["key_columns"], list):
                    raise ValueError("テーブルフィルタの'key_columns'はリストである必要があります。" + "例: " + example_table_filter)
                for col in filters["table_filter"]["key_columns"]:
                    if col not in available_columns - {"科目"}:
                        raise ValueError(f"テーブルフィルタのキーカラム '{col}' が利用可能なカラムに見つかりません: {available_columns}。")

        # ステップのフィルタ設定を更新
        if len(filters["category_filter"].keys()) != 0:
            self.all_steps[step_index]["config"]["category_filter"] = init_category_filter(
                [(col, list(source_data[col].dropna().unique())) for col in source_data.columns if col != "値"]
            )
            for col, values in filters["category_filter"].items():
                if col in self.all_steps[step_index]["config"]["category_filter"]:
                    self.all_steps[step_index]["config"]["category_filter"][col] = list(set(values))
                else:
                    raise ValueError(f"カテゴリフィルタのカラム '{col}' が利用可能なカラムに見つかりません: {available_columns}。")
        else:
            self.all_steps[step_index]["config"]["category_filter"] = init_category_filter(
                [(col, list(source_data[col].dropna().unique())) for col in source_data.columns if col != "値"]
            )

        if len(filters["numeric_filter"].keys()) != 0:
            # 新しいフィルタ設定をマージ（既存の設定を保持しつつ更新）
            current_numeric_filter = self.all_steps[step_index]["config"]["numeric_filter"].copy()
            current_numeric_filter.update(filters["numeric_filter"])
            self.all_steps[step_index]["config"]["numeric_filter"] = current_numeric_filter
        else:
            # デフォルト設定にリセット
            self.all_steps[step_index]["config"]["numeric_filter"] = {
                "column": "値",
                "filter_type": "range",
                "enable_min": False,
                "min_value": 0.0,
                "include_min": True,
                "enable_max": False,
                "max_value": 100.0,
                "include_max": True,
                "k_value": 10,
                "ascending": False,
                "min_percentile": 0.0,
                "max_percentile": 100.0,
            }

        if len(filters["table_filter"].keys()) != 0:
            self.all_steps[step_index]["config"]["table_filter"] = filters["table_filter"]
        else:
            self.all_steps[step_index]["config"]["table_filter"] = {
                "table_df": None,
                "key_columns": [],
                "exclude_mode": True,
                "enable": False,
            }

        self.apply(step_index)  # Apply the step to ensure data is processed
        data = self.all_steps[step_index]["result_data"]
        overview = "結果データの概要:\n"
        overview += f"  データ: {len(data)}件\n  コラム:\n"
        for col in data.columns:
            if col == "値":
                continue
            unique_values = data[col].unique()
            overview += f"    {col}: {', '.join(map(str, unique_values))}\n"
        return overview

    def get_transform(self, step_index):
        """
        指定したステップの変換設定を取得する
        Args:
            step_index (int): 変換設定を取得するステップのインデックス
        Returns:
            dict: 変換設定
        """
        assert self.all_steps[step_index]["type"] == "transform"
        return self.all_steps[step_index]["config"]["transform_config"]

    def set_transform(self, step_index, transform_config):
        """
        指定したステップに変換設定を設定する
        Args:
            step_index (int): 変換設定を設定するステップのインデックス
            transform_config (dict): 変換設定の内容
        """
        example_config = """
        {
            "operations": [
                {
                    "operation_type": "add_axis",
                    "target_name": "新しい軸名",
                    "calculation": {
                        "type": "formula",
                        "formula_type": "+",
                        "operands": ["軸A", "軸B"],
                        "constant_value": None
                    },
                },
                {
                    "operation_type": "add_axis",
                    "target_name": "新しい軸名",
                    "calculation": {
                        "type": "formula",
                        "formula_type": "+",
                        "operands": ["軸A"],
                        "constant_value": 123.45
                    },
                },
                {
                    "operation_type": "modify_subject",
                    "target_name": "既存科目名",
                    "calculation": {
                        "type": "copy",
                        "copy_from": "別の科目名"
                    },
                },
                {
                    "operation_type": "add_subject",
                    "target_name": "新しい科目名",
                    "calculation": {
                        "type": "mapping",
                        "mapping_dict": {
                            "元の科目A": 1.0,
                            "元の科目B": 2.0,
                            "元の科目C": 3.0
                        },
                    },
                },
                {
                    "operation_type": "modify_axis",
                    "target_name": "既存軸名",
                    "calculation": {
                        "type": "constant",
                        "constant_value": 100.0
                    },
                },
            ]
        }
        """
        example_config = example_config.replace("\n", "")
        if self.all_steps[step_index]["type"] != "transform":
            raise ValueError("変換はtransformタイプのステップにのみ設定できます。")

        if not isinstance(transform_config, dict):
            raise ValueError("変換設定は辞書型である必要があります。" + "例: " + example_config)

        if "operations" not in transform_config or not isinstance(transform_config["operations"], list):
            raise ValueError("変換設定には'operations'をリストとして含める必要があります。" + "例: " + example_config)

        source_data = self.get_source_data(step_index)
        assert isinstance(source_data, pd.DataFrame)
        available_axes = set(source_data.columns) - {"値", "科目"}
        available_subjects = set(source_data["科目"].values)

        for operation in transform_config["operations"]:
            required_keys = {"operation_type", "target_name", "calculation"}
            if not required_keys.issubset(set(operation.keys())):
                raise ValueError(f"各操作には'operation_type', 'target_name', 'calculation'が必要です。例: {example_config}")

            if operation["operation_type"] not in ["add_axis", "modify_axis", "add_subject", "modify_subject"]:
                raise ValueError(
                    f"サポートされていないoperation_type: {operation['operation_type']}。"
                    "'add_axis', 'modify_axis', 'add_subject', 'modify_subject'のいずれかを指定してください。"
                    f"例: {example_config}"
                )
            target_type = "axis" if "axis" in operation["operation_type"] else "subject"

            calculation = operation["calculation"]
            if calculation["type"] not in ["formula", "constant", "copy", "mapping"]:
                raise ValueError(f"サポートされていない計算タイプ: {calculation['type']}")

            # 計算式の妥当性チェック
            if calculation["type"] == "formula":
                operands = calculation.get("operands", [])
                constant_value = calculation.get("constant_value", None)
                formula_type = calculation.get("formula_type", None)
                if formula_type not in ["+", "-", "*", "/"]:
                    raise ValueError(f"サポートされていないformula_type: {formula_type}。'+', '-', '*', '/'のいずれかを指定してください。")
                if not isinstance(operands, list):
                    raise ValueError("operandsはリストである必要があります。" + "例: " + example_config)
                if len(operands) != 2 and constant_value is None:
                    raise ValueError("constant_valueが指定されていない場合、operandsには2つの要素が必要です。" + "例: " + example_config)
                if len(operands) != 1 and constant_value is not None:
                    raise ValueError("constant_valueが指定されている場合、operandsには1つの要素が必要です。" + "例: " + example_config)
                if constant_value is not None and not isinstance(constant_value, (int, float)):
                    raise ValueError("constant_valueは数値である必要があります。" + "例: " + example_config)
                if target_type == "axis":
                    # 軸レベルの操作の場合、軸名をチェック
                    for operand in operands:
                        if operand not in available_axes:
                            raise ValueError(f"operand '{operand}' が利用可能な軸に見つかりません: {available_axes}")
                elif target_type == "subject":
                    # 科目レベルの操作の場合、科目名をチェック
                    for operand in operands:
                        if operand not in available_subjects:
                            raise ValueError(f"operand '{operand}' が利用可能な科目に見つかりません: {available_subjects}")
            # copyの妥当性チェック
            elif calculation["type"] == "copy":
                copy_from = calculation.get("copy_from", None)
                if copy_from is None:
                    raise ValueError("copy計算には'copy_from'が必要です。" + "例: " + example_config)
                if target_type == "axis":
                    if copy_from not in available_axes:
                        raise ValueError(f"コピー元の軸 '{copy_from}' が利用可能な軸に見つかりません: {available_axes}")
                elif target_type == "subject":
                    if copy_from not in available_subjects:
                        raise ValueError(f"コピー元の科目 '{copy_from}' が利用可能な科目に見つかりません: {available_subjects}")
            # constantの妥当性チェック
            elif calculation["type"] == "constant":
                constant_value = calculation.get("constant_value", None)
                if constant_value is None:
                    raise ValueError("constant計算には値が必要です。" + "例: " + example_config)
            # mappingの妥当性チェック
            elif calculation["type"] == "mapping":
                mapping_dict = calculation.get("mapping_dict", None)
                if mapping_dict is None or not isinstance(mapping_dict, dict):
                    raise ValueError("mapping計算には'mapping_dict'を辞書として含める必要があります。" + "例: " + example_config)
                if target_type == "subject":
                    for key in mapping_dict.keys():
                        if key not in available_subjects:
                            raise ValueError(f"マッピングキー '{key}' が利用可能な科目に見つかりません: {available_subjects}")

        # 変換設定を保存
        self.all_steps[step_index]["config"]["transform_config"] = transform_config

        self.apply(step_index)  # Apply the step to ensure data is processed

        data = self.all_steps[step_index]["result_data"]
        overview = "結果データの概要:\n"
        overview += f"  データ: {len(data)}件\n  軸:\n"
        for col in data.columns:
            if col == "値":
                continue
            unique_values = data[col].unique()
            overview += f"    {col}: {', '.join(map(str, unique_values))}\n"
        return overview

    def get_data_overview(self):
        """
        original_df,及び全てのステップの結果データの概要を取得する。
        データ件数、コラム名と値の概要を返す。
        Returns:
            str: データの件数と各カラムの情報
        """
        data_list = [self.original_df]
        data_list += [step["result_data"] for step in self.all_steps if step["result_data"] is not None]
        overview = "データの概要:\n"
        for i, data in enumerate(data_list):
            if i == 0:
                overview += "\nデータセット original:\n"
            else:
                overview += f"\nデータセット step_{i}:\n"
            if data is None or data.empty:
                overview += "データ: 空のデータ\n"
                continue
            overview += f"データ: {len(data)}件\n"
            for col in data.columns:
                if col == "値":
                    continue
                unique_values = data[col].unique()
                overview += f"  {col}: {', '.join(map(str, unique_values))}\n"
        return overview

    def get_step_overview(self):
        """
        現在の全ての分析ステップの概要を取得する。
        各ステップの名前、タイプ、データソース、実行状態を返す。
        Returns:
            str: ステップの概要
        """
        if not self.all_steps:
            return "分析ステップは作成されていません"

        overview = "現在の分析ステップ:\n\n"
        for i, step in enumerate(self.all_steps):
            step_type = step.get("type", "unknown")
            step_name = step.get("name", f"ステップ{i + 1}")
            data_source = step.get("data_source", "original")

            overview += f"Step {i}: {step_name} ({step_type})\n"
            overview += f"  - データソース: {data_source}\n"

            if step_type == "filter":
                category_filter = step["config"].get("category_filter", {})
                overview += f"  - カテゴリーフィルタ: {', '.join([f'{k}: {v}' for k, v in category_filter.items()])}\n"

                numeric_filter = step["config"].get("numeric_filter", {})
                filter_type = numeric_filter.get("filter_type", "range")

                if filter_type == "range":
                    if numeric_filter.get("enable_min") and not numeric_filter.get("enable_max"):
                        overview += (
                            f"  - 数値フィルタ(範囲): 最小値 {numeric_filter['min_value']} "
                            f"({'含む' if numeric_filter.get('include_min') else '含まない'})\n"
                        )
                    elif not numeric_filter.get("enable_min") and numeric_filter.get("enable_max"):
                        overview += (
                            f"  - 数値フィルタ(範囲): 最大値 {numeric_filter['max_value']} "
                            f"({'含む' if numeric_filter.get('include_max') else '含まない'})\n"
                        )
                    elif numeric_filter.get("enable_min") and numeric_filter.get("enable_max"):
                        overview += (
                            "  - 数値フィルタ(範囲): "
                            f"最小値 {numeric_filter['min_value']} ({'含む' if numeric_filter.get('include_min') else '含まない'}), "
                            f"最大値 {numeric_filter['max_value']} ({'含む' if numeric_filter.get('include_max') else '含まない'})\n"
                        )
                    else:
                        overview += "  - 数値フィルタ(範囲): 設定なし\n"

                elif filter_type == "topk":
                    k_value = numeric_filter.get("k_value", 0)
                    if k_value > 0:
                        ascending = numeric_filter.get("ascending", False)
                        order_text = "下位" if ascending else "上位"
                        overview += f"  - 数値フィルタ(TopK): {order_text}{k_value}件を抽出\n"
                    else:
                        overview += "  - 数値フィルタ(TopK): 設定なし\n"

                elif filter_type == "percentage":
                    min_pct = numeric_filter.get("min_percentile", 0)
                    max_pct = numeric_filter.get("max_percentile", 100)
                    if min_pct > 0 or max_pct < 100:
                        overview += f"  - 数値フィルタ(パーセンタイル): {min_pct}% - {max_pct}%\n"
                    else:
                        overview += "  - 数値フィルタ(パーセンタイル): 全範囲\n"

                table_filter = step["config"].get("table_filter", {})
                if table_filter.get("enable"):
                    overview += (
                        f"  - テーブルフィルタ: キーカラム {', '.join(table_filter['key_columns'])}, "
                        f"モード: {'除外' if table_filter['exclude_mode'] else '包含'}\n"
                    )

            elif step_type == "aggregate":
                group_by = step["config"].get("group_by_axis", [])
                agg_config = step["config"].get("aggregation_config", [])
                overview += f"  - 集計: グループ化 {', '.join(group_by)}\n"
                overview += f"  - 集計方法: {', '.join([f'{agg["subject"]} ({agg["method"]})' for agg in agg_config])}\n"

            elif step_type == "summary":
                formulas = step["config"].get("formulas", [])
                overview += f"  - 計算式: {len(formulas)}個\n"
                for formula in formulas:
                    overview += f"    - {formula['target_subject']}: {formula['type']} ({formula['unit']})\n"

                chart_config = step["config"].get("chart_config", {})
                if chart_config:
                    chart_type = chart_config.get("graph_type", "unknown")
                    overview += f"  - チャート設定: {chart_type}\n"
                else:
                    overview += "  - チャート設定: なし\n"

                table_config = step["config"].get("table_config", {})
                if table_config:
                    show_source = table_config.get("show_source_data", False)
                    table_name = table_config.get("table_name", "N/A")
                    overview += f"  - テーブル設定: {table_name} (ソースデータ表示: {'あり' if show_source else 'なし'})\n"
                else:
                    overview += "  - テーブル設定: なし\n"

            elif step_type == "transform":
                transform_config = step["config"].get("transform_config", {})
                operations = transform_config.get("operations", [])
                overview += f"  - 変換操作: {len(operations)}個\n"
                for j, operation in enumerate(operations):
                    op_type = operation.get("operation_type", "unknown")
                    target_name = operation.get("target_name", "unknown")
                    calc_type = operation.get("calculation", {}).get("type", "unknown")
                    overview += f"    - {j + 1}. {op_type}: {target_name} ({calc_type})\n"

        return overview
