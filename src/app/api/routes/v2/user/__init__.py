"""ユーザーAPI v2エンドポイント。

パス変更: /user_account → /user
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.core import CurrentUserAccountDep, RoleHistoryServiceDep, UserAccountServiceDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.user_account import (
    RoleHistoryListResponse,
    UserAccountListResponse,
    UserAccountResponse,
    UserAccountRoleUpdate,
    UserAccountUpdate,
)

logger = get_logger(__name__)

user_router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@user_router.get(
    "/user",
    response_model=UserAccountListResponse,
    summary="ユーザー一覧取得",
    description="システム内のユーザー一覧を取得します。",
)
@handle_service_errors
async def list_users(
    current_user: CurrentUserAccountDep,
    user_service: UserAccountServiceDep,
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    is_active: bool | None = Query(None, description="アクティブフラグフィルタ"),
) -> UserAccountListResponse:
    """ユーザー一覧を取得します。"""
    logger.info(f"ユーザー一覧取得: user_id={current_user.id}")
    return await user_service.list_users(skip=skip, limit=limit, is_active=is_active)


@user_router.get(
    "/user/me",
    response_model=UserAccountResponse,
    summary="自分のユーザー情報取得",
    description="現在ログイン中のユーザー情報を取得します。",
)
@handle_service_errors
async def get_current_user(
    current_user: CurrentUserAccountDep,
) -> UserAccountResponse:
    """現在のユーザー情報を取得します。"""
    logger.info(f"自分のユーザー情報取得: user_id={current_user.id}")
    return UserAccountResponse.model_validate(current_user)


@user_router.get(
    "/user/{user_id}",
    response_model=UserAccountResponse,
    summary="ユーザー詳細取得",
    description="指定されたユーザーの詳細情報を取得します。",
)
@handle_service_errors
async def get_user(
    current_user: CurrentUserAccountDep,
    user_service: UserAccountServiceDep,
    user_id: uuid.UUID = Path(..., description="ユーザーID"),
) -> UserAccountResponse:
    """ユーザー詳細を取得します。"""
    logger.info(f"ユーザー詳細取得: user_id={user_id}, by={current_user.id}")
    return await user_service.get_user(user_id)


# ================================================================================
# PATCH Endpoints
# ================================================================================


@user_router.patch(
    "/user/me",
    response_model=UserAccountResponse,
    summary="自分のユーザー情報更新",
    description="現在ログイン中のユーザー情報を更新します。",
)
@handle_service_errors
async def update_current_user(
    current_user: CurrentUserAccountDep,
    user_service: UserAccountServiceDep,
    user_update: UserAccountUpdate,
) -> UserAccountResponse:
    """現在のユーザー情報を更新します。"""
    logger.info(f"自分のユーザー情報更新: user_id={current_user.id}")
    return await user_service.update_user(current_user.id, user_update)


@user_router.patch(
    "/user/{user_id}/activate",
    response_model=UserAccountResponse,
    summary="ユーザー有効化",
    description="指定されたユーザーを有効化します（管理者のみ）。",
)
@handle_service_errors
async def activate_user(
    current_user: CurrentUserAccountDep,
    user_service: UserAccountServiceDep,
    user_id: uuid.UUID = Path(..., description="ユーザーID"),
) -> UserAccountResponse:
    """ユーザーを有効化します。"""
    logger.info(f"ユーザー有効化: user_id={user_id}, by={current_user.id}")
    return await user_service.activate_user(user_id)


@user_router.patch(
    "/user/{user_id}/deactivate",
    response_model=UserAccountResponse,
    summary="ユーザー無効化",
    description="指定されたユーザーを無効化します（管理者のみ）。",
)
@handle_service_errors
async def deactivate_user(
    current_user: CurrentUserAccountDep,
    user_service: UserAccountServiceDep,
    user_id: uuid.UUID = Path(..., description="ユーザーID"),
) -> UserAccountResponse:
    """ユーザーを無効化します。"""
    logger.info(f"ユーザー無効化: user_id={user_id}, by={current_user.id}")
    return await user_service.deactivate_user(user_id)


# ================================================================================
# PUT Endpoints
# ================================================================================


@user_router.put(
    "/user/{user_id}/role",
    response_model=UserAccountResponse,
    summary="ユーザーロール更新",
    description="指定されたユーザーのシステムロールを更新します（管理者のみ）。",
)
@handle_service_errors
async def update_user_role(
    current_user: CurrentUserAccountDep,
    user_service: UserAccountServiceDep,
    user_id: uuid.UUID = Path(..., description="ユーザーID"),
    role_update: UserAccountRoleUpdate = ...,
) -> UserAccountResponse:
    """ユーザーロールを更新します。"""
    logger.info(f"ユーザーロール更新: user_id={user_id}, by={current_user.id}")
    return await user_service.update_user_role(user_id, role_update)


# ================================================================================
# DELETE Endpoints
# ================================================================================


@user_router.delete(
    "/user/{user_id}",
    status_code=204,
    summary="ユーザー削除",
    description="指定されたユーザーを削除します（管理者のみ）。",
)
@handle_service_errors
async def delete_user(
    current_user: CurrentUserAccountDep,
    user_service: UserAccountServiceDep,
    user_id: uuid.UUID = Path(..., description="ユーザーID"),
) -> None:
    """ユーザーを削除します。"""
    logger.info(f"ユーザー削除: user_id={user_id}, by={current_user.id}")
    await user_service.delete_user(user_id)


# ================================================================================
# Role History Endpoints
# ================================================================================


@user_router.get(
    "/user/{user_id}/role-history",
    response_model=RoleHistoryListResponse,
    summary="ユーザーロール履歴取得",
    description="指定されたユーザーのロール変更履歴を取得します。",
)
@handle_service_errors
async def get_user_role_history(
    current_user: CurrentUserAccountDep,
    role_history_service: RoleHistoryServiceDep,
    user_id: uuid.UUID = Path(..., description="ユーザーID"),
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(50, ge=1, le=200, description="取得件数"),
) -> RoleHistoryListResponse:
    """ユーザーのロール履歴を取得します。"""
    logger.info(f"ロール履歴取得: user_id={user_id}, by={current_user.id}")
    return await role_history_service.get_user_role_history(user_id, skip, limit)


__all__ = ["user_router"]
