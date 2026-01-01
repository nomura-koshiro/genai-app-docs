"""通知テンプレートリポジトリ。

このモジュールは、通知テンプレートのデータアクセスを提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system.notification_template import NotificationTemplate
from app.repositories.base import BaseRepository


class NotificationTemplateRepository(BaseRepository[NotificationTemplate, uuid.UUID]):
    """通知テンプレートリポジトリ。

    通知テンプレートのCRUD操作を提供します。

    メソッド:
        - get_by_event_type: イベント種別で取得
        - list_active: アクティブなテンプレートを取得
        - list_all: 全テンプレートを取得
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(NotificationTemplate, db)

    async def get_by_event_type(self, event_type: str) -> NotificationTemplate | None:
        """イベント種別でテンプレートを取得します。

        Args:
            event_type: イベント種別

        Returns:
            NotificationTemplate | None: 通知テンプレート
        """
        query = select(NotificationTemplate).where(NotificationTemplate.event_type == event_type)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NotificationTemplate]:
        """アクティブなテンプレートを取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[NotificationTemplate]: テンプレートリスト
        """
        query = (
            select(NotificationTemplate)
            .where(NotificationTemplate.is_active == True)  # noqa: E712
            .order_by(NotificationTemplate.event_type)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NotificationTemplate]:
        """全テンプレートを取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[NotificationTemplate]: テンプレートリスト
        """
        query = select(NotificationTemplate).order_by(NotificationTemplate.event_type).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
