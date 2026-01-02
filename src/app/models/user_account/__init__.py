"""ユーザー関連のSQLAlchemyモデル。

このモジュールは、ユーザー管理機能に関連するデータベースモデルを提供します。

主なモデル:
    - UserAccount: ユーザーモデル（認証、プロフィール、システムロール）
    - SystemUserRole: システムロール（admin, user）
    - RoleHistory: ロール変更履歴モデル
    - RoleChangeActionEnum: ロール変更アクション種別
    - UserSettings: ユーザー設定モデル

使用例:
    >>> from app.models.user_account import UserAccount, SystemUserRole
    >>> user = UserAccount(
    ...     email="user@example.com",
    ...     full_name="山田太郎",
    ...     system_role=SystemUserRole.USER
    ... )
"""

from app.models.user_account.role_history import RoleChangeActionEnum, RoleHistory
from app.models.user_account.user_account import SystemUserRole, UserAccount
from app.models.user_account.user_session import UserSession
from app.models.user_account.user_settings import (
    LanguageEnum,
    ProjectViewEnum,
    ThemeEnum,
    UserSettings,
)

__all__ = [
    "LanguageEnum",
    "ProjectViewEnum",
    "RoleChangeActionEnum",
    "RoleHistory",
    "SystemUserRole",
    "ThemeEnum",
    "UserAccount",
    "UserSession",
    "UserSettings",
]
