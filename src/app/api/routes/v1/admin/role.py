"""ロール一覧APIエンドポイント。

システムロールおよびプロジェクトロールの一覧を取得するエンドポイントを提供します。
"""

from fastapi import APIRouter, status

from app.api.core import CurrentUserAccountDep
from app.core.logging import get_logger
from app.models.enums import ProjectRole, SystemUserRole
from app.schemas.admin import AllRolesResponse, RoleInfo

logger = get_logger(__name__)

admin_role_router = APIRouter()


# システムロールの定義
SYSTEM_ROLES = [
    RoleInfo(
        value=SystemUserRole.SYSTEM_ADMIN.value,
        label="システム管理者",
        description="システム全体の管理権限を持ちます。全プロジェクトへのアクセス、システム設定の変更が可能です。",
    ),
    RoleInfo(
        value=SystemUserRole.USER.value,
        label="一般ユーザー",
        description="デフォルトのロールです。プロジェクト単位でアクセス権限が管理されます。",
    ),
]

# プロジェクトロールの定義
PROJECT_ROLES = [
    RoleInfo(
        value=ProjectRole.PROJECT_MANAGER.value,
        label="プロジェクトマネージャー",
        description="プロジェクトの最高権限を持ちます。削除、設定変更、全メンバー管理が可能です。",
    ),
    RoleInfo(
        value=ProjectRole.PROJECT_MODERATOR.value,
        label="権限管理者",
        description="メンバー管理を担当します。メンバーの追加・削除・ロール変更（一部）が可能です。",
    ),
    RoleInfo(
        value=ProjectRole.MEMBER.value,
        label="メンバー",
        description="一般メンバーです。ファイルのアップロード・ダウンロード、プロジェクト内の編集が可能です。",
    ),
    RoleInfo(
        value=ProjectRole.VIEWER.value,
        label="閲覧者",
        description="閲覧のみ可能です。ファイルの閲覧・ダウンロードができます。",
    ),
]


@admin_role_router.get(
    "/admin/role",
    response_model=AllRolesResponse,
    status_code=status.HTTP_200_OK,
    summary="ロール一覧取得",
    description="""
    システムロールおよびプロジェクトロールの一覧を取得します。

    **認証が必要です。**

    レスポンス:
        - AllRolesResponse: 全ロール一覧
            - system_roles (list): システムロール一覧
                - value (str): ロール値
                - label (str): 表示名
                - description (str): ロールの説明
            - project_roles (list): プロジェクトロール一覧
                - value (str): ロール値
                - label (str): 表示名
                - description (str): ロールの説明

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
async def get_roles(
    current_user: CurrentUserAccountDep,
) -> AllRolesResponse:
    """システムロールおよびプロジェクトロールの一覧を取得します。"""
    logger.info(
        "ロール一覧取得リクエスト",
        user_id=str(current_user.id),
        action="get_roles",
    )

    return AllRolesResponse(
        system_roles=SYSTEM_ROLES,
        project_roles=PROJECT_ROLES,
    )
