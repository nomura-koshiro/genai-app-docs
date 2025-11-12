"""分析関連のPydanticスキーマパッケージ。

このパッケージは、分析機能に関連するすべてのスキーマを提供します。

モジュール:
    config: 分析ステップ設定スキーマ (FilterConfig, AggregateConfig等)
    session: 分析セッション関連スキーマ (AnalysisChatMessage, ResultFormula等)
    template: 分析テンプレート関連スキーマ (InitialAxisConfig等)

使用方法:
    >>> from app.schemas.analysis import AnalysisChatMessage, FilterConfig
    >>> from app.schemas.analysis.session import AnalysisSessionCreate
    >>> from app.schemas.analysis.config import NumericFilterConfig
"""

# ================================================================================
# config.py からのエクスポート
# ================================================================================

from app.schemas.analysis.config import (
    AggregateConfig,
    AggregationColumnConfig,
    CategoryFilterConfig,
    FilterConfig,
    FormulaItemConfig,
    NumericFilterConfig,
    SummaryConfig,
    TableFilterConfig,
    ToolUsage,
    TransformConfig,
    UploadFileData,
)

# ================================================================================
# session.py からのエクスポート
# ================================================================================
from app.schemas.analysis.session import (
    AnalysisChatMessage,
    AnalysisFileBase,
    AnalysisFileMetadata,
    AnalysisFileResponse,
    AnalysisFileUploadRequest,
    AnalysisResultFormula,
    AnalysisResultFormulaList,
    AnalysisSessionBase,
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisSessionResponse,
    AnalysisSessionUpdate,
    AnalysisStepBase,
    AnalysisStepCreate,
    AnalysisStepResponse,
    AnalysisStepSnapshot,
    ChatHistory,
    ChatRequest,
    ChatResponse,
    SnapshotHistory,
    SnapshotHistoryItem,
)

# ================================================================================
# template.py からのエクスポート
# ================================================================================
from app.schemas.analysis.template import (
    AnalysisTemplateBase,
    AnalysisTemplateChartBase,
    AnalysisTemplateChartCreate,
    AnalysisTemplateChartResponse,
    AnalysisTemplateCreate,
    AnalysisTemplateDetailResponse,
    AnalysisTemplateResponse,
    AnalysisTemplateUpdate,
    InitialAxisConfig,
    InitialAxisList,
)

__all__ = [
    # config
    "FilterConfig",
    "NumericFilterConfig",
    "CategoryFilterConfig",
    "TableFilterConfig",
    "AggregateConfig",
    "AggregationColumnConfig",
    "TransformConfig",
    "SummaryConfig",
    "FormulaItemConfig",
    "UploadFileData",
    "ToolUsage",
    # session
    "AnalysisStepSnapshot",
    "SnapshotHistoryItem",
    "SnapshotHistory",
    "AnalysisChatMessage",
    "ChatHistory",
    "AnalysisResultFormula",
    "AnalysisResultFormulaList",
    "AnalysisFileMetadata",
    "AnalysisSessionBase",
    "AnalysisSessionCreate",
    "AnalysisSessionUpdate",
    "AnalysisSessionResponse",
    "AnalysisSessionDetailResponse",
    "AnalysisStepBase",
    "AnalysisStepCreate",
    "AnalysisStepResponse",
    "AnalysisFileBase",
    "AnalysisFileUploadRequest",
    "AnalysisFileResponse",
    "ChatRequest",
    "ChatResponse",
    # template
    "InitialAxisConfig",
    "InitialAxisList",
    "AnalysisTemplateChartBase",
    "AnalysisTemplateChartCreate",
    "AnalysisTemplateChartResponse",
    "AnalysisTemplateBase",
    "AnalysisTemplateCreate",
    "AnalysisTemplateUpdate",
    "AnalysisTemplateResponse",
    "AnalysisTemplateDetailResponse",
]
