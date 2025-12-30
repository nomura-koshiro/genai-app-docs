"""システム設定管理APIエンドポイント。

システム設定の管理APIを提供します。

主な機能:
    - 全設定取得（GET /api/v1/admin/settings）
    - カテゴリ別設定取得（GET /api/v1/admin/settings/{category}）
    - 設定更新（PATCH /api/v1/admin/settings/{category}/{key}）
    - メンテナンスモード有効化（POST /api/v1/admin/settings/maintenance/enable）
    - メンテナンスモード無効化（POST /api/v1/admin/settings/maintenance/disable）

セキュリティ:
    - システム管理者権限必須
"""

from fastapi import APIRouter, status

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    RequireSystemAdminDep,
    SystemSettingServiceDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.system_setting import (
    MaintenanceModeRequest,
    MaintenanceModeResponse,
    SettingCategoryResponse,
    SettingUpdateRequest,
    SettingUpdateResponse,
    SystemSettingsResponse,
)

logger = get_logger(__name__)

settings_router = APIRouter(prefix="/settings", tags=["System Settings"])


@settings_router.get(
    "",
    response_model=SystemSettingsResponse,
    summary="全設定取得",
    description="""
    全システム設定を取得します。

    **権限**: システム管理者

    レスポンス:
        - categories: カテゴリ別設定マップ
            - GENERAL: 一般設定
            - SECURITY: セキュリティ設定
            - MAINTENANCE: メンテナンス設定
    """,
)
@handle_service_errors
async def get_all_settings(
    _: RequireSystemAdminDep,
    service: SystemSettingServiceDep,
    current_user: CurrentUserAccountDep,
) -> SystemSettingsResponse:
    """全システム設定を取得します。"""
    logger.info(
        "全設定取得",
        user_id=str(current_user.id),
        action="get_all_settings",
    )

    result = await service.get_all_settings()

    return result


@settings_router.get(
    "/{category}",
    response_model=SettingCategoryResponse,
    summary="カテゴリ別設定取得",
    description="""
    カテゴリ別の設定を取得します。

    **権限**: システム管理者

    パスパラメータ:
        - category: カテゴリ名（GENERAL/SECURITY/MAINTENANCE）
    """,
)
@handle_service_errors
async def get_settings_by_category(
    category: str,
    _: RequireSystemAdminDep,
    service: SystemSettingServiceDep,
    current_user: CurrentUserAccountDep,
) -> SettingCategoryResponse:
    """カテゴリ別設定を取得します。"""
    logger.info(
        "カテゴリ別設定取得",
        user_id=str(current_user.id),
        category=category,
        action="get_settings_by_category",
    )

    result = await service.get_settings_by_category(category=category.upper())

    return result


@settings_router.patch(
    "/{category}/{key}",
    response_model=SettingUpdateResponse,
    summary="設定更新",
    description="""
    設定を更新します。

    **権限**: システム管理者

    パスパラメータ:
        - category: カテゴリ名
        - key: 設定キー
    """,
)
@handle_service_errors
async def update_setting(
    category: str,
    key: str,
    request: SettingUpdateRequest,
    _: RequireSystemAdminDep,
    service: SystemSettingServiceDep,
    current_user: CurrentUserAccountDep,
) -> SettingUpdateResponse:
    """設定を更新します。"""
    logger.info(
        "設定更新",
        user_id=str(current_user.id),
        category=category,
        key=key,
        action="update_setting",
    )

    result = await service.update_setting(
        category=category.upper(),
        key=key,
        value=request.value,
        updated_by=current_user.id,
    )

    return result


@settings_router.post(
    "/maintenance/enable",
    response_model=MaintenanceModeResponse,
    status_code=status.HTTP_200_OK,
    summary="メンテナンスモード有効化",
    description="""
    メンテナンスモードを有効化します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def enable_maintenance_mode(
    request: MaintenanceModeRequest,
    _: RequireSystemAdminDep,
    service: SystemSettingServiceDep,
    current_user: CurrentUserAccountDep,
) -> MaintenanceModeResponse:
    """メンテナンスモードを有効化します。"""
    logger.info(
        "メンテナンスモード有効化",
        user_id=str(current_user.id),
        message=request.message,
        action="enable_maintenance_mode",
    )

    result = await service.enable_maintenance_mode(
        message=request.message,
        allow_admin_access=request.allow_admin_access,
        updated_by=current_user.id,
    )

    return result


@settings_router.post(
    "/maintenance/disable",
    response_model=MaintenanceModeResponse,
    status_code=status.HTTP_200_OK,
    summary="メンテナンスモード無効化",
    description="""
    メンテナンスモードを無効化します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def disable_maintenance_mode(
    _: RequireSystemAdminDep,
    service: SystemSettingServiceDep,
    current_user: CurrentUserAccountDep,
) -> MaintenanceModeResponse:
    """メンテナンスモードを無効化します。"""
    logger.info(
        "メンテナンスモード無効化",
        user_id=str(current_user.id),
        action="disable_maintenance_mode",
    )

    result = await service.disable_maintenance_mode(updated_by=current_user.id)

    return result
