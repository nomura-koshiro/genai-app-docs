import json

from langchain.tools import BaseTool
from langchain_core.callbacks import BaseCallbackHandler

from ..state import AnalysisState


class ToolTrackingHandler(BaseCallbackHandler):
    def __init__(self):
        self.tool_usage = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "unknown tool")
        self.tool_usage.append({"tool": tool_name, "input": input_str})

    def on_tool_end(self, output, **kwargs):
        if self.tool_usage:  # 最後に使用したツールの出力を追加
            self.tool_usage[-1]["output"] = output


class GetDataOverviewTool(BaseTool):
    name: str = "get_data_overview"
    description: str = "現在のデータセットの概要を取得します。データセットの数、各データセットの行数、列名などを含みます。"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        overview = self.analysis_state.get_data_overview()
        return overview


class GetStepOverviewTool(BaseTool):
    name: str = "get_step_overview"
    description: str = "現在の分析ステップの概要を取得します。各ステップの設定、フィルタ条件、結果データの概要などを含みます。"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        overview = self.analysis_state.get_step_overview()
        return overview


class AddStepTool(BaseTool):
    name: str = "add_step"
    description: str = (
        "新しい分析ステップを追加します。入力形式: "
        "'step_name, step_type('filter', 'summary', 'aggregate' のいずれか), "
        "data_source('original', 'step_0', 'step_1', ... のいずれか)' "
    )
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            parts = input_str.split(",", 2)
            if len(parts) == 3:
                step_name = parts[0].strip()
                step_type = parts[1].strip().lower()
                data_source = parts[2].strip().lower()
            else:
                return "実行失敗: 入力形式が不正です。形式: 'step_name, step_type', 'data_source'"

            if step_type not in ["filter", "summary", "aggregate", "transform"]:
                return (
                    "実行失敗: ステップタイプが不正です。"
                    "'filter', 'summary', 'aggregate', 'transform' のいずれかを指定してください。"
                    f"現在の指定値: {step_type}。"
                )

            # ステップを追加
            self.analysis_state.add_step(step_name, step_type, data_source)
            if step_type == "filter":
                example_prompt = """
{
    "category_filter": {
        "コラム1": [コラム1の値1, コラム1の値2],
        "コラム2": [コラム2の値1, コラム2の値2]
    },
    "numeric_filter": {
        "column": "値",
        "filter_type": "range | topk | percentage",

        // rangeタイプの場合
        "enable_min": 最小値を有効にするかどうか,
        "min_value": 最小値,
        "include_min": 最小値を含むかどうか,
        "enable_max": 最大値を有効にするかどうか,
        "max_value": 最大値,
        "include_max": 最大値を含むかどうか,

        // topkタイプの場合
        "k_value": 抽出件数,
        "ascending": false(上位K件) | true(下位K件),

        // percentageタイプの場合
        "min_percentile": 下位パーセンタイル(0-100),
        "max_percentile": 上位パーセンタイル(0-100)
    },
    "table_filter": {
        "table_df": str,  # フィルタ対象のDataFrame
        "key_columns": [フィルタ対象のキーとなるカラム名1, フィルタ対象のキーとなるカラム名2],
        "exclude_mode": 除外モードかどうか,  # Trueなら除外、Falseなら包含
        "enable": テーブルフィルタを有効にするかどうか
    }
}
"""
            elif step_type == "summary":
                example_prompt = """
{
    "formulas": [
        {"target_subject": "科目1", "type": 計算方法, "formula_text": 計算式の名称, "unit": 単位},
        {"target_subject": "科目2", "type": 計算方法, "formula_text": 計算式の名称, "unit": 単位},
    ]
    "chart_config": {
        "graph_type": "グラフの種類",
        ... (# グラフの種類に応じて様々な設定が必要です)
    },
    "table_config": {
        "show_source_data": ソースデータを表示するかどうか,
        "table_name": "テーブルの名称"
    }
}
"""
            elif step_type == "aggregate":
                example_prompt = """
{
    "group_by_axis": ["コラム1", "コラム2"],
    "aggregation_config":[{"subject": "科目1", "method": "sum"}, {"subject": "科目2", "method": "mean"}]
}
"""
            elif step_type == "transform":
                example_prompt = """
{
    "operations": [
        {
            "operation_type": "add_axis | modify_axis | add_subject | modify_subject",
            "target_name": "新しい名前または変更する名前",
            "calculation": {
                "type": "constant | copy | formula | mapping",

                // constantタイプの場合
                "constant_value": 定数値,

                // copyタイプの場合
                "copy_from": "コピー元の軸名または科目名",

                // formulaタイプの場合
                "formula_type": "+ | - | * | /",
                "operands": ["軸名1", "軸名2"] または ["科目名1", "科目名2"],
                "constant_value": 定数値（定数との計算の場合）,

                // mappingタイプの場合
                "operands": ["変換元の軸名または科目名"],
                "mapping_dict": {"元の値1": "新しい値1", "元の値2": "新しい値2"}
            }
        }
    ]
}
"""
            msg = (
                f"ステップインデックス: {len(self.analysis_state.all_steps) - 1}に、"
                f"ステップ「{step_name}」（タイプ: {step_type}, データソース: {data_source}）を追加しました。"
            )
            msg += f"\n\n以下の設定例を参考にして具体的なsetをしてください。 {example_prompt}"
            return msg

        except Exception as e:
            return f"実行失敗: ステップの追加中にエラーが発生しました: {str(e)}"


