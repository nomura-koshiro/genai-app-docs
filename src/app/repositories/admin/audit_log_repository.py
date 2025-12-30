"""監査ログリポジトリ。

このモジュールは、監査ログのデータアクセスを提供します。
"""

import uuid
from datetime import datetime

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog, uuid.UUID]):
    """監査ログリポジトリ。

    監査ログのCRUD操作と検索機能を提供します。

    メソッド:
        - get_with_user: ユーザー情報付きで取得
        - list_with_filters: フィルタ付き一覧取得
        - list_by_event_type: イベント種別で取得
        - list_by_resource: リソースで取得
        - count_with_filters: フィルタ付きカウント
        - delete_old_records: 古いレコード削除
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。"""
        super().__init__(AuditLog, db)

    async def get_with_user(self, id: uuid.UUID) -> AuditLog | None:
        """ユーザー情報付きで監査ログを取得します。

        Args:
            id: 監査ログID

        Returns:
            AuditLog | None: 監査ログ（ユーザー情報付き）
        """
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.id == id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        event_type: str | None = None,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        severity: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """フィルタ付きで監査ログ一覧を取得します。

        Args:
            event_type: イベント種別
            user_id: ユーザーID
            resource_type: リソース種別
            resource_id: リソースID
            severity: 重要度
            start_date: 開始日時
            end_date: 終了日時
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[AuditLog]: 監査ログリスト
        """
        query = select(AuditLog).options(selectinload(AuditLog.user))

        conditions = []

        if event_type:
            conditions.append(AuditLog.event_type == event_type)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if severity:
            conditions.append(AuditLog.severity == severity)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_event_type(
        self,
        event_type: str,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """イベント種別で監査ログを取得します。

        Args:
            event_type: イベント種別（DATA_CHANGE/ACCESS/SECURITY）
            start_date: 開始日時
            end_date: 終了日時
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[AuditLog]: 監査ログリスト
        """
        return await self.list_with_filters(
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

    async def list_by_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """リソースで監査ログを取得します。

        Args:
            resource_type: リソース種別
            resource_id: リソースID
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[AuditLog]: 監査ログリスト
        """
        return await self.list_with_filters(
            resource_type=resource_type,
            resource_id=resource_id,
            skip=skip,
            limit=limit,
        )

    async def count_with_filters(
        self,
        *,
        event_type: str | None = None,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        severity: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """フィルタ付きでカウントを取得します。

        Args:
            event_type: イベント種別
            user_id: ユーザーID
            resource_type: リソース種別
            resource_id: リソースID
            severity: 重要度
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            int: レコード数
        """
        query = select(func.count()).select_from(AuditLog)

        conditions = []

        if event_type:
            conditions.append(AuditLog.event_type == event_type)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if severity:
            conditions.append(AuditLog.severity == severity)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar_one()

    async def delete_old_records(self, before_date: datetime) -> int:
        """古いレコードを削除します。

        Args:
            before_date: この日付より前のレコードを削除

        Returns:
            int: 削除件数
        """
        query = delete(AuditLog).where(AuditLog.created_at < before_date)
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount
