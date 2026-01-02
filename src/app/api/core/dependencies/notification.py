"""ユーザー通知サービス依存性。

UserNotificationServiceのDI定義を提供します。
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services.notification import UserNotificationService

__all__ = [
    "UserNotificationServiceDep",
    "get_user_notification_service",
]


def get_user_notification_service(db: DatabaseDep) -> UserNotificationService:
    """ユーザー通知サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        UserNotificationService: 初期化されたユーザー通知サービスインスタンス
    """
    return UserNotificationService(db)


UserNotificationServiceDep = Annotated[
    UserNotificationService, Depends(get_user_notification_service)
]
"""ユーザー通知サービスの依存性型。

エンドポイント関数にUserNotificationServiceインスタンスを自動注入します。
"""