class DeleteStepTool(BaseTool):
    name: str = "delete_step"
    description: str = "指定したインデックスの分析ステップを削除します。入力形式: 'step_index' (数値)"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            step_index_str = input_str.strip()
            if not step_index_str:
                return "実行失敗: ステップインデックスが指定されていません。形式: 'step_index'"

            try:
                step_index = int(step_index_str)
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {step_index_str}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            # 削除前にステップ名を取得
            step_name = self.analysis_state.all_steps[step_index].get("name", f"ステップ{step_index}")

            # ステップを削除
            self.analysis_state.delete_step(step_index)

            return f"ステップ{step_index}「{step_name}」を削除しました。残りステップ数: {len(self.analysis_state.all_steps)}"

        except Exception as e:
            return f"実行失敗: ステップの削除中にエラーが発生しました: {str(e)}"


# class GetFormulaTool(BaseTool):
#     name: str = "get_formula"
#     description: str = "指定したステップの計算式設定を取得します。入力形式: 'step_index' (数値)"
#     analysis_state: AnalysisState

#     def __init__(self, analysis_state: AnalysisState):
#         super().__init__(analysis_state=analysis_state)

#     def _run(self, input_str: str = "") -> str:
#         try:
#             step_index_str = input_str.strip()
#             if not step_index_str:
#                 return "ステップインデックスが指定されていません。形式: 'step_index'"

#             try:
#                 step_index = int(step_index_str)
#             except ValueError:
#                 return f"ステップインデックスは数値で指定してください。指定値: {step_index_str}"

#             if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
#                 return f"ステップインデックスが範囲外です。有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"

#             if self.analysis_state.all_steps[step_index]['type'] != 'summary':
#                 return f"ステップ{step_index}は計算ステップではありません。計算式設定は'summary'タイプのステップでのみ利用可能です。"

#             formulas = self.analysis_state.get_formula(step_index)
#             if not formulas:
#                 return f"ステップ{step_index}には計算式が設定されていません。"

#             result = f"ステップ{step_index}の計算式設定:\n"
#             for i, formula in enumerate(formulas):
#                 result += f"  {i+1}. 科目: {formula['target_subject']}, 計算: {formula['type']}, 単位: {formula['unit']}\n"

#             return result

#         except Exception as e:
#             return f"計算式の取得中にエラーが発生しました: {str(e)}"


