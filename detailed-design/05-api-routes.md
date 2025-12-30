# API層詳細設計

## 1. 概要

本ドキュメントでは、システム管理機能（SA-001〜SA-043）のFastAPI APIルーター実装の詳細設計を定義する。

### 1.1 設計原則

- 既存の`src/app/api/routes/v1/project/project.py`のパターンに準拠
- `@handle_service_errors`デコレータでエラーハンドリング
- FastAPI Dependency Injectionによるサービス注入
- 権限チェックは依存関係として実装
- OpenAPIドキュメント用の詳細なdocstring

### 1.2 ルーター構成

```
src/app/api/routes/v1/admin/
├── __init__.py
├── activity_logs.py      # 操作履歴API（SA-001〜SA-006）
├── projects.py           # 全プロジェクト管理API（SA-007〜SA-011）
├── audit_logs.py         # 監査ログAPI（SA-012〜SA-016）
├── settings.py           # システム設定API（SA-017〜SA-021）
├── statistics.py         # システム統計API（SA-022〜SA-026）
├── bulk_operations.py    # 一括操作API（SA-027〜SA-030）
├── notifications.py      # 通知管理API（SA-031〜SA-034）
├── security.py           # セキュリティ管理API（SA-035〜SA-036）
├── data_management.py    # データ管理API（SA-037〜SA-040）
└── support_tools.py      # サポートツールAPI（SA-041〜SA-043）
```

---

## 2. 共通実装

### 2.1 依存関係定義

```python
# src/app/api/core/dependencies.py に追加

from typing import Annotated

from fastapi import Depends

from app.core.exceptions import AuthorizationError
from app.models.user_account import SystemRole
from app.services.admin import (
    ActivityTrackingService,
    AuditLogService,
    SystemSettingService,
    StatisticsService,
    BulkOperationService,
    AnnouncementService,
    NotificationTemplateService,
    SystemAlertService,
    SessionManagementService,
    DataManagementService,
    SupportToolsService,
    HealthCheckService,
    ProjectAdminService,
)


# サービス依存関係
ActivityTrackingServiceDep = Annotated[
    ActivityTrackingService,
    Depends(get_activity_tracking_service)
]
AuditLogServiceDep = Annotated[AuditLogService, Depends(get_audit_log_service)]
SystemSettingServiceDep = Annotated[SystemSettingService, Depends(get_system_setting_service)]
StatisticsServiceDep = Annotated[StatisticsService, Depends(get_statistics_service)]
BulkOperationServiceDep = Annotated[BulkOperationService, Depends(get_bulk_operation_service)]
AnnouncementServiceDep = Annotated[AnnouncementService, Depends(get_announcement_service)]
NotificationTemplateServiceDep = Annotated[
    NotificationTemplateService,
    Depends(get_notification_template_service)
]
SystemAlertServiceDep = Annotated[SystemAlertService, Depends(get_system_alert_service)]
SessionManagementServiceDep = Annotated[
    SessionManagementService,
    Depends(get_session_management_service)
]
DataManagementServiceDep = Annotated[DataManagementService, Depends(get_data_management_service)]
SupportToolsServiceDep = Annotated[SupportToolsService, Depends(get_support_tools_service)]
HealthCheckServiceDep = Annotated[HealthCheckService, Depends(get_health_check_service)]
ProjectAdminServiceDep = Annotated[ProjectAdminService, Depends(get_project_admin_service)]


# 権限チェック依存関係
async def require_system_admin(
    current_user: CurrentUserAccountDep,
) -> None:
    """システム管理者権限を要求する依存関係。"""
    if current_user.system_role != SystemRole.ADMIN:
        raise AuthorizationError(
            "システム管理者権限が必要です",
            details={"required_role": "ADMIN", "current_role": current_user.system_role.value},
        )


RequireSystemAdminDep = Annotated[None, Depends(require_system_admin)]
```

### 2.2 ルーター登録

```python
# src/app/api/routes/v1/admin/__init__.py

from fastapi import APIRouter

from .activity_logs import activity_logs_router
from .audit_logs import audit_logs_router
from .bulk_operations import bulk_operations_router
from .data_management import data_management_router
from .notifications import notifications_router
from .projects import projects_admin_router
from .security import security_router
from .settings import settings_router
from .statistics import statistics_router
from .support_tools import support_tools_router

admin_router = APIRouter(prefix="/admin", tags=["System Admin"])

admin_router.include_router(activity_logs_router)
admin_router.include_router(audit_logs_router)
admin_router.include_router(bulk_operations_router)
admin_router.include_router(data_management_router)
admin_router.include_router(notifications_router)
admin_router.include_router(projects_admin_router)
admin_router.include_router(security_router)
admin_router.include_router(settings_router)
admin_router.include_router(statistics_router)
admin_router.include_router(support_tools_router)

__all__ = ["admin_router"]
```

---

## 3. 操作履歴API（SA-001〜SA-006）

### 3.1 activity_logs.py

```python
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
from datetime import datetime

from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from app.api.core import (
    ActivityTrackingServiceDep,
    CurrentUserAccountDep,
    RequireSystemAdminDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
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

    csv_stream = await service.export_to_csv(filter_params=filter_params)

    return StreamingResponse(
        csv_stream,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=activity_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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
```

---

## 4. 全プロジェクト管理API（SA-007〜SA-011）

### 4.1 projects.py

