"""分析関連のPydanticスキーマパッケージ。

このパッケージは、分析機能に関連するすべてのスキーマを提供します。

モジュール:
    config: 分析ステップ設定スキーマ (AnalysisFilterConfig, AnalysisAggregateConfig等)
    session: 分析セッション関連スキーマ (AnalysisChatMessage, AnalysisResultFormula等)
    template: 分析テンプレート関連スキーマ (AnalysisInitialAxisConfig等)

使用方法:
    >>> from app.schemas.analysis import AnalysisChatMessage, AnalysisFilterConfig
    >>> from app.schemas.analysis.session import AnalysisSessionCreate
    >>> from app.schemas.analysis.config import AnalysisNumericFilterConfig
"""

# ================================================================================
# config.py からのエクスポート
# ================================================================================

from app.schemas.analysis.analysis_config import (
    AggregationColumnConfig,
    AnalysisAggregateConfig,
    AnalysisCategoryFilterConfig,
    AnalysisFilterConfig,
    AnalysisNumericFilterConfig,
    AnalysisSummaryConfig,
    AnalysisTableFilterConfig,
    AnalysisTransformCalculation,
    AnalysisTransformConfig,
    AnalysisTransformOperation,
    AnalysisValidationConfig,
    FormulaItemConfig,
    ToolUsage,
    UploadFileData,
)

# ================================================================================
# session.py からのエクスポート
# ================================================================================
from app.schemas.analysis.analysis_session import (
    AnalysisChatMessage,
    AnalysisChatRequest,
    AnalysisChatResponse,
    AnalysisDummyDataResponse,
    AnalysisFileBase,
    AnalysisFileMetadata,
    AnalysisFileResponse,
    AnalysisFileUploadRequest,
    AnalysisFileUploadResponse,
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
    AnalysisValidationConfigResponse,
    ChatHistory,
    SnapshotHistory,
    SnapshotHistoryItem,
)

# ================================================================================
# template.py からのエクスポート
# ================================================================================
from app.schemas.analysis.analysis_template import (
    AnalysisInitialAxisConfig,
    AnalysisInitialAxisList,
    AnalysisPlotlyChartData,
    AnalysisTemplateBase,
    AnalysisTemplateChartBase,
    AnalysisTemplateChartCreate,
    AnalysisTemplateChartResponse,
    AnalysisTemplateCreate,
    AnalysisTemplateDetailResponse,
    AnalysisTemplateResponse,
    AnalysisTemplateUpdate,
)

__all__ = [
    # config
    "AnalysisAggregateConfig",
    "AnalysisCategoryFilterConfig",
    "AnalysisFilterConfig",
    "AnalysisNumericFilterConfig",
    "AnalysisSummaryConfig",
    "AnalysisTableFilterConfig",
    "AnalysisTransformCalculation",
    "AnalysisTransformConfig",
    "AnalysisTransformOperation",
    "AnalysisValidationConfig",
    "AggregationColumnConfig",
    "FormulaItemConfig",
    "ToolUsage",
    "UploadFileData",
    # session
    "AnalysisChatMessage",
    "AnalysisChatRequest",
    "AnalysisChatResponse",
    "AnalysisDummyDataResponse",
    "AnalysisFileBase",
    "AnalysisFileMetadata",
    "AnalysisFileResponse",
    "AnalysisFileUploadRequest",
    "AnalysisFileUploadResponse",
    "AnalysisResultFormula",
    "AnalysisResultFormulaList",
    "AnalysisSessionBase",
    "AnalysisSessionCreate",
    "AnalysisSessionDetailResponse",
    "AnalysisSessionResponse",
    "AnalysisSessionUpdate",
    "AnalysisStepBase",
    "AnalysisStepCreate",
    "AnalysisStepResponse",
    "AnalysisStepSnapshot",
    "AnalysisValidationConfigResponse",
    "ChatHistory",
    "SnapshotHistory",
    "SnapshotHistoryItem",
    # template
    "AnalysisInitialAxisConfig",
    "AnalysisInitialAxisList",
    "AnalysisPlotlyChartData",
    "AnalysisTemplateBase",
    "AnalysisTemplateChartBase",
    "AnalysisTemplateChartCreate",
    "AnalysisTemplateChartResponse",
    "AnalysisTemplateCreate",
    "AnalysisTemplateDetailResponse",
    "AnalysisTemplateResponse",
    "AnalysisTemplateUpdate",
]
