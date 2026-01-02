"""操作履歴リポジトリ。

このモジュールは、ユーザー操作履歴のデータアクセスを提供します。
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, delete, func, select
from sqlalchemy.engine import CursorResult
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

    def _build_filter_conditions(
        self,
        *,
        user_id: uuid.UUID | None = None,
        action_type: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        has_error: bool | None = None,
    ) -> list:
        """フィルタ条件を構築します（DRY原則適用）。

        Args:
            user_id: ユーザーID
            action_type: 操作種別
            resource_type: リソース種別
            start_date: 開始日時
            end_date: 終了日時
            has_error: エラーのみ

        Returns:
            list: SQLAlchemy条件式のリスト
        """
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

        return conditions

    async def get_with_user(self, id: uuid.UUID) -> UserActivity | None:
        """ユーザー情報付きで操作履歴を取得します。

        Args:
            id: 操作履歴ID

        Returns:
            UserActivity | None: 操作履歴（ユーザー情報付き）
        """
        query = select(UserActivity).options(selectinload(UserActivity.user)).where(UserActivity.id == id)
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

        # 共通メソッドでフィルタ条件を構築（DRY原則）
        conditions = self._build_filter_conditions(
            user_id=user_id,
            action_type=action_type,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            has_error=has_error,
        )

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

        # 共通メソッドでフィルタ条件を構築（DRY原則）
        conditions = self._build_filter_conditions(
            user_id=user_id,
            action_type=action_type,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            has_error=has_error,
        )

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
        # 日付条件を構築
        conditions = self._build_filter_conditions(
            start_date=start_date,
            end_date=end_date,
        )

        # クエリを構築
        total_query = select(func.count()).select_from(UserActivity)
        if conditions:
            total_query = total_query.where(and_(*conditions))

        error_conditions = [*conditions, UserActivity.error_message.isnot(None)]
        error_query = select(func.count()).select_from(UserActivity).where(and_(*error_conditions))

        avg_query = select(func.avg(UserActivity.duration_ms)).select_from(UserActivity)
        if conditions:
            avg_query = avg_query.where(and_(*conditions))

        # 3つのクエリを並行実行（パフォーマンス最適化）
        total_result, error_result, avg_result = await asyncio.gather(
            self.db.execute(total_query),
            self.db.execute(error_query),
            self.db.execute(avg_query),
        )

        return {
            "total_count": total_result.scalar_one(),
            "error_count": error_result.scalar_one(),
            "average_duration_ms": float(avg_result.scalar_one() or 0),
        }

    async def get_date_range(
        self,
        *,
        end_date: datetime | None = None,
    ) -> tuple[datetime | None, datetime | None]:
        """レコードの日付範囲を取得します。

        Args:
            end_date: 終了日時（フィルタ）

        Returns:
            tuple[datetime | None, datetime | None]: (最古日時, 最新日時)
        """
        # MIN/MAXを単一クエリで取得（パフォーマンス最適化）
        query = select(
            func.min(UserActivity.created_at).label("oldest"),
            func.max(UserActivity.created_at).label("newest"),
        )
        if end_date:
            query = query.where(UserActivity.created_at <= end_date)

        result = await self.db.execute(query)
        row = result.one()
        return (row.oldest, row.newest)

    async def delete_old_records(self, before_date: datetime) -> int:
        """古いレコードを削除します。

        Args:
            before_date: この日付より前のレコードを削除

        Returns:
            int: 削除件数
        """
        query = delete(UserActivity).where(UserActivity.created_at < before_date)
        result: CursorResult[Any] = await self.db.execute(query)  # type: ignore[assignment]
        await self.db.flush()
        return result.rowcount or 0
