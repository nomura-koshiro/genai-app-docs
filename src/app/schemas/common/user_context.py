"""ユーザーコンテキスト関連のPydanticスキーマ。

共通UI設計書（UI-001〜UI-003, UI-011）に基づくユーザーコンテキスト機能のスキーマ定義。
サイドバー表示、ヘッダー情報、権限情報などをまとめて返却する。
"""

from typing import Literal
from uuid import UUID

from app.schemas.base import BaseCamelCaseModel

__all__ = [
    # Info schemas
    "NavigationInfo",
    "NotificationBadgeInfo",
    "PermissionsInfo",
    "SidebarInfo",
    "UserContextInfo",
    # Response schemas
    "UserContextResponse",
]


class UserContextInfo(BaseCamelCaseModel):
    """ユーザー基本情報スキーマ。

    ヘッダー表示用のユーザー基本情報。
    """

    id: UUID
    display_name: str
    email: str
    roles: list[str]


class PermissionsInfo(BaseCamelCaseModel):
    """権限情報スキーマ。

    システム権限とアクセス可能な機能の情報。
    """

    is_system_admin: bool
    can_access_admin_panel: bool
    can_manage_users: bool
    can_manage_masters: bool
    can_view_audit_logs: bool


class NavigationInfo(BaseCamelCaseModel):
    """ナビゲーション情報スキーマ。

    プロジェクト数に応じた遷移先情報。
    """

    project_count: int
    default_project_id: UUID | None = None
    default_project_name: str | None = None
    project_navigation_type: Literal["list", "detail"]


class NotificationBadgeInfo(BaseCamelCaseModel):
    """通知バッジ情報スキーマ。

    ヘッダーの未読通知バッジ表示用。
    """

    unread_count: int


class SidebarInfo(BaseCamelCaseModel):
    """サイドバー表示情報スキーマ。

    権限に応じた表示/非表示セクション情報。
    """

    visible_sections: list[str]
    hidden_sections: list[str]


class UserContextResponse(BaseCamelCaseModel):
    """ユーザーコンテキストレスポンススキーマ。

    ログイン直後やページリロード時に取得する、
    UIの動的表示に必要な情報をすべてまとめたレスポンス。
    """

    user: UserContextInfo
    permissions: PermissionsInfo
    navigation: NavigationInfo
    notifications: NotificationBadgeInfo
    sidebar: SidebarInfo