class GetFilterTool(BaseTool):
    name: str = "get_filter"
    description: str = "指定したステップのフィルタ設定を取得します。入力形式: 'step_index' (数値)"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            step_index_str = input_str.strip()
            if not step_index_str:
                return "実行失敗: ステップインデックスが指定されていません。形式: 'step_index'"

            try:
                step_index = int(step_index_str)
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {step_index_str}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            if self.analysis_state.all_steps[step_index]["type"] != "filter":
                return (
                    f"実行失敗: ステップ{step_index}はフィルタステップではありません。"
                    "フィルタ設定は'filter'タイプのステップでのみ利用可能です。"
                )

            filters = self.analysis_state.get_filter(step_index)

            result = f"ステップ{step_index}のフィルタ設定:\n"

            # カテゴリフィルタ
            if filters["category_filter"]:
                result += "カテゴリフィルタ:\n"
                for col, values in filters["category_filter"].items():
                    result += f"  {col}: {', '.join(map(str, values))}\n"
            else:
                result += "カテゴリフィルタ: 設定なし\n"

            # 数値フィルタ
            numeric = filters["numeric_filter"]
            filter_type = numeric.get("filter_type", "range")

            result += f"数値フィルタ (タイプ: {filter_type}):\n"

            if filter_type == "range":
                if numeric.get("enable_min", False) or numeric.get("enable_max", False):
                    if numeric.get("enable_min", False):
                        result += f"  最小値: {numeric['min_value']} ({'含む' if numeric.get('include_min', True) else '含まない'})\n"
                    if numeric.get("enable_max", False):
                        result += f"  最大値: {numeric['max_value']} ({'含む' if numeric.get('include_max', True) else '含まない'})\n"
                else:
                    result += "  設定なし\n"

            elif filter_type == "topk":
                k_value = numeric.get("k_value", 0)
                if k_value > 0:
                    ascending = numeric.get("ascending", False)
                    order_text = "下位" if ascending else "上位"
                    result += f"  {order_text}{k_value}件を抽出\n"
                else:
                    result += "  設定なし\n"

            elif filter_type == "percentage":
                min_pct = numeric.get("min_percentile", 0)
                max_pct = numeric.get("max_percentile", 100)
                if min_pct > 0 or max_pct < 100:
                    result += f"  パーセンタイル範囲: {min_pct}% - {max_pct}%\n"
                else:
                    result += "  設定なし (全範囲)\n"

            # テーブルフィルタ
            table = filters["table_filter"]
            if table.get("enable", False):
                result += (
                    "テーブルフィルタ: "
                    f"キーカラム {', '.join(table['key_columns'])}, モード: {'除外' if table['exclude_mode'] else '包含'}\n"
                )
            else:
                result += "テーブルフィルタ: 設定なし\n"

            return result

        except Exception as e:
            return f"実行失敗: フィルタ設定の取得中にエラーが発生しました: {str(e)}"


class GetAggregationTool(BaseTool):
    name: str = "get_aggregation"
    description: str = "指定したステップの集計設定を取得します。入力形式: 'step_index' (数値)"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            step_index_str = input_str.strip()
            if not step_index_str:
                return "実行失敗: ステップインデックスが指定されていません。形式: 'step_index'"

            try:
                step_index = int(step_index_str)
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {step_index_str}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            if self.analysis_state.all_steps[step_index]["type"] != "aggregate":
                return (
                    f"実行失敗: ステップ{step_index}は集計ステップではありません。集計設定は'aggregate'タイプのステップでのみ利用可能です。"
                )

            aggregation = self.analysis_state.get_aggregation(step_index)

            result = f"ステップ{step_index}の集計設定:\n"

            # グループ化軸
            if aggregation["group_by_axis"]:
                result += f"グループ化軸: {', '.join(aggregation['group_by_axis'])}\n"
            else:
                result += "グループ化軸: 設定なし\n"

            # 集計設定
            if aggregation["aggregation_config"]:
                result += "集計設定:\n"
                for agg in aggregation["aggregation_config"]:
                    result += f"  名称: {agg['name']}, 科目: {agg['subject']}, 方法: {agg['method']}\n"
            else:
                result += "集計設定: 設定なし\n"

            return result

        except Exception as e:
            return f"実行失敗: 集計設定の取得中にエラーが発生しました: {str(e)}"


