"""システムアラートリポジトリ。

このモジュールは、システムアラートのデータアクセスを提供します。
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.system.system_alert import SystemAlert
from app.repositories.base import BaseRepository


class SystemAlertRepository(BaseRepository[SystemAlert, uuid.UUID]):
    """システムアラートリポジトリ。

    システムアラートのCRUD操作を提供します。

    メソッド:
        - get_with_creator: 作成者情報付きで取得
        - list_enabled: 有効なアラートを取得
        - list_by_condition_type: 条件種別でアラートを取得
        - list_all: 全アラートを取得
        - update_trigger_info: 発火情報を更新
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(SystemAlert, db)

    async def get_with_creator(self, id: uuid.UUID) -> SystemAlert | None:
        """作成者情報付きでアラートを取得します。

        Args:
            id: アラートID

        Returns:
            SystemAlert | None: アラート（作成者情報付き）
        """
        query = select(SystemAlert).options(selectinload(SystemAlert.creator)).where(SystemAlert.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_enabled(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAlert]:
        """有効なアラートを取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAlert]: アラートリスト
        """
        query = (
            select(SystemAlert)
            .options(selectinload(SystemAlert.creator))
            .where(SystemAlert.is_enabled == True)  # noqa: E712
            .order_by(SystemAlert.name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_condition_type(
        self,
        condition_type: str,
        *,
        enabled_only: bool = True,
    ) -> list[SystemAlert]:
        """条件種別でアラートを取得します。

        Args:
            condition_type: 条件種別
            enabled_only: 有効なアラートのみ

        Returns:
            list[SystemAlert]: アラートリスト
        """
        query = select(SystemAlert).where(SystemAlert.condition_type == condition_type)

        if enabled_only:
            query = query.where(SystemAlert.is_enabled == True)  # noqa: E712

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAlert]:
        """全アラートを取得します。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[SystemAlert]: アラートリスト
        """
        query = select(SystemAlert).options(selectinload(SystemAlert.creator)).order_by(SystemAlert.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_trigger_info(
        self,
        alert_id: uuid.UUID,
        triggered_at: datetime,
    ) -> SystemAlert | None:
        """発火情報を更新します。

        Args:
            alert_id: アラートID
            triggered_at: 発火日時

        Returns:
            SystemAlert | None: 更新されたアラート
        """
        alert = await self.get(alert_id)
        if alert is None:
            return None

        alert.last_triggered_at = triggered_at
        alert.trigger_count += 1

        await self.db.flush()
        await self.db.refresh(alert)
        return alert
