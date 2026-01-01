"""カテゴリマスタ管理APIエンドポイント。"""

from fastapi import APIRouter, Query, status

from app.api.core import AdminCategoryServiceDep, CurrentUserAccountDep
from app.api.decorators import handle_service_errors
from app.core.exceptions import AuthorizationError
from app.core.logging import get_logger
from app.schemas.admin.category import (
    DriverTreeCategoryCreate,
    DriverTreeCategoryListResponse,
    DriverTreeCategoryResponse,
    DriverTreeCategoryUpdate,
)

logger = get_logger(__name__)

admin_category_router = APIRouter()


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


@admin_category_router.get(
    "/admin/category",
    response_model=DriverTreeCategoryListResponse,
    summary="カテゴリマスタ一覧取得",
    description="カテゴリマスタ一覧を取得します（管理者専用）。",
)
@handle_service_errors
async def list_categories(
    category_service: AdminCategoryServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
) -> DriverTreeCategoryListResponse:
    """カテゴリマスタ一覧を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "カテゴリマスタ一覧取得",
        admin_user_id=str(current_user.id),
        skip=skip,
        limit=limit,
    )

    return await category_service.list_categories(skip=skip, limit=limit)


@admin_category_router.get(
    "/admin/category/{category_id}",
    response_model=DriverTreeCategoryResponse,
    summary="カテゴリマスタ詳細取得",
    description="カテゴリマスタ詳細を取得します（管理者専用）。",
)
@handle_service_errors
async def get_category(
    category_id: int,
    category_service: AdminCategoryServiceDep,
    current_user: CurrentUserAccountDep,
) -> DriverTreeCategoryResponse:
    """カテゴリマスタ詳細を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "カテゴリマスタ詳細取得",
        admin_user_id=str(current_user.id),
        category_id=category_id,
    )

    return await category_service.get_category(category_id)


@admin_category_router.post(
    "/admin/category",
    response_model=DriverTreeCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="カテゴリマスタ作成",
    description="カテゴリマスタを作成します（管理者専用）。",
)
@handle_service_errors
async def create_category(
    category_create: DriverTreeCategoryCreate,
    category_service: AdminCategoryServiceDep,
    current_user: CurrentUserAccountDep,
) -> DriverTreeCategoryResponse:
    """カテゴリマスタを作成します。"""
    _check_admin_role(current_user)

    logger.info(
        "カテゴリマスタ作成",
        admin_user_id=str(current_user.id),
        category_data=category_create.model_dump(),
    )

    return await category_service.create_category(category_create)


@admin_category_router.patch(
    "/admin/category/{category_id}",
    response_model=DriverTreeCategoryResponse,
    summary="カテゴリマスタ更新",
    description="カテゴリマスタを更新します（管理者専用）。",
)
@handle_service_errors
async def update_category(
    category_id: int,
    category_update: DriverTreeCategoryUpdate,
    category_service: AdminCategoryServiceDep,
    current_user: CurrentUserAccountDep,
) -> DriverTreeCategoryResponse:
    """カテゴリマスタを更新します。"""
    _check_admin_role(current_user)

    logger.info(
        "カテゴリマスタ更新",
        admin_user_id=str(current_user.id),
        category_id=category_id,
        update_data=category_update.model_dump(exclude_unset=True),
    )

    return await category_service.update_category(category_id, category_update)


@admin_category_router.delete(
    "/admin/category/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="カテゴリマスタ削除",
    description="カテゴリマスタを削除します（管理者専用）。",
)
@handle_service_errors
async def delete_category(
    category_id: int,
    category_service: AdminCategoryServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """カテゴリマスタを削除します。"""
    _check_admin_role(current_user)

    logger.info(
        "カテゴリマスタ削除",
        admin_user_id=str(current_user.id),
        category_id=category_id,
    )

    await category_service.delete_category(category_id)
