"""セキュリティ管理APIエンドポイント。

セッション管理・強制ログアウトAPIを提供します。

主な機能:
    - アクティブセッション一覧取得（GET /api/v1/admin/sessions）
    - ユーザー別セッション取得（GET /api/v1/admin/sessions/user/{user_id}）
    - セッション終了（POST /api/v1/admin/sessions/{id}/terminate）
    - ユーザー全セッション終了（POST /api/v1/admin/sessions/user/{user_id}/terminate-all）

セキュリティ:
    - システム管理者権限必須
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    RequireSystemAdminDep,
    SessionManagementServiceDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.session_management import (
    SessionFilter,
    SessionListResponse,
    SessionTerminateRequest,
    SessionTerminateResponse,
)

logger = get_logger(__name__)

security_router = APIRouter(prefix="/sessions", tags=["Security"])


@security_router.get(
    "",
    response_model=SessionListResponse,
    summary="アクティブセッション一覧取得",
    description="""
    アクティブセッション一覧を取得します。

    **権限**: システム管理者

    クエリパラメータ:
        - user_id: ユーザーID
        - ip_address: IPアドレス
        - skip: スキップ数
        - limit: 取得件数
    """,
)
@handle_service_errors
async def list_sessions(
    _: RequireSystemAdminDep,
    service: SessionManagementServiceDep,
    current_user: CurrentUserAccountDep,
    user_id: uuid.UUID | None = Query(None, description="ユーザーID"),
    ip_address: str | None = Query(None, description="IPアドレス"),
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> SessionListResponse:
    """アクティブセッション一覧を取得します。"""
    logger.info(
        "アクティブセッション一覧取得",
        user_id=str(current_user.id),
        action="list_sessions",
    )

    filter_params = SessionFilter(
        user_id=user_id,
        ip_address=ip_address,
        page=(skip // limit) + 1 if limit > 0 else 1,
        limit=limit,
    )
    result = await service.list_sessions(filter_params)

    return result


@security_router.get(
    "/user/{user_id}",
    response_model=SessionListResponse,
    summary="ユーザー別セッション取得",
    description="""
    特定ユーザーのセッション一覧を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_user_sessions(
    user_id: uuid.UUID,
    _: RequireSystemAdminDep,
    service: SessionManagementServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> SessionListResponse:
    """ユーザーのセッション一覧を取得します。"""
    logger.info(
        "ユーザー別セッション取得",
        user_id=str(current_user.id),
        target_user_id=str(user_id),
        action="get_user_sessions",
    )

    filter_params = SessionFilter(
        user_id=user_id,
        page=(skip // limit) + 1 if limit > 0 else 1,
        limit=limit,
    )
    result = await service.list_sessions(filter_params)

    return result


@security_router.post(
    "/{session_id}/terminate",
    response_model=SessionTerminateResponse,
    status_code=status.HTTP_200_OK,
    summary="セッション終了",
    description="""
    特定セッションを終了（強制ログアウト）します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def terminate_session(
    session_id: uuid.UUID,
    request: SessionTerminateRequest,
    _: RequireSystemAdminDep,
    service: SessionManagementServiceDep,
    current_user: CurrentUserAccountDep,
) -> SessionTerminateResponse:
    """セッションを終了します。"""
    logger.info(
        "セッション終了",
        user_id=str(current_user.id),
        session_id=str(session_id),
        reason=request.reason,
        action="terminate_session",
    )

    await service.terminate_session(
        session_id=session_id,
        reason=request.reason,
        terminated_by=current_user.id,
    )

    return SessionTerminateResponse(
        terminated_count=1,
        message="セッションを終了しました",
    )


@security_router.post(
    "/user/{user_id}/terminate-all",
    response_model=SessionTerminateResponse,
    status_code=status.HTTP_200_OK,
    summary="ユーザー全セッション終了",
    description="""
    特定ユーザーの全セッションを終了します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def terminate_all_user_sessions(
    user_id: uuid.UUID,
    request: SessionTerminateRequest,
    _: RequireSystemAdminDep,
    service: SessionManagementServiceDep,
    current_user: CurrentUserAccountDep,
) -> SessionTerminateResponse:
    """ユーザーの全セッションを終了します。"""
    logger.info(
        "ユーザー全セッション終了",
        user_id=str(current_user.id),
        target_user_id=str(user_id),
        reason=request.reason,
        action="terminate_all_user_sessions",
    )

    terminated_count = await service.terminate_all_user_sessions(
        user_id=user_id,
        reason=request.reason,
        terminated_by=current_user.id,
    )

    return SessionTerminateResponse(
        terminated_count=terminated_count,
        message=f"{terminated_count}件のセッションを終了しました",
    )
