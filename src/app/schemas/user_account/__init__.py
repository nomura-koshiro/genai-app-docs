"""ユーザー関連のPydanticスキーマ。

このモジュールは、ユーザー管理機能に関連するリクエスト/レスポンススキーマを提供します。

主なスキーマ:
    - UserAccountResponse: ユーザー詳細レスポンス
    - UserAccountDetailResponse: ユーザー詳細情報レスポンス（統計情報含む）
    - UserAccountUpdate: ユーザー更新リクエスト
    - UserAccountListResponse: ユーザー一覧レスポンス
    - UserActivityStats: ユーザーアクティビティ統計情報
    - RoleHistoryResponse: ロール履歴レスポンス
    - RoleHistoryListResponse: ロール履歴一覧レスポンス
    - UserSettingsResponse: ユーザー設定レスポンス
    - UserSettingsUpdate: ユーザー設定更新リクエスト

使用例:
    >>> from app.schemas.user_account import UserAccountUpdate, UserAccountResponse
    >>> user_update = UserAccountUpdate(full_name="新しい名前")
    >>> # API経由でユーザー情報を更新
"""

from app.schemas.user_account.role_history import (
    RoleChangeActionEnum,
    RoleHistoryListResponse,
    RoleHistoryResponse,
    RoleTypeEnum,
)
from app.schemas.user_account.user_account import (
    UserAccountDetailResponse,
    UserAccountListResponse,
    UserAccountResponse,
    UserAccountRoleUpdate,
    UserAccountUpdate,
    UserActivityStats,
)
from app.schemas.user_account.user_settings import (
    DisplaySettingsInfo,
    DisplaySettingsUpdate,
    LanguageEnum,
    NotificationSettingsInfo,
    NotificationSettingsUpdate,
    ProjectViewEnum,
    ThemeEnum,
    UserSettingsResponse,
    UserSettingsUpdate,
)

__all__ = [
    "DisplaySettingsInfo",
    "DisplaySettingsUpdate",
    "LanguageEnum",
    "NotificationSettingsInfo",
    "NotificationSettingsUpdate",
    "ProjectViewEnum",
    "RoleChangeActionEnum",
    "RoleHistoryListResponse",
    "RoleHistoryResponse",
    "RoleTypeEnum",
    "ThemeEnum",
    "UserAccountDetailResponse",
    "UserAccountListResponse",
    "UserAccountResponse",
    "UserAccountRoleUpdate",
    "UserAccountUpdate",
    "UserActivityStats",
    "UserSettingsResponse",
    "UserSettingsUpdate",
]
