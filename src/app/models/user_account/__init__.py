"""ユーザー関連のSQLAlchemyモデル。

このモジュールは、ユーザー管理機能に関連するデータベースモデルを提供します。

主なモデル:
    - UserAccount: ユーザーモデル（認証、プロフィール、システムロール）
    - RoleHistory: ロール変更履歴モデル
    - UserSettings: ユーザー設定モデル
    - UserSession: ユーザーセッションモデル

Enum定義はapp.models.enumsパッケージで一元管理されています:
    - SystemUserRole: システムロール（admin, user）
    - RoleChangeActionEnum: ロール変更アクション種別
    - ThemeEnum, LanguageEnum, ProjectViewEnum: ユーザー設定関連

使用例:
    >>> from app.models.user_account import UserAccount
    >>> from app.models.enums import SystemUserRole
    >>> user = UserAccount(
    ...     email="user@example.com",
    ...     full_name="山田太郎",
    ...     system_role=SystemUserRole.USER
    ... )
"""

from app.models.user_account.role_history import RoleHistory
from app.models.user_account.user_account import UserAccount
from app.models.user_account.user_session import UserSession
from app.models.user_account.user_settings import UserSettings

__all__ = [
    "RoleHistory",
    "UserAccount",
    "UserSession",
    "UserSettings",
]