```python
"""全プロジェクト管理APIエンドポイント。

システム管理者向けの全プロジェクト管理APIを提供します。

主な機能:
    - 全プロジェクト一覧取得（GET /api/v1/admin/projects）
    - プロジェクト詳細取得（GET /api/v1/admin/projects/{id}）
    - ストレージ使用量取得（GET /api/v1/admin/projects/storage）
    - 非アクティブプロジェクト一覧（GET /api/v1/admin/projects/inactive）
    - 一括アーカイブ（POST /api/v1/admin/projects/bulk-archive）
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, status

from app.api.core import (
    CurrentUserAccountDep,
    ProjectAdminServiceDep,
    RequireSystemAdminDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
    BulkArchiveRequest,
    BulkArchiveResponse,
    InactiveProjectListResponse,
    ProjectAdminDetailResponse,
    ProjectAdminFilter,
    ProjectAdminListResponse,
    StorageUsageListResponse,
)

logger = get_logger(__name__)

projects_admin_router = APIRouter(prefix="/projects", tags=["Project Admin"])


@projects_admin_router.get(
    "",
    response_model=ProjectAdminListResponse,
    summary="全プロジェクト一覧取得",
    description="""
    全プロジェクト一覧を取得します（管理者ビュー）。

    **権限**: システム管理者

    クエリパラメータ:
        - status: ステータス（active/archived/deleted）
        - owner_id: オーナーで絞り込み
        - inactive_days: 指定日数以上非アクティブ
        - search: プロジェクト名検索
        - sort_by: ソート項目（storage/last_activity/created_at）
        - sort_order: ソート順（asc/desc）
        - page: ページ番号
        - limit: 取得件数
    """,
)
@handle_service_errors
async def list_all_projects(
    _: RequireSystemAdminDep,
    service: ProjectAdminServiceDep,
    current_user: CurrentUserAccountDep,
    status_filter: str | None = Query(None, alias="status", description="ステータス"),
    owner_id: uuid.UUID | None = Query(None, description="オーナーID"),
    inactive_days: int | None = Query(None, ge=1, description="非アクティブ日数"),
    search: str | None = Query(None, description="検索文字列"),
    sort_by: str = Query("created_at", description="ソート項目"),
    sort_order: str = Query("desc", description="ソート順"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> ProjectAdminListResponse:
    """全プロジェクト一覧を取得します。"""
    logger.info(
        "全プロジェクト一覧取得",
        user_id=str(current_user.id),
        action="list_all_projects",
    )

    filter_params = ProjectAdminFilter(
        status=status_filter,
        owner_id=owner_id,
        inactive_days=inactive_days,
        search=search,
    )

    result = await service.get_all_projects(
        filter_params=filter_params,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )

    return result


@projects_admin_router.get(
    "/storage",
    response_model=StorageUsageListResponse,
    summary="ストレージ使用量取得",
    description="""
    プロジェクト別ストレージ使用量を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_storage_usage(
    _: RequireSystemAdminDep,
    service: ProjectAdminServiceDep,
    current_user: CurrentUserAccountDep,
    sort_by: str = Query("storage_used", description="ソート項目"),
    sort_order: str = Query("desc", description="ソート順"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> StorageUsageListResponse:
    """ストレージ使用量を取得します。"""
    logger.info(
        "ストレージ使用量取得",
        user_id=str(current_user.id),
        action="get_storage_usage",
    )

    result = await service.get_storage_usage(
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )

    return result


@projects_admin_router.get(
    "/inactive",
    response_model=InactiveProjectListResponse,
    summary="非アクティブプロジェクト一覧取得",
    description="""
    非アクティブプロジェクト一覧を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def list_inactive_projects(
    _: RequireSystemAdminDep,
    service: ProjectAdminServiceDep,
    current_user: CurrentUserAccountDep,
    inactive_days: int = Query(30, ge=1, description="非アクティブ日数"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> InactiveProjectListResponse:
    """非アクティブプロジェクト一覧を取得します。"""
    logger.info(
        "非アクティブプロジェクト一覧取得",
        user_id=str(current_user.id),
        inactive_days=inactive_days,
        action="list_inactive_projects",
    )

    result = await service.get_inactive_projects(
        inactive_days=inactive_days,
        page=page,
        limit=limit,
    )

    return result


@projects_admin_router.post(
    "/bulk-archive",
    response_model=BulkArchiveResponse,
    status_code=status.HTTP_200_OK,
    summary="一括アーカイブ",
    description="""
    複数プロジェクトを一括アーカイブします。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def bulk_archive_projects(
    request: BulkArchiveRequest,
    _: RequireSystemAdminDep,
    service: ProjectAdminServiceDep,
    current_user: CurrentUserAccountDep,
) -> BulkArchiveResponse:
    """プロジェクトを一括アーカイブします。"""
    logger.info(
        "一括アーカイブ",
        user_id=str(current_user.id),
        project_count=len(request.project_ids) if request.project_ids else "by_days",
        action="bulk_archive_projects",
    )

    result = await service.bulk_archive(
        project_ids=request.project_ids,
        inactive_days=request.inactive_days,
        dry_run=request.dry_run,
        executor_id=current_user.id,
    )

    return result


@projects_admin_router.get(
    "/{project_id}",
    response_model=ProjectAdminDetailResponse,
    summary="プロジェクト詳細取得（管理者ビュー）",
    description="""
    プロジェクト詳細を取得します（管理者ビュー）。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_project_admin(
    project_id: uuid.UUID,
    _: RequireSystemAdminDep,
    service: ProjectAdminServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectAdminDetailResponse:
    """プロジェクト詳細を取得します（管理者ビュー）。"""
    logger.info(
        "プロジェクト詳細取得（管理者）",
        user_id=str(current_user.id),
        project_id=str(project_id),
        action="get_project_admin",
    )

    result = await service.get_project_detail(project_id=project_id)

    return result
```

---

## 5. 監査ログAPI（SA-012〜SA-016）

### 5.1 audit_logs.py

