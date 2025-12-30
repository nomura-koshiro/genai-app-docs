"""監査ログ管理APIエンドポイント。

詳細な監査ログの管理APIを提供します。

主な機能:
    - 監査ログ一覧取得（GET /api/v1/admin/audit-logs）
    - データ変更履歴取得（GET /api/v1/admin/audit-logs/changes）
    - アクセスログ取得（GET /api/v1/admin/audit-logs/access）
    - セキュリティイベント取得（GET /api/v1/admin/audit-logs/security）
    - リソース変更履歴追跡（GET /api/v1/admin/audit-logs/resource/{type}/{id}）
    - 監査ログエクスポート（GET /api/v1/admin/audit-logs/export）

セキュリティ:
    - システム管理者権限必須
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    AuditLogServiceDep,
    RequireSystemAdminDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.audit_log import (
    AuditLogFilter,
    AuditLogListResponse,
)

logger = get_logger(__name__)

audit_logs_router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@audit_logs_router.get(
    "",
    response_model=AuditLogListResponse,
    summary="監査ログ一覧取得",
    description="""
    監査ログ一覧を取得します。

    **権限**: システム管理者

    クエリパラメータ:
        - event_type: イベント種別（DATA_CHANGE/ACCESS/SECURITY）
        - user_id: ユーザーID
        - resource_type: リソース種別
        - resource_id: リソースID
        - severity: 重要度（INFO/WARNING/CRITICAL）
        - start_date: 開始日時
        - end_date: 終了日時
        - page: ページ番号
        - limit: 取得件数
    """,
)
@handle_service_errors
async def list_audit_logs(
    _: RequireSystemAdminDep,
    service: AuditLogServiceDep,
    current_user: CurrentUserAccountDep,
    event_type: str | None = Query(None, description="イベント種別"),
    user_id: uuid.UUID | None = Query(None, description="ユーザーID"),
    resource_type: str | None = Query(None, description="リソース種別"),
    resource_id: uuid.UUID | None = Query(None, description="リソースID"),
    severity: str | None = Query(None, description="重要度"),
    start_date: datetime | None = Query(None, description="開始日時"),
    end_date: datetime | None = Query(None, description="終了日時"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> AuditLogListResponse:
    """監査ログ一覧を取得します。"""
    logger.info(
        "監査ログ一覧取得",
        user_id=str(current_user.id),
        action="list_audit_logs",
    )

    filter_params = AuditLogFilter(
        event_type=event_type,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
    )

    result = await service.get_audit_logs(
        filter_params=filter_params,
        page=page,
        limit=limit,
    )

    return result


@audit_logs_router.get(
    "/changes",
    response_model=AuditLogListResponse,
    summary="データ変更履歴取得",
    description="""
    データ変更履歴を取得します（event_type=DATA_CHANGE）。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def list_data_changes(
    _: RequireSystemAdminDep,
    service: AuditLogServiceDep,
    current_user: CurrentUserAccountDep,
    user_id: uuid.UUID | None = Query(None, description="ユーザーID"),
    resource_type: str | None = Query(None, description="リソース種別"),
    start_date: datetime | None = Query(None, description="開始日時"),
    end_date: datetime | None = Query(None, description="終了日時"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> AuditLogListResponse:
    """データ変更履歴を取得します。"""
    logger.info(
        "データ変更履歴取得",
        user_id=str(current_user.id),
        action="list_data_changes",
    )

    filter_params = AuditLogFilter(
        event_type="DATA_CHANGE",
        user_id=user_id,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
    )

    result = await service.get_audit_logs(
        filter_params=filter_params,
        page=page,
        limit=limit,
    )

    return result


@audit_logs_router.get(
    "/access",
    response_model=AuditLogListResponse,
    summary="アクセスログ取得",
    description="""
    アクセスログを取得します（event_type=ACCESS）。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def list_access_logs(
    _: RequireSystemAdminDep,
    service: AuditLogServiceDep,
    current_user: CurrentUserAccountDep,
    user_id: uuid.UUID | None = Query(None, description="ユーザーID"),
    start_date: datetime | None = Query(None, description="開始日時"),
    end_date: datetime | None = Query(None, description="終了日時"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> AuditLogListResponse:
    """アクセスログを取得します。"""
    logger.info(
        "アクセスログ取得",
        user_id=str(current_user.id),
        action="list_access_logs",
    )

    filter_params = AuditLogFilter(
        event_type="ACCESS",
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    result = await service.get_audit_logs(
        filter_params=filter_params,
        page=page,
        limit=limit,
    )

    return result


@audit_logs_router.get(
    "/security",
    response_model=AuditLogListResponse,
    summary="セキュリティイベント取得",
    description="""
    セキュリティイベントを取得します（event_type=SECURITY）。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def list_security_events(
    _: RequireSystemAdminDep,
    service: AuditLogServiceDep,
    current_user: CurrentUserAccountDep,
    user_id: uuid.UUID | None = Query(None, description="ユーザーID"),
    severity: str | None = Query(None, description="重要度"),
    start_date: datetime | None = Query(None, description="開始日時"),
    end_date: datetime | None = Query(None, description="終了日時"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> AuditLogListResponse:
    """セキュリティイベントを取得します。"""
    logger.info(
        "セキュリティイベント取得",
        user_id=str(current_user.id),
        action="list_security_events",
    )

    filter_params = AuditLogFilter(
        event_type="SECURITY",
        user_id=user_id,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
    )

    result = await service.get_audit_logs(
        filter_params=filter_params,
        page=page,
        limit=limit,
    )

    return result


@audit_logs_router.get(
    "/resource/{resource_type}/{resource_id}",
    response_model=AuditLogListResponse,
    summary="リソース変更履歴追跡",
    description="""
    特定リソースの変更履歴を追跡します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_resource_history(
    resource_type: str,
    resource_id: uuid.UUID,
    _: RequireSystemAdminDep,
    service: AuditLogServiceDep,
    current_user: CurrentUserAccountDep,
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> AuditLogListResponse:
    """リソースの変更履歴を追跡します。"""
    logger.info(
        "リソース変更履歴追跡",
        user_id=str(current_user.id),
        resource_type=resource_type,
        resource_id=str(resource_id),
        action="get_resource_history",
    )

    filter_params = AuditLogFilter(
        resource_type=resource_type,
        resource_id=resource_id,
    )

    result = await service.get_audit_logs(
        filter_params=filter_params,
        page=page,
        limit=limit,
    )

    return result


@audit_logs_router.get(
    "/export",
    summary="監査ログエクスポート",
    description="""
    監査ログをエクスポートします（CSV/JSON）。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def export_audit_logs(
    _: RequireSystemAdminDep,
    service: AuditLogServiceDep,
    current_user: CurrentUserAccountDep,
    format: str = Query("csv", description="出力形式（csv/json）"),
    event_type: str | None = Query(None, description="イベント種別"),
    start_date: datetime | None = Query(None, description="開始日時"),
    end_date: datetime | None = Query(None, description="終了日時"),
) -> StreamingResponse:
    """監査ログをエクスポートします。"""
    logger.info(
        "監査ログエクスポート",
        user_id=str(current_user.id),
        format=format,
        action="export_audit_logs",
    )

    filter_params = AuditLogFilter(
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )

    if format.lower() == "json":
        content = await service.export_to_json(filter_params=filter_params)
        media_type = "application/json"
        extension = "json"
    else:
        content = await service.export_to_csv(filter_params=filter_params)
        media_type = "text/csv"
        extension = "csv"

    filename = f"audit_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.{extension}"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
