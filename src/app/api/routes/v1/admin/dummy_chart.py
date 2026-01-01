"""ダミーチャートマスタ管理APIエンドポイント。"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core import AdminDummyChartServiceDep, CurrentUserAccountDep
from app.api.decorators import handle_service_errors
from app.core.exceptions import AuthorizationError
from app.core.logging import get_logger
from app.schemas.admin.dummy_chart import AnalysisDummyChartListResponse
from app.schemas.analysis.analysis_template import (
    AnalysisDummyChartCreate,
    AnalysisDummyChartResponse,
    AnalysisDummyChartUpdate,
)

logger = get_logger(__name__)

admin_dummy_chart_router = APIRouter()


def _check_admin_role(current_user: CurrentUserAccountDep) -> None:
    """管理者権限チェック。"""
    if "system_admin" not in current_user.roles:
        logger.warning(
            "管理者権限がないユーザーが管理機能にアクセス",
            user_id=str(current_user.id),
            roles=current_user.roles,
        )
        raise AuthorizationError(
            "管理者権限が必要です",
            details={"required_role": "system_admin", "user_roles": current_user.roles},
        )


@admin_dummy_chart_router.get(
    "/admin/dummy-chart",
    response_model=AnalysisDummyChartListResponse,
    summary="ダミーチャートマスタ一覧取得",
    description="ダミーチャートマスタ一覧を取得します（管理者専用）。",
)
@handle_service_errors
async def list_dummy_charts(
    dummy_chart_service: AdminDummyChartServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    issue_id: uuid.UUID | None = Query(None, description="課題マスタIDでフィルタ"),
) -> AnalysisDummyChartListResponse:
    """ダミーチャートマスタ一覧を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミーチャートマスタ一覧取得",
        admin_user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        issue_id=str(issue_id) if issue_id else None,
    )

    return await dummy_chart_service.list_charts(skip=skip, limit=limit, issue_id=issue_id)


@admin_dummy_chart_router.get(
    "/admin/dummy-chart/{chart_id}",
    response_model=AnalysisDummyChartResponse,
    summary="ダミーチャートマスタ詳細取得",
    description="ダミーチャートマスタ詳細を取得します（管理者専用）。",
)
@handle_service_errors
async def get_dummy_chart(
    chart_id: uuid.UUID,
    dummy_chart_service: AdminDummyChartServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisDummyChartResponse:
    """ダミーチャートマスタ詳細を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミーチャートマスタ詳細取得",
        admin_user_id=str(current_user.id),
        chart_id=str(chart_id),
    )

    return await dummy_chart_service.get_chart(chart_id)


@admin_dummy_chart_router.post(
    "/admin/dummy-chart",
    response_model=AnalysisDummyChartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ダミーチャートマスタ作成",
    description="ダミーチャートマスタを作成します（管理者専用）。",
)
@handle_service_errors
async def create_dummy_chart(
    chart_create: AnalysisDummyChartCreate,
    dummy_chart_service: AdminDummyChartServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisDummyChartResponse:
    """ダミーチャートマスタを作成します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミーチャートマスタ作成",
        admin_user_id=str(current_user.id),
        chart_data=chart_create.model_dump(),
    )

    return await dummy_chart_service.create_chart(chart_create)


@admin_dummy_chart_router.patch(
    "/admin/dummy-chart/{chart_id}",
    response_model=AnalysisDummyChartResponse,
    summary="ダミーチャートマスタ更新",
    description="ダミーチャートマスタを更新します（管理者専用）。",
)
@handle_service_errors
async def update_dummy_chart(
    chart_id: uuid.UUID,
    chart_update: AnalysisDummyChartUpdate,
    dummy_chart_service: AdminDummyChartServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisDummyChartResponse:
    """ダミーチャートマスタを更新します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミーチャートマスタ更新",
        admin_user_id=str(current_user.id),
        chart_id=str(chart_id),
        update_data=chart_update.model_dump(exclude_unset=True),
    )

    return await dummy_chart_service.update_chart(chart_id, chart_update)


@admin_dummy_chart_router.delete(
    "/admin/dummy-chart/{chart_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ダミーチャートマスタ削除",
    description="ダミーチャートマスタを削除します（管理者専用）。",
)
@handle_service_errors
async def delete_dummy_chart(
    chart_id: uuid.UUID,
    dummy_chart_service: AdminDummyChartServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """ダミーチャートマスタを削除します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミーチャートマスタ削除",
        admin_user_id=str(current_user.id),
        chart_id=str(chart_id),
    )

    await dummy_chart_service.delete_chart(chart_id)
