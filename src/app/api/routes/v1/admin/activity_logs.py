"""操作履歴管理APIエンドポイント。

このモジュールは、システム管理者向けのユーザー操作履歴管理APIを提供します。

主な機能:
    - 操作履歴一覧取得（GET /api/v1/admin/activity-logs）
    - 操作履歴詳細取得（GET /api/v1/admin/activity-logs/{id}）
    - エラー履歴取得（GET /api/v1/admin/activity-logs/errors）
    - 操作履歴エクスポート（GET /api/v1/admin/activity-logs/export）

セキュリティ:
    - システム管理者権限必須
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    ActivityTrackingServiceDep,
    RequireSystemAdminDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.activity_log import (
    ActivityLogDetailResponse,
    ActivityLogFilter,
    ActivityLogListResponse,
)

logger = get_logger(__name__)

activity_logs_router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@activity_logs_router.get(
    "",
    response_model=ActivityLogListResponse,
    summary="操作履歴一覧取得",
    description="""
    操作履歴一覧を取得します。

    **権限**: システム管理者

    クエリパラメータ:
        - user_id: ユーザーIDで絞り込み
        - action_type: 操作種別で絞り込み（CREATE/READ/UPDATE/DELETE/ERROR）
        - resource_type: リソース種別で絞り込み（PROJECT/SESSION/TREE等）
        - start_date: 開始日時
        - end_date: 終了日時
        - has_error: エラーのみ取得
        - page: ページ番号（デフォルト: 1）
        - limit: 取得件数（デフォルト: 50、最大: 100）

    レスポンス:
        - items: 操作履歴リスト
        - total: 総件数
        - page: 現在のページ
        - limit: 取得件数
        - total_pages: 総ページ数
    """,
)
@handle_service_errors
async def list_activity_logs(
    _: RequireSystemAdminDep,
    service: ActivityTrackingServiceDep,
    current_user: CurrentUserAccountDep,
    user_id: uuid.UUID | None = Query(None, description="ユーザーIDで絞り込み"),
    action_type: str | None = Query(None, description="操作種別で絞り込み"),
    resource_type: str | None = Query(None, description="リソース種別で絞り込み"),
    start_date: datetime | None = Query(None, description="開始日時"),
    end_date: datetime | None = Query(None, description="終了日時"),
    has_error: bool | None = Query(None, description="エラーのみ取得"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> ActivityLogListResponse:
    """操作履歴一覧を取得します。"""
    logger.info(
        "操作履歴一覧取得",
        user_id=str(current_user.id),
        action="list_activity_logs",
    )

    filter_params = ActivityLogFilter(
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        has_error=has_error,
    )

    result = await service.get_activity_logs(
        filter_params=filter_params,
        page=page,
        limit=limit,
    )

    return result


@activity_logs_router.get(
    "/errors",
    response_model=ActivityLogListResponse,
    summary="エラー履歴取得",
    description="""
    エラー履歴のみを取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def list_error_logs(
    _: RequireSystemAdminDep,
    service: ActivityTrackingServiceDep,
    current_user: CurrentUserAccountDep,
    user_id: uuid.UUID | None = Query(None, description="ユーザーIDで絞り込み"),
    start_date: datetime | None = Query(None, description="開始日時"),
    end_date: datetime | None = Query(None, description="終了日時"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> ActivityLogListResponse:
    """エラー履歴のみを取得します。"""
    logger.info(
        "エラー履歴取得",
        user_id=str(current_user.id),
        action="list_error_logs",
    )

    filter_params = ActivityLogFilter(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        has_error=True,
    )

    result = await service.get_activity_logs(
        filter_params=filter_params,
        page=page,
        limit=limit,
    )

    return result


@activity_logs_router.get(
    "/export",
    summary="操作履歴エクスポート",
    description="""
    操作履歴をCSV形式でエクスポートします。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def export_activity_logs(
    _: RequireSystemAdminDep,
    service: ActivityTrackingServiceDep,
    current_user: CurrentUserAccountDep,
    user_id: uuid.UUID | None = Query(None, description="ユーザーIDで絞り込み"),
    action_type: str | None = Query(None, description="操作種別で絞り込み"),
    start_date: datetime | None = Query(None, description="開始日時"),
    end_date: datetime | None = Query(None, description="終了日時"),
    has_error: bool | None = Query(None, description="エラーのみ取得"),
) -> StreamingResponse:
    """操作履歴をCSVエクスポートします。"""
    logger.info(
        "操作履歴エクスポート",
        user_id=str(current_user.id),
        action="export_activity_logs",
    )

    filter_params = ActivityLogFilter(
        user_id=user_id,
        action_type=action_type,
        start_date=start_date,
        end_date=end_date,
        has_error=has_error,
    )

    csv_content = await service.export_to_csv(filter_params=filter_params)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=activity_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )


@activity_logs_router.get(
    "/{activity_id}",
    response_model=ActivityLogDetailResponse,
    summary="操作履歴詳細取得",
    description="""
    操作履歴の詳細を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_activity_log(
    activity_id: uuid.UUID,
    _: RequireSystemAdminDep,
    service: ActivityTrackingServiceDep,
    current_user: CurrentUserAccountDep,
) -> ActivityLogDetailResponse:
    """操作履歴の詳細を取得します。"""
    logger.info(
        "操作履歴詳細取得",
        user_id=str(current_user.id),
        activity_id=str(activity_id),
        action="get_activity_log",
    )

    result = await service.get_activity_log_detail(activity_id=activity_id)

    return result
