"""APIリクエスト/レスポンス検証のためのPydanticスキーマ。"""

from app.schemas.analysis import (
    AnalysisDummyChartBase,
    AnalysisDummyChartCreate,
    AnalysisDummyChartResponse,
    AnalysisDummyChartUpdate,
    AnalysisDummyFormulaBase,
    AnalysisDummyFormulaCreate,
    AnalysisDummyFormulaResponse,
    AnalysisDummyFormulaUpdate,
    AnalysisFileBase,
    AnalysisFileCreate,
    AnalysisFileListResponse,
    AnalysisFileResponse,
    AnalysisFileUpdate,
    AnalysisGraphAxisBase,
    AnalysisGraphAxisCreate,
    AnalysisGraphAxisResponse,
    AnalysisGraphAxisUpdate,
    AnalysisIssueBase,
    AnalysisIssueCatalogListResponse,
    AnalysisIssueCatalogResponse,
    AnalysisIssueCreate,
    AnalysisIssueDetailResponse,
    AnalysisIssueUpdate,
    AnalysisSessionListResponse,
    AnalysisSessionResponse,
    AnalysisSessionResultListResponse,
    AnalysisSessionResultResponse,
    AnalysisTemplateCreateRequest,
    AnalysisTemplateCreateResponse,
    AnalysisTemplateDeleteResponse,
    AnalysisValidationBase,
    AnalysisValidationCreate,
    AnalysisValidationResponse,
    AnalysisValidationUpdate,
)
from app.schemas.common import HealthResponse, MessageResponse, ProblemDetails

# from app.schemas.driver_tree.driver_tree import (
#     DriverTreeFormulaCreateRequest,
#     DriverTreeFormulaResponse,
#     DriverTreeKPIListResponse,
#     DriverTreeNodeCreate,
#     DriverTreeNodeResponse,
#     DriverTreeNodeUpdate,
#     DriverTreeResponse,
# )
# from app.schemas.ppt_generator import (
#     PPTDownloadRequest,
#     PPTSlideExportRequest,
#     PPTSlideImageRequest,
#     PPTUploadRequest,
#     PPTUploadResponse,
#     QuestionDownloadRequest,
# )
from app.schemas.project.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatsResponse,
    ProjectUpdate,
)
from app.schemas.project.project_file import (
    ProjectFileDeleteResponse,
    ProjectFileListResponse,
    ProjectFileResponse,
    ProjectFileUploadRequest,
    ProjectFileUploadResponse,
)
from app.schemas.project.project_member import (
    ProjectMemberBulkCreate,
    ProjectMemberBulkError,
    ProjectMemberBulkResponse,
    ProjectMemberCreate,
    ProjectMemberDetailResponse,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectMemberUpdate,
    UserRoleResponse,
)

# from app.schemas.sample.sample_agents import (
#     SampleChatRequest,
#     SampleChatResponse,
# )
# from app.schemas.sample.sample_file import (
#     SampleFileDeleteResponse,
#     SampleFileListResponse,
#     SampleFileResponse,
#     SampleFileUploadResponse,
# )
# from app.schemas.sample.sample_sessions import (
#     SampleDeleteResponse,
#     SampleMessageResponse,
#     SampleSessionCreateRequest,
#     SampleSessionListResponse,
#     SampleSessionResponse,
#     SampleSessionUpdateRequest,
# )
# from app.schemas.sample.sample_user import (
#     SampleAPIKeyResponse,
#     SampleRefreshTokenRequest,
#     SampleToken,
#     SampleTokenWithRefresh,
#     SampleUserCreate,
#     SampleUserLogin,
#     SampleUserResponse,
# )
from app.schemas.user_account.user_account import (
    UserAccountListResponse,
    UserAccountResponse,
    UserAccountRoleUpdate,
    UserAccountUpdate,
)

__all__ = [
    # 共通スキーマ
    "ProblemDetails",
    "HealthResponse",
    "MessageResponse",
    # 分析ファイルスキーマ
    "AnalysisFileBase",
    "AnalysisFileCreate",
    "AnalysisFileListResponse",
    "AnalysisFileResponse",
    "AnalysisFileUpdate",
    # 分析セッションスキーマ
    "AnalysisSessionListResponse",
    "AnalysisSessionResponse",
    "AnalysisSessionResultListResponse",
    "AnalysisSessionResultResponse",
    # 分析施策スキーマ
    "AnalysisValidationBase",
    "AnalysisValidationCreate",
    "AnalysisValidationResponse",
    "AnalysisValidationUpdate",
    # 分析課題スキーマ
    "AnalysisIssueBase",
    "AnalysisIssueCatalogListResponse",
    "AnalysisIssueCatalogResponse",
    "AnalysisIssueCreate",
    "AnalysisIssueDetailResponse",
    "AnalysisIssueUpdate",
    # グラフ軸設定スキーマ
    "AnalysisGraphAxisBase",
    "AnalysisGraphAxisCreate",
    "AnalysisGraphAxisResponse",
    "AnalysisGraphAxisUpdate",
    # ダミー計算式スキーマ
    "AnalysisDummyFormulaBase",
    "AnalysisDummyFormulaCreate",
    "AnalysisDummyFormulaResponse",
    "AnalysisDummyFormulaUpdate",
    # ダミーチャートスキーマ
    "AnalysisDummyChartBase",
    "AnalysisDummyChartCreate",
    "AnalysisDummyChartResponse",
    "AnalysisDummyChartUpdate",
    # プロジェクトスキーマ
    "ProjectCreate",
    "ProjectDetailResponse",
    "ProjectListResponse",
    "ProjectResponse",
    "ProjectStatsResponse",
    "ProjectUpdate",
    # プロジェクトファイルスキーマ
    "ProjectFileUploadRequest",
    "ProjectFileUploadResponse",
    "ProjectFileResponse",
    "ProjectFileListResponse",
    "ProjectFileDeleteResponse",
    # プロジェクトメンバースキーマ
    "ProjectMemberCreate",
    "ProjectMemberUpdate",
    "ProjectMemberResponse",
    "ProjectMemberDetailResponse",
    "ProjectMemberListResponse",
    "ProjectMemberBulkCreate",
    "ProjectMemberBulkResponse",
    "ProjectMemberBulkError",
    "UserRoleResponse",
    # ユーザースキーマ
    "UserAccountListResponse",
    "UserAccountResponse",
    "UserAccountRoleUpdate",
    "UserAccountUpdate",
]
