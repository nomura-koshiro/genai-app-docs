"""Azure AD認証用プロジェクトメンバー管理APIエンドポイント。

このモジュールは、Azure AD認証に対応したプロジェクトメンバー管理のRESTful APIエンドポイントを定義します。
メンバーの追加・削除・ロール更新・退出、権限制御を提供します。

主な機能:
    - メンバー追加（POST /api/v1/projects/{project_id}/members - PROJECT_MANAGER）
    - メンバー一覧取得（GET /api/v1/projects/{project_id}/members - メンバー以上）
    - ロール更新（PATCH /api/v1/projects/{project_id}/members/{member_id} - PROJECT_MANAGER）
    - メンバー削除（DELETE /api/v1/projects/{project_id}/members/{member_id} - PROJECT_MANAGER）
    - プロジェクト退出（DELETE /api/v1/projects/{project_id}/members/me - 任意のメンバー）
    - 自分のロール取得（GET /api/v1/projects/{project_id}/members/me - メンバー以上）

セキュリティ:
    - Azure AD Bearer認証（本番環境）
    - モック認証（開発環境）
    - プロジェクトレベルのロールベースアクセス制御（RBAC）

使用例:
    >>> # メンバー追加
    >>> POST /api/v1/projects/{project_id}/members
    >>> Authorization: Bearer <Azure_AD_Token>
    >>> {
    ...     "user_id": "user-uuid",
    ...     "role": "member"
    ... }
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.core import CurrentUserAzureDep, DatabaseDep
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
from app.services import ProjectMemberService

logger = get_logger(__name__)

project_members_router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@project_members_router.get(
    "",
    response_model=ProjectMemberListResponse,
    summary="プロジェクトメンバー一覧取得",
    description="""
    プロジェクトのメンバー一覧を取得します。

    **メンバー以上の権限が必要です。**

    - ユーザー情報付きで返されます
    - ページネーション対応

    クエリパラメータ:
        - skip: スキップするレコード数（デフォルト: 0）
        - limit: 取得する最大レコード数（デフォルト: 100、最大: 1000）
    """,
)
@handle_service_errors
async def get_project_members(
    project_id: uuid.UUID,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> ProjectMemberListResponse:
    """プロジェクトのメンバー一覧を取得します。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        db (AsyncSession): データベースセッション（自動注入）
        current_user (User): 認証済みユーザー（自動注入）
        skip (int): スキップするレコード数
        limit (int): 取得する最大レコード数

    Returns:
        ProjectMemberListResponse: メンバー一覧レスポンス

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: メンバーでない
            - 404: プロジェクトが見つからない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/projects/{project_id}/members?skip=0&limit=10
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "members": [
        ...         {
        ...             "id": "member-uuid",
        ...             "project_id": "project-uuid",
        ...             "user_id": "user-uuid",
        ...             "role": "project_manager",
        ...             "joined_at": "2024-01-15T10:30:00Z",
        ...             "added_by": null,
        ...             "user": {
        ...                 "id": "user-uuid",
        ...                 "email": "admin@example.com",
        ...                 "display_name": "Admin Name",
        ...                 ...
        ...             }
        ...         },
        ...         ...
        ...     ],
        ...     "total": 15,
        ...     "project_id": "project-uuid"
        ... }

    Note:
        - リクエスタがプロジェクトのメンバーである必要があります
    """
    logger.debug(
        "メンバー一覧取得リクエスト",
        project_id=str(project_id),
        requester_id=str(current_user.id),
        skip=skip,
        limit=limit,
        action="get_members",
    )

    member_service = ProjectMemberService(db)
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
    "/me",
    response_model=UserRoleResponse,
    summary="自分のロール取得",
    description="""
    プロジェクトにおける自分のロールを取得します。

    **メンバー以上の権限が必要です。**

    返されるデータ:
        - project_id: プロジェクトUUID
        - user_id: ユーザーUUID
        - role: プロジェクトロール
        - is_owner: PROJECT_MANAGER ロールかどうか（後方互換性のため維持）
        - is_admin: PROJECT_MANAGER ロールかどうか（後方互換性のため維持）
    """,
)
@handle_service_errors
async def get_my_role(
    project_id: uuid.UUID,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> UserRoleResponse:
    """プロジェクトにおける自分のロールを取得します。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        db (AsyncSession): データベースセッション（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        UserRoleResponse: ロール情報レスポンス

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 404: プロジェクトまたはメンバーシップが見つからない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/projects/{project_id}/members/me
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "project_id": "project-uuid",
        ...     "user_id": "user-uuid",
        ...     "role": "project_manager",
        ...     "is_owner": true,
        ...     "is_admin": true
        ... }

    Note:
        - プロジェクトのメンバーである必要があります
    """
    logger.debug(
        "自分のロール取得リクエスト",
        project_id=str(project_id),
        user_id=str(current_user.id),
        action="get_my_role",
    )

    member_service = ProjectMemberService(db)
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
    "",
    response_model=ProjectMemberDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクトメンバー追加",
    description="""
    プロジェクトに新しいメンバーを追加します。

    **PROJECT_MANAGERの権限が必要です。**

    - 重複するメンバーは追加できません

    リクエストボディ:
        - user_id: 追加するユーザーのUUID
        - role: プロジェクトロール（project_manager/member/viewer）
    """,
)
@handle_service_errors
async def add_project_member(
    project_id: uuid.UUID,
    member_data: ProjectMemberCreate,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> ProjectMemberDetailResponse:
    """プロジェクトにメンバーを追加します。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        member_data (ProjectMemberCreate): メンバー追加データ
        db (AsyncSession): データベースセッション（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        ProjectMemberDetailResponse: 追加されたメンバー情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: 権限不足
            - 404: プロジェクトまたはユーザーが見つからない
            - 409: メンバーが既に存在
            - 422: バリデーションエラー
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> POST /api/v1/projects/{project_id}/members
        >>> Authorization: Bearer <Azure_AD_Token>
        >>> {
        ...     "user_id": "user-uuid",
        ...     "role": "member"
        ... }
        >>>
        >>> # レスポンス (201 Created)
        >>> {
        ...     "id": "member-uuid",
        ...     "project_id": "project-uuid",
        ...     "user_id": "user-uuid",
        ...     "role": "member",
        ...     "joined_at": "2024-01-15T10:30:00Z",
        ...     "added_by": "admin-uuid",
        ...     "user": {
        ...         "id": "user-uuid",
        ...         "email": "user@example.com",
        ...         "display_name": "User Name",
        ...         ...
        ...     }
        ... }

    Note:
        - PROJECT_MANAGER の権限が必要
    """
    logger.info(
        "メンバー追加リクエスト",
        project_id=str(project_id),
        user_id=str(member_data.user_id),
        role=member_data.role.value,
        added_by=str(current_user.id),
        action="add_member",
    )

    member_service = ProjectMemberService(db)
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
    "/bulk",
    response_model=ProjectMemberBulkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクトメンバー複数人追加",
    description="""
    プロジェクトに複数のメンバーを一括追加します。

    **PROJECT_MANAGERの権限が必要です。**

    - 一部失敗しても成功したメンバーは追加されます
    - 最大100人まで一度に追加可能

    リクエストボディ:
        - members: 追加するメンバーのリスト
            - user_id: 追加するユーザーのUUID
            - role: プロジェクトロール（project_manager/member/viewer）

    レスポンス:
        - added: 追加に成功したメンバーリスト
        - failed: 追加に失敗したメンバーリスト（エラー理由付き）
        - total_requested: リクエストされたメンバー数
        - total_added: 追加に成功したメンバー数
        - total_failed: 追加に失敗したメンバー数
    """,
)
@handle_service_errors
async def add_project_members_bulk(
    project_id: uuid.UUID,
    bulk_data: ProjectMemberBulkCreate,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> ProjectMemberBulkResponse:
    """プロジェクトに複数のメンバーを一括追加します。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        bulk_data (ProjectMemberBulkCreate): 一括追加データ
        db (AsyncSession): データベースセッション（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        ProjectMemberBulkResponse: 一括追加レスポンス

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: 権限不足
            - 404: プロジェクトが見つからない
            - 422: バリデーションエラー
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> POST /api/v1/projects/{project_id}/members/bulk
        >>> Authorization: Bearer <Azure_AD_Token>
        >>> {
        ...     "members": [
        ...         {"user_id": "user1-uuid", "role": "member"},
        ...         {"user_id": "user2-uuid", "role": "viewer"}
        ...     ]
        ... }
        >>>
        >>> # レスポンス (201 Created)
        >>> {
        ...     "project_id": "project-uuid",
        ...     "added": [
        ...         {
        ...             "id": "member1-uuid",
        ...             "project_id": "project-uuid",
        ...             "user_id": "user1-uuid",
        ...             "role": "member",
        ...             "joined_at": "2024-01-15T10:30:00Z",
        ...             "added_by": "admin-uuid",
        ...             "user": { ... }
        ...         }
        ...     ],
        ...     "failed": [
        ...         {
        ...             "user_id": "user2-uuid",
        ...             "role": "viewer",
        ...             "error": "ユーザーが見つかりません"
        ...         }
        ...     ],
        ...     "total_requested": 2,
        ...     "total_added": 1,
        ...     "total_failed": 1
        ... }

    Note:
        - PROJECT_MANAGER の権限が必要
        - 一部失敗しても成功したメンバーは追加されます
    """
    logger.info(
        "メンバー一括追加リクエスト",
        project_id=str(project_id),
        member_count=len(bulk_data.members),
        added_by=str(current_user.id),
        action="add_members_bulk",
    )

    member_service = ProjectMemberService(db)
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
    "/{member_id}",
    response_model=ProjectMemberDetailResponse,
    summary="メンバーロール更新",
    description="""
    プロジェクトメンバーのロールを更新します。

    **PROJECT_MANAGER の権限が必要です。**

    - 最後の PROJECT_MANAGER は降格できません

    リクエストボディ:
        - role: 新しいプロジェクトロール
    """,
)
@handle_service_errors
async def update_member_role(
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    update_data: ProjectMemberUpdate,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> ProjectMemberDetailResponse:
    """メンバーのロールを更新します。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        member_id (uuid.UUID): メンバーシップのUUID
        update_data (ProjectMemberUpdate): ロール更新データ
        db (AsyncSession): データベースセッション（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        ProjectMemberDetailResponse: 更新されたメンバー情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: 権限不足
            - 404: メンバーが見つからない
            - 422: バリデーションエラー（最後のPROJECT_MANAGER降格）
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> PATCH /api/v1/projects/{project_id}/members/{member_id}
        >>> Authorization: Bearer <Azure_AD_Token>
        >>> {
        ...     "role": "member"
        ... }
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "id": "member-uuid",
        ...     "project_id": "project-uuid",
        ...     "user_id": "user-uuid",
        ...     "role": "member",
        ...     "joined_at": "2024-01-15T10:30:00Z",
        ...     "added_by": "admin-uuid",
        ...     "user": { ... }
        ... }

    Note:
        - PROJECT_MANAGER のみが実行可能
    """
    logger.info(
        "ロール更新リクエスト",
        project_id=str(project_id),
        member_id=str(member_id),
        new_role=update_data.role.value,
        requester_id=str(current_user.id),
        action="update_role",
    )

    member_service = ProjectMemberService(db)
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
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="メンバー削除",
    description="""
    プロジェクトからメンバーを削除します。

    **PROJECT_MANAGER の権限が必要です。**

    - 自分自身は削除できません（プロジェクト退出を使用）
    - 最後の PROJECT_MANAGER は削除できません
    """,
)
@handle_service_errors
async def remove_member(
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> None:
    """プロジェクトからメンバーを削除します。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        member_id (uuid.UUID): メンバーシップのUUID
        db (AsyncSession): データベースセッション（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: 権限不足
            - 404: メンバーが見つからない
            - 422: バリデーションエラー（自分自身削除、最後のPROJECT_MANAGER削除）
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> DELETE /api/v1/projects/{project_id}/members/{member_id}
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (204 No Content)

    Note:
        - PROJECT_MANAGER のみが実行可能
        - 自分自身は削除できません
    """
    logger.info(
        "メンバー削除リクエスト",
        project_id=str(project_id),
        member_id=str(member_id),
        requester_id=str(current_user.id),
        action="remove_member",
    )

    member_service = ProjectMemberService(db)
    await member_service.remove_member(
        member_id=member_id,
        requester_id=current_user.id,
    )

    logger.info(
        "メンバーを削除しました",
        member_id=str(member_id),
    )


@project_members_router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="プロジェクト退出",
    description="""
    プロジェクトから自分自身を退出します。

    **任意のメンバーが実行可能です。**

    - 最後の PROJECT_MANAGER は退出できません
    """,
)
@handle_service_errors
async def leave_project(
    project_id: uuid.UUID,
    db: DatabaseDep,
    current_user: CurrentUserAzureDep,
) -> None:
    """プロジェクトから退出します。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        db (AsyncSession): データベースセッション（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 404: メンバーシップが見つからない
            - 422: バリデーションエラー（最後のPROJECT_MANAGER退出）
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> DELETE /api/v1/projects/{project_id}/members/me
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (204 No Content)

    Note:
        - 最後の PROJECT_MANAGER は退出できません
    """
    logger.info(
        "プロジェクト退出リクエスト",
        project_id=str(project_id),
        user_id=str(current_user.id),
        action="leave_project",
    )

    member_service = ProjectMemberService(db)
    await member_service.leave_project(
        project_id=project_id,
        user_id=current_user.id,
    )

    logger.info(
        "プロジェクトから退出しました",
        project_id=str(project_id),
        user_id=str(current_user.id),
    )
