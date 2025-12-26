"""プロジェクトメンバー管理サービス。

このモジュールは、プロジェクトメンバーの管理に関する全てのビジネスロジックを提供します。

主な機能:
    - メンバーの追加（単一・一括）
    - メンバーのロール更新
    - メンバーの削除・退出
    - 権限チェック
    - メンバー一覧取得

サブモジュール:
    - base.py: 共通ベースクラス
    - crud.py: CRUD操作
    - leave.py: プロジェクト退出操作
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProjectMember, ProjectRole
from app.schemas import ProjectMemberBulkError, ProjectMemberCreate
from app.services.project.project_member.crud import ProjectMemberCrudService
from app.services.project.project_member.leave import ProjectMemberLeaveService


class ProjectMemberService:
    """プロジェクトメンバー管理のビジネスロジックを提供するサービスクラス。

    CRUD操作、退出操作を提供します。
    各機能は専用のサービスクラスに委譲されます。
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトメンバーサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self._crud_service = ProjectMemberCrudService(db)
        self._leave_service = ProjectMemberLeaveService(db)

    # ================================================================================
    # Member Addition
    # ================================================================================

    async def add_member(
        self,
        project_id: uuid.UUID,
        member_data: ProjectMemberCreate,
        added_by: uuid.UUID,
    ) -> ProjectMember:
        """プロジェクトに新しいメンバーを追加します。"""
        return await self._crud_service.add_member(project_id, member_data, added_by)

    async def add_members_bulk(
        self,
        project_id: uuid.UUID,
        members_data: list[ProjectMemberCreate],
        added_by: uuid.UUID,
    ) -> tuple[list[ProjectMember], list[ProjectMemberBulkError]]:
        """プロジェクトに複数のメンバーを一括追加します。"""
        return await self._crud_service.add_members_bulk(project_id, members_data, added_by)

    # ================================================================================
    # Member Retrieval
    # ================================================================================

    async def get_project_members(
        self,
        project_id: uuid.UUID,
        requester_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ProjectMember], int]:
        """プロジェクトのメンバー一覧を取得します。"""
        return await self._crud_service.get_project_members(project_id, requester_id, skip, limit)

    async def get_user_role(self, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectRole | None:
        """指定したユーザーのプロジェクトロールを取得します。"""
        return await self._crud_service.get_user_role(project_id, user_id)

    # ================================================================================
    # Member Update
    # ================================================================================

    async def update_member_role(
        self,
        member_id: uuid.UUID,
        new_role: ProjectRole,
        requester_id: uuid.UUID,
    ) -> ProjectMember:
        """メンバーのロールを更新します。"""
        return await self._crud_service.update_member_role(member_id, new_role, requester_id)

    # ================================================================================
    # Member Removal
    # ================================================================================

    async def remove_member(self, member_id: uuid.UUID, requester_id: uuid.UUID) -> None:
        """プロジェクトからメンバーを削除します。"""
        return await self._crud_service.remove_member(member_id, requester_id)

    async def leave_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """プロジェクトから退出します。"""
        return await self._leave_service.leave_project(project_id, user_id)


__all__ = ["ProjectMemberService"]