```python
"""監査ログ管理APIエンドポイント。

詳細な監査ログの管理APIを提供します。

主な機能:
    - 監査ログ一覧取得（GET /api/v1/admin/audit-logs）
    - データ変更履歴取得（GET /api/v1/admin/audit-logs/changes）
    - アクセスログ取得（GET /api/v1/admin/audit-logs/access）
    - セキュリティイベント取得（GET /api/v1/admin/audit-logs/security）
    - リソース変更履歴追跡（GET /api/v1/admin/audit-logs/resource/{type}/{id}）
    - 監査ログエクスポート（GET /api/v1/admin/audit-logs/export）
"""

import uuid
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from app.api.core import (
    AuditLogServiceDep,
    CurrentUserAccountDep,
    RequireSystemAdminDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
    AuditLogFilter,
    AuditLogListResponse,
    ExportFormat,
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
    format: ExportFormat = Query(ExportFormat.CSV, description="出力形式"),
    event_type: str | None = Query(None, description="イベント種別"),
    start_date: datetime | None = Query(None, description="開始日時"),
    end_date: datetime | None = Query(None, description="終了日時"),
) -> StreamingResponse:
    """監査ログをエクスポートします。"""
    logger.info(
        "監査ログエクスポート",
        user_id=str(current_user.id),
        format=format.value,
        action="export_audit_logs",
    )

    filter_params = AuditLogFilter(
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )

    if format == ExportFormat.CSV:
        stream = await service.export_to_csv(filter_params=filter_params)
        media_type = "text/csv"
        extension = "csv"
    else:
        stream = await service.export_to_json(filter_params=filter_params)
        media_type = "application/json"
        extension = "json"

    filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"

    return StreamingResponse(
        stream,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
```

---

## 6. システム設定API（SA-017〜SA-021）

### 6.1 settings.py

```python
"""システム設定管理APIエンドポイント。

システム設定の管理APIを提供します。

主な機能:
    - 全設定取得（GET /api/v1/admin/settings）
    - カテゴリ別設定取得（GET /api/v1/admin/settings/{category}）
    - 設定更新（PATCH /api/v1/admin/settings/{category}/{key}）
    - メンテナンスモード有効化（POST /api/v1/admin/settings/maintenance/enable）
    - メンテナンスモード無効化（POST /api/v1/admin/settings/maintenance/disable）
"""

from fastapi import APIRouter, status

from app.api.core import (
    CurrentUserAccountDep,
    RequireSystemAdminDep,
    SystemSettingServiceDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
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
```

---

## 7. システム統計API（SA-022〜SA-026）

### 7.1 statistics.py

```python
"""システム統計APIエンドポイント。

システム統計・ダッシュボード用APIを提供します。

主な機能:
    - 統計概要取得（GET /api/v1/admin/statistics/overview）
    - ユーザー統計取得（GET /api/v1/admin/statistics/users）
    - ストレージ統計取得（GET /api/v1/admin/statistics/storage）
    - APIリクエスト統計取得（GET /api/v1/admin/statistics/api-requests）
    - エラー統計取得（GET /api/v1/admin/statistics/errors）
"""

from datetime import date

from fastapi import APIRouter, Query

from app.api.core import (
    CurrentUserAccountDep,
    RequireSystemAdminDep,
    StatisticsServiceDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
    ApiRequestStatisticsResponse,
    ErrorStatisticsResponse,
    StatisticsPeriod,
    StatisticsOverviewResponse,
    StorageStatisticsResponse,
    UserStatisticsResponse,
)

logger = get_logger(__name__)

statistics_router = APIRouter(prefix="/statistics", tags=["Statistics"])


@statistics_router.get(
    "/overview",
    response_model=StatisticsOverviewResponse,
    summary="統計概要取得",
    description="""
    システム統計概要を取得します。

    **権限**: システム管理者

    クエリパラメータ:
        - period: 期間（day/week/month/year）
        - start_date: 開始日
        - end_date: 終了日
    """,
)
@handle_service_errors
async def get_statistics_overview(
    _: RequireSystemAdminDep,
    service: StatisticsServiceDep,
    current_user: CurrentUserAccountDep,
    period: StatisticsPeriod = Query(StatisticsPeriod.MONTH, description="期間"),
    start_date: date | None = Query(None, description="開始日"),
    end_date: date | None = Query(None, description="終了日"),
) -> StatisticsOverviewResponse:
    """システム統計概要を取得します。"""
    logger.info(
        "統計概要取得",
        user_id=str(current_user.id),
        period=period.value,
        action="get_statistics_overview",
    )

    result = await service.get_overview(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    return result


@statistics_router.get(
    "/users",
    response_model=UserStatisticsResponse,
    summary="ユーザー統計取得",
    description="""
    ユーザー統計（アクティブユーザー推移）を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_user_statistics(
    _: RequireSystemAdminDep,
    service: StatisticsServiceDep,
    current_user: CurrentUserAccountDep,
    period: StatisticsPeriod = Query(StatisticsPeriod.MONTH, description="期間"),
    start_date: date | None = Query(None, description="開始日"),
    end_date: date | None = Query(None, description="終了日"),
) -> UserStatisticsResponse:
    """ユーザー統計を取得します。"""
    logger.info(
        "ユーザー統計取得",
        user_id=str(current_user.id),
        period=period.value,
        action="get_user_statistics",
    )

    result = await service.get_user_statistics(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    return result


@statistics_router.get(
    "/storage",
    response_model=StorageStatisticsResponse,
    summary="ストレージ統計取得",
    description="""
    ストレージ使用量推移を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_storage_statistics(
    _: RequireSystemAdminDep,
    service: StatisticsServiceDep,
    current_user: CurrentUserAccountDep,
    period: StatisticsPeriod = Query(StatisticsPeriod.MONTH, description="期間"),
    start_date: date | None = Query(None, description="開始日"),
    end_date: date | None = Query(None, description="終了日"),
) -> StorageStatisticsResponse:
    """ストレージ統計を取得します。"""
    logger.info(
        "ストレージ統計取得",
        user_id=str(current_user.id),
        period=period.value,
        action="get_storage_statistics",
    )

    result = await service.get_storage_statistics(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    return result


@statistics_router.get(
    "/api-requests",
    response_model=ApiRequestStatisticsResponse,
    summary="APIリクエスト統計取得",
    description="""
    APIリクエスト統計を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_api_request_statistics(
    _: RequireSystemAdminDep,
    service: StatisticsServiceDep,
    current_user: CurrentUserAccountDep,
    period: StatisticsPeriod = Query(StatisticsPeriod.DAY, description="期間"),
    start_date: date | None = Query(None, description="開始日"),
    end_date: date | None = Query(None, description="終了日"),
) -> ApiRequestStatisticsResponse:
    """APIリクエスト統計を取得します。"""
    logger.info(
        "APIリクエスト統計取得",
        user_id=str(current_user.id),
        period=period.value,
        action="get_api_request_statistics",
    )

    result = await service.get_api_request_statistics(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    return result


@statistics_router.get(
    "/errors",
    response_model=ErrorStatisticsResponse,
    summary="エラー統計取得",
    description="""
    エラー発生率統計を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_error_statistics(
    _: RequireSystemAdminDep,
    service: StatisticsServiceDep,
    current_user: CurrentUserAccountDep,
    period: StatisticsPeriod = Query(StatisticsPeriod.DAY, description="期間"),
    start_date: date | None = Query(None, description="開始日"),
    end_date: date | None = Query(None, description="終了日"),
) -> ErrorStatisticsResponse:
    """エラー統計を取得します。"""
    logger.info(
        "エラー統計取得",
        user_id=str(current_user.id),
        period=period.value,
        action="get_error_statistics",
    )

    result = await service.get_error_statistics(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    return result
```

---

## 8. 一括操作API（SA-027〜SA-030）

### 8.1 bulk_operations.py

```python
"""一括操作APIエンドポイント。

ユーザー・プロジェクトの一括操作APIを提供します。

主な機能:
    - ユーザー一括インポート（POST /api/v1/admin/bulk/users/import）
    - ユーザー一括エクスポート（GET /api/v1/admin/bulk/users/export）
    - 非アクティブユーザー一括無効化（POST /api/v1/admin/bulk/users/deactivate）
    - プロジェクト一括アーカイブ（POST /api/v1/admin/bulk/projects/archive）
"""

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.core import (
    BulkOperationServiceDep,
    CurrentUserAccountDep,
    RequireSystemAdminDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
    BulkDeactivateRequest,
    BulkDeactivateResponse,
    BulkImportResponse,
    BulkProjectArchiveRequest,
    BulkProjectArchiveResponse,
    ExportFormat,
)

logger = get_logger(__name__)

bulk_operations_router = APIRouter(prefix="/bulk", tags=["Bulk Operations"])


@bulk_operations_router.post(
    "/users/import",
    response_model=BulkImportResponse,
    status_code=status.HTTP_200_OK,
    summary="ユーザー一括インポート",
    description="""
    ユーザーをCSVファイルから一括インポートします。

    **権限**: システム管理者

    リクエスト:
        - file: CSVファイル
        - dry_run: プレビューのみ（デフォルト: false）
    """,
)
@handle_service_errors
async def import_users(
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
    file: UploadFile = File(..., description="CSVファイル"),
    dry_run: bool = Query(False, description="プレビューのみ"),
) -> BulkImportResponse:
    """ユーザーを一括インポートします。"""
    logger.info(
        "ユーザー一括インポート",
        user_id=str(current_user.id),
        filename=file.filename,
        dry_run=dry_run,
        action="import_users",
    )

    result = await service.import_users(
        file=file,
        dry_run=dry_run,
        executor_id=current_user.id,
    )

    return result


@bulk_operations_router.get(
    "/users/export",
    summary="ユーザー一括エクスポート",
    description="""
    ユーザー情報を一括エクスポートします。

    **権限**: システム管理者

    クエリパラメータ:
        - status: ステータスフィルタ
        - role: ロールフィルタ
        - format: 出力形式（csv/xlsx）
    """,
)
@handle_service_errors
async def export_users(
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
    status_filter: str | None = Query(None, alias="status", description="ステータス"),
    role: str | None = Query(None, description="ロール"),
    format: ExportFormat = Query(ExportFormat.CSV, description="出力形式"),
) -> StreamingResponse:
    """ユーザー情報を一括エクスポートします。"""
    logger.info(
        "ユーザー一括エクスポート",
        user_id=str(current_user.id),
        format=format.value,
        action="export_users",
    )

    stream, filename, media_type = await service.export_users(
        status_filter=status_filter,
        role=role,
        format=format,
    )

    return StreamingResponse(
        stream,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@bulk_operations_router.post(
    "/users/deactivate",
    response_model=BulkDeactivateResponse,
    status_code=status.HTTP_200_OK,
    summary="非アクティブユーザー一括無効化",
    description="""
    非アクティブユーザーを一括無効化します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def deactivate_inactive_users(
    request: BulkDeactivateRequest,
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
) -> BulkDeactivateResponse:
    """非アクティブユーザーを一括無効化します。"""
    logger.info(
        "非アクティブユーザー一括無効化",
        user_id=str(current_user.id),
        inactive_days=request.inactive_days,
        dry_run=request.dry_run,
        action="deactivate_inactive_users",
    )

    result = await service.deactivate_inactive_users(
        inactive_days=request.inactive_days,
        dry_run=request.dry_run,
        executor_id=current_user.id,
    )

    return result


@bulk_operations_router.post(
    "/projects/archive",
    response_model=BulkProjectArchiveResponse,
    status_code=status.HTTP_200_OK,
    summary="プロジェクト一括アーカイブ",
    description="""
    古いプロジェクトを一括アーカイブします。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def archive_old_projects(
    request: BulkProjectArchiveRequest,
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
) -> BulkProjectArchiveResponse:
    """プロジェクトを一括アーカイブします。"""
    logger.info(
        "プロジェクト一括アーカイブ",
        user_id=str(current_user.id),
        inactive_days=request.inactive_days,
        dry_run=request.dry_run,
        action="archive_old_projects",
    )

    result = await service.archive_old_projects(
        inactive_days=request.inactive_days,
        dry_run=request.dry_run,
        executor_id=current_user.id,
    )

    return result
```

