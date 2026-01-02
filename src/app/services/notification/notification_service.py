"""ユーザー通知サービスの実装。

共通UI設計書（UI-006〜UI-011）に基づくユーザー通知機能を提供します。
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.notification import NotificationTypeEnum, ReferenceTypeEnum, UserNotification
from app.schemas.notification import (
    NotificationCreateRequest,
    NotificationInfo,
    NotificationListResponse,
    ReadAllResponse,
)

logger = get_logger(__name__)


class UserNotificationService:
    """ユーザー通知サービス。

    ユーザー向け通知のCRUD操作、既読管理、通知生成機能を提供します。
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db

    async def list_notifications(
        self,
        user_id: uuid.UUID,
        is_read: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> NotificationListResponse:
        """通知一覧を取得します。

        Args:
            user_id: ユーザーID
            is_read: 既読/未読フィルター
            skip: スキップ数
            limit: 取得件数

        Returns:
            NotificationListResponse: 通知一覧レスポンス
        """
        # 基本クエリ
        base_query = select(UserNotification).where(UserNotification.user_id == user_id)

        if is_read is not None:
            base_query = base_query.where(UserNotification.is_read == is_read)

        # 総数をカウント
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 未読数をカウント
        unread_stmt = select(func.count()).where(
            UserNotification.user_id == user_id,
            UserNotification.is_read == False,  # noqa: E712
        )
        unread_result = await self.db.execute(unread_stmt)
        unread_count = unread_result.scalar() or 0

        # 通知一覧を取得
        list_stmt = (
            base_query.order_by(UserNotification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        list_result = await self.db.execute(list_stmt)
        notifications = list_result.scalars().all()

        return NotificationListResponse(
            notifications=[self._to_info(n) for n in notifications],
            total=total,
            unread_count=unread_count,
            skip=skip,
            limit=limit,
        )

    async def get_notification(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> NotificationInfo | None:
        """通知詳細を取得します。

        Args:
            notification_id: 通知ID
            user_id: ユーザーID

        Returns:
            NotificationInfo | None: 通知情報（見つからない場合はNone）
        """
        stmt = select(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification is None:
            return None

        return self._to_info(notification)

    async def mark_as_read(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> NotificationInfo | None:
        """通知を既読にします。

        Args:
            notification_id: 通知ID
            user_id: ユーザーID

        Returns:
            NotificationInfo | None: 更新後の通知情報（見つからない場合はNone）
        """
        stmt = select(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification is None:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
            await self.db.commit()
            await self.db.refresh(notification)
            logger.info(
                "通知を既読にしました",
                notification_id=str(notification_id),
                user_id=str(user_id),
            )

        return self._to_info(notification)

    async def mark_all_as_read(self, user_id: uuid.UUID) -> ReadAllResponse:
        """すべての通知を既読にします。

        Args:
            user_id: ユーザーID

        Returns:
            ReadAllResponse: 更新件数を含むレスポンス
        """
        now = datetime.now(UTC)
        stmt = (
            update(UserNotification)
            .where(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False,  # noqa: E712
            )
            .values(is_read=True, read_at=now)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        updated_count = result.rowcount
        logger.info(
            "すべての通知を既読にしました",
            user_id=str(user_id),
            updated_count=updated_count,
        )

        return ReadAllResponse(updated_count=updated_count)

    async def delete_notification(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """通知を削除します。

        Args:
            notification_id: 通知ID
            user_id: ユーザーID

        Returns:
            bool: 削除成功した場合True
        """
        stmt = select(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification is None:
            return False

        await self.db.delete(notification)
        await self.db.commit()

        logger.info(
            "通知を削除しました",
            notification_id=str(notification_id),
            user_id=str(user_id),
        )

        return True

    async def create_notification(
        self,
        data: NotificationCreateRequest,
    ) -> NotificationInfo:
        """通知を作成します。

        システム内部から通知を生成する際に使用します。

        Args:
            data: 通知作成データ

        Returns:
            NotificationInfo: 作成された通知情報
        """
        notification = UserNotification(
            user_id=data.user_id,
            type=data.type,
            title=data.title,
            message=data.message,
            icon=data.icon,
            link_url=data.link_url,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        logger.info(
            "通知を作成しました",
            notification_id=str(notification.id),
            user_id=str(data.user_id),
            type=data.type.value,
        )

        return self._to_info(notification)

    async def count_unread(self, user_id: uuid.UUID) -> int:
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

    def _to_info(self, notification: UserNotification) -> NotificationInfo:
        """UserNotificationモデルをNotificationInfoスキーマに変換します。

        Args:
            notification: 通知モデル

        Returns:
            NotificationInfo: 通知情報スキーマ
        """
        return NotificationInfo(
            id=notification.id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            icon=notification.icon,
            link_url=notification.link_url,
            reference_type=notification.reference_type,
            reference_id=notification.reference_id,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
        )
