"""ユーザー通知APIエンドポイント。

共通UI設計書（UI-006〜UI-011）に基づくユーザー通知のRESTful APIエンドポイントを定義します。

主な機能:
    - 通知一覧取得（GET /api/v1/notifications）
    - 通知詳細取得（GET /api/v1/notifications/{notification_id}）
    - 通知既読化（PATCH /api/v1/notifications/{notification_id}/read）
    - 全通知既読化（PATCH /api/v1/notifications/read-all）
    - 通知削除（DELETE /api/v1/notifications/{notification_id}）
"""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.core import CurrentUserAccountDep, UserNotificationServiceDep
from app.api.decorators import handle_service_errors
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.schemas.notification import (
    NotificationInfo,
    NotificationListResponse,
    ReadAllResponse,
)

logger = get_logger(__name__)

user_notifications_router = APIRouter()


@user_notifications_router.get(
    "/notifications",
    response_model=NotificationListResponse,
    summary="通知一覧取得",
    description="""
    ユーザーの通知一覧を取得します。

    **認証が必要です。**

    クエリパラメータ:
        - is_read: bool - 既読/未読フィルター
        - skip: int - スキップ数（デフォルト: 0）
        - limit: int - 取得件数（デフォルト: 20、最大: 100）

    レスポンス:
        - NotificationListResponse: 通知一覧
            - notifications: list[NotificationInfo] - 通知リスト
            - total: int - 総件数
            - unread_count: int - 未読件数
            - skip: int - スキップ数
            - limit: int - 取得件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
@handle_service_errors
async def list_notifications(
    current_user: CurrentUserAccountDep,
    notification_service: UserNotificationServiceDep,
    is_read: bool | None = Query(None, description="既読/未読フィルター"),
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(20, ge=1, le=100, description="取得件数"),
) -> NotificationListResponse:
    """通知一覧を取得します。"""
    logger.info(
        "通知一覧取得",
        user_id=str(current_user.id),
        is_read=is_read,
        skip=skip,
        limit=limit,
        action="list_notifications",
    )

    result = await notification_service.list_notifications(
        user_id=current_user.id,
        is_read=is_read,
        skip=skip,
        limit=limit,
    )

    logger.info(
        "通知一覧を取得しました",
        user_id=str(current_user.id),
        count=len(result.notifications),
        total=result.total,
        unread_count=result.unread_count,
    )

    return result


@user_notifications_router.get(
    "/notifications/{notification_id}",
    response_model=NotificationInfo,
    summary="通知詳細取得",
    description="""
    特定の通知の詳細を取得します。

    **認証が必要です。**

    パスパラメータ:
        - notification_id: UUID - 通知ID

    レスポンス:
        - NotificationInfo: 通知情報

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 404: 通知が見つからない
    """,
)
@handle_service_errors
async def get_notification(
    notification_id: UUID,
    current_user: CurrentUserAccountDep,
    notification_service: UserNotificationServiceDep,
) -> NotificationInfo:
    """通知詳細を取得します。"""
    logger.info(
        "通知詳細取得",
        user_id=str(current_user.id),
        notification_id=str(notification_id),
        action="get_notification",
    )

    result = await notification_service.get_notification(
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if result is None:
        raise NotFoundError(
            "通知が見つかりません",
            details={"notification_id": str(notification_id)},
        )

    logger.info(
        "通知詳細を取得しました",
        user_id=str(current_user.id),
        notification_id=str(notification_id),
    )

    return result


@user_notifications_router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationInfo,
    summary="通知既読化",
    description="""
    特定の通知を既読にします。

    **認証が必要です。**

    パスパラメータ:
        - notification_id: UUID - 通知ID

    レスポンス:
        - NotificationInfo: 更新後の通知情報

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 404: 通知が見つからない
    """,
)
@handle_service_errors
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: CurrentUserAccountDep,
    notification_service: UserNotificationServiceDep,
) -> NotificationInfo:
    """通知を既読にします。"""
    logger.info(
        "通知既読化",
        user_id=str(current_user.id),
        notification_id=str(notification_id),
        action="mark_notification_as_read",
    )

    result = await notification_service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if result is None:
        raise NotFoundError(
            "通知が見つかりません",
            details={"notification_id": str(notification_id)},
        )

    logger.info(
        "通知を既読にしました",
        user_id=str(current_user.id),
        notification_id=str(notification_id),
    )

    return result


@user_notifications_router.patch(
    "/notifications/read-all",
    response_model=ReadAllResponse,
    summary="全通知既読化",
    description="""
    すべての未読通知を既読にします。

    **認証が必要です。**

    レスポンス:
        - ReadAllResponse: 更新件数
            - updated_count: int - 更新された通知数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
@handle_service_errors
async def mark_all_notifications_as_read(
    current_user: CurrentUserAccountDep,
    notification_service: UserNotificationServiceDep,
) -> ReadAllResponse:
    """すべての通知を既読にします。"""
    logger.info(
        "全通知既読化",
        user_id=str(current_user.id),
        action="mark_all_notifications_as_read",
    )

    result = await notification_service.mark_all_as_read(user_id=current_user.id)

    logger.info(
        "すべての通知を既読にしました",
        user_id=str(current_user.id),
        updated_count=result.updated_count,
    )

    return result


@user_notifications_router.delete(
    "/notifications/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="通知削除",
    description="""
    特定の通知を削除します。

    **認証が必要です。**

    パスパラメータ:
        - notification_id: UUID - 通知ID

    ステータスコード:
        - 204: 削除成功
        - 401: 認証されていない
        - 404: 通知が見つからない
    """,
)
@handle_service_errors
async def delete_notification(
    notification_id: UUID,
    current_user: CurrentUserAccountDep,
    notification_service: UserNotificationServiceDep,
) -> None:
    """通知を削除します。"""
    logger.info(
        "通知削除",
        user_id=str(current_user.id),
        notification_id=str(notification_id),
        action="delete_notification",
    )

    success = await notification_service.delete_notification(
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if not success:
        raise NotFoundError(
            "通知が見つかりません",
            details={"notification_id": str(notification_id)},
        )

    logger.info(
        "通知を削除しました",
        user_id=str(current_user.id),
        notification_id=str(notification_id),
    )
