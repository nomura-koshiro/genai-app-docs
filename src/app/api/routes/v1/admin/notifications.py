"""通知管理APIエンドポイント。

アラート・お知らせ・通知テンプレート管理APIを提供します。

主な機能:
    - アラート管理（CRUD）
    - 通知テンプレート管理（CRUD）
    - お知らせ管理（CRUD）

セキュリティ:
    - システム管理者権限必須
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    NotificationServiceDep,
    RequireSystemAdminDep,
)
from app.core.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.announcement import (
    AnnouncementCreate,
    AnnouncementListResponse,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from app.schemas.admin.notification_template import (
    NotificationTemplateListResponse,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
)
from app.schemas.admin.system_alert import (
    SystemAlertCreate,
    SystemAlertListResponse,
    SystemAlertResponse,
    SystemAlertUpdate,
)

logger = get_logger(__name__)

notifications_router = APIRouter(tags=["Notifications"])


# ================================================================================
# System Alerts
# ================================================================================

alerts_router = APIRouter(prefix="/alerts")


@alerts_router.get(
    "",
    response_model=SystemAlertListResponse,
    summary="システムアラート一覧取得",
)
@handle_service_errors
async def list_alerts(
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> SystemAlertListResponse:
    """システムアラート一覧を取得します。"""
    logger.info(
        "システムアラート一覧取得",
        user_id=str(current_user.id),
        action="list_alerts",
    )

    result = await service.list_alerts(skip=skip, limit=limit)

    return result


@alerts_router.post(
    "",
    response_model=SystemAlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="システムアラート作成",
)
@handle_service_errors
async def create_alert(
    request: SystemAlertCreate,
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
) -> SystemAlertResponse:
    """システムアラートを作成します。"""
    logger.info(
        "システムアラート作成",
        user_id=str(current_user.id),
        name=request.name,
        action="create_alert",
    )

    result = await service.create_alert(
        data=request,
        created_by=current_user.id,
    )

    return result


@alerts_router.patch(
    "/{alert_id}",
    response_model=SystemAlertResponse,
    summary="システムアラート更新",
)
@handle_service_errors
async def update_alert(
    alert_id: uuid.UUID,
    request: SystemAlertUpdate,
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
) -> SystemAlertResponse:
    """システムアラートを更新します。"""
    logger.info(
        "システムアラート更新",
        user_id=str(current_user.id),
        alert_id=str(alert_id),
        action="update_alert",
    )

    result = await service.update_alert(
        alert_id=alert_id,
        data=request,
    )

    return result


@alerts_router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="システムアラート削除",
)
@handle_service_errors
async def delete_alert(
    alert_id: uuid.UUID,
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """システムアラートを削除します。"""
    logger.info(
        "システムアラート削除",
        user_id=str(current_user.id),
        alert_id=str(alert_id),
        action="delete_alert",
    )

    await service.delete_alert(alert_id=alert_id)


# ================================================================================
# Notification Templates
# ================================================================================

templates_router = APIRouter(prefix="/notification-templates")


@templates_router.get(
    "",
    response_model=NotificationTemplateListResponse,
    summary="通知テンプレート一覧取得",
)
@handle_service_errors
async def list_templates(
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> NotificationTemplateListResponse:
    """通知テンプレート一覧を取得します。"""
    logger.info(
        "通知テンプレート一覧取得",
        user_id=str(current_user.id),
        action="list_templates",
    )

    result = await service.list_templates(skip=skip, limit=limit)

    return result


@templates_router.patch(
    "/{template_id}",
    response_model=NotificationTemplateResponse,
    summary="通知テンプレート更新",
)
@handle_service_errors
async def update_template(
    template_id: uuid.UUID,
    request: NotificationTemplateUpdate,
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
) -> NotificationTemplateResponse:
    """通知テンプレートを更新します。"""
    logger.info(
        "通知テンプレート更新",
        user_id=str(current_user.id),
        template_id=str(template_id),
        action="update_template",
    )

    result = await service.update_template(
        template_id=template_id,
        data=request,
    )

    return result


# ================================================================================
# Announcements
# ================================================================================

announcements_router = APIRouter(prefix="/announcements")


@announcements_router.get(
    "",
    response_model=AnnouncementListResponse,
    summary="システムお知らせ一覧取得",
)
@handle_service_errors
async def list_announcements(
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
    is_active: bool | None = Query(None, description="有効フラグ"),
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> AnnouncementListResponse:
    """システムお知らせ一覧を取得します。"""
    logger.info(
        "システムお知らせ一覧取得",
        user_id=str(current_user.id),
        action="list_announcements",
    )

    result = await service.list_announcements(
        is_active=is_active,
        skip=skip,
        limit=limit,
    )

    return result


@announcements_router.post(
    "",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="システムお知らせ作成",
)
@handle_service_errors
async def create_announcement(
    request: AnnouncementCreate,
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnnouncementResponse:
    """システムお知らせを作成します。"""
    logger.info(
        "システムお知らせ作成",
        user_id=str(current_user.id),
        title=request.title,
        action="create_announcement",
    )

    result = await service.create_announcement(
        data=request,
        created_by=current_user.id,
    )

    return result


@announcements_router.patch(
    "/{announcement_id}",
    response_model=AnnouncementResponse,
    summary="システムお知らせ更新",
)
@handle_service_errors
async def update_announcement(
    announcement_id: uuid.UUID,
    request: AnnouncementUpdate,
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnnouncementResponse:
    """システムお知らせを更新します。"""
    logger.info(
        "システムお知らせ更新",
        user_id=str(current_user.id),
        announcement_id=str(announcement_id),
        action="update_announcement",
    )

    result = await service.update_announcement(
        announcement_id=announcement_id,
        data=request,
    )

    return result


@announcements_router.delete(
    "/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="システムお知らせ削除",
)
@handle_service_errors
async def delete_announcement(
    announcement_id: uuid.UUID,
    _: RequireSystemAdminDep,
    service: NotificationServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """システムお知らせを削除します。"""
    logger.info(
        "システムお知らせ削除",
        user_id=str(current_user.id),
        announcement_id=str(announcement_id),
        action="delete_announcement",
    )

    await service.delete_announcement(announcement_id=announcement_id)


# メインルーターに各サブルーターを登録
notifications_router.include_router(alerts_router)
notifications_router.include_router(templates_router)
notifications_router.include_router(announcements_router)
