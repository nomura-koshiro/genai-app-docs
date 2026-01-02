"""認可依存性（Authorization Dependencies）。

プロジェクトメンバーシップやロールベースの認可チェックを提供します。

依存性の種類:
    - ProjectMemberDep: プロジェクトメンバーであることを確認
    - ProjectManagerDep: PROJECT_MANAGER権限を確認
    - ProjectModeratorDep: PROJECT_MODERATOR以上の権限を確認

使用例:
    >>> @router.get("/project/{project_id}/resource")
    >>> async def get_resource(
    ...     project_id: uuid.UUID,
    ...     member: ProjectMemberDep,  # 自動的にメンバーシップ検証
    ... ):
    ...     # ここに到達 = メンバーであることが保証されている
    ...     return {"member_role": member.role}
"""

import uuid
from typing import Annotated

from fastapi import Depends, Path

from app.api.core.dependencies.auth import CurrentUserAccountDep
from app.api.core.dependencies.database import DatabaseDep
from app.core.exceptions import AuthorizationError
from app.core.logging import get_logger
from app.models import ProjectMember
from app.models.enums import ProjectRole
from app.repositories import ProjectMemberRepository

__all__ = [
    # 依存性型
    "ProjectMemberDep",
    "ProjectManagerDep",
    "ProjectModeratorDep",
    # ファクトリ関数
    "get_project_member",
    "get_project_manager",
    "get_project_moderator",
]

logger = get_logger(__name__)


async def get_project_member(
    project_id: Annotated[uuid.UUID, Path(description="プロジェクトID")],
    current_user: CurrentUserAccountDep,
    db: DatabaseDep,
) -> ProjectMember:
    """プロジェクトメンバーであることを確認し、メンバー情報を返します。

    この依存性を使用すると、エンドポイントは自動的にプロジェクトメンバーシップを検証します。
    メンバーでないユーザーはアクセスを拒否されます（403エラー）。

    Args:
        project_id: プロジェクトID（パスパラメータから自動取得）
        current_user: 認証済みユーザー（自動注入）
        db: データベースセッション（自動注入）

    Returns:
        ProjectMember: プロジェクトメンバー情報（ロール含む）

    Raises:
        AuthorizationError: ユーザーがプロジェクトメンバーでない場合
    """
    repository = ProjectMemberRepository(db)
    member = await repository.get_by_project_and_user(project_id, current_user.id)

    if not member:
        logger.warning(
            "project_member_access_denied",
            user_id=str(current_user.id),
            project_id=str(project_id),
        )
        raise AuthorizationError(
            "このプロジェクトへのアクセス権限がありません",
            details={"project_id": str(project_id)},
        )

    logger.debug(
        "project_member_verified",
        user_id=str(current_user.id),
        project_id=str(project_id),
        role=member.role.value,
    )

    return member


async def get_project_manager(
    member: Annotated[ProjectMember, Depends(get_project_member)],
) -> ProjectMember:
    """PROJECT_MANAGER権限を確認します。

    この依存性を使用すると、エンドポイントはPROJECT_MANAGERロールを検証します。
    PROJECT_MANAGER以外のメンバーはアクセスを拒否されます（403エラー）。

    Args:
        member: プロジェクトメンバー（get_project_memberから自動注入）

    Returns:
        ProjectMember: PROJECT_MANAGERメンバー情報

    Raises:
        AuthorizationError: ユーザーがPROJECT_MANAGERでない場合
    """
    if member.role != ProjectRole.PROJECT_MANAGER:
        logger.warning(
            "project_manager_access_denied",
            user_id=str(member.user_id),
            project_id=str(member.project_id),
            current_role=member.role.value,
        )
        raise AuthorizationError(
            "この操作にはPROJECT_MANAGER権限が必要です",
            details={
                "project_id": str(member.project_id),
                "required_role": "PROJECT_MANAGER",
                "current_role": member.role.value,
            },
        )

    return member


async def get_project_moderator(
    member: Annotated[ProjectMember, Depends(get_project_member)],
) -> ProjectMember:
    """PROJECT_MODERATOR以上の権限を確認します。

    この依存性を使用すると、エンドポイントはPROJECT_MODERATORまたはPROJECT_MANAGERロールを検証します。
    それ以外のメンバーはアクセスを拒否されます（403エラー）。

    Args:
        member: プロジェクトメンバー（get_project_memberから自動注入）

    Returns:
        ProjectMember: PROJECT_MODERATOR以上のメンバー情報

    Raises:
        AuthorizationError: ユーザーがPROJECT_MODERATOR以上でない場合
    """
    allowed_roles = {ProjectRole.PROJECT_MANAGER, ProjectRole.PROJECT_MODERATOR}

    if member.role not in allowed_roles:
        logger.warning(
            "project_moderator_access_denied",
            user_id=str(member.user_id),
            project_id=str(member.project_id),
            current_role=member.role.value,
        )
        raise AuthorizationError(
            "この操作にはPROJECT_MODERATORまたはPROJECT_MANAGER権限が必要です",
            details={
                "project_id": str(member.project_id),
                "required_role": "PROJECT_MODERATOR or PROJECT_MANAGER",
                "current_role": member.role.value,
            },
        )

    return member


# ================================================================================
# 依存性型エイリアス
# ================================================================================

ProjectMemberDep = Annotated[ProjectMember, Depends(get_project_member)]
"""プロジェクトメンバーの依存性型。

この依存性を使用すると、エンドポイントはプロジェクトメンバーシップを自動的に検証します。
メンバーでないユーザーはアクセスを拒否されます（403エラー）。

使用例:
    >>> @router.get("/project/{project_id}/sessions")
    >>> async def list_sessions(
    ...     project_id: uuid.UUID,
    ...     member: ProjectMemberDep,
    ... ):
    ...     # member.role でロールにアクセス可能
    ...     return {"role": member.role}
"""

ProjectManagerDep = Annotated[ProjectMember, Depends(get_project_manager)]
"""PROJECT_MANAGER権限の依存性型。

この依存性を使用すると、エンドポイントはPROJECT_MANAGERロールを自動的に検証します。
PROJECT_MANAGER以外のメンバーはアクセスを拒否されます（403エラー）。
"""

ProjectModeratorDep = Annotated[ProjectMember, Depends(get_project_moderator)]
"""PROJECT_MODERATOR以上の権限の依存性型。

この依存性を使用すると、エンドポイントはPROJECT_MODERATORまたはPROJECT_MANAGERロールを
自動的に検証します。それ以外のメンバーはアクセスを拒否されます（403エラー）。
"""
