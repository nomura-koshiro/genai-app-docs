"""通知関連のPydanticスキーマ。

共通UI設計書（UI-006〜UI-011）に基づく通知機能のスキーマ定義。
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.notification import NotificationTypeEnum, ReferenceTypeEnum
from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel

__all__ = [
    # Info schemas
    "NotificationInfo",
    # Request schemas
    "NotificationCreateRequest",
    # Response schemas
    "NotificationListResponse",
    "ReadAllResponse",
]


class NotificationInfo(BaseCamelCaseORMModel):
    """通知情報スキーマ。

    通知の詳細情報を表すスキーマ。
    通知一覧・詳細取得・既読更新のレスポンスで使用。
    """

    id: UUID
    type: NotificationTypeEnum
    title: str
    message: str | None = None
    icon: str | None = None
    link_url: str | None = None
    reference_type: ReferenceTypeEnum | None = None
    reference_id: UUID | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationCreateRequest(BaseCamelCaseModel):
    """通知作成リクエストスキーマ。

    システム内部で通知を作成する際に使用。
    """

    user_id: UUID
    type: NotificationTypeEnum
    title: str = Field(..., max_length=255)
    message: str | None = Field(default=None, max_length=1000)
    icon: str | None = Field(default=None, max_length=10)
    link_url: str | None = Field(default=None, max_length=500)
    reference_type: ReferenceTypeEnum | None = None
    reference_id: UUID | None = None


class NotificationListResponse(BaseCamelCaseModel):
    """通知一覧レスポンススキーマ。

    ページネーション情報と未読件数を含む通知一覧。
    """

    notifications: list[NotificationInfo]
    total: int
    unread_count: int
    skip: int
    limit: int


class ReadAllResponse(BaseCamelCaseModel):
    """全件既読レスポンススキーマ。

    すべて既読にする操作の結果。
    """

    updated_count: int
