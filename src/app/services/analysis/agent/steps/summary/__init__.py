"""サマリーステップの実装。

このモジュールは、分析結果のサマリーと可視化機能を提供します。
camp-backend-code-analysisのsummary/funcs_formula.pyとfuncs_chart.pyから移植しています。

主な機能:
    - 数式計算: 集計値の計算、四則演算
    - グラフ生成: Plotlyを使用した8種類のグラフ

使用例:
    >>> from app.services.analysis.agent.steps.summary import SummaryStep
    >>>
    >>> summary_step = SummaryStep()
    >>> result = await summary_step.execute(
    ...     source_data=df,
    ...     config={
    ...         "formula": [
    ...             {"target_subject": "売上", "type": "sum", "formula_text": "売上合計", "unit": "円"}
    ...         ],
    ...         "chart": {
    ...             "graph_type": "bar",
    ...             "x_axis": "地域",
    ...             "y_axis": "売上"
    ...         }
    ...     }
    ... )
"""

from typing import Any

import pandas as pd
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.schemas.analysis import AnalysisResultFormula, AnalysisSummaryConfig, FormulaItemConfig
from app.services.analysis.agent.steps.base import AnalysisStepResult, BaseAnalysisStep

logger = get_logger(__name__)

# 対応している数式タイプ
SUPPORTED_FORMULA_TYPES = ["sum", "mean", "count", "max", "min", "+", "-", "*", "/", "arithmetic"]

# 対応しているグラフタイプ
SUPPORTED_GRAPH_TYPES = [
    "bar",
    "line",
    "pie",
    "scatter",
    "heatmap",
    "box",
    "histogram",
    "area",
    "waterfall",
    "sunburst",
    "treemap",
    # エイリアス
    "horizontal_bar",
    "stacked_bar",
    "line_bar",
]


class SummaryStep(BaseAnalysisStep):
    """サマリーステップ。

    分析結果を要約・可視化します。

    Attributes:
        step_type (str): "summary"

    Example:
        >>> summary_step = SummaryStep()
        >>> config = {
        ...     "formula": [
        ...         {"target_subject": "売上", "type": "sum", "formula_text": "売上合計", "unit": "円"},
        ...         {"target_subject": ["売上合計", "100"], "type": "/", "formula_text": "売上（百円）", "unit": "百円"}
        ...     ],
        ...     "chart": {
        ...         "graph_type": "bar",
        ...         "x_axis": "地域",
        ...         "y_axis": "売上"
        ...     }
        ... }
        >>> result = await summary_step.execute(df, config)
    """

    step_type = "summary"

    async def validate_config(
        self,
        config: dict[str, Any],
        source_data: pd.DataFrame | None = None,
    ) -> None:
        """サマリー設定を検証します。

        Args:
            config: サマリー設定
            source_data: ソースデータ

        Raises:
            ValidationError: 設定が不正な場合
        """
        logger.debug("サマリー設定を検証中")

        try:
            summary_config = AnalysisSummaryConfig.model_validate(config)
        except PydanticValidationError as e:
            raise ValidationError(
                "サマリー設定の形式が不正です",
                details={"validation_errors": e.errors()},
            ) from e

        # chartの追加検証（graph_type）
        if summary_config.chart is not None and "graph_type" in summary_config.chart:
            graph_type = summary_config.chart["graph_type"]
            if graph_type not in SUPPORTED_GRAPH_TYPES:
                raise ValidationError(
                    f"未対応のgraph_typeです: {graph_type}",
                    details={"graph_type": graph_type, "supported": SUPPORTED_GRAPH_TYPES},
                )

        logger.debug("サマリー設定の検証が完了しました")

    async def execute(
        self,
        source_data: pd.DataFrame,
        config: dict[str, Any],
        **kwargs: Any,
    ) -> AnalysisStepResult:
        """サマリーを実行します。

        Args:
            source_data: ソースデータ
            config: サマリー設定
            **kwargs: 追加パラメータ

        Returns:
            AnalysisStepResult: サマリー結果
                - result_data: 元データまたはNone
                - result_chart: チャート情報（Plotly JSON）
                - result_formula: 計算式結果
        """
        try:
            summary_config = AnalysisSummaryConfig.model_validate(config)
        except PydanticValidationError as e:
            raise ValidationError(
                "サマリー設定の形式が不正です",
                details={"validation_errors": e.errors()},
            ) from e

        logger.info(
            "サマリーを実行中",
            rows=len(source_data),
            has_formula=summary_config.formula is not None,
            has_chart=summary_config.chart is not None,
        )

        result_formula = None
        result_chart = None

        # 数式計算
        if summary_config.formula is not None:
            result_formula = await self._apply_formula(source_data, summary_config.formula)
            logger.debug("数式計算完了", formulas_count=len(result_formula))

        # グラフ生成
        if summary_config.chart is not None:
            result_chart = await self._apply_chart(source_data, summary_config.chart)
            logger.debug("グラフ生成完了", graph_type=summary_config.chart.get("graph_type"))

        logger.info(
            "サマリーが完了しました",
            has_formula=result_formula is not None,
            has_chart=result_chart is not None,
        )

        # result_dataは元データを保持（オプション）
        result_data = source_data if config.get("table", {}).get("show_source_data", False) else None

        return AnalysisStepResult(
            result_data=result_data,
            result_chart=result_chart,
            result_formula=result_formula,
        )

    async def _apply_formula(
        self,
        source_data: pd.DataFrame,
        formulas: list[FormulaItemConfig],
    ) -> list[AnalysisResultFormula]:
        """数式計算を適用します。

        Args:
            source_data: ソースデータ
            formulas: 計算式設定のリスト

        Returns:
            list[AnalysisResultFormula]: 計算結果のリスト

        Example:
            >>> formulas = [
            ...     FormulaItemConfig(target_subject="売上", type="sum", formula_text="売上合計", unit="円"),
            ... ]
            >>> result = await self._apply_formula(df, formulas)
            >>> print([f.model_dump() for f in result])
            [{"name": "売上合計", "formula": "sum", "result": 1000000.0, "unit": "円"}]
        """
        logger.debug("数式計算を実行中", formulas_count=len(formulas))

        results = []
        intermediate_results = {}  # 中間結果を保持（四則演算用）

        for formula in formulas:
            target_subject = formula.target_subject
            formula_type = formula.type
            formula_text = formula.formula_text
            unit = formula.unit if formula.unit is not None else ""
            portion = formula.portion  # 重み係数

            if formula_type in ["sum", "mean", "count", "max", "min"]:
                # 基本集計
                if target_subject not in source_data.columns:
                    raise ValidationError(
                        f"カラムが存在しません: {target_subject}",
                        details={"target_subject": target_subject},
                    )

                if formula_type == "sum":
                    result = source_data[target_subject].sum() * portion
                elif formula_type == "mean":
                    result = source_data[target_subject].mean() * portion
                elif formula_type == "count":
                    result = source_data[target_subject].count() * portion
                elif formula_type == "max":
                    result = source_data[target_subject].max() * portion
                elif formula_type == "min":
                    result = source_data[target_subject].min() * portion

                intermediate_results[formula_text] = result

            elif formula_type == "arithmetic":
                # 算術式の実行（例: "sales - cost"）
                try:
                    # DataFrameのカラムをローカル変数として使用可能にする
                    local_vars = {col: source_data[col] for col in source_data.columns}
                    result_series = eval(formula_text, {"__builtins__": {}}, local_vars)

                    # Seriesの場合は合計を返す
                    if hasattr(result_series, "sum"):
                        result = result_series.sum() * portion
                    else:
                        result = result_series * portion

                    intermediate_results[formula_text] = result
                except Exception as e:
                    raise ValidationError(
                        f"算術式の評価に失敗しました: {formula_text}",
                        details={"error": str(e), "formula_text": formula_text},
                    ) from e

            elif formula_type in ["+", "-", "*", "/"]:
                # 四則演算
                if not isinstance(target_subject, list) or len(target_subject) != 2:
                    raise ValidationError(
                        "四則演算のtarget_subjectは2要素のlistである必要があります",
                        details={"target_subject": target_subject},
                    )

                left_name, right_name = target_subject

                # 中間結果から取得
                if left_name not in intermediate_results:
                    raise ValidationError(
                        f"未定義の計算式を参照しています: {left_name}",
                        details={"reference": left_name},
                    )

                if right_name not in intermediate_results:
                    raise ValidationError(
                        f"未定義の計算式を参照しています: {right_name}",
                        details={"reference": right_name},
                    )

                left_value = intermediate_results[left_name]
                right_value = intermediate_results[right_name]

                if formula_type == "+":
                    result = (left_value + right_value) * portion
                elif formula_type == "-":
                    result = (left_value - right_value) * portion
                elif formula_type == "*":
                    result = (left_value * right_value) * portion
                elif formula_type == "/":
                    if right_value == 0:
                        result = None
                    else:
                        result = (left_value / right_value) * portion

                intermediate_results[formula_text] = result

            # result が pandas Series の場合は値を抽出
            final_result: float
            if result is None:
                final_result = 0.0
            elif hasattr(result, "item"):
                # pandas の scalar 型（numpy scalar など）
                final_result = float(result.item())  # type: ignore[arg-type]
            elif isinstance(result, int | float):
                final_result = float(result)
            else:
                # Series や他の型の場合、値を抽出
                try:
                    final_result = float(result)  # type: ignore[arg-type]
                except (TypeError, ValueError) as e:
                    raise ValidationError(
                        f"計算結果をfloatに変換できません: {type(result)}",
                        details={"result_type": type(result).__name__},
                    ) from e

            results.append(
                AnalysisResultFormula(
                    name=formula_text,
                    formula=formula_type,  # 計算式タイプ（sum, mean, +, - など）
                    result=final_result,
                    unit=unit if unit else None,
                )
            )

        logger.debug("数式計算完了", results_count=len(results))

        return results

    async def _apply_chart(
        self,
        source_data: pd.DataFrame,
        chart_config: dict[str, Any],
    ) -> dict[str, Any]:
        """グラフ生成を適用します。

        11種類のグラフをサポート:
            - bar: 棒グラフ
            - line: 折れ線グラフ
            - pie: 円グラフ
            - scatter: 散布図
            - heatmap: ヒートマップ
            - box: 箱ひげ図
            - histogram: ヒストグラム
            - area: 面グラフ
            - waterfall: ウォーターフォール図
            - sunburst: サンバースト図
            - treemap: ツリーマップ

        Args:
            source_data: ソースデータ
            chart_config: グラフ設定
                - graph_type (str): グラフタイプ
                - その他: グラフタイプ固有のパラメータ

        Returns:
            dict: Plotly JSON形式のグラフ

        Raises:
            ValidationError: グラフタイプが不正な場合

        Example:
            >>> chart = await self._apply_chart(
            ...     df,
            ...     {"graph_type": "bar", "x_axis": "地域", "y_axis": "売上"}
            ... )
        """
        from app.services.analysis.agent.steps.summary.graphs import (
            AreaGraph,
            BarGraph,
            BoxGraph,
            HeatmapGraph,
            HistogramGraph,
            LineGraph,
            PieGraph,
            ScatterGraph,
            SunburstGraph,
            TreemapGraph,
            WaterfallGraph,
        )

        graph_type = chart_config.get("graph_type", "bar")

        logger.debug("グラフ生成中", graph_type=graph_type)

        # グラフクラスマッピング
        graph_classes = {
            "bar": BarGraph,
            "line": LineGraph,
            "pie": PieGraph,
            "scatter": ScatterGraph,
            "heatmap": HeatmapGraph,
            "box": BoxGraph,
            "histogram": HistogramGraph,
            "area": AreaGraph,
            "waterfall": WaterfallGraph,
            "sunburst": SunburstGraph,
            "treemap": TreemapGraph,
            # エイリアス
            "horizontal_bar": BarGraph,  # orientation='h'で実装
            "stacked_bar": BarGraph,  # barmode='stack'で実装
            "line_bar": LineGraph,  # 複数系列で実装可能
        }

        if graph_type not in graph_classes:
            raise ValidationError(
                f"未対応のgraph_typeです: {graph_type}",
                details={"graph_type": graph_type, "supported": list(graph_classes.keys())},
            )

        # グラフインスタンス作成
        graph_class = graph_classes[graph_type]
        graph = graph_class()

        # グラフ生成
        try:
            fig = graph.create(source_data, **chart_config)

            # Plotly JSONに変換
            chart_json = fig.to_dict()

            logger.debug("グラフ生成完了", graph_type=graph_type)

            return chart_json

        except Exception as e:
            logger.error(
                "グラフ生成エラー",
                graph_type=graph_type,
                error=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"グラフ生成に失敗しました: {str(e)}",
                details={"graph_type": graph_type, "config": chart_config},
            ) from e
