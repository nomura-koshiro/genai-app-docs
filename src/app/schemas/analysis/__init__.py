"""分析関連のPydanticスキーマパッケージ。

このパッケージは、分析機能に関連するすべてのスキーマを提供します。

モジュール:
    config: 分析ステップ設定スキーマ (FilterConfig, AggregateConfig等)
    session: 分析セッション関連スキーマ (ChatMessage, ResultFormula等)
    template: 分析テンプレート関連スキーマ (InitialAxisConfig等)

使用方法:
    >>> from app.schemas.analysis import ChatMessage, FilterConfig
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
    AnalysisFileBase,
    AnalysisFileResponse,
    AnalysisFileUploadRequest,
    AnalysisSessionBase,
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisSessionResponse,
    AnalysisSessionUpdate,
    AnalysisStepBase,
    AnalysisStepCreate,
    AnalysisStepResponse,
    ChatHistory,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    FileMetadata,
    ResultFormula,
    ResultFormulaList,
    SnapshotHistory,
    SnapshotHistoryItem,
    StepSnapshot,
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
    "StepSnapshot",
    "SnapshotHistoryItem",
    "SnapshotHistory",
    "ChatMessage",
    "ChatHistory",
    "ResultFormula",
    "ResultFormulaList",
    "FileMetadata",
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
