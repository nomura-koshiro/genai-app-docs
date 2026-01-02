"""課題マスタ管理APIエンドポイント。"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core import AdminIssueServiceDep, CurrentUserAccountDep
from app.core.decorators import handle_service_errors
from app.core.exceptions import AuthorizationError
from app.core.logging import get_logger
from app.schemas.admin.issue import (
    AnalysisIssueCreate,
    AnalysisIssueListResponse,
    AnalysisIssueResponse,
    AnalysisIssueUpdate,
)

logger = get_logger(__name__)

admin_issue_router = APIRouter()


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


@admin_issue_router.get(
    "/admin/issue",
    response_model=AnalysisIssueListResponse,
    summary="課題マスタ一覧取得",
    description="課題マスタ一覧を取得します（管理者専用）。",
)
@handle_service_errors
async def list_issues(
    issue_service: AdminIssueServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    validation_id: uuid.UUID | None = Query(None, description="検証マスタIDでフィルタ"),
) -> AnalysisIssueListResponse:
    """課題マスタ一覧を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "課題マスタ一覧取得",
        admin_user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        validation_id=str(validation_id) if validation_id else None,
    )

    return await issue_service.list_issues(skip=skip, limit=limit, validation_id=validation_id)


@admin_issue_router.get(
    "/admin/issue/{issue_id}",
    response_model=AnalysisIssueResponse,
    summary="課題マスタ詳細取得",
    description="課題マスタ詳細を取得します（管理者専用）。",
)
@handle_service_errors
async def get_issue(
    issue_id: uuid.UUID,
    issue_service: AdminIssueServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisIssueResponse:
    """課題マスタ詳細を取得します。"""
    _check_admin_role(current_user)

    logger.info(
        "課題マスタ詳細取得",
        admin_user_id=str(current_user.id),
        issue_id=str(issue_id),
    )

    return await issue_service.get_issue(issue_id)


@admin_issue_router.post(
    "/admin/issue",
    response_model=AnalysisIssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="課題マスタ作成",
    description="課題マスタを作成します（管理者専用）。",
)
@handle_service_errors
async def create_issue(
    issue_create: AnalysisIssueCreate,
    issue_service: AdminIssueServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisIssueResponse:
    """課題マスタを作成します。"""
    _check_admin_role(current_user)

    logger.info(
        "課題マスタ作成",
        admin_user_id=str(current_user.id),
        issue_data=issue_create.model_dump(),
    )

    return await issue_service.create_issue(issue_create)


@admin_issue_router.patch(
    "/admin/issue/{issue_id}",
    response_model=AnalysisIssueResponse,
    summary="課題マスタ更新",
    description="課題マスタを更新します（管理者専用）。",
)
@handle_service_errors
async def update_issue(
    issue_id: uuid.UUID,
    issue_update: AnalysisIssueUpdate,
    issue_service: AdminIssueServiceDep,
    current_user: CurrentUserAccountDep,
) -> AnalysisIssueResponse:
    """課題マスタを更新します。"""
    _check_admin_role(current_user)

    logger.info(
        "課題マスタ更新",
        admin_user_id=str(current_user.id),
        issue_id=str(issue_id),
        update_data=issue_update.model_dump(exclude_unset=True),
    )

    return await issue_service.update_issue(issue_id, issue_update)


@admin_issue_router.delete(
    "/admin/issue/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="課題マスタ削除",
    description="課題マスタを削除します（管理者専用）。",
)
@handle_service_errors
async def delete_issue(
    issue_id: uuid.UUID,
    issue_service: AdminIssueServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """課題マスタを削除します。"""
    _check_admin_role(current_user)

    logger.info(
        "課題マスタ削除",
        admin_user_id=str(current_user.id),
        issue_id=str(issue_id),
    )

    await issue_service.delete_issue(issue_id)