---

## 9. 通知管理API（SA-031〜SA-034）

### 9.1 notifications.py

```python
"""通知管理APIエンドポイント。

アラート・お知らせ・通知テンプレート管理APIを提供します。

主な機能:
    - アラート管理（CRUD）
    - 通知テンプレート管理（CRUD）
    - お知らせ管理（CRUD）
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core import (
    AnnouncementServiceDep,
    CurrentUserAccountDep,
    NotificationTemplateServiceDep,
    RequireSystemAdminDep,
    SystemAlertServiceDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
    AnnouncementCreate,
    AnnouncementListResponse,
    AnnouncementResponse,
    AnnouncementUpdate,
    NotificationTemplateCreate,
    NotificationTemplateListResponse,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
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
    service: SystemAlertServiceDep,
    current_user: CurrentUserAccountDep,
    is_enabled: bool | None = Query(None, description="有効フラグ"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> SystemAlertListResponse:
    """システムアラート一覧を取得します。"""
    logger.info(
        "システムアラート一覧取得",
        user_id=str(current_user.id),
        action="list_alerts",
    )

    result = await service.get_alerts(
        is_enabled=is_enabled,
        page=page,
        limit=limit,
    )

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
    service: SystemAlertServiceDep,
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
    service: SystemAlertServiceDep,
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
    service: SystemAlertServiceDep,
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
    service: NotificationTemplateServiceDep,
    current_user: CurrentUserAccountDep,
    is_active: bool | None = Query(None, description="有効フラグ"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> NotificationTemplateListResponse:
    """通知テンプレート一覧を取得します。"""
    logger.info(
        "通知テンプレート一覧取得",
        user_id=str(current_user.id),
        action="list_templates",
    )

    result = await service.get_templates(
        is_active=is_active,
        page=page,
        limit=limit,
    )

    return result


@templates_router.post(
    "",
    response_model=NotificationTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="通知テンプレート作成",
)
@handle_service_errors
async def create_template(
    request: NotificationTemplateCreate,
    _: RequireSystemAdminDep,
    service: NotificationTemplateServiceDep,
    current_user: CurrentUserAccountDep,
) -> NotificationTemplateResponse:
    """通知テンプレートを作成します。"""
    logger.info(
        "通知テンプレート作成",
        user_id=str(current_user.id),
        name=request.name,
        action="create_template",
    )

    result = await service.create_template(data=request)

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
    service: NotificationTemplateServiceDep,
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
    service: AnnouncementServiceDep,
    current_user: CurrentUserAccountDep,
    is_active: bool | None = Query(None, description="有効フラグ"),
    announcement_type: str | None = Query(None, description="種別"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> AnnouncementListResponse:
    """システムお知らせ一覧を取得します。"""
    logger.info(
        "システムお知らせ一覧取得",
        user_id=str(current_user.id),
        action="list_announcements",
    )

    result = await service.get_announcements(
        is_active=is_active,
        announcement_type=announcement_type,
        page=page,
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
    service: AnnouncementServiceDep,
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
    service: AnnouncementServiceDep,
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
    service: AnnouncementServiceDep,
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
```

---

## 10. セキュリティ管理API（SA-035〜SA-036）

### 10.1 security.py

```python
"""セキュリティ管理APIエンドポイント。

セッション管理・強制ログアウトAPIを提供します。

主な機能:
    - アクティブセッション一覧取得（GET /api/v1/admin/sessions）
    - ユーザー別セッション取得（GET /api/v1/admin/sessions/user/{user_id}）
    - セッション終了（POST /api/v1/admin/sessions/{id}/terminate）
    - ユーザー全セッション終了（POST /api/v1/admin/sessions/user/{user_id}/terminate-all）
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core import (
    CurrentUserAccountDep,
    RequireSystemAdminDep,
    SessionManagementServiceDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
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
        - page: ページ番号
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
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> SessionListResponse:
    """アクティブセッション一覧を取得します。"""
    logger.info(
        "アクティブセッション一覧取得",
        user_id=str(current_user.id),
        action="list_sessions",
    )

    result = await service.get_active_sessions(
        user_id=user_id,
        ip_address=ip_address,
        page=page,
        limit=limit,
    )

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
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> SessionListResponse:
    """ユーザーのセッション一覧を取得します。"""
    logger.info(
        "ユーザー別セッション取得",
        user_id=str(current_user.id),
        target_user_id=str(user_id),
        action="get_user_sessions",
    )

    result = await service.get_active_sessions(
        user_id=user_id,
        page=page,
        limit=limit,
    )

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

    result = await service.terminate_session(
        session_id=session_id,
        reason=request.reason,
        terminated_by=current_user.id,
    )

    return result


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

    result = await service.terminate_all_user_sessions(
        user_id=user_id,
        reason=request.reason,
        terminated_by=current_user.id,
    )

    return result
```

---

## 11. データ管理API（SA-037〜SA-040）

