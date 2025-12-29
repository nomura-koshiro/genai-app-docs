"""ユーザー操作履歴リポジトリ。

このモジュールは、ユーザー操作履歴のデータアクセス操作を提供します。

主な機能:
    - 操作履歴の記録
    - ユーザー別履歴検索
    - 日時範囲検索
    - エラー履歴検索

使用例:
    >>> from app.repositories.system.user_activity import UserActivityRepository
    >>> async with get_db() as db:
    ...     repo = UserActivityRepository(db)
    ...     activities = await repo.get_by_user(user_id, skip=0, limit=50)
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.system import UserActivity
from app.repositories.base import BaseRepository


class UserActivityRepository(BaseRepository[UserActivity, uuid.UUID]):
    """ユーザー操作履歴リポジトリクラス。

    ユーザーの操作履歴（API呼び出し、UI操作）の記録と検索を提供します。

    メソッド:
        - create_activity(): 操作履歴を記録
        - get_by_user(): ユーザー別履歴を取得
        - get_by_date_range(): 日時範囲で検索
        - get_errors(): エラー履歴を取得
        - search(): 複合条件で検索

    継承されるメソッド（BaseRepositoryから）:
        - get(id): IDによる取得
        - get_multi(): ページネーション付き一覧取得
        - count(): レコード数カウント

    Note:
        - 履歴は基本的に読み取り専用（更新・削除は通常不要）
        - 大量データのため、常にページネーションを使用すること
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(UserActivity, db)

    async def create_activity(
        self,
        user_id: uuid.UUID,
        event_type: str,
        action: str,
        *,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        endpoint: str | None = None,
        method: str | None = None,
        page_path: str | None = None,
        status: str = "success",
        status_code: int | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        duration_ms: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UserActivity:
        """ユーザー操作履歴を記録します。

        Args:
            user_id: ユーザーID
            event_type: イベント種別（api_call / ui_action）
            action: 操作内容（create_project, button_click等）
            resource_type: リソース種別（project, session等）
            resource_id: 対象リソースのID
            endpoint: APIエンドポイント
            method: HTTPメソッド
            page_path: ページパス（UI操作時）
            status: 処理結果（success / error）
            status_code: HTTPステータスコード
            error_type: エラー種別
            error_message: エラーメッセージ
            duration_ms: 処理時間（ミリ秒）
            ip_address: クライアントIPアドレス
            user_agent: ユーザーエージェント
            metadata: 追加メタデータ

        Returns:
            作成された操作履歴レコード

        Example:
            >>> activity = await repo.create_activity(
            ...     user_id=user.id,
            ...     event_type="api_call",
            ...     action="create_project",
            ...     resource_type="project",
            ...     resource_id=project_id,
            ...     endpoint="/api/v1/projects",
            ...     method="POST",
            ...     status="success",
            ...     status_code=201,
            ...     duration_ms=150,
            ... )
        """
        return await self.create(
            user_id=user_id,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            endpoint=endpoint,
            method=method,
            page_path=page_path,
            status=status,
            status_code=status_code,
            error_type=error_type,
            error_message=error_message,
            duration_ms=duration_ms,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
        event_type: str | None = None,
        status: str | None = None,
    ) -> list[UserActivity]:
        """ユーザー別の操作履歴を取得します。

        Args:
            user_id: ユーザーID
            skip: スキップするレコード数
            limit: 取得する最大レコード数
            event_type: イベント種別でフィルタ（api_call / ui_action）
            status: ステータスでフィルタ（success / error）

        Returns:
            操作履歴のリスト（新しい順）

        Example:
            >>> activities = await repo.get_by_user(
            ...     user_id=user.id,
            ...     limit=20,
            ...     status="error",
            ... )
        """
        query = (
            select(UserActivity)
            .where(UserActivity.user_id == user_id)
            .order_by(desc(UserActivity.created_at))
        )

        if event_type:
            query = query.where(UserActivity.event_type == event_type)
        if status:
            query = query.where(UserActivity.status == status)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        *,
        user_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserActivity]:
        """日時範囲で操作履歴を検索します。

        Args:
            start_date: 検索開始日時
            end_date: 検索終了日時
            user_id: 特定ユーザーに限定（オプション）
            skip: スキップするレコード数
            limit: 取得する最大レコード数

        Returns:
            操作履歴のリスト（新しい順）

        Example:
            >>> from datetime import datetime, timedelta
            >>> end = datetime.now()
            >>> start = end - timedelta(days=7)
            >>> activities = await repo.get_by_date_range(start, end, limit=100)
        """
        query = (
            select(UserActivity)
            .options(selectinload(UserActivity.user))
            .where(
                and_(
                    UserActivity.created_at >= start_date,
                    UserActivity.created_at <= end_date,
                )
            )
            .order_by(desc(UserActivity.created_at))
        )

        if user_id:
            query = query.where(UserActivity.user_id == user_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_errors(
        self,
        *,
        user_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 50,
        since: datetime | None = None,
    ) -> list[UserActivity]:
        """エラー履歴を取得します。

        Args:
            user_id: 特定ユーザーに限定（オプション）
            skip: スキップするレコード数
            limit: 取得する最大レコード数
            since: この日時以降のエラーのみ取得

        Returns:
            エラー履歴のリスト（新しい順）

        Example:
            >>> from datetime import datetime, timedelta
            >>> since = datetime.now() - timedelta(hours=24)
            >>> errors = await repo.get_errors(since=since, limit=100)
        """
        query = (
            select(UserActivity)
            .options(selectinload(UserActivity.user))
            .where(UserActivity.status == "error")
            .order_by(desc(UserActivity.created_at))
        )

        if user_id:
            query = query.where(UserActivity.user_id == user_id)
        if since:
            query = query.where(UserActivity.created_at >= since)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        *,
        user_id: uuid.UUID | None = None,
        event_type: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[UserActivity], int]:
        """複合条件で操作履歴を検索します。

        Args:
            user_id: ユーザーID
            event_type: イベント種別
            action: 操作内容
            resource_type: リソース種別
            status: ステータス
            start_date: 検索開始日時
            end_date: 検索終了日時
            skip: スキップするレコード数
            limit: 取得する最大レコード数

        Returns:
            (操作履歴のリスト, 総件数)

        Example:
            >>> activities, total = await repo.search(
            ...     user_id=user.id,
            ...     action="create_project",
            ...     start_date=start,
            ...     end_date=end,
            ...     limit=20,
            ... )
            >>> print(f"Found {total} activities, showing {len(activities)}")
        """
        # ベースクエリ
        base_query = select(UserActivity).options(selectinload(UserActivity.user))
        count_query = select(func.count()).select_from(UserActivity)

        # フィルタを構築
        conditions = []
        if user_id:
            conditions.append(UserActivity.user_id == user_id)
        if event_type:
            conditions.append(UserActivity.event_type == event_type)
        if action:
            conditions.append(UserActivity.action == action)
        if resource_type:
            conditions.append(UserActivity.resource_type == resource_type)
        if status:
            conditions.append(UserActivity.status == status)
        if start_date:
            conditions.append(UserActivity.created_at >= start_date)
        if end_date:
            conditions.append(UserActivity.created_at <= end_date)

        if conditions:
            base_query = base_query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 総件数を取得
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        # ページネーション適用
        query = (
            base_query.order_by(desc(UserActivity.created_at)).offset(skip).limit(limit)
        )
        result = await self.db.execute(query)

        return list(result.scalars().all()), total

    async def count_by_user(
        self,
        user_id: uuid.UUID,
        *,
        status: str | None = None,
        since: datetime | None = None,
    ) -> int:
        """ユーザーの操作履歴数をカウントします。

        Args:
            user_id: ユーザーID
            status: ステータスでフィルタ
            since: この日時以降のみカウント

        Returns:
            操作履歴数

        Example:
            >>> error_count = await repo.count_by_user(
            ...     user_id=user.id,
            ...     status="error",
            ...     since=datetime.now() - timedelta(days=7),
            ... )
        """
        query = select(func.count()).select_from(UserActivity).where(
            UserActivity.user_id == user_id
        )

        if status:
            query = query.where(UserActivity.status == status)
        if since:
            query = query.where(UserActivity.created_at >= since)

        result = await self.db.execute(query)
        return result.scalar_one()