class GetTransformTool(BaseTool):
    name: str = "get_transform"
    description: str = "指定したステップの変換設定を取得します。入力形式: 'step_index' (数値)"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            step_index_str = input_str.strip()
            if not step_index_str:
                return "実行失敗: ステップインデックスが指定されていません。形式: 'step_index'"

            try:
                step_index = int(step_index_str)
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {step_index_str}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            if self.analysis_state.all_steps[step_index]["type"] != "transform":
                return (
                    f"実行失敗: ステップ{step_index}は変換ステップではありません。変換設定は'transform'タイプのステップでのみ利用可能です。"
                )

            transform_config = self.analysis_state.get_transform(step_index)

            result = f"ステップ{step_index}の変換設定:\n"

            operations = transform_config.get("operations", [])
            if operations:
                result += "変換操作:\n"
                for i, operation in enumerate(operations):
                    op_type = operation.get("operation_type", "unknown")
                    target_name = operation.get("target_name", "unknown")
                    calc_type = operation.get("calculation", {}).get("type", "unknown")
                    result += f"  {i + 1}. {op_type}: {target_name} ({calc_type})\n"
            else:
                result += "変換操作: 設定なし\n"

            return result

        except Exception as e:
            return f"実行失敗: 変換設定の取得中にエラーが発生しました: {str(e)}"


class GetSummaryTool(BaseTool):
    name: str = "get_summary"
    description: str = "指定したステップのサマリ設定（計算式とチャート設定）を取得します。入力形式: 'step_index' (数値)"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            step_index_str = input_str.strip()
            if not step_index_str:
                return "実行失敗: ステップインデックスが指定されていません。形式: 'step_index'"

            try:
                step_index = int(step_index_str)
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {step_index_str}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            if self.analysis_state.all_steps[step_index]["type"] != "summary":
                return f"実行失敗: ステップ{step_index}はサマリステップではありません。"

            summary = self.analysis_state.get_summary(step_index)

            result = f"ステップ{step_index}のサマリ設定:\n"

            # 計算式
            if summary["formulas"]:
                result += "計算式:\n"
                for i, formula in enumerate(summary["formulas"]):
                    result += f"  {i + 1}. 科目: {formula['target_subject']}, 計算: {formula['type']}, 単位: {formula['unit']}\n"
            else:
                result += "計算式: 設定なし\n"

            # チャート設定
            if summary["chart_config"]:
                result += f"チャート設定: あり（タイプ: {summary['chart_config'].get('type', 'unknown')}）\n"
            else:
                result += "チャート設定: 設定なし\n"

            # テーブル設定
            if summary["table_config"]:
                if "show_source_data" in summary["table_config"].keys() and summary["table_config"]["show_source_data"]:
                    result += f"テーブル設定: ステップの入力データを表記, 名称: {summary['table_config']['table_name']}\n"
                else:
                    result += "テーブル設定: ステップの入力データをを表記しない\n"

            return result

        except Exception as e:
            return f"実行失敗: サマリ設定の取得中にエラーが発生しました: {str(e)}"


# class SetFormulaTool(BaseTool):
#     name: str = "set_formula"
#     description: str = "指定したステップに計算式を設定します。入力形式: 'step_index, formula_json' (formula_jsonは計算式の配列)"
#     analysis_state: AnalysisState

#     def __init__(self, analysis_state: AnalysisState):
#         super().__init__(analysis_state=analysis_state)

#     def _run(self, input_str: str = "") -> str:
#         try:
#             parts = input_str.split(',', 1)
#             if len(parts) != 2:
#                 return "入力形式が不正です。形式: 'step_index, formula_json'"

#             try:
#                 step_index = int(parts[0].strip())
#             except ValueError:
#                 return f"ステップインデックスは数値で指定してください。指定値: {parts[0].strip()}"

#             if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
#                 return f"ステップインデックスが範囲外です。有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"

#             if self.analysis_state.all_steps[step_index]['type'] != 'summary':
#                 return f"ステップ{step_index}は計算ステップではありません。計算式設定は'summary'タイプのステップでのみ利用可能です。"

#             try:
#                 formula_json = json.loads(parts[1].strip())
#             except json.JSONDecodeError as e:
#                 return f"JSON形式が不正です: {str(e)}"

#             self.analysis_state.set_formula(step_index, formula_json)

