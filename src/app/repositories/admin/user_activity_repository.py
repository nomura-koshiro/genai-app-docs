"""操作履歴リポジトリ。

このモジュールは、ユーザー操作履歴のデータアクセスを提供します。
"""

import uuid
from datetime import datetime

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit.user_activity import UserActivity
from app.repositories.base import BaseRepository


class UserActivityRepository(BaseRepository[UserActivity, uuid.UUID]):
    """操作履歴リポジトリ。

    ユーザー操作履歴のCRUD操作と検索機能を提供します。

    メソッド:
        - get_with_user: ユーザー情報付きで取得
        - list_with_filters: フィルタ付き一覧取得
        - list_errors: エラーのみ取得
        - count_with_filters: フィルタ付きカウント
        - get_statistics: 統計情報取得
        - delete_old_records: 古いレコード削除
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(UserActivity, db)

    async def get_with_user(self, id: uuid.UUID) -> UserActivity | None:
        """ユーザー情報付きで操作履歴を取得します。

        Args:
            id: 操作履歴ID

        Returns:
            UserActivity | None: 操作履歴（ユーザー情報付き）
        """
        query = (
            select(UserActivity)
            .options(selectinload(UserActivity.user))
            .where(UserActivity.id == id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        user_id: uuid.UUID | None = None,
        action_type: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        has_error: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserActivity]:
        """フィルタ付きで操作履歴一覧を取得します。

        Args:
            user_id: ユーザーID
            action_type: 操作種別
            resource_type: リソース種別
            start_date: 開始日時
            end_date: 終了日時
            has_error: エラーのみ
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[UserActivity]: 操作履歴リスト
        """
        query = select(UserActivity).options(selectinload(UserActivity.user))

        # フィルタ条件を構築
        conditions = []

        if user_id:
            conditions.append(UserActivity.user_id == user_id)
        if action_type:
            conditions.append(UserActivity.action_type == action_type)
        if resource_type:
            conditions.append(UserActivity.resource_type == resource_type)
        if start_date:
            conditions.append(UserActivity.created_at >= start_date)
        if end_date:
            conditions.append(UserActivity.created_at <= end_date)
        if has_error is True:
            conditions.append(UserActivity.error_message.isnot(None))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(UserActivity.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_errors(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserActivity]:
        """エラー履歴のみを取得します。

        Args:
            start_date: 開始日時
            end_date: 終了日時
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[UserActivity]: エラー履歴リスト
        """
        return await self.list_with_filters(
            start_date=start_date,
            end_date=end_date,
            has_error=True,
            skip=skip,
            limit=limit,
        )

    async def count_with_filters(
        self,
        *,
        user_id: uuid.UUID | None = None,
        action_type: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        has_error: bool | None = None,
    ) -> int:
        """フィルタ付きでカウントを取得します。

        Args:
            user_id: ユーザーID
            action_type: 操作種別
            resource_type: リソース種別
            start_date: 開始日時
            end_date: 終了日時
            has_error: エラーのみ

        Returns:
            int: レコード数
        """
        query = select(func.count()).select_from(UserActivity)

        conditions = []

        if user_id:
            conditions.append(UserActivity.user_id == user_id)
        if action_type:
            conditions.append(UserActivity.action_type == action_type)
        if resource_type:
            conditions.append(UserActivity.resource_type == resource_type)
        if start_date:
            conditions.append(UserActivity.created_at >= start_date)
        if end_date:
            conditions.append(UserActivity.created_at <= end_date)
        if has_error is True:
            conditions.append(UserActivity.error_message.isnot(None))

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_statistics(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """統計情報を取得します。

        Args:
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            dict: 統計情報
                - total_count: 総件数
                - error_count: エラー件数
                - average_duration_ms: 平均処理時間
        """
        conditions = []

        if start_date:
            conditions.append(UserActivity.created_at >= start_date)
        if end_date:
            conditions.append(UserActivity.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else True

        # 総件数
        total_query = select(func.count()).select_from(UserActivity).where(where_clause)
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar_one()

        # エラー件数
        error_query = (
            select(func.count())
            .select_from(UserActivity)
            .where(and_(where_clause, UserActivity.error_message.isnot(None)))
        )
        error_result = await self.db.execute(error_query)
        error_count = error_result.scalar_one()

        # 平均処理時間
        avg_query = (
            select(func.avg(UserActivity.duration_ms))
            .select_from(UserActivity)
            .where(where_clause)
        )
        avg_result = await self.db.execute(avg_query)
        average_duration_ms = avg_result.scalar_one() or 0

        return {
            "total_count": total_count,
            "error_count": error_count,
            "average_duration_ms": float(average_duration_ms),
        }

    async def delete_old_records(self, before_date: datetime) -> int:
        """古いレコードを削除します。

        Args:
            before_date: この日付より前のレコードを削除

        Returns:
            int: 削除件数
        """
        query = delete(UserActivity).where(UserActivity.created_at < before_date)
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount
