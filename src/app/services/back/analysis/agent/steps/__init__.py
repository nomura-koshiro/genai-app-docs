"""分析ステップサービスモジュール。

このパッケージは、データ分析の各ステップ（filter, aggregate, transform, summary）の
実装を提供します。

主な機能:
    - filter: データフィルタリング
    - aggregate: データ集計
    - transform: データ変換
    - summary: 結果サマリー・可視化

使用例:
    >>> from app.services.analysis_steps import FilterStep
    >>> from app.services.analysis.agent.steps.base import AnalysisStepResult
    >>>
    >>> filter_step = FilterStep()
    >>> result = await filter_step.execute(
    ...     source_data=df,
    ...     config={"category_filter": {"地域": ["東京"]}}
    ... )
"""

from app.services.analysis.agent.steps.aggregation import AggregationStep
from app.services.analysis.agent.steps.base import AnalysisStepResult, BaseAnalysisStep
from app.services.analysis.agent.steps.filter import FilterStep
from app.services.analysis.agent.steps.summary import SummaryStep
from app.services.analysis.agent.steps.transform import TransformStep

__all__ = [
    "BaseAnalysisStep",
    "AnalysisStepResult",
    "FilterStep",
    "AggregationStep",
    "TransformStep",
    "SummaryStep",
]
