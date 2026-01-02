"""一括操作APIエンドポイント。

ユーザー・プロジェクトの一括操作APIを提供します。

主な機能:
    - ユーザー一括インポート（POST /api/v1/admin/bulk/users/import）
    - ユーザー一括エクスポート（GET /api/v1/admin/bulk/users/export）
    - 非アクティブユーザー一括無効化（POST /api/v1/admin/bulk/users/deactivate）
    - プロジェクト一括アーカイブ（POST /api/v1/admin/bulk/projects/archive）

セキュリティ:
    - システム管理者権限必須
"""

from datetime import UTC, datetime

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    BulkOperationServiceDep,
    RequireSystemAdminDep,
)
from app.core.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.bulk_operation import (
    BulkArchiveResponse,
    BulkDeactivateResponse,
    BulkImportResponse,
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
    """,
)
@handle_service_errors
async def import_users(
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
    file: UploadFile = File(..., description="CSVファイル"),
) -> BulkImportResponse:
    """ユーザーを一括インポートします。"""
    logger.info(
        "ユーザー一括インポート",
        user_id=str(current_user.id),
        filename=file.filename,
        action="import_users",
    )

    # CSVコンテンツを読み込み
    csv_content = (await file.read()).decode("utf-8")

    result = await service.import_users(
        csv_content=csv_content,
        performed_by=current_user.id,
    )

    return result


@bulk_operations_router.get(
    "/users/export",
    summary="ユーザー一括エクスポート",
    description="""
    ユーザー情報を一括エクスポートします。

    **権限**: システム管理者

    クエリパラメータ:
        - is_active: アクティブフィルタ
    """,
)
@handle_service_errors
async def export_users(
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
    is_active: bool | None = Query(None, description="アクティブフィルタ"),
) -> StreamingResponse:
    """ユーザー情報を一括エクスポートします。"""
    logger.info(
        "ユーザー一括エクスポート",
        user_id=str(current_user.id),
        is_active=is_active,
        action="export_users",
    )

    csv_content = await service.export_users(is_active=is_active)

    filename = f"users_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
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
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
    inactive_days: int = Query(..., ge=1, description="非アクティブ日数"),
    dry_run: bool = Query(False, description="プレビューのみ"),
) -> BulkDeactivateResponse:
    """非アクティブユーザーを一括無効化します。"""
    logger.info(
        "非アクティブユーザー一括無効化",
        user_id=str(current_user.id),
        inactive_days=inactive_days,
        dry_run=dry_run,
        action="deactivate_inactive_users",
    )

    result = await service.deactivate_inactive_users(
        inactive_days=inactive_days,
        dry_run=dry_run,
        performed_by=current_user.id,
    )

    return result


@bulk_operations_router.post(
    "/projects/archive",
    response_model=BulkArchiveResponse,
    status_code=status.HTTP_200_OK,
    summary="プロジェクト一括アーカイブ",
    description="""
    古いプロジェクトを一括アーカイブします。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def archive_old_projects(
    _: RequireSystemAdminDep,
    service: BulkOperationServiceDep,
    current_user: CurrentUserAccountDep,
    inactive_days: int = Query(..., ge=1, description="非アクティブ日数"),
    dry_run: bool = Query(False, description="プレビューのみ"),
) -> BulkArchiveResponse:
    """プロジェクトを一括アーカイブします。"""
    logger.info(
        "プロジェクト一括アーカイブ",
        user_id=str(current_user.id),
        inactive_days=inactive_days,
        dry_run=dry_run,
        action="archive_old_projects",
    )

    result = await service.archive_inactive_projects(
        inactive_days=inactive_days,
        dry_run=dry_run,
        performed_by=current_user.id,
    )

    return result
