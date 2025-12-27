"""ダッシュボードAPIエンドポイント。

このモジュールは、ダッシュボード機能のRESTful APIエンドポイントを定義します。
統計情報、アクティビティログ、チャートデータの取得を提供します。

主な機能:
    - 統計情報取得（GET /api/v1/dashboard/stats - 認証必須）
    - アクティビティログ取得（GET /api/v1/dashboard/activities - 認証必須）
    - チャートデータ取得（GET /api/v1/dashboard/charts - 認証必須）

セキュリティ:
    - Azure AD Bearer認証（本番環境）
    - モック認証（開発環境）
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.core import CurrentUserAccountDep, DatabaseDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.dashboard.dashboard import (
    DashboardActivitiesResponse,
    DashboardChartsResponse,
    DashboardStatsResponse,
)
from app.services.dashboard.dashboard import DashboardService

logger = get_logger(__name__)

router = APIRouter()


# ================================================================================
# 依存性注入
# ================================================================================


async def get_dashboard_service(db: DatabaseDep) -> DashboardService:
    """ダッシュボードサービスを取得。

    Args:
        db: データベースセッション

    Returns:
        DashboardService: ダッシュボードサービスインスタンス
    """
    return DashboardService(db)


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


# ================================================================================
# GET Endpoints
# ================================================================================


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="統計情報取得",
    description="""
    ダッシュボードの統計情報を取得します。

    **認証が必要です。**

    レスポンス:
        - projects: プロジェクト統計（総数、アクティブ数、アーカイブ数）
        - sessions: セッション統計（総数、状態別数）
        - trees: ツリー統計（総数、状態別数）
        - users: ユーザー統計（総数、アクティブ数）
        - generated_at: 統計生成日時
    """,
)
@handle_service_errors
async def get_stats(
    current_user: CurrentUserAccountDep,
    dashboard_service: DashboardServiceDep,
) -> DashboardStatsResponse:
    """統計情報を取得。

    Args:
        current_user: 現在のユーザー
        dashboard_service: ダッシュボードサービス

    Returns:
        DashboardStatsResponse: 統計情報
    """
    logger.info(f"ダッシュボード統計取得: user_id={current_user.id}")
    return await dashboard_service.get_stats()


@router.get(
    "/activities",
    response_model=DashboardActivitiesResponse,
    summary="アクティビティログ取得",
    description="""
    最近のアクティビティログを取得します。

    **認証が必要です。**

    クエリパラメータ:
        - skip: スキップ数（デフォルト: 0）
        - limit: 取得件数（デフォルト: 20、最大: 100）

    レスポンス:
        - activities: アクティビティリスト
        - total: 総件数
        - skip: スキップ数
        - limit: 取得件数

    **注意**: アクティビティログ機能は準備中です。現在は空のレスポンスを返します。
    """,
)
@handle_service_errors
async def get_activities(
    current_user: CurrentUserAccountDep,
    skip: int = Query(default=0, ge=0, description="スキップ数"),
    limit: int = Query(default=20, ge=1, le=100, description="取得件数"),
) -> DashboardActivitiesResponse:
    """アクティビティログを取得。

    Args:
        current_user: 現在のユーザー
        skip: スキップ数
        limit: 取得件数

    Returns:
        DashboardActivitiesResponse: アクティビティログ

    Note:
        アクティビティログ機能は準備中です。現在は空のレスポンスを返します。
    """
    logger.info(f"アクティビティログ取得: user_id={current_user.id}, skip={skip}, limit={limit}")

    # TODO: アクティビティログモデルとリポジトリを実装後、実際のデータを返す
    return DashboardActivitiesResponse(
        activities=[],
        total=0,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/charts",
    response_model=DashboardChartsResponse,
    summary="チャートデータ取得",
    description="""
    ダッシュボードのチャートデータを取得します。

    **認証が必要です。**

    クエリパラメータ:
        - days: 集計対象日数（デフォルト: 30、最大: 365）

    レスポンス:
        - session_trend: セッション作成トレンド
        - tree_trend: ツリー作成トレンド
        - project_distribution: プロジェクト状態分布
        - user_activity: ユーザーアクティビティ
        - generated_at: 統計生成日時
    """,
)
@handle_service_errors
async def get_charts(
    current_user: CurrentUserAccountDep,
    dashboard_service: DashboardServiceDep,
    days: int = Query(default=30, ge=1, le=365, description="集計対象日数"),
) -> DashboardChartsResponse:
    """チャートデータを取得。

    Args:
        current_user: 現在のユーザー
        dashboard_service: ダッシュボードサービス
        days: 集計対象日数

    Returns:
        DashboardChartsResponse: チャートデータ
    """
    logger.info(f"チャートデータ取得: user_id={current_user.id}, days={days}")
    return await dashboard_service.get_charts(days=days)
