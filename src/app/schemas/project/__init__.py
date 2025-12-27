"""プロジェクト関連のPydanticスキーマ。

このモジュールは、プロジェクト管理機能に関連するリクエスト/レスポンススキーマを提供します。

主なスキーマ:
    プロジェクト:
        - ProjectCreate: プロジェクト作成リクエスト
        - ProjectUpdate: プロジェクト更新リクエスト
        - ProjectResponse: プロジェクトレスポンス

    プロジェクトファイル:
        - ProjectFileUploadResponse: ファイルアップロードレスポンス
        - ProjectFileResponse: ファイル詳細レスポンス
        - ProjectFileListResponse: ファイル一覧レスポンス
        - ProjectFileDeleteResponse: ファイル削除レスポンス

    プロジェクトメンバー:
        - ProjectMemberCreate: メンバー追加リクエスト
        - ProjectMemberUpdate: メンバー更新リクエスト
        - ProjectMemberResponse: メンバーレスポンス
        - ProjectMemberDetailResponse: メンバー詳細レスポンス
        - ProjectMemberListResponse: メンバー一覧レスポンス
        - ProjectMemberBulkCreate: 一括追加リクエスト

使用例:
    >>> from app.schemas.project import ProjectCreate, ProjectMemberCreate
    >>> project_data = ProjectCreate(
    ...     name="新規施策検討",
    ...     description="市場拡大施策の分析"
    ... )
    >>> member_data = ProjectMemberCreate(
    ...     user_id=user_id,
    ...     role="manager"
    ... )
"""

from app.schemas.project.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatsResponse,
    ProjectUpdate,
)
from app.schemas.project.project_file import (
    FileUsageItem,
    ProjectFileDeleteResponse,
    ProjectFileListResponse,
    ProjectFileResponse,
    ProjectFileUploadRequest,
    ProjectFileUploadResponse,
    ProjectFileUsageResponse,
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

__all__ = [
    "FileUsageItem",
    "ProjectCreate",
    "ProjectDetailResponse",
    "ProjectListResponse",
    "ProjectResponse",
    "ProjectStatsResponse",
    "ProjectUpdate",
    "ProjectFileDeleteResponse",
    "ProjectFileListResponse",
    "ProjectFileResponse",
    "ProjectFileUploadRequest",
    "ProjectFileUploadResponse",
    "ProjectFileUsageResponse",
    "ProjectMemberBulkCreate",
    "ProjectMemberBulkError",
    "ProjectMemberBulkResponse",
    "ProjectMemberCreate",
    "ProjectMemberListResponse",
    "ProjectMemberResponse",
    "ProjectMemberUpdate",
    "ProjectMemberDetailResponse",
    "UserRoleResponse",
]