#             return f"ステップ{step_index}に計算式を設定しました。計算式数: {len(formula_json)}"

#         except Exception as e:
#             return f"計算式の設定中にエラーが発生しました: {e.args[0] if hasattr(e, 'args') and e.args else str(e)}"


class SetFilterTool(BaseTool):
    name: str = "set_filter"
    description: str = "指定したステップにフィルタ設定を適用します。入力形式: 'step_index, filter_json' (filter_jsonはフィルタ設定のJSON)"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "実行失敗: 入力形式が不正です。形式: 'step_index, filter_json'"

            try:
                step_index = int(parts[0].strip())
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {parts[0].strip()}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            if self.analysis_state.all_steps[step_index]["type"] != "filter":
                return (
                    f"実行失敗: ステップ{step_index}はフィルタステップではありません。"
                    "フィルタ設定は'filter'タイプのステップでのみ利用可能です。"
                )

            try:
                filter_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"フィルタ設定中にエラーが発生しました: JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            result_overview = self.analysis_state.set_filter(step_index, filter_json)
            return f"ステップ{step_index}にフィルタ設定を適用しました。\n{result_overview}"

        except Exception as e:
            return f"実行失敗: フィルタ設定中にエラーが発生しました: {str(e)}"


class SetAggregationTool(BaseTool):
    name: str = "set_aggregation"
    description: str = "指定したステップに集計設定を適用します。入力形式: 'step_index, aggregation_json' (aggregation_jsonは集計設定のJSON)"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "実行失敗: 入力形式が不正です。形式: 'step_index, aggregation_json'"

            try:
                step_index = int(parts[0].strip())
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {parts[0].strip()}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            if self.analysis_state.all_steps[step_index]["type"] != "aggregate":
                return (
                    f"実行失敗: ステップ{step_index}は集計ステップではありません。集計設定は'aggregate'タイプのステップでのみ利用可能です。"
                )

            try:
                aggregation_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"実行失敗: 集計設定中にエラーが発生しました: JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            result_overview = self.analysis_state.set_aggregation(step_index, aggregation_json)
            return f"ステップ{step_index}に集計設定を適用しました。\n{result_overview}"

        except Exception as e:
            return f"実行失敗: 集計設定中にエラーが発生しました: {str(e)}"


class SetTransformTool(BaseTool):
    name: str = "set_transform"
    description: str = "指定したステップに変換設定を適用します。入力形式: 'step_index, transform_json' (transform_jsonは変換設定のJSON)"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "実行失敗: 入力形式が不正です。形式: 'step_index, transform_json'"

            try:
                step_index = int(parts[0].strip())
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {parts[0].strip()}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            if self.analysis_state.all_steps[step_index]["type"] != "transform":
                return (
                    f"実行失敗: ステップ{step_index}は変換ステップではありません。変換設定は'transform'タイプのステップでのみ利用可能です。"
                )

            try:
                transform_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"実行失敗: 変換設定中にエラーが発生しました: JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            result_overview = self.analysis_state.set_transform(step_index, transform_json)
            return f"ステップ{step_index}に変換設定を適用しました。\n{result_overview}"

        except Exception as e:
            return f"実行失敗: 変換設定中にエラーが発生しました: {str(e)}"


class SetSummaryTool(BaseTool):
    name: str = "set_summary"
    description: str = "指定したステップにサマリ設定（計算式とチャート設定）を設定します。入力形式: 'step_index, summary_json'"
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "実行失敗: 入力形式が不正です。形式: 'step_index, summary_json'"

            try:
                step_index = int(parts[0].strip())
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {parts[0].strip()}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            if self.analysis_state.all_steps[step_index]["type"] != "summary":
                return f"実行失敗: ステップ{step_index}はサマリステップではありません。"

            try:
                summary_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"実行失敗: サマリ設定中にエラーが発生しました:  JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            self.analysis_state.set_summary(step_index, summary_json)

            formulas_count = len(summary_json.get("formulas", []))
            chart_status = "あり" if summary_json.get("chart_config") else "なし"
            table_config = summary_json.get("table_config", {})
            if table_config.get("show_source_data", False):
                table_status = f"{table_config.get('table_name', '名称未設定')} で表記"
            else:
                table_status = "表記しない"

            return (
                "ステップ{step_index}にサマリ設定を適用しました。"
                f"計算式: {formulas_count}個, チャート設定: {chart_status}, テーブル設定: {table_status}"
            )

        except Exception as e:
            return f"実行失敗: サマリ設定中にエラーが発生しました: {str(e)}"


