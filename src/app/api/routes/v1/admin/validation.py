"""検証マスタ管理APIエンドポイント。"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core import AdminValidationServiceDep, CurrentUserAccountDep
from app.core.decorators import handle_service_errors
from app.core.exceptions import AuthorizationError
from app.core.logging import get_logger
from app.schemas.admin.validation import (
    AnalysisValidationCreate,
    AnalysisValidationListResponse,
    AnalysisValidationResponse,
    AnalysisValidationUpdate,
)

logger = get_logger(__name__)

admin_validation_router = APIRouter()


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


@admin_validation_router.get(
    "/admin/validation",
    response_model=AnalysisValidationListResponse,
    summary="検証マスタ一覧取得",
    description="検証マスタ一覧を取得します（管理者専用）。",
)
@handle_service_errors
async def list_validations(
    validation_service: AdminValidationServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
) -> AnalysisValidationListResponse:
    """検証マスタ一覧を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "検証マスタ一覧取得",
        admin_user_id=str(current_user.id),
        skip=skip,
        limit=limit,
    )

    return await validation_service.list_validations(skip=skip, limit=limit)


@admin_validation_router.get(
    "/admin/validation/{validation_id}",
    response_model=AnalysisValidationResponse,
    summary="検証マスタ詳細取得",
    description="検証マスタ詳細を取得します（管理者専用）。",
)
@handle_service_errors
async def get_validation(
    validation_id: uuid.UUID,
    validation_service: AdminValidationServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisValidationResponse:
    """検証マスタ詳細を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "検証マスタ詳細取得",
        admin_user_id=str(current_user.id),
        validation_id=str(validation_id),
    )

    return await validation_service.get_validation(validation_id)


@admin_validation_router.post(
    "/admin/validation",
    response_model=AnalysisValidationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="検証マスタ作成",
    description="検証マスタを作成します（管理者専用）。",
)
@handle_service_errors
async def create_validation(
    validation_create: AnalysisValidationCreate,
    validation_service: AdminValidationServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisValidationResponse:
    """検証マスタを作成します。"""
    _check_admin_role(current_user)

    logger.info(
        "検証マスタ作成",
        admin_user_id=str(current_user.id),
        validation_data=validation_create.model_dump(),
    )

    return await validation_service.create_validation(validation_create)


@admin_validation_router.patch(
    "/admin/validation/{validation_id}",
    response_model=AnalysisValidationResponse,
    summary="検証マスタ更新",
    description="検証マスタを更新します（管理者専用）。",
)
@handle_service_errors
async def update_validation(
    validation_id: uuid.UUID,
    validation_update: AnalysisValidationUpdate,
    validation_service: AdminValidationServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisValidationResponse:
    """検証マスタを更新します。"""
    _check_admin_role(current_user)

    logger.info(
        "検証マスタ更新",
        admin_user_id=str(current_user.id),
        validation_id=str(validation_id),
        update_data=validation_update.model_dump(exclude_unset=True),
    )

    return await validation_service.update_validation(validation_id, validation_update)


@admin_validation_router.delete(
    "/admin/validation/{validation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="検証マスタ削除",
    description="検証マスタを削除します（管理者専用）。",
)
@handle_service_errors
async def delete_validation(
    validation_id: uuid.UUID,
    validation_service: AdminValidationServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """検証マスタを削除します。"""
    _check_admin_role(current_user)

    logger.info(
        "検証マスタ削除",
        admin_user_id=str(current_user.id),
        validation_id=str(validation_id),
    )

    await validation_service.delete_validation(validation_id)
