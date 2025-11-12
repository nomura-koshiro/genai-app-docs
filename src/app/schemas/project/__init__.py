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
        - ProjectMemberBulkUpdate: 一括更新リクエスト
        - ProjectMemberRoleUpdate: ロール変更リクエスト

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
    ProjectMemberBulkUpdate,
    ProjectMemberBulkUpdateError,
    ProjectMemberBulkUpdateResponse,
    ProjectMemberCreate,
    ProjectMemberDetailResponse,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectMemberRoleUpdate,
    ProjectMemberUpdate,
    UserRoleResponse,
)
from app.schemas.project.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)

__all__ = [
    "ProjectCreate",
    "ProjectResponse",
    "ProjectUpdate",
    "ProjectFileDeleteResponse",
    "ProjectFileListResponse",
    "ProjectFileResponse",
    "ProjectFileUploadResponse",
    "ProjectMemberBulkCreate",
    "ProjectMemberBulkError",
    "ProjectMemberBulkResponse",
    "ProjectMemberBulkUpdateError",
    "ProjectMemberBulkUpdate",
    "ProjectMemberBulkUpdateResponse",
    "ProjectMemberCreate",
    "ProjectMemberListResponse",
    "ProjectMemberResponse",
    "ProjectMemberRoleUpdate",
    "ProjectMemberUpdate",
    "ProjectMemberDetailResponse",
    "UserRoleResponse",
]
