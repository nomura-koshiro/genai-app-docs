"""Azure AD認証用プロジェクトメンバー管理APIエンドポイント。

このモジュールは、Azure AD認証に対応したプロジェクトメンバー管理のRESTful APIエンドポイントを定義します。
メンバーの追加・削除・ロール更新・退出、権限制御を提供します。

主な機能:
    - メンバー追加（POST /api/v1/project/{project_id}/member - PROJECT_MANAGER）
    - メンバー複数人追加（POST /api/v1/project/{project_id}/member/bulk - PROJECT_MANAGER）
    - メンバー一覧取得（GET /api/v1/project/{project_id}/member - メンバー以上）
    - ロール更新（PATCH /api/v1/project/{project_id}/member/{member_id} - PROJECT_MANAGER）
    - メンバー削除（DELETE /api/v1/project/{project_id}/member/{member_id} - PROJECT_MANAGER）
    - プロジェクト退出（DELETE /api/v1/project/{project_id}/member/me - 任意のメンバー）
    - 自分のロール取得（GET /api/v1/project/{project_id}/member/me - メンバー以上）

セキュリティ:
    - Azure AD Bearer認証（本番環境）
    - モック認証（開発環境）
    - プロジェクトレベルのロールベースアクセス制御（RBAC）

使用例:
    >>> # メンバー追加
    >>> POST /api/v1/project/{project_id}/member
    >>> Authorization: Bearer <Azure_AD_Token>
    >>> {
    ...     "user_id": "user-uuid",
    ...     "role": "member"
    ... }
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.core import CurrentUserAccountDep, ProjectMemberServiceDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.models import ProjectRole
from app.schemas import (
    ProjectMemberBulkCreate,
    ProjectMemberBulkResponse,
    ProjectMemberCreate,
    ProjectMemberDetailResponse,
    ProjectMemberListResponse,
    ProjectMemberUpdate,
    UserRoleResponse,
)

logger = get_logger(__name__)

project_members_router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@project_members_router.get(
    "/project/{project_id}/member",
    response_model=ProjectMemberListResponse,
    summary="プロジェクトメンバー一覧取得",
    description="""
    プロジェクトのメンバー一覧を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    クエリパラメータ:
        - skip: int - スキップ数（デフォルト: 0）
        - limit: int - 取得件数（デフォルト: 100）

    レスポンス:
        - ProjectMemberListResponse: プロジェクトメンバー一覧レスポンス
            - members (list[ProjectMemberDetailResponse]): メンバーリスト
                - id (uuid): メンバーシップID
                - project_id (uuid): プロジェクトID
                - user_id (uuid): ユーザーID
                - role (str): プロジェクトロール（project_manager/project_moderator/member/viewer）
                - joined_at (datetime): 参加日時
                - added_by (uuid): 追加者のユーザーID
                - user (UserAccountResponse): ユーザー情報
            - total (int): 総件数
            - project_id (uuid): プロジェクトID

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
@handle_service_errors
async def get_project_members(
    project_id: uuid.UUID,
    member_service: ProjectMemberServiceDep,
    current_user: CurrentUserAccountDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> ProjectMemberListResponse:
    """プロジェクトのメンバー一覧を取得します。"""
    logger.debug(
        "メンバー一覧取得リクエスト",
        project_id=str(project_id),
        requester_id=str(current_user.id),
        skip=skip,
        limit=limit,
        action="get_members",
    )

    members, total = await member_service.get_project_members(
        project_id=project_id,
        requester_id=current_user.id,
        skip=skip,
        limit=limit,
    )

    logger.debug(
        "メンバー一覧を取得しました",
        project_id=str(project_id),
        count=len(members),
        total=total,
    )

    return ProjectMemberListResponse(
        members=[ProjectMemberDetailResponse.model_validate(m) for m in members],
        total=total,
        project_id=project_id,
    )


@project_members_router.get(
    "/project/{project_id}/member/me",
    response_model=UserRoleResponse,
    summary="自分のロール取得",
    description="""
    プロジェクトにおける自分のロールを取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    レスポンス:
        - UserRoleResponse: ユーザーロール情報
            - project_id (uuid): プロジェクトID
            - user_id (uuid): ユーザーID
            - role (str): ロール
            - is_owner (bool): オーナーフラグ
            - is_admin (bool): 管理者フラグ

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
@handle_service_errors
async def get_my_role(
    project_id: uuid.UUID,
    member_service: ProjectMemberServiceDep,
    current_user: CurrentUserAccountDep,
) -> UserRoleResponse:
    """プロジェクトにおける自分のロールを取得します。"""
    logger.debug(
        "自分のロール取得リクエスト",
        project_id=str(project_id),
        user_id=str(current_user.id),
        action="get_my_role",
    )

    role = await member_service.get_user_role(
        project_id=project_id,
        user_id=current_user.id,
    )

    # ロールが見つからない場合はプロジェクトメンバーでない
    if role is None:
        logger.warning(
            "ユーザーはプロジェクトメンバーではありません",
            project_id=str(project_id),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトメンバーシップが見つかりません",
        )

    logger.debug(
        "ロール情報を取得しました",
        project_id=str(project_id),
        user_id=str(current_user.id),
        role=role.value,
    )

    # UserRoleResponseオブジェクトを構築
    is_manager = role == ProjectRole.PROJECT_MANAGER
    return UserRoleResponse(
        project_id=project_id,
        user_id=current_user.id,
        role=role,
        is_owner=is_manager,
        is_admin=is_manager,
    )


# ================================================================================
# POST Endpoints
# ================================================================================


@project_members_router.post(
    "/project/{project_id}/member",
    response_model=ProjectMemberDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクトメンバー追加",
    description="""
    プロジェクトにメンバーを追加します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    リクエストボディ:
        - ProjectMemberCreate: メンバー追加データ
            - user_id (uuid): 追加するユーザーID（必須）
            - role (str): プロジェクトロール（デフォルト: member）

    レスポンス:
        - ProjectMemberDetailResponse: プロジェクトメンバー詳細情報
            - id (uuid): メンバーシップID
            - project_id (uuid): プロジェクトID
            - user_id (uuid): ユーザーID
            - role (str): プロジェクトロール
            - joined_at (datetime): 参加日時
            - added_by (uuid): 追加者のユーザーID
            - user (UserAccountResponse): ユーザー情報

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 422: バリデーションエラー
    """,
)
@handle_service_errors
async def add_project_member(
    project_id: uuid.UUID,
    member_data: ProjectMemberCreate,
    member_service: ProjectMemberServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectMemberDetailResponse:
    """プロジェクトにメンバーを追加します。"""
    logger.info(
        "メンバー追加リクエスト",
        project_id=str(project_id),
        user_id=str(member_data.user_id),
        role=member_data.role.value,
        added_by=str(current_user.id),
        action="add_member",
    )

    member = await member_service.add_member(
        project_id=project_id,
        member_data=member_data,
        added_by=current_user.id,
    )

    logger.info(
        "メンバーを追加しました",
        member_id=str(member.id),
        project_id=str(project_id),
        user_id=str(member_data.user_id),
        role=member_data.role.value,
    )

    return ProjectMemberDetailResponse.model_validate(member)


@project_members_router.post(
    "/project/{project_id}/member/bulk",
    response_model=ProjectMemberBulkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクトメンバー複数人追加",
    description="""
    プロジェクトに複数のメンバーを一括追加します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    リクエストボディ:
        - ProjectMemberBulkCreate: メンバー一括追加データ
            - members (list[ProjectMemberCreate]): 追加するメンバーのリスト（最大100件）
                - user_id (uuid): 追加するユーザーID（必須）
                - role (str): プロジェクトロール（デフォルト: member）

    レスポンス:
        - ProjectMemberBulkResponse: メンバー一括追加結果
            - project_id (uuid): プロジェクトID
            - added (list[ProjectMemberDetailResponse]): 追加に成功したメンバーリスト
            - failed (list[ProjectMemberBulkError]): 追加に失敗したメンバーリスト
            - total_requested (int): リクエストされたメンバー数
            - total_added (int): 追加に成功したメンバー数
            - total_failed (int): 追加に失敗したメンバー数

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 422: バリデーションエラー
    """,
)
@handle_service_errors
async def add_project_members_bulk(
    project_id: uuid.UUID,
    bulk_data: ProjectMemberBulkCreate,
    member_service: ProjectMemberServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectMemberBulkResponse:
    """プロジェクトに複数のメンバーを一括追加します。"""
    logger.info(
        "メンバー一括追加リクエスト",
        project_id=str(project_id),
        member_count=len(bulk_data.members),
        added_by=str(current_user.id),
        action="add_members_bulk",
    )

    added_members, failed_members = await member_service.add_members_bulk(
        project_id=project_id,
        members_data=bulk_data.members,
        added_by=current_user.id,
    )

    logger.info(
        "メンバー一括追加完了",
        project_id=str(project_id),
        total_requested=len(bulk_data.members),
        total_added=len(added_members),
        total_failed=len(failed_members),
    )

    return ProjectMemberBulkResponse(
        project_id=project_id,
        added=[ProjectMemberDetailResponse.model_validate(m) for m in added_members],
        failed=failed_members,
        total_requested=len(bulk_data.members),
        total_added=len(added_members),
        total_failed=len(failed_members),
    )


# ================================================================================
# PATCH Endpoints
# ================================================================================


@project_members_router.patch(
    "/project/{project_id}/member/{member_id}",
    response_model=ProjectMemberDetailResponse,
    summary="メンバーロール更新",
    description="""
    メンバーのロールを更新します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - member_id: uuid - メンバーシップID（必須）

    リクエストボディ:
        - ProjectMemberUpdate: メンバーロール更新データ
            - role (str): 新しいプロジェクトロール（必須）

    レスポンス:
        - ProjectMemberDetailResponse: プロジェクトメンバー詳細情報
            - id (uuid): メンバーシップID
            - project_id (uuid): プロジェクトID
            - user_id (uuid): ユーザーID
            - role (str): プロジェクトロール
            - joined_at (datetime): 参加日時
            - added_by (uuid): 追加者のユーザーID
            - user (UserAccountResponse): ユーザー情報

    ステータスコード:
        - 200: 更新成功
        - 401: 認証されていない
        - 404: リソースが見つからない
    """,
)
@handle_service_errors
async def update_member_role(
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    update_data: ProjectMemberUpdate,
    member_service: ProjectMemberServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectMemberDetailResponse:
    """メンバーのロールを更新します。"""
    logger.info(
        "ロール更新リクエスト",
        project_id=str(project_id),
        member_id=str(member_id),
        new_role=update_data.role.value,
        requester_id=str(current_user.id),
        action="update_role",
    )

    updated_member = await member_service.update_member_role(
        member_id=member_id,
        new_role=update_data.role,
        requester_id=current_user.id,
    )

    logger.info(
        "ロールを更新しました",
        member_id=str(member_id),
        new_role=update_data.role.value,
    )

    return ProjectMemberDetailResponse.model_validate(updated_member)


# ================================================================================
# DELETE Endpoints
# ================================================================================


@project_members_router.delete(
    "/project/{project_id}/member/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="プロジェクト退出",
    description="""
    プロジェクトから退出します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    レスポンス:
        - None（204 No Content）

    ステータスコード:
        - 204: 退出成功
        - 401: 認証されていない
        - 404: メンバーシップが見つからない
        - 422: 最後のPROJECT_MANAGERは退出できない
    """,
)
@handle_service_errors
async def leave_project(
    project_id: uuid.UUID,
    member_service: ProjectMemberServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """プロジェクトから退出します。"""
    logger.info(
        "プロジェクト退出リクエスト",
        project_id=str(project_id),
        user_id=str(current_user.id),
        action="leave_project",
    )

    await member_service.leave_project(
        project_id=project_id,
        user_id=current_user.id,
    )

    logger.info(
        "プロジェクトから退出しました",
        project_id=str(project_id),
        user_id=str(current_user.id),
    )


@project_members_router.delete(
    "/project/{project_id}/member/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="メンバー削除",
    description="""
    プロジェクトからメンバーを削除します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - member_id: uuid - メンバーシップID（必須）

    レスポンス:
        - None（204 No Content）

    ステータスコード:
        - 204: 削除成功
        - 401: 認証されていない
        - 404: リソースが見つからない
    """,
)
@handle_service_errors
async def remove_member(
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    member_service: ProjectMemberServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """プロジェクトからメンバーを削除します。"""
    logger.info(
        "メンバー削除リクエスト",
        project_id=str(project_id),
        member_id=str(member_id),
        requester_id=str(current_user.id),
        action="remove_member",
    )

    await member_service.remove_member(
        member_id=member_id,
        requester_id=current_user.id,
    )

    logger.info(
        "メンバーを削除しました",
        member_id=str(member_id),
    )
