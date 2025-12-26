"""プロジェクト管理サービス。

このモジュールは、プロジェクト管理のビジネスロジックを提供します。

主な機能:
    - プロジェクトの作成（作成者を自動的にOWNERとして追加）
    - プロジェクトコードの重複チェック
    - ユーザーの権限チェック（OWNER/ADMIN/MEMBER/VIEWER）
    - プロジェクトメンバーシップの管理
    - プロジェクト削除時の関連データ確認

サブモジュール:
    - base.py: 共通ベースクラス
    - crud.py: CRUD操作
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate
from app.services.project.project.crud import ProjectCrudService


class ProjectService:
    """プロジェクト管理のビジネスロジックを提供するサービスクラス。

    CRUD操作を提供します。
    各機能は専用のサービスクラスに委譲されます。
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self._crud_service = ProjectCrudService(db)

    # ================================================================================
    # CRUD操作
    # ================================================================================

    async def create_project(
        self,
        project_data: ProjectCreate,
        creator_id: uuid.UUID,
    ) -> Project:
        """新しいプロジェクトを作成します。"""
        return await self._crud_service.create_project(project_data, creator_id)

    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        """プロジェクトIDでプロジェクト情報を取得します。"""
        return await self._crud_service.get_project(project_id)

    async def get_project_by_code(self, code: str) -> Project:
        """プロジェクトコードでプロジェクト情報を取得します。"""
        return await self._crud_service.get_project_by_code(code)

    async def list_projects(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """プロジェクトの一覧を取得します（管理者用）。"""
        return await self._crud_service.list_projects(skip, limit)

    async def list_user_projects(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[Project]:
        """特定ユーザーが所属するプロジェクトの一覧を取得します。"""
        return await self._crud_service.list_user_projects(user_id, skip, limit, is_active)

    async def update_project(
        self,
        project_id: uuid.UUID,
        update_data: ProjectUpdate,
        user_id: uuid.UUID,
    ) -> Project:
        """プロジェクト情報を更新します。"""
        return await self._crud_service.update_project(project_id, update_data, user_id)

    async def delete_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """プロジェクトを削除します。"""
        return await self._crud_service.delete_project(project_id, user_id)

    async def check_user_access(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """ユーザーがプロジェクトにアクセスできるかチェックします。"""
        return await self._crud_service.check_user_access(project_id, user_id)


__all__ = ["ProjectService"]
