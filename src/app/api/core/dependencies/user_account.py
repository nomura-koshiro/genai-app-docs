"""UserAccountサービス依存性。

UserAccountServiceのDI定義を提供します。
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services import UserAccountService
from app.services.user_account import RoleHistoryService, UserSettingsService

__all__ = [
    "RoleHistoryServiceDep",
    "UserServiceDep",
    "UserSettingsServiceDep",
    "get_role_history_service",
    "get_user_service",
    "get_user_settings_service",
]


def get_user_service(db: DatabaseDep) -> UserAccountService:
    """ユーザーサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        UserAccountService: 初期化されたユーザーサービスインスタンス

    Note:
        - この関数はFastAPIのDependsで自動的に呼び出されます
        - サービスインスタンスはリクエストごとに生成されます
    """
    return UserAccountService(db)


def get_role_history_service(db: DatabaseDep) -> RoleHistoryService:
    """ロール履歴サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        RoleHistoryService: 初期化されたロール履歴サービスインスタンス
    """
    return RoleHistoryService(db)


def get_user_settings_service(db: DatabaseDep) -> UserSettingsService:
    """ユーザー設定サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        UserSettingsService: 初期化されたユーザー設定サービスインスタンス
    """
    return UserSettingsService(db)


UserServiceDep = Annotated[UserAccountService, Depends(get_user_service)]
"""ユーザーサービスの依存性型。

エンドポイント関数にUserAccountServiceインスタンスを自動注入します。
"""

RoleHistoryServiceDep = Annotated[RoleHistoryService, Depends(get_role_history_service)]
"""ロール履歴サービスの依存性型。

エンドポイント関数にRoleHistoryServiceインスタンスを自動注入します。
"""

UserSettingsServiceDep = Annotated[UserSettingsService, Depends(get_user_settings_service)]
"""ユーザー設定サービスの依存性型。

エンドポイント関数にUserSettingsServiceインスタンスを自動注入します。
"""
