"""ダミー数式マスタ管理APIエンドポイント。"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core import AdminDummyFormulaServiceDep, CurrentUserAccountDep
from app.core.decorators import handle_service_errors
from app.core.exceptions import AuthorizationError
from app.core.logging import get_logger
from app.schemas.admin.dummy_formula import AnalysisDummyFormulaListResponse
from app.schemas.analysis.analysis_template import (
    AnalysisDummyFormulaCreate,
    AnalysisDummyFormulaResponse,
    AnalysisDummyFormulaUpdate,
)

logger = get_logger(__name__)

admin_dummy_formula_router = APIRouter()


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


@admin_dummy_formula_router.get(
    "/admin/dummy-formula",
    response_model=AnalysisDummyFormulaListResponse,
    summary="ダミー数式マスタ一覧取得",
    description="ダミー数式マスタ一覧を取得します（管理者専用）。",
)
@handle_service_errors
async def list_dummy_formulas(
    dummy_formula_service: AdminDummyFormulaServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    issue_id: uuid.UUID | None = Query(None, description="課題マスタIDでフィルタ"),
) -> AnalysisDummyFormulaListResponse:
    """ダミー数式マスタ一覧を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミー数式マスタ一覧取得",
        admin_user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        issue_id=str(issue_id) if issue_id else None,
    )

    return await dummy_formula_service.list_formulas(skip=skip, limit=limit, issue_id=issue_id)


@admin_dummy_formula_router.get(
    "/admin/dummy-formula/{formula_id}",
    response_model=AnalysisDummyFormulaResponse,
    summary="ダミー数式マスタ詳細取得",
    description="ダミー数式マスタ詳細を取得します（管理者専用）。",
)
@handle_service_errors
async def get_dummy_formula(
    formula_id: uuid.UUID,
    dummy_formula_service: AdminDummyFormulaServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisDummyFormulaResponse:
    """ダミー数式マスタ詳細を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミー数式マスタ詳細取得",
        admin_user_id=str(current_user.id),
        formula_id=str(formula_id),
    )

    return await dummy_formula_service.get_formula(formula_id)


@admin_dummy_formula_router.post(
    "/admin/dummy-formula",
    response_model=AnalysisDummyFormulaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ダミー数式マスタ作成",
    description="ダミー数式マスタを作成します（管理者専用）。",
)
@handle_service_errors
async def create_dummy_formula(
    formula_create: AnalysisDummyFormulaCreate,
    dummy_formula_service: AdminDummyFormulaServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisDummyFormulaResponse:
    """ダミー数式マスタを作成します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミー数式マスタ作成",
        admin_user_id=str(current_user.id),
        formula_data=formula_create.model_dump(),
    )

    return await dummy_formula_service.create_formula(formula_create)


@admin_dummy_formula_router.patch(
    "/admin/dummy-formula/{formula_id}",
    response_model=AnalysisDummyFormulaResponse,
    summary="ダミー数式マスタ更新",
    description="ダミー数式マスタを更新します（管理者専用）。",
)
@handle_service_errors
async def update_dummy_formula(
    formula_id: uuid.UUID,
    formula_update: AnalysisDummyFormulaUpdate,
    dummy_formula_service: AdminDummyFormulaServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisDummyFormulaResponse:
    """ダミー数式マスタを更新します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミー数式マスタ更新",
        admin_user_id=str(current_user.id),
        formula_id=str(formula_id),
        update_data=formula_update.model_dump(exclude_unset=True),
    )

    return await dummy_formula_service.update_formula(formula_id, formula_update)


@admin_dummy_formula_router.delete(
    "/admin/dummy-formula/{formula_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ダミー数式マスタ削除",
    description="ダミー数式マスタを削除します（管理者専用）。",
)
@handle_service_errors
async def delete_dummy_formula(
    formula_id: uuid.UUID,
    dummy_formula_service: AdminDummyFormulaServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """ダミー数式マスタを削除します。"""
    _check_admin_role(current_user)

    logger.info(
        "ダミー数式マスタ削除",
        admin_user_id=str(current_user.id),
        formula_id=str(formula_id),
    )

    await dummy_formula_service.delete_formula(formula_id)