### 11.1 data_management.py

```python
"""データ管理APIエンドポイント。

データクリーンアップ・保持ポリシー管理APIを提供します。

主な機能:
    - 削除プレビュー（GET /api/v1/admin/data/cleanup/preview）
    - データ一括削除（POST /api/v1/admin/data/cleanup/execute）
    - 孤立ファイル一覧（GET /api/v1/admin/data/orphan-files）
    - 孤立ファイル削除（POST /api/v1/admin/data/orphan-files/cleanup）
    - 保持ポリシー取得（GET /api/v1/admin/data/retention-policy）
    - 保持ポリシー更新（PATCH /api/v1/admin/data/retention-policy）
"""

from fastapi import APIRouter, File, Query, UploadFile, status

from app.api.core import (
    CurrentUserAccountDep,
    DataManagementServiceDep,
    RequireSystemAdminDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
    CleanupExecuteRequest,
    CleanupExecuteResponse,
    CleanupPreviewResponse,
    OrphanFileCleanupRequest,
    OrphanFileCleanupResponse,
    OrphanFileListResponse,
    RetentionPolicyResponse,
    RetentionPolicyUpdate,
)

logger = get_logger(__name__)

data_management_router = APIRouter(prefix="/data", tags=["Data Management"])


@data_management_router.get(
    "/cleanup/preview",
    response_model=CleanupPreviewResponse,
    summary="削除対象データプレビュー",
    description="""
    削除対象データのプレビューを取得します。

    **権限**: システム管理者

    クエリパラメータ:
        - target_types: 対象種別（activity_logs/audit_logs/deleted_projects等）
        - retention_days: 保持日数
    """,
)
@handle_service_errors
async def preview_cleanup(
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
    target_types: list[str] = Query(..., description="対象種別"),
    retention_days: int = Query(..., ge=1, description="保持日数"),
) -> CleanupPreviewResponse:
    """削除対象データをプレビューします。"""
    logger.info(
        "削除対象データプレビュー",
        user_id=str(current_user.id),
        target_types=target_types,
        retention_days=retention_days,
        action="preview_cleanup",
    )

    result = await service.preview_cleanup(
        target_types=target_types,
        retention_days=retention_days,
    )

    return result


@data_management_router.post(
    "/cleanup/execute",
    response_model=CleanupExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="データ一括削除",
    description="""
    古いデータを一括削除します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def execute_cleanup(
    request: CleanupExecuteRequest,
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
) -> CleanupExecuteResponse:
    """データを一括削除します。"""
    logger.info(
        "データ一括削除",
        user_id=str(current_user.id),
        target_types=request.target_types,
        retention_days=request.retention_days,
        dry_run=request.dry_run,
        action="execute_cleanup",
    )

    result = await service.execute_cleanup(
        target_types=request.target_types,
        retention_days=request.retention_days,
        dry_run=request.dry_run,
        executor_id=current_user.id,
    )

    return result


@data_management_router.get(
    "/orphan-files",
    response_model=OrphanFileListResponse,
    summary="孤立ファイル一覧取得",
    description="""
    孤立ファイル一覧を取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def list_orphan_files(
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> OrphanFileListResponse:
    """孤立ファイル一覧を取得します。"""
    logger.info(
        "孤立ファイル一覧取得",
        user_id=str(current_user.id),
        action="list_orphan_files",
    )

    result = await service.get_orphan_files(
        page=page,
        limit=limit,
    )

    return result


@data_management_router.post(
    "/orphan-files/cleanup",
    response_model=OrphanFileCleanupResponse,
    status_code=status.HTTP_200_OK,
    summary="孤立ファイル削除",
    description="""
    孤立ファイルを削除します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def cleanup_orphan_files(
    request: OrphanFileCleanupRequest,
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
) -> OrphanFileCleanupResponse:
    """孤立ファイルを削除します。"""
    logger.info(
        "孤立ファイル削除",
        user_id=str(current_user.id),
        file_count=len(request.file_ids) if request.file_ids else "all",
        action="cleanup_orphan_files",
    )

    result = await service.cleanup_orphan_files(
        file_ids=request.file_ids,
        delete_all=request.delete_all,
        executor_id=current_user.id,
    )

    return result


@data_management_router.get(
    "/retention-policy",
    response_model=RetentionPolicyResponse,
    summary="保持ポリシー取得",
    description="""
    データ保持ポリシーを取得します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_retention_policy(
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
) -> RetentionPolicyResponse:
    """保持ポリシーを取得します。"""
    logger.info(
        "保持ポリシー取得",
        user_id=str(current_user.id),
        action="get_retention_policy",
    )

    result = await service.get_retention_policy()

    return result


@data_management_router.patch(
    "/retention-policy",
    response_model=RetentionPolicyResponse,
    summary="保持ポリシー更新",
    description="""
    データ保持ポリシーを更新します。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def update_retention_policy(
    request: RetentionPolicyUpdate,
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
) -> RetentionPolicyResponse:
    """保持ポリシーを更新します。"""
    logger.info(
        "保持ポリシー更新",
        user_id=str(current_user.id),
        action="update_retention_policy",
    )

    result = await service.update_retention_policy(
        data=request,
        updated_by=current_user.id,
    )

    return result


@data_management_router.post(
    "/master/import",
    summary="マスタデータインポート",
    description="""
    マスタデータを一括インポートします。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def import_master_data(
    _: RequireSystemAdminDep,
    service: DataManagementServiceDep,
    current_user: CurrentUserAccountDep,
    file: UploadFile = File(..., description="インポートファイル"),
    dry_run: bool = Query(False, description="プレビューのみ"),
):
    """マスタデータをインポートします。"""
    logger.info(
        "マスタデータインポート",
        user_id=str(current_user.id),
        filename=file.filename,
        dry_run=dry_run,
        action="import_master_data",
    )

    result = await service.import_master_data(
        file=file,
        dry_run=dry_run,
        executor_id=current_user.id,
    )

    return result
```

