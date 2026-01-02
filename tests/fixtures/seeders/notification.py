"""UserNotification シーダー。"""

import uuid
from datetime import UTC, datetime

from app.models import NotificationTypeEnum, ReferenceTypeEnum, UserNotification

from .base import BaseSeeder


class NotificationSeederMixin(BaseSeeder):
    """UserNotification作成用Mixin。"""

    async def create_notification(
        self,
        *,
        user_id: uuid.UUID,
        type: NotificationTypeEnum = NotificationTypeEnum.SYSTEM_ANNOUNCEMENT,
        title: str = "テスト通知",
        message: str = "テスト通知メッセージ",
        icon: str | None = "📢",
        link_url: str | None = None,
        reference_type: ReferenceTypeEnum | None = None,
        reference_id: uuid.UUID | None = None,
        is_read: bool = False,
        read_at: datetime | None = None,
    ) -> UserNotification:
        """テスト用通知を作成。"""
        notification = UserNotification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            icon=icon,
            link_url=link_url,
            reference_type=reference_type,
            reference_id=reference_id,
            is_read=is_read,
            read_at=read_at,
        )
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def create_unread_notifications(
        self,
        user_id: uuid.UUID,
        count: int = 3,
    ) -> list[UserNotification]:
        """複数の未読通知を作成。"""
        notifications = []
        for i in range(count):
            notification = await self.create_notification(
                user_id=user_id,
                title=f"テスト通知 {i + 1}",
                message=f"テスト通知メッセージ {i + 1}",
                is_read=False,
            )
            notifications.append(notification)
        return notifications

    async def create_read_notification(
        self,
        user_id: uuid.UUID,
        title: str = "既読通知",
        message: str = "既読通知メッセージ",
    ) -> UserNotification:
        """既読通知を作成。"""
        return await self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            is_read=True,
            read_at=datetime.now(UTC),
        )
