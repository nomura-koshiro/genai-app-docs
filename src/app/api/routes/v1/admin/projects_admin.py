"""管理者用プロジェクト管理APIエンドポイント。

全プロジェクトの閲覧・管理APIを提供します。

主な機能:
    - 全プロジェクト一覧取得（GET /api/v1/admin/projects）
    - プロジェクト詳細取得（GET /api/v1/admin/projects/{id}）
    - ストレージ使用量取得（GET /api/v1/admin/projects/storage）
    - 非アクティブプロジェクト一覧（GET /api/v1/admin/projects/inactive）

セキュリティ:
    - システム管理者権限必須
"""

import uuid

from fastapi import APIRouter, Path, Query

from app.api.core.dependencies import CurrentUserAccountDep
from app.api.core.dependencies.system_admin import (
    ProjectsAdminServiceDep,
    RequireSystemAdminDep,
)
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.admin.project_admin import (
    AdminProjectDetailResponse,
    AdminProjectListResponse,
    ProjectStorageListResponse,
)

logger = get_logger(__name__)

admin_projects_router = APIRouter(prefix="/projects", tags=["Admin Projects"])


@admin_projects_router.get(
    "",
    response_model=AdminProjectListResponse,
    summary="全プロジェクト一覧取得",
    description="""
    全プロジェクト一覧を取得します（管理者専用）。

    **権限**: システム管理者

    クエリパラメータ:
        - status: ステータスフィルタ（active/archived）
        - owner_id: オーナーIDフィルタ
        - inactive_days: 非アクティブ日数フィルタ
        - search: プロジェクト名検索
        - sort_by: ソート項目（storage/last_activity/created_at）
        - sort_order: ソート順（asc/desc）
        - page: ページ番号
        - limit: 取得件数
    """,
)
@handle_service_errors
async def get_all_projects(
    _: RequireSystemAdminDep,
    service: ProjectsAdminServiceDep,
    current_user: CurrentUserAccountDep,
    status: str | None = Query(None, description="ステータスフィルタ"),
    owner_id: uuid.UUID | None = Query(None, description="オーナーIDフィルタ"),
    inactive_days: int | None = Query(None, ge=1, description="非アクティブ日数"),
    search: str | None = Query(None, description="検索キーワード"),
    sort_by: str | None = Query(None, description="ソート項目"),
    sort_order: str = Query("desc", description="ソート順"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> AdminProjectListResponse:
    """全プロジェクト一覧を取得します。"""
    logger.info(
        "全プロジェクト一覧取得",
        user_id=str(current_user.id),
        status=status,
        page=page,
        action="get_all_projects",
    )

    result = await service.get_all_projects(
        status=status,
        owner_id=owner_id,
        inactive_days=inactive_days,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )

    return result


@admin_projects_router.get(
    "/storage",
    response_model=ProjectStorageListResponse,
    summary="プロジェクト別ストレージ使用量取得",
    description="""
    プロジェクト別ストレージ使用量を取得します。

    **権限**: システム管理者

    クエリパラメータ:
        - sort_by: ソート項目（storage/file_count）
        - limit: 取得件数
    """,
)
@handle_service_errors
async def get_storage_usage(
    _: RequireSystemAdminDep,
    service: ProjectsAdminServiceDep,
    current_user: CurrentUserAccountDep,
    sort_by: str = Query("storage", description="ソート項目"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> ProjectStorageListResponse:
    """プロジェクト別ストレージ使用量を取得します。"""
    logger.info(
        "プロジェクト別ストレージ使用量取得",
        user_id=str(current_user.id),
        sort_by=sort_by,
        action="get_storage_usage",
    )

    result = await service.get_storage_usage(
        sort_by=sort_by,
        limit=limit,
    )

    return result


@admin_projects_router.get(
    "/inactive",
    response_model=AdminProjectListResponse,
    summary="非アクティブプロジェクト一覧取得",
    description="""
    非アクティブプロジェクト一覧を取得します。

    **権限**: システム管理者

    クエリパラメータ:
        - inactive_days: 非アクティブ判定日数（デフォルト: 30日）
        - page: ページ番号
        - limit: 取得件数
    """,
)
@handle_service_errors
async def get_inactive_projects(
    _: RequireSystemAdminDep,
    service: ProjectsAdminServiceDep,
    current_user: CurrentUserAccountDep,
    inactive_days: int = Query(30, ge=1, description="非アクティブ日数"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
) -> AdminProjectListResponse:
    """非アクティブプロジェクト一覧を取得します。"""
    logger.info(
        "非アクティブプロジェクト一覧取得",
        user_id=str(current_user.id),
        inactive_days=inactive_days,
        page=page,
        action="get_inactive_projects",
    )

    result = await service.get_inactive_projects(
        inactive_days=inactive_days,
        page=page,
        limit=limit,
    )

    return result


@admin_projects_router.get(
    "/{project_id}",
    response_model=AdminProjectDetailResponse,
    summary="プロジェクト詳細取得（管理者ビュー）",
    description="""
    プロジェクト詳細を取得します（管理者ビュー）。

    **権限**: システム管理者
    """,
)
@handle_service_errors
async def get_project_detail(
    _: RequireSystemAdminDep,
    service: ProjectsAdminServiceDep,
    current_user: CurrentUserAccountDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
) -> AdminProjectDetailResponse:
    """プロジェクト詳細を取得します（管理者ビュー）。"""
    logger.info(
        "プロジェクト詳細取得",
        user_id=str(current_user.id),
        project_id=str(project_id),
        action="get_project_detail",
    )

    result = await service.get_project_detail(project_id)

    return result
