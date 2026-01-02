"""ユーザーコンテキストサービスの実装。

共通UI設計書（UI-001〜UI-003, UI-011）に基づくユーザーコンテキスト機能を提供します。
"""

import uuid
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.notification import UserNotification
from app.models.project import Project, ProjectMember
from app.models.user_account import UserAccount
from app.schemas.common.user_context import (
    NavigationInfo,
    NotificationBadgeInfo,
    PermissionsInfo,
    SidebarInfo,
    UserContextInfo,
    UserContextResponse,
)

logger = get_logger(__name__)

# サイドバーセクション設定
SIDEBAR_SECTIONS = {
    "dashboard": {"roles": ["user", "system_admin"]},
    "project": {"roles": ["user", "system_admin"]},
    "analysis": {"roles": ["user", "system_admin"]},
    "driver-tree": {"roles": ["user", "system_admin"]},
    "file": {"roles": ["user", "system_admin"]},
    "system-admin": {"roles": ["system_admin"]},
    "monitoring": {"roles": ["system_admin"]},
    "operations": {"roles": ["system_admin"]},
}


class UserContextService:
    """ユーザーコンテキストサービス。

    ユーザーのコンテキスト情報（権限、ナビゲーション、通知バッジなど）を
    集約して返却する機能を提供します。
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db

    async def get_user_context(
        self,
        user: UserAccount,
    ) -> UserContextResponse:
        """ユーザーコンテキスト情報を取得します。

        ログイン直後やページリロード時に呼び出され、
        UIの動的表示に必要な情報をまとめて返却します。

        Args:
            user: ユーザーアカウント

        Returns:
            UserContextResponse: ユーザーコンテキスト情報
        """
        # 権限情報を構築
        permissions = self._build_permissions(user.roles)

        # ナビゲーション情報を構築
        navigation = await self._build_navigation(user.id)

        # 未読通知数を取得
        unread_count = await self._count_unread_notifications(user.id)

        # サイドバー情報を構築
        sidebar = self._build_sidebar(permissions)

        return UserContextResponse(
            user=UserContextInfo(
                id=user.id,
                display_name=user.display_name or user.email,
                email=user.email,
                roles=user.roles,
            ),
            permissions=permissions,
            navigation=navigation,
            notifications=NotificationBadgeInfo(unread_count=unread_count),
            sidebar=sidebar,
        )

    def _build_permissions(self, roles: list[str]) -> PermissionsInfo:
        """ロールから権限情報を構築します。

        Args:
            roles: ユーザーのロールリスト

        Returns:
            PermissionsInfo: 権限情報
        """
        is_admin = "system_admin" in roles
        return PermissionsInfo(
            is_system_admin=is_admin,
            can_access_admin_panel=is_admin,
            can_manage_users=is_admin,
            can_manage_masters=is_admin,
            can_view_audit_logs=is_admin,
        )

    async def _build_navigation(self, user_id: uuid.UUID) -> NavigationInfo:
        """ナビゲーション情報を構築します。

        プロジェクト参加数に応じて遷移先を切り替えます。

        Args:
            user_id: ユーザーID

        Returns:
            NavigationInfo: ナビゲーション情報
        """
        # アクティブなプロジェクトを取得
        stmt = (
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                ProjectMember.user_id == user_id,
                Project.is_active == True,  # noqa: E712
            )
            .order_by(Project.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        projects = result.scalars().all()

        project_count = len(projects)

        if project_count == 1:
            project = projects[0]
            navigation_type: Literal["list", "detail"] = "detail"
            return NavigationInfo(
                project_count=1,
                default_project_id=project.id,
                default_project_name=project.name,
                project_navigation_type=navigation_type,
            )
        else:
            navigation_type = "list"
            return NavigationInfo(
                project_count=project_count,
                default_project_id=None,
                default_project_name=None,
                project_navigation_type=navigation_type,
            )

    async def _count_unread_notifications(self, user_id: uuid.UUID) -> int:
        """未読通知数をカウントします。

        Args:
            user_id: ユーザーID

        Returns:
            int: 未読通知数
        """
        stmt = select(func.count()).where(
            UserNotification.user_id == user_id,
            UserNotification.is_read == False,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    def _build_sidebar(self, permissions: PermissionsInfo) -> SidebarInfo:
        """サイドバー表示情報を構築します。

        権限に応じて表示/非表示セクションを決定します。

        Args:
            permissions: 権限情報

        Returns:
            SidebarInfo: サイドバー情報
        """
        visible_sections: list[str] = []
        hidden_sections: list[str] = []

        # ユーザーが持っているロールを特定
        user_roles = set()
        if permissions.is_system_admin:
            user_roles.add("system_admin")
        user_roles.add("user")

        for section, config in SIDEBAR_SECTIONS.items():
            allowed_roles = set(config["roles"])
            if user_roles & allowed_roles:
                visible_sections.append(section)
            else:
                hidden_sections.append(section)

        return SidebarInfo(
            visible_sections=visible_sections,
            hidden_sections=hidden_sections,
        )
