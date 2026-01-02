"""グラフ軸マスタ管理APIエンドポイント。"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core import AdminGraphAxisServiceDep, CurrentUserAccountDep
from app.core.decorators import handle_service_errors
from app.core.exceptions import AuthorizationError
from app.core.logging import get_logger
from app.schemas.admin.graph_axis import AnalysisGraphAxisListResponse
from app.schemas.analysis.analysis_template import (
    AnalysisGraphAxisCreate,
    AnalysisGraphAxisResponse,
    AnalysisGraphAxisUpdate,
)

logger = get_logger(__name__)

admin_graph_axis_router = APIRouter()


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


@admin_graph_axis_router.get(
    "/admin/graph-axis",
    response_model=AnalysisGraphAxisListResponse,
    summary="グラフ軸マスタ一覧取得",
    description="グラフ軸マスタ一覧を取得します（管理者専用）。",
)
@handle_service_errors
async def list_graph_axes(
    graph_axis_service: AdminGraphAxisServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    issue_id: uuid.UUID | None = Query(None, description="課題マスタIDでフィルタ"),
) -> AnalysisGraphAxisListResponse:
    """グラフ軸マスタ一覧を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "グラフ軸マスタ一覧取得",
        admin_user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        issue_id=str(issue_id) if issue_id else None,
    )

    return await graph_axis_service.list_axes(skip=skip, limit=limit, issue_id=issue_id)


@admin_graph_axis_router.get(
    "/admin/graph-axis/{axis_id}",
    response_model=AnalysisGraphAxisResponse,
    summary="グラフ軸マスタ詳細取得",
    description="グラフ軸マスタ詳細を取得します（管理者専用）。",
)
@handle_service_errors
async def get_graph_axis(
    axis_id: uuid.UUID,
    graph_axis_service: AdminGraphAxisServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisGraphAxisResponse:
    """グラフ軸マスタ詳細を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "グラフ軸マスタ詳細取得",
        admin_user_id=str(current_user.id),
        axis_id=str(axis_id),
    )

    return await graph_axis_service.get_axis(axis_id)


@admin_graph_axis_router.post(
    "/admin/graph-axis",
    response_model=AnalysisGraphAxisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="グラフ軸マスタ作成",
    description="グラフ軸マスタを作成します（管理者専用）。",
)
@handle_service_errors
async def create_graph_axis(
    axis_create: AnalysisGraphAxisCreate,
    graph_axis_service: AdminGraphAxisServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisGraphAxisResponse:
    """グラフ軸マスタを作成します。"""
    _check_admin_role(current_user)

    logger.info(
        "グラフ軸マスタ作成",
        admin_user_id=str(current_user.id),
        axis_data=axis_create.model_dump(),
    )

    return await graph_axis_service.create_axis(axis_create)


@admin_graph_axis_router.patch(
    "/admin/graph-axis/{axis_id}",
    response_model=AnalysisGraphAxisResponse,
    summary="グラフ軸マスタ更新",
    description="グラフ軸マスタを更新します（管理者専用）。",
)
@handle_service_errors
async def update_graph_axis(
    axis_id: uuid.UUID,
    axis_update: AnalysisGraphAxisUpdate,
    graph_axis_service: AdminGraphAxisServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisGraphAxisResponse:
    """グラフ軸マスタを更新します。"""
    _check_admin_role(current_user)

    logger.info(
        "グラフ軸マスタ更新",
        admin_user_id=str(current_user.id),
        axis_id=str(axis_id),
        update_data=axis_update.model_dump(exclude_unset=True),
    )

    return await graph_axis_service.update_axis(axis_id, axis_update)


@admin_graph_axis_router.delete(
    "/admin/graph-axis/{axis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="グラフ軸マスタ削除",
    description="グラフ軸マスタを削除します（管理者専用）。",
)
@handle_service_errors
async def delete_graph_axis(
    axis_id: uuid.UUID,
    graph_axis_service: AdminGraphAxisServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """グラフ軸マスタを削除します。"""
    _check_admin_role(current_user)

    logger.info(
        "グラフ軸マスタ削除",
        admin_user_id=str(current_user.id),
        axis_id=str(axis_id),
    )

    await graph_axis_service.delete_axis(axis_id)