---

## 12. サポートツールAPI（SA-041〜SA-043）

### 12.1 support_tools.py

```python
"""サポートツールAPIエンドポイント。

代行操作・デバッグ・ヘルスチェックAPIを提供します。

主な機能:
    - ユーザー代行操作開始（POST /api/v1/admin/impersonate/{user_id}）
    - ユーザー代行操作終了（POST /api/v1/admin/impersonate/end）
    - デバッグモード有効化（POST /api/v1/admin/debug/enable）
    - デバッグモード無効化（POST /api/v1/admin/debug/disable）
    - 簡易ヘルスチェック（GET /api/v1/admin/health-check）
    - 詳細ヘルスチェック（GET /api/v1/admin/health-check/detailed）
"""

import uuid

from fastapi import APIRouter, status

from app.api.core import (
    CurrentUserAccountDep,
    HealthCheckServiceDep,
    RequireSystemAdminDep,
    SupportToolsServiceDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin import (
    DebugModeResponse,
    DetailedHealthCheckResponse,
    HealthCheckResponse,
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
        admin_id=current_user.id,
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

    result = await service.end_impersonation(admin_id=current_user.id)

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

    result = await service.enable_debug_mode(enabled_by=current_user.id)

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

    result = await service.disable_debug_mode(disabled_by=current_user.id)

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
    service: HealthCheckServiceDep,
    current_user: CurrentUserAccountDep,
) -> HealthCheckResponse:
    """簡易ヘルスチェックを実行します。"""
    logger.info(
        "簡易ヘルスチェック",
        user_id=str(current_user.id),
        action="health_check",
    )

    result = await service.check_health()

    return result


@support_tools_router.get(
    "/health-check/detailed",
    response_model=DetailedHealthCheckResponse,
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
    service: HealthCheckServiceDep,
    current_user: CurrentUserAccountDep,
) -> DetailedHealthCheckResponse:
    """詳細ヘルスチェックを実行します。"""
    logger.info(
        "詳細ヘルスチェック",
        user_id=str(current_user.id),
        action="detailed_health_check",
    )

    result = await service.check_health_detailed()

    return result
```

---

## 13. メインルーター登録

```python
# src/app/api/routes/v1/__init__.py に追加

from app.api.routes.v1.admin import admin_router

# 既存のルーター登録後に追加
v1_router.include_router(admin_router)
```

---

## 14. エラーハンドリング

### 14.1 カスタム例外

```python
# src/app/core/exceptions.py に追加（必要に応じて）

class MaintenanceModeError(AppError):
    """メンテナンスモード中のエラー。"""

    def __init__(self, message: str = "システムはメンテナンス中です"):
        super().__init__(message=message, status_code=503)


class ImpersonationError(AppError):
    """代行操作エラー。"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message=message, status_code=400, details=details)
```

---

## 15. 実装時の注意事項

### 15.1 権限チェック

- 全エンドポイントで`RequireSystemAdminDep`を使用
- 依存関係として権限チェックを行い、不正アクセスを防止

### 15.2 ログ出力

- 全操作でロギングを実施
- `action`キーで操作種別を識別可能に

### 15.3 監査ログ

- 重要な操作（削除、設定変更、代行操作等）は監査ログに記録
- サービス層で`AuditLogService`を呼び出して記録

### 15.4 パフォーマンス

- 大量データ取得時はページネーション必須
- エクスポート処理はストリーミングレスポンス使用
- 一括操作は非同期バックグラウンドタスク検討

### 15.5 セキュリティ

- 機密設定（`is_secret=True`）は値をマスクして返却
- 代行操作は監査ログに詳細記録
- セッショントークンはハッシュ化して保存

---

## 16. レート制限設計

### 16.1 概要

高負荷エンドポイント（エクスポート、一括操作等）に対してレート制限を設け、
システムの安定性を確保します。

### 16.2 レート制限の実装

```python
"""レート制限デコレータ。

高負荷APIエンドポイントへのアクセスを制限します。
"""

import time
from collections import defaultdict
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Request, status

from app.core.config import settings


class RateLimiter:
    """インメモリレート制限。

    注意: 本番環境ではRedisベースの実装を推奨します。

    Attributes:
        requests: ユーザーごとのリクエスト記録
        max_requests: 時間枠内の最大リクエスト数
        window_seconds: 時間枠（秒）
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def is_allowed(self, user_id: str) -> tuple[bool, int]:
        """リクエストが許可されるかチェック。

        Args:
            user_id: ユーザー識別子

        Returns:
            tuple[bool, int]: (許可フラグ, 残りリクエスト数)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # 時間枠外のリクエストを削除
        self.requests[user_id] = [
            ts for ts in self.requests[user_id] if ts > window_start
        ]

        remaining = self.max_requests - len(self.requests[user_id])

        if remaining <= 0:
            return False, 0

        self.requests[user_id].append(now)
        return True, remaining - 1

    def get_retry_after(self, user_id: str) -> int:
        """次にリクエスト可能になるまでの秒数を取得。"""
        if not self.requests[user_id]:
            return 0
        oldest = min(self.requests[user_id])
        return max(0, int(self.window_seconds - (time.time() - oldest)))


# レート制限インスタンス（エンドポイント種別ごと）
RATE_LIMITERS = {
    "export": RateLimiter(max_requests=5, window_seconds=300),     # 5分間に5回
    "bulk_operation": RateLimiter(max_requests=3, window_seconds=600),  # 10分間に3回
    "import": RateLimiter(max_requests=10, window_seconds=3600),   # 1時間に10回
    "cleanup": RateLimiter(max_requests=2, window_seconds=3600),   # 1時間に2回
}


def rate_limit(limiter_name: str):
    """レート制限デコレータ。

    Args:
        limiter_name: 使用するレート制限の名前

    Example:
        @rate_limit("export")
        async def export_users(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Requestオブジェクトを取得
            request: Request | None = kwargs.get("request")
            current_user = kwargs.get("current_user")

            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="認証が必要です",
                )

            user_id = str(current_user.id)
            limiter = RATE_LIMITERS.get(limiter_name)

            if limiter is None:
                # レート制限が定義されていない場合はそのまま実行
                return await func(*args, **kwargs)

            allowed, remaining = limiter.is_allowed(user_id)

            if not allowed:
                retry_after = limiter.get_retry_after(user_id)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "TooManyRequests",
                        "message": f"リクエスト制限に達しました。{retry_after}秒後に再試行してください。",
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            # レスポンスヘッダーに残りリクエスト数を追加
            response = await func(*args, **kwargs)

            # FastAPIのResponseオブジェクトの場合はヘッダーを追加
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)

            return response

        return wrapper
    return decorator
```