class GetDataValueTool(BaseTool):
    name: str = "get_data_value"
    description: str = (
        "指定したステップの入力データから特定の軸・科目の組み合わせに対応する値を取得します。"
        "入力形式: 'step_index, filter_json' "
        '(例: \'0, {{"科目": "利益", "地域": "日本", "製品": "自動車部品"}}\')'
    )
    analysis_state: AnalysisState

    def __init__(self, analysis_state: AnalysisState):
        super().__init__(analysis_state=analysis_state)

    def _run(self, input_str: str = "") -> str:
        try:
            parts = input_str.split(",", 1)
            if len(parts) != 2:
                return "入力形式が不正です。形式: 'step_index, filter_json'"

            try:
                step_index = int(parts[0].strip())
            except ValueError:
                return f"実行失敗: ステップインデックスは数値で指定してください。指定値: {parts[0].strip()}"

            if step_index < 0 or step_index >= len(self.analysis_state.all_steps):
                return (
                    "実行失敗: ステップインデックスが範囲外です。"
                    f"有効範囲: 0-{len(self.analysis_state.all_steps) - 1}, 指定値: {step_index}"
                )

            try:
                filter_json = json.loads(parts[1].strip())
            except json.JSONDecodeError as e:
                return f"実行失敗: JSON形式が不正です、入力をチェックしてやり直してください。 {str(e)}"

            if not isinstance(filter_json, dict):
                return "実行失敗: フィルタ条件は辞書形式で指定してください。例: {'科目': '利益', '地域': '日本'}"

            # ステップの入力データを取得
            source_data = self.analysis_state.get_source_data(step_index)

            if source_data is None or source_data.empty:
                return f"ステップ{step_index}の入力データが存在しません。"

            # フィルタ条件を適用してデータを絞り込み
            filtered_data = source_data.copy()

            for column, value in filter_json.items():
                if column not in filtered_data.columns:
                    available_columns = list(filtered_data.columns)
                    return f"指定された列 '{column}' がデータに存在しません。利用可能な列: {', '.join(available_columns)}"
                if isinstance(value, list):
                    return "実行失敗: 値は単一の値で指定してください。リスト形式はサポートされていません。"

                # 値のマッチング
                mask = filtered_data[column] == value
                if not mask.any():
                    unique_values = filtered_data[column].unique()
                    return (
                        f"実行失敗: 指定された値 '{value}' が列 '{column}' に存在しません。"
                        f"利用可能な値: {', '.join(map(str, unique_values))}"
                    )

                filtered_data = filtered_data[mask]

            # 結果の確認
            if filtered_data.empty:
                return f"指定された条件 {filter_json} に一致するデータが見つかりませんでした。"

            if len(filtered_data) == 1:
                # 単一の値が見つかった場合
                value = filtered_data.iloc[0]["値"] if "値" in filtered_data.columns else "値列が見つかりません"
                condition_str = ", ".join([f"{k}='{v}'" for k, v in filter_json.items()])
                return f"ステップ{step_index}の入力データで条件 ({condition_str}) に該当する値: {value}"

            else:
                # 複数の値が見つかった場合
                if "値" in filtered_data.columns:
                    values = filtered_data["値"].tolist()
                    condition_str = ", ".join([f"{k}='{v}'" for k, v in filter_json.items()])
                    return (
                        f"ステップ{step_index}の入力データで条件 ({condition_str}) に該当する値が複数見つかりました: "
                        f"{values} (合計{len(values)}件)"
                    )
                else:
                    return f"指定された条件に該当するデータが{len(filtered_data)}件見つかりましたが、値列が存在しません。"

        except Exception as e:
            return f"実行失敗: データ値の取得中にエラーが発生しました: {str(e)}"
