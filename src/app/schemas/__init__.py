"""APIリクエスト/レスポンス検証のためのPydanticスキーマ。"""

from app.schemas.common import HealthResponse, MessageResponse, ProblemDetails
from app.schemas.driver_tree.schemas import (
    DriverTreeFormulaCreateRequest,
    DriverTreeFormulaResponse,
    DriverTreeKPIListResponse,
    DriverTreeNodeCreate,
    DriverTreeNodeResponse,
    DriverTreeNodeUpdate,
    DriverTreeResponse,
)
from app.schemas.project.file import (
    ProjectFileDeleteResponse,
    ProjectFileListResponse,
    ProjectFileResponse,
    ProjectFileUploadResponse,
)
from app.schemas.project.member import (
    ProjectMemberBulkCreate,
    ProjectMemberBulkError,
    ProjectMemberBulkResponse,
    ProjectMemberBulkUpdateError,
    ProjectMemberBulkUpdateRequest,
    ProjectMemberBulkUpdateResponse,
    ProjectMemberCreate,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectMemberRoleUpdate,
    ProjectMemberUpdate,
    ProjectMemberWithUser,
    UserRoleResponse,
)
from app.schemas.project.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.sample.sample_agents import (
    SampleChatRequest,
    SampleChatResponse,
)
from app.schemas.sample.sample_file import (
    SampleFileDeleteResponse,
    SampleFileListResponse,
    SampleFileResponse,
    SampleFileUploadResponse,
)
from app.schemas.sample.sample_sessions import (
    SampleDeleteResponse,
    SampleMessageResponse,
    SampleSessionCreateRequest,
    SampleSessionListResponse,
    SampleSessionResponse,
    SampleSessionUpdateRequest,
)
from app.schemas.sample.sample_user import (
    SampleToken,
    SampleUserCreate,
    SampleUserLogin,
    SampleUserResponse,
)
from app.schemas.user import (
    UserListResponse,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # 共通スキーマ
    "ProblemDetails",
    "HealthResponse",
    "MessageResponse",
    # Driver Treeスキーマ
    "DriverTreeNodeCreate",
    "DriverTreeNodeUpdate",
    "DriverTreeNodeResponse",
    "DriverTreeResponse",
    "DriverTreeFormulaCreateRequest",
    "DriverTreeFormulaResponse",
    "DriverTreeKPIListResponse",
    # サンプルユーザースキーマ
    "SampleToken",
    "SampleUserCreate",
    "SampleUserLogin",
    "SampleUserResponse",
    # ファイルスキーマ
    "SampleFileUploadResponse",
    "SampleFileResponse",
    "SampleFileListResponse",
    "SampleFileDeleteResponse",
    # エージェント/チャットスキーマ
    "SampleChatRequest",
    "SampleChatResponse",
    # セッションスキーマ
    "SampleMessageResponse",
    "SampleSessionResponse",
    "SampleSessionListResponse",
    "SampleSessionCreateRequest",
    "SampleSessionUpdateRequest",
    "SampleDeleteResponse",
    # プロジェクトスキーマ
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    # プロジェクトファイルスキーマ
    "ProjectFileUploadResponse",
    "ProjectFileResponse",
    "ProjectFileListResponse",
    "ProjectFileDeleteResponse",
    # プロジェクトメンバースキーマ
    "ProjectMemberCreate",
    "ProjectMemberUpdate",
    "ProjectMemberResponse",
    "ProjectMemberWithUser",
    "ProjectMemberListResponse",
    "ProjectMemberBulkCreate",
    "ProjectMemberBulkResponse",
    "ProjectMemberBulkError",
    "ProjectMemberRoleUpdate",
    "ProjectMemberBulkUpdateRequest",
    "ProjectMemberBulkUpdateResponse",
    "ProjectMemberBulkUpdateError",
    "UserRoleResponse",
    # ユーザースキーマ
    "UserResponse",
    "UserUpdate",
    "UserListResponse",
]