### 16.3 エンドポイントでの使用例

```python
from app.api.core.rate_limit import rate_limit


@bulk_operations_router.post(
    "/users/export",
    response_class=StreamingResponse,
    summary="ユーザー一括エクスポート",
)
@handle_service_errors
@rate_limit("export")  # レート制限を適用
async def export_users(
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
    filter_params: UserExportFilter = Depends(),
) -> StreamingResponse:
    """ユーザーを一括エクスポートします。

    レート制限: 5分間に5回まで
    """
    ...


@bulk_operations_router.post(
    "/users/deactivate",
    response_model=BulkDeactivateResponse,
    summary="非アクティブユーザー一括無効化",
)
@handle_service_errors
@rate_limit("bulk_operation")  # レート制限を適用
async def deactivate_inactive_users(
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
    request_body: BulkUserDeactivateRequest,
) -> BulkDeactivateResponse:
    """非アクティブユーザーを一括無効化します。

    レート制限: 10分間に3回まで
    """
    ...
```

### 16.4 レート制限対象エンドポイント一覧

| エンドポイント | 制限種別 | 制限値 | 理由 |
|--------------|---------|--------|------|
| `POST /bulk-operations/users/export` | export | 5回/5分 | 大量データ取得による負荷 |
| `POST /bulk-operations/projects/export` | export | 5回/5分 | 大量データ取得による負荷 |
| `GET /audit-logs/export` | export | 5回/5分 | 大量データ取得による負荷 |
| `GET /activity-logs/export` | export | 5回/5分 | 大量データ取得による負荷 |
| `POST /bulk-operations/users/import` | import | 10回/1時間 | DB負荷・検証処理 |
| `POST /bulk-operations/users/deactivate` | bulk_operation | 3回/10分 | 大量レコード更新 |
| `POST /bulk-operations/projects/archive` | bulk_operation | 3回/10分 | 大量レコード更新 |
| `POST /data-management/cleanup/execute` | cleanup | 2回/1時間 | 大量データ削除 |
| `DELETE /data-management/orphan-files` | cleanup | 2回/1時間 | 大量ファイル削除 |

### 16.5 本番環境向けRedis実装

```python
"""Redisベースのレート制限（本番環境推奨）。

スケーラブルで分散環境に対応したレート制限を提供します。
"""

import redis.asyncio as redis

from app.core.config import settings


class RedisRateLimiter:
    """Redisベースのスライディングウィンドウレート制限。"""

    def __init__(
        self,
        redis_client: redis.Redis,
        max_requests: int,
        window_seconds: int,
        key_prefix: str = "rate_limit",
    ):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    async def is_allowed(self, user_id: str) -> tuple[bool, int]:
        """リクエストが許可されるかチェック。"""
        key = f"{self.key_prefix}:{user_id}"
        now = time.time()
        window_start = now - self.window_seconds

        pipe = self.redis.pipeline()
        # 古いエントリを削除
        pipe.zremrangebyscore(key, 0, window_start)
        # 現在のカウントを取得
        pipe.zcard(key)
        # 新しいエントリを追加
        pipe.zadd(key, {str(now): now})
        # TTLを設定
        pipe.expire(key, self.window_seconds)

        results = await pipe.execute()
        current_count = results[1]

        remaining = max(0, self.max_requests - current_count - 1)

        if current_count >= self.max_requests:
            # 追加したエントリを削除
            await self.redis.zrem(key, str(now))
            return False, 0

        return True, remaining

    async def get_retry_after(self, user_id: str) -> int:
        """次にリクエスト可能になるまでの秒数を取得。"""
        key = f"{self.key_prefix}:{user_id}"
        oldest = await self.redis.zrange(key, 0, 0, withscores=True)
        if not oldest:
            return 0
        oldest_time = oldest[0][1]
        return max(0, int(self.window_seconds - (time.time() - oldest_time)))
```

### 16.6 レート制限レスポンスヘッダー

レート制限されたエンドポイントは以下のヘッダーを返します：

| ヘッダー | 説明 | 例 |
|---------|------|-----|
| `X-RateLimit-Limit` | 時間枠内の最大リクエスト数 | `5` |
| `X-RateLimit-Remaining` | 残りリクエスト数 | `3` |
| `Retry-After` | 再試行可能になるまでの秒数（429の場合のみ） | `120` |

### 16.7 レート制限超過時のレスポンス

```json
{
    "error": "TooManyRequests",
    "message": "リクエスト制限に達しました。120秒後に再試行してください。",
    "retry_after": 120
}
```

HTTP Status: `429 Too Many Requests`
