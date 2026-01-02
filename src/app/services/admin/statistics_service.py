"""統計情報サービス。

このモジュールは、システム統計情報の集計機能を提供します。
"""

import asyncio
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import measure_performance
from app.core.logging import get_logger
from app.models import Project, UserAccount
from app.models.audit.user_activity import UserActivity
from app.schemas.admin.statistics import (
    ApiStatistics,
    ApiStatisticsDetailResponse,
    ErrorStatisticsDetailResponse,
    ProjectStatistics,
    StatisticsOverviewResponse,
    StorageStatistics,
    StorageStatisticsDetailResponse,
    TimeSeriesDataPoint,
    UserStatistics,
    UserStatisticsDetailResponse,
)
from app.utils import DataFormatter

logger = get_logger(__name__)


class StatisticsService:
    """統計情報サービス。

    システム統計情報の集計機能を提供します。

    メソッド:
        - get_overview: 統計概要を取得
        - get_user_statistics: ユーザー統計を取得
        - get_storage_statistics: ストレージ統計を取得
        - get_api_statistics: API統計を取得
        - get_error_statistics: エラー統計を取得
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db

    @measure_performance
    async def get_overview(
        self,
        period: str = "day",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> StatisticsOverviewResponse:
        """統計概要を取得します。

        Args:
            period: 期間（day/week/month/year）
            start_date: 開始日
            end_date: 終了日

        Returns:
            StatisticsOverviewResponse: 統計概要
        """
        logger.info(
            "統計概要を取得中",
            period=period,
            action="get_statistics_overview",
        )

        # 4つの統計を並行実行
        users, projects, storage, api = await asyncio.gather(
            self._get_user_summary(),
            self._get_project_summary(),
            self._get_storage_summary(),
            self._get_api_summary(),
        )

        return StatisticsOverviewResponse(
            users=users,
            projects=projects,
            storage=storage,
            api=api,
        )

    async def _get_user_summary(self) -> UserStatistics:
        """ユーザー統計サマリーを取得します。"""
        # 総ユーザー数
        total_query = select(func.count()).select_from(UserAccount)

        # 今日アクティブなユーザー数
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        active_query = select(func.count(func.distinct(UserActivity.user_id))).where(
            UserActivity.created_at >= today_start
        )

        # 今月の新規ユーザー数
        month_start = datetime.now(UTC).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        new_query = (
            select(func.count())
            .select_from(UserAccount)
            .where(UserAccount.created_at >= month_start)
        )

        # 3つのクエリを並行実行
        total_result, active_result, new_result = await asyncio.gather(
            self.db.execute(total_query),
            self.db.execute(active_query),
            self.db.execute(new_query),
        )

        total = total_result.scalar_one() or 0
        active_today = active_result.scalar_one() or 0
        new_this_month = new_result.scalar_one() or 0

        return UserStatistics(
            total=total,
            active_today=active_today,
            new_this_month=new_this_month,
        )

    async def _get_project_summary(self) -> ProjectStatistics:
        """プロジェクト統計サマリーを取得します。"""
        from sqlalchemy import case

        month_start = datetime.now(UTC).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # 1クエリで全カウントを取得
        result = await self.db.execute(
            select(
                func.count(Project.id).label("total"),
                func.count(case((Project.is_active == True, 1))).label(  # noqa: E712
                    "active"
                ),
                func.count(case((Project.created_at >= month_start, 1))).label(
                    "created_this_month"
                ),
            )
        )
        row = result.one()

        return ProjectStatistics(
            total=row.total or 0,
            active=row.active or 0,
            created_this_month=row.created_this_month or 0,
        )

    async def _get_storage_summary(self) -> StorageStatistics:
        """ストレージ統計サマリーを取得します。"""
        # TODO: 実際のストレージ使用量を計算
        # ここではプレースホルダー値を返す
        total_bytes = 0
        used_percentage = 0.0

        return StorageStatistics(
            total_bytes=total_bytes,
            total_display=DataFormatter.format_bytes(total_bytes),
            used_percentage=used_percentage,
        )

    async def _get_api_summary(self) -> ApiStatistics:
        """API統計サマリーを取得します。"""
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # 今日のリクエスト数
        request_query = (
            select(func.count())
            .select_from(UserActivity)
            .where(UserActivity.created_at >= today_start)
        )

        # 平均レスポンス時間
        avg_query = select(func.avg(UserActivity.duration_ms)).where(
            UserActivity.created_at >= today_start
        )

        # エラー率
        error_query = (
            select(func.count())
            .select_from(UserActivity)
            .where(
                UserActivity.created_at >= today_start,
                UserActivity.response_status >= 400,
            )
        )

        # 3つのクエリを並行実行
        request_result, avg_result, error_result = await asyncio.gather(
            self.db.execute(request_query),
            self.db.execute(avg_query),
            self.db.execute(error_query),
        )

        requests_today = request_result.scalar_one() or 0
        average_response_ms = avg_result.scalar_one() or 0
        error_count = error_result.scalar_one() or 0
        error_rate = (error_count / requests_today * 100) if requests_today > 0 else 0

        return ApiStatistics(
            requests_today=requests_today,
            average_response_ms=float(average_response_ms),
            error_rate_percentage=round(error_rate, 2),
        )

    @measure_performance
    async def get_user_statistics(
        self,
        days: int = 30,
    ) -> UserStatisticsDetailResponse:
        """ユーザー統計詳細を取得します。

        Args:
            days: 取得日数

        Returns:
            UserStatisticsDetailResponse: ユーザー統計詳細
        """
        # 総ユーザー数
        total_query = select(func.count()).select_from(UserAccount)
        result = await self.db.execute(total_query)
        total = result.scalar_one() or 0

        active_users = await self._get_active_users_trend(days)
        new_users = await self._get_new_users_trend(days)

        return UserStatisticsDetailResponse(
            total=total,
            active_users=active_users,
            new_users=new_users,
        )

    async def _get_active_users_trend(self, days: int) -> list[TimeSeriesDataPoint]:
        """アクティブユーザー推移を取得します。"""
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        # 1回のGROUP BYクエリで全日付のカウントを取得
        query = (
            select(
                cast(UserActivity.created_at, Date).label("date"),
                func.count(func.distinct(UserActivity.user_id)).label("count"),
            )
            .where(
                UserActivity.created_at
                >= datetime.combine(start_date, datetime.min.time()).replace(
                    tzinfo=UTC
                ),
                UserActivity.created_at
                < datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                ).replace(tzinfo=UTC),
            )
            .group_by(cast(UserActivity.created_at, Date))
        )

        result = await self.db.execute(query)
        count_map: dict[date, int] = {row.date: row.count for row in result.all()}  # type: ignore[misc]

        # 結果を構築（0埋め）
        data_points = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            data_points.append(
                TimeSeriesDataPoint(
                    date=current_date, value=float(count_map.get(current_date, 0))
                )
            )

        return data_points

    async def _get_new_users_trend(self, days: int) -> list[TimeSeriesDataPoint]:
        """新規ユーザー推移を取得します。"""
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        # 1回のGROUP BYクエリで全日付のカウントを取得
        query = (
            select(
                cast(UserAccount.created_at, Date).label("date"),
                func.count().label("count"),
            )
            .where(
                UserAccount.created_at
                >= datetime.combine(start_date, datetime.min.time()).replace(
                    tzinfo=UTC
                ),
                UserAccount.created_at
                < datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                ).replace(tzinfo=UTC),
            )
            .group_by(cast(UserAccount.created_at, Date))
        )

        result = await self.db.execute(query)
        count_map: dict[date, int] = {row.date: row.count for row in result.all()}  # type: ignore[misc]

        # 結果を構築（0埋め）
        data_points = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            data_points.append(
                TimeSeriesDataPoint(
                    date=current_date, value=float(count_map.get(current_date, 0))
                )
            )

        return data_points

    @measure_performance
    async def get_storage_statistics(
        self,
        days: int = 30,
    ) -> StorageStatisticsDetailResponse:
        """ストレージ使用量推移を取得します。

        Args:
            days: 取得日数

        Returns:
            StorageStatisticsDetailResponse: ストレージ統計詳細
        """
        # TODO: 実際のストレージ使用量を計算
        # 現在はプレースホルダー値を返す
        total_bytes = 0

        usage_trend = await self._get_storage_usage_trend(days)

        return StorageStatisticsDetailResponse(
            total_bytes=total_bytes,
            total_display=DataFormatter.format_bytes(total_bytes),
            usage_trend=usage_trend,
        )

    async def _get_storage_usage_trend(self, days: int) -> list[TimeSeriesDataPoint]:
        """ストレージ使用量推移を取得します。"""
        # TODO: 実際のストレージ使用量を計算
        # 現在はプレースホルダー値を返す
        result = []
        today = date.today()

        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            result.append(TimeSeriesDataPoint(date=target_date, value=0.0))

        return result

    @measure_performance
    async def get_api_request_statistics(
        self,
        days: int = 30,
    ) -> ApiStatisticsDetailResponse:
        """APIリクエスト統計を取得します。

        Args:
            days: 取得日数

        Returns:
            ApiStatisticsDetailResponse: APIリクエスト統計詳細
        """
        request_trend = await self._get_api_request_trend(days)

        # 総リクエスト数を計算
        total_requests = sum(int(point.value) for point in request_trend)

        # 平均レスポンス時間を計算
        avg_query = select(func.avg(UserActivity.duration_ms))
        result = await self.db.execute(avg_query)
        average_response_ms = result.scalar_one() or 0

        return ApiStatisticsDetailResponse(
            total_requests=total_requests,
            request_trend=request_trend,
            average_response_ms=float(average_response_ms),
        )

    async def _get_api_request_trend(self, days: int) -> list[TimeSeriesDataPoint]:
        """APIリクエスト数推移を取得します。"""
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        # 1回のGROUP BYクエリで全日付のカウントを取得
        query = (
            select(
                cast(UserActivity.created_at, Date).label("date"),
                func.count().label("count"),
            )
            .where(
                UserActivity.created_at
                >= datetime.combine(start_date, datetime.min.time()).replace(
                    tzinfo=UTC
                ),
                UserActivity.created_at
                < datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                ).replace(tzinfo=UTC),
            )
            .group_by(cast(UserActivity.created_at, Date))
        )

        result = await self.db.execute(query)
        count_map: dict[date, int] = {row.date: row.count for row in result.all()}  # type: ignore[misc]

        # 結果を構築（0埋め）
        data_points = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            data_points.append(
                TimeSeriesDataPoint(
                    date=current_date, value=float(count_map.get(current_date, 0))
                )
            )

        return data_points

    @measure_performance
    async def get_error_statistics(
        self,
        days: int = 30,
    ) -> ErrorStatisticsDetailResponse:
        """エラー統計を取得します。

        Args:
            days: 取得日数

        Returns:
            ErrorStatisticsDetailResponse: エラー統計詳細
        """
        # 総エラー数を計算
        error_query = (
            select(func.count())
            .select_from(UserActivity)
            .where(UserActivity.response_status >= 400)
        )

        # エラー率を計算
        total_query = select(func.count()).select_from(UserActivity)

        # 4つの処理を並行実行
        error_trend, error_result, total_result, error_by_type = await asyncio.gather(
            self._get_error_rate_trend(days),
            self.db.execute(error_query),
            self.db.execute(total_query),
            self._get_error_by_type(),
        )

        total_errors = error_result.scalar_one() or 0
        total_requests = total_result.scalar_one() or 0
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        return ErrorStatisticsDetailResponse(
            total_errors=total_errors,
            error_rate=round(error_rate, 2),
            error_trend=error_trend,
            error_by_type=error_by_type,
        )

    async def _get_error_rate_trend(self, days: int) -> list[TimeSeriesDataPoint]:
        """エラー率推移を取得します。"""
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        # 1回のGROUP BYクエリで全日付の総リクエスト数とエラー数を取得
        query = (
            select(
                cast(UserActivity.created_at, Date).label("date"),
                func.count().label("total_count"),
                func.sum(
                    func.case((UserActivity.response_status >= 400, 1), else_=0)
                ).label("error_count"),
            )
            .where(
                UserActivity.created_at
                >= datetime.combine(start_date, datetime.min.time()).replace(
                    tzinfo=UTC
                ),
                UserActivity.created_at
                < datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                ).replace(tzinfo=UTC),
            )
            .group_by(cast(UserActivity.created_at, Date))
        )

        result = await self.db.execute(query)
        stats_map = {
            row.date: (row.total_count, row.error_count or 0) for row in result.all()
        }

        # 結果を構築（0埋め）
        data_points = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            total_count, error_count = stats_map.get(current_date, (0, 0))
            error_rate = (error_count / total_count * 100) if total_count > 0 else 0

            data_points.append(
                TimeSeriesDataPoint(date=current_date, value=round(error_rate, 2))
            )

        return data_points

    async def _get_error_by_type(self) -> dict[str, int]:
        """エラー種別ごとのカウントを取得します。"""
        query = (
            select(UserActivity.response_status, func.count())
            .where(UserActivity.response_status >= 400)
            .group_by(UserActivity.response_status)
        )

        result = await self.db.execute(query)
        rows = result.all()

        error_by_type = {}
        for status_code, count in rows:
            status_name = {
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                422: "Validation Error",
                500: "Internal Server Error",
                502: "Bad Gateway",
                503: "Service Unavailable",
            }.get(status_code, f"HTTP {status_code}")

            error_by_type[status_name] = count

        return error_by_type
