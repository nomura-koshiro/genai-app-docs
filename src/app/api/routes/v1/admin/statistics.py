"""システム統計APIエンドポイント。

システム統計・ダッシュボード用APIを提供します。

主な機能:
    - 統計概要取得（GET /api/v1/admin/statistics/overview）
    - ユーザー統計取得（GET /api/v1/admin/statistics/users）

セキュリティ:
    - システム管理者権限必須
"""

from datetime import date

from fastapi import APIRouter, Query

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    RequireSystemAdminDep,
    StatisticsServiceDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.statistics import (
    StatisticsOverviewResponse,
    UserStatisticsDetailResponse,
)

logger = get_logger(__name__)

statistics_router = APIRouter(prefix="/statistics", tags=["Statistics"])


@statistics_router.get(
    "/overview",
    response_model=StatisticsOverviewResponse,
    summary="統計概要取得",
    description="""
    システム統計概要を取得します。

    **権限**: システム管理者

    クエリパラメータ:
        - period: 期間（day/week/month/year）
        - start_date: 開始日
        - end_date: 終了日
    """,
)
@handle_service_errors
async def get_statistics_overview(
    _: RequireSystemAdminDep,
    service: StatisticsServiceDep,
    current_user: CurrentUserAccountDep,
    period: str = Query("month", description="期間"),
    start_date: date | None = Query(None, description="開始日"),
    end_date: date | None = Query(None, description="終了日"),
) -> StatisticsOverviewResponse:
    """システム統計概要を取得します。"""
    logger.info(
        "統計概要取得",
        user_id=str(current_user.id),
        period=period,
        action="get_statistics_overview",
    )

    result = await service.get_overview(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    return result


@statistics_router.get(
    "/users",
    response_model=UserStatisticsDetailResponse,
    summary="ユーザー統計取得",
    description="""
    ユーザー統計（アクティブユーザー推移）を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_user_statistics(
    _: RequireSystemAdminDep,
    service: StatisticsServiceDep,
    current_user: CurrentUserAccountDep,
    days: int = Query(30, ge=1, le=365, description="取得日数"),
) -> UserStatisticsDetailResponse:
    """ユーザー統計を取得します。"""
    logger.info(
        "ユーザー統計取得",
        user_id=str(current_user.id),
        days=days,
        action="get_user_statistics",
    )

    result = await service.get_user_statistics(days=days)

    return result
