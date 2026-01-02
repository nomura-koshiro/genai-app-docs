"""サポートツールAPIエンドポイント。

代行操作・デバッグ・ヘルスチェックAPIを提供します。

主な機能:
    - ユーザー代行操作開始（POST /api/v1/admin/impersonate/{user_id}）
    - ユーザー代行操作終了（POST /api/v1/admin/impersonate/end）
    - デバッグモード有効化（POST /api/v1/admin/debug/enable）
    - デバッグモード無効化（POST /api/v1/admin/debug/disable）
    - 簡易ヘルスチェック（GET /api/v1/admin/health-check）
    - 詳細ヘルスチェック（GET /api/v1/admin/health-check/detailed）

セキュリティ:
    - システム管理者権限必須
"""

import uuid

from fastapi import APIRouter, status

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    RequireSystemAdminDep,
    SupportToolsServiceDep,
)
from app.core.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.health_check import (
    HealthCheckDetailResponse,
    HealthCheckResponse,
)
from app.schemas.admin.support_tools import (
    DebugModeResponse,
    ImpersonateEndRequest,
    ImpersonateEndResponse,
    ImpersonateRequest,
    ImpersonateResponse,
)

logger = get_logger(__name__)

support_tools_router = APIRouter(tags=["Support Tools"])


# ================================================================================
# Impersonation
# ================================================================================


@support_tools_router.post(
    "/impersonate/{user_id}",
    response_model=ImpersonateResponse,
    status_code=status.HTTP_200_OK,
    summary="ユーザー代行操作開始",
    description="""
    ユーザー代行操作を開始します。

    **権限**: システム管理者

    注意: 代行操作中の全アクションは監査ログに記録されます。
    """,
)
@handle_service_errors
async def start_impersonation(
    user_id: uuid.UUID,
    request: ImpersonateRequest,
    _: RequireSystemAdminDep,
    service: SupportToolsServiceDep,
    current_user: CurrentUserAccountDep,
) -> ImpersonateResponse:
    """ユーザー代行操作を開始します。"""
    logger.info(
        "ユーザー代行操作開始",
        admin_id=str(current_user.id),
        target_user_id=str(user_id),
        reason=request.reason,
        action="start_impersonation",
    )

    result = await service.start_impersonation(
        admin_user_id=current_user.id,
        target_user_id=user_id,
        reason=request.reason,
    )

    return result


@support_tools_router.post(
    "/impersonate/end",
    response_model=ImpersonateEndResponse,
    status_code=status.HTTP_200_OK,
    summary="ユーザー代行操作終了",
    description="""
    ユーザー代行操作を終了します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def end_impersonation(
    request: ImpersonateEndRequest,
    _: RequireSystemAdminDep,
    service: SupportToolsServiceDep,
    current_user: CurrentUserAccountDep,
) -> ImpersonateEndResponse:
    """ユーザー代行操作を終了します。"""
    logger.info(
        "ユーザー代行操作終了",
        admin_id=str(current_user.id),
        action="end_impersonation",
    )

    result = await service.end_impersonation(
        token=request.token,
        admin_user_id=current_user.id,
    )

    return result


# ================================================================================
# Debug Mode
# ================================================================================


@support_tools_router.post(
    "/debug/enable",
    response_model=DebugModeResponse,
    status_code=status.HTTP_200_OK,
    summary="デバッグモード有効化",
    description="""
    デバッグモードを有効化します。

    **権限**: システム管理者

    注意: デバッグモードは詳細なログ出力を有効にします。
    """,
)
@handle_service_errors
async def enable_debug_mode(
    _: RequireSystemAdminDep,
    service: SupportToolsServiceDep,
    current_user: CurrentUserAccountDep,
) -> DebugModeResponse:
    """デバッグモードを有効化します。"""
    logger.info(
        "デバッグモード有効化",
        user_id=str(current_user.id),
        action="enable_debug_mode",
    )

    result = await service.enable_debug_mode(admin_user_id=current_user.id)

    return result


@support_tools_router.post(
    "/debug/disable",
    response_model=DebugModeResponse,
    status_code=status.HTTP_200_OK,
    summary="デバッグモード無効化",
    description="""
    デバッグモードを無効化します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def disable_debug_mode(
    _: RequireSystemAdminDep,
    service: SupportToolsServiceDep,
    current_user: CurrentUserAccountDep,
) -> DebugModeResponse:
    """デバッグモードを無効化します。"""
    logger.info(
        "デバッグモード無効化",
        user_id=str(current_user.id),
        action="disable_debug_mode",
    )

    result = await service.disable_debug_mode(admin_user_id=current_user.id)

    return result


# ================================================================================
# Health Check
# ================================================================================


@support_tools_router.get(
    "/health-check",
    response_model=HealthCheckResponse,
    summary="簡易ヘルスチェック",
    description="""
    簡易ヘルスチェックを実行します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def health_check(
    _: RequireSystemAdminDep,
    service: SupportToolsServiceDep,
    current_user: CurrentUserAccountDep,
) -> HealthCheckResponse:
    """簡易ヘルスチェックを実行します。"""
    logger.info(
        "簡易ヘルスチェック",
        user_id=str(current_user.id),
        action="health_check",
    )

    result = await service.simple_health_check()

    return result


@support_tools_router.get(
    "/health-check/detailed",
    response_model=HealthCheckDetailResponse,
    summary="詳細ヘルスチェック",
    description="""
    詳細ヘルスチェックを実行します。

    **権限**: システム管理者

    チェック項目:
        - データベース接続
        - キャッシュ接続
        - ストレージ接続
        - 外部API（Azure AD等）
    """,
)
@handle_service_errors
async def detailed_health_check(
    _: RequireSystemAdminDep,
    service: SupportToolsServiceDep,
    current_user: CurrentUserAccountDep,
) -> HealthCheckDetailResponse:
    """詳細ヘルスチェックを実行します。"""
    logger.info(
        "詳細ヘルスチェック",
        user_id=str(current_user.id),
        action="detailed_health_check",
    )

    result = await service.detailed_health_check()

    return result
