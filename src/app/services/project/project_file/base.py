"""プロジェクトファイルサービス共通ベース。

このモジュールは、プロジェクトファイルサービスの共通機能を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError
from app.core.logging import get_logger
from app.models import ProjectRole
from app.repositories import ProjectFileRepository, ProjectMemberRepository
from app.services import storage as storage_module
from app.services.storage import StorageService

logger = get_logger(__name__)


class ProjectFileServiceBase:
    """プロジェクトファイルサービスの共通ベースクラス。"""

    db: AsyncSession
    repository: ProjectFileRepository
    member_repository: ProjectMemberRepository
    storage: StorageService

    def __init__(self, db: AsyncSession, storage: StorageService | None = None):
        """プロジェクトファイルサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
            storage: ストレージサービス（指定しない場合はデフォルトのストレージサービスを使用）
        """
        self.db = db
        self.repository = ProjectFileRepository(db)
        self.member_repository = ProjectMemberRepository(db)
        # モジュール経由でアクセスすることでテスト時のモックが効くようにする
        self.storage = storage if storage is not None else storage_module.get_storage_service()

    async def _check_member_role(self, project_id: uuid.UUID, user_id: uuid.UUID, required_roles: list[ProjectRole]) -> None:
        """ユーザーのプロジェクトメンバーシップと権限をチェックします。

        Args:
            project_id: プロジェクトID
            user_id: ユーザーID
            required_roles: 必要なロールのリスト

        Raises:
            AuthorizationError: ユーザーがメンバーでない、または権限が不足している場合
        """
        member = await self.member_repository.get_by_project_and_user(project_id, user_id)
        if not member:
            raise AuthorizationError(
                "You are not a member of this project",
                details={"project_id": str(project_id), "user_id": str(user_id)},
            )

        if member.role not in required_roles:
            raise AuthorizationError(
                f"Insufficient permissions. Required roles: {[r.value for r in required_roles]}",
                details={"user_role": member.role.value, "required_roles": [r.value for r in required_roles]},
            )

    def _generate_storage_path(self, project_id: uuid.UUID, file_id: uuid.UUID, filename: str) -> str:
        """ストレージパスを生成します。

        Args:
            project_id: プロジェクトID
            file_id: ファイルID
            filename: ファイル名

        Returns:
            str: ストレージパス
        """
        return f"projects/{project_id}/{file_id}_{filename}"
