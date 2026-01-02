"""通知スキーマパッケージ。

共通UI設計書（UI-006〜UI-011）に基づく通知機能のスキーマ定義。
"""

from app.schemas.notification.notification import (
    NotificationCreateRequest,
    NotificationInfo,
    NotificationListResponse,
    ReadAllResponse,
)

__all__ = [
    "NotificationCreateRequest",
    "NotificationInfo",
    "NotificationListResponse",
    "ReadAllResponse",
]
