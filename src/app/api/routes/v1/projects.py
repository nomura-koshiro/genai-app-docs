"""Azure AD認証用プロジェクト管理APIエンドポイント。

このモジュールは、Azure AD認証に対応したプロジェクト管理のRESTful APIエンドポイントを定義します。
プロジェクトのCRUD操作、メンバーシップ管理、権限制御を提供します。

主な機能:
    - プロジェクト作成（POST /api/v1/projects - 認証必須、自動的にOWNERとして追加）
    - プロジェクト一覧取得（GET /api/v1/projects - 自分がメンバーのプロジェクトのみ）
    - プロジェクト詳細取得（GET /api/v1/projects/{project_id} - メンバーのみ）
    - プロジェクトコード検索（GET /api/v1/projects/code/{code} - メンバーのみ）
    - プロジェクト更新（PATCH /api/v1/projects/{project_id} - OWNER/ADMINのみ）
    - プロジェクト削除（DELETE /api/v1/projects/{project_id} - OWNERのみ）

セキュリティ:
    - Azure AD Bearer認証（本番環境）
    - モック認証（開発環境）
    - プロジェクトレベルのロールベースアクセス制御（RBAC）

使用例:
    >>> # プロジェクト作成
    >>> POST /api/v1/projects
    >>> Authorization: Bearer <Azure_AD_Token>
    >>> {
    ...     "name": "AI Development Project",
    ...     "code": "AI-001",
    ...     "description": "Project for AI model development"
    ... }
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core import CurrentUserAzureDep, ProjectServiceDep
from app.api.decorators import handle_service_errors
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクト作成",
    description="""
    新しいプロジェクトを作成します。

    **認証が必要です。**

    - 作成者は自動的にOWNERロールとしてプロジェクトメンバーに追加されます
    - プロジェクトコードは一意である必要があります

    リクエストボディ:
        - name: プロジェクト名（最大255文字）
        - code: プロジェクトコード（最大50文字、一意）
        - description: プロジェクト説明（オプション）
    """,
)
@handle_service_errors
async def create_project(
    project_data: ProjectCreate,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAzureDep,
) -> ProjectResponse:
    """プロジェクトを作成します。

    Args:
        project_data (ProjectCreate): プロジェクト作成データ
        project_service (ProjectService): プロジェクトサービス（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        ProjectResponse: 作成されたプロジェクト情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 409: プロジェクトコード重複
            - 422: バリデーションエラー
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> POST /api/v1/projects
        >>> Authorization: Bearer <Azure_AD_Token>
        >>> {
        ...     "name": "AI Project",
        ...     "code": "AI-001",
        ...     "description": "AI development project"
        ... }
        >>>
        >>> # レスポンス (201 Created)
        >>> {
        ...     "id": "12345678-1234-1234-1234-123456789abc",
        ...     "name": "AI Project",
        ...     "code": "AI-001",
        ...     "description": "AI development project",
        ...     "is_active": true,
        ...     "created_by": "87654321-4321-4321-4321-cba987654321",
        ...     "created_at": "2024-01-15T10:30:00Z",
        ...     "updated_at": "2024-01-15T10:30:00Z"
        ... }

    Note:
        - 作成者は自動的にOWNERとしてプロジェクトメンバーに追加されます
        - プロジェクトコードは一意である必要があります（重複チェック実施）
    """
    logger.info(
        "プロジェクト作成リクエスト",
        user_id=str(current_user.id),
        email=current_user.email,
        project_code=project_data.code,
        action="create_project",
    )

    project = await project_service.create_project(
        project_data=project_data,
        creator_id=current_user.id,
    )

    logger.info(
        "プロジェクトを作成しました",
        project_id=str(project.id),
        project_code=project.code,
        user_id=str(current_user.id),
    )

    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="プロジェクト一覧取得",
    description="""
    認証されたユーザーが所属するプロジェクトの一覧を取得します。

    **認証が必要です。**

    - 自分がメンバーとして所属するプロジェクトのみ表示されます
    - ロール（OWNER/ADMIN/MEMBER/VIEWER）に関係なく全て取得されます

    クエリパラメータ:
        - skip: スキップするレコード数（デフォルト: 0）
        - limit: 取得する最大レコード数（デフォルト: 100、最大: 1000）
        - is_active: アクティブフラグフィルタ（オプション）
    """,
)
@handle_service_errors
async def list_projects(
    project_service: ProjectServiceDep,
    current_user: CurrentUserAzureDep,
    skip: int = Query(0, ge=0, description="スキップするレコード数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大レコード数"),
    is_active: bool | None = Query(None, description="アクティブフラグフィルタ"),
) -> list[ProjectResponse]:
    """プロジェクト一覧を取得します（ユーザーが所属するプロジェクトのみ）。

    Args:
        project_service (ProjectService): プロジェクトサービス（自動注入）
        current_user (User): 認証済みユーザー（自動注入）
        skip (int): スキップするレコード数
        limit (int): 取得する最大レコード数
        is_active (bool | None): アクティブフラグフィルタ

    Returns:
        list[ProjectResponse]: プロジェクト一覧

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/projects?skip=0&limit=10&is_active=true
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (200 OK)
        >>> [
        ...     {
        ...         "id": "12345678-1234-1234-1234-123456789abc",
        ...         "name": "AI Project",
        ...         "code": "AI-001",
        ...         "description": "AI development project",
        ...         "is_active": true,
        ...         "created_by": "87654321-4321-4321-4321-cba987654321",
        ...         "created_at": "2024-01-15T10:30:00Z",
        ...         "updated_at": "2024-01-15T10:30:00Z"
        ...     }
        ... ]

    Note:
        - 自分がメンバーとして所属するプロジェクトのみ表示されます
        - ページネーションを使用して効率的にデータを取得できます
    """
    logger.info(
        "プロジェクト一覧取得",
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        is_active=is_active,
        action="list_projects",
    )

    projects = await project_service.list_user_projects(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )

    logger.info(
        "プロジェクト一覧を取得しました",
        user_id=str(current_user.id),
        count=len(projects),
    )

    return [ProjectResponse.model_validate(project) for project in projects]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="プロジェクト詳細取得",
    description="""
    指定されたIDのプロジェクト情報を取得します。

    **認証が必要です。**
    **プロジェクトメンバーのみアクセス可能です。**

    パスパラメータ:
        - project_id: プロジェクトID（UUID形式）
    """,
)
@handle_service_errors
async def get_project(
    project_id: uuid.UUID,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAzureDep,
) -> ProjectResponse:
    """プロジェクト情報を取得します（メンバーのみ）。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        project_service (ProjectService): プロジェクトサービス（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        ProjectResponse: プロジェクト情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: プロジェクトが見つからない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/projects/12345678-1234-1234-1234-123456789abc
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "id": "12345678-1234-1234-1234-123456789abc",
        ...     "name": "AI Project",
        ...     "code": "AI-001",
        ...     "description": "AI development project",
        ...     "is_active": true,
        ...     "created_by": "87654321-4321-4321-4321-cba987654321",
        ...     "created_at": "2024-01-15T10:30:00Z",
        ...     "updated_at": "2024-01-15T10:30:00Z"
        ... }

    Note:
        - プロジェクトメンバーのみアクセス可能です
        - ロール（OWNER/ADMIN/MEMBER/VIEWER）に関係なくアクセスできます
    """
    logger.info(
        "プロジェクト詳細取得",
        user_id=str(current_user.id),
        project_id=str(project_id),
        action="get_project",
    )

    # プロジェクト取得
    project = await project_service.get_project(project_id)
    if not project:
        logger.warning(
            "プロジェクトが見つかりません",
            user_id=str(current_user.id),
            project_id=str(project_id),
        )
        raise NotFoundError(
            "プロジェクトが見つかりません",
            details={"project_id": str(project_id)},
        )

    # アクセス権チェック
    has_access = await project_service.check_user_access(
        project_id=project_id,
        user_id=current_user.id,
    )
    if not has_access:
        logger.warning(
            "プロジェクトへのアクセス権がありません",
            user_id=str(current_user.id),
            project_id=str(project_id),
        )
        raise AuthorizationError(
            "このプロジェクトへのアクセス権限がありません",
            details={"project_id": str(project_id)},
        )

    logger.info(
        "プロジェクト詳細を取得しました",
        user_id=str(current_user.id),
        project_id=str(project.id),
        project_code=project.code,
    )

    return ProjectResponse.model_validate(project)


@router.get(
    "/code/{code}",
    response_model=ProjectResponse,
    summary="プロジェクトコード検索",
    description="""
    指定されたコードのプロジェクト情報を取得します。

    **認証が必要です。**
    **プロジェクトメンバーのみアクセス可能です。**

    パスパラメータ:
        - code: プロジェクトコード
    """,
)
@handle_service_errors
async def get_project_by_code(
    code: str,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAzureDep,
) -> ProjectResponse:
    """プロジェクトコードで検索します（メンバーのみ）。

    Args:
        code (str): プロジェクトコード
        project_service (ProjectService): プロジェクトサービス（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        ProjectResponse: プロジェクト情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: プロジェクトメンバーではない
            - 404: プロジェクトが見つからない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/projects/code/AI-001
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "id": "12345678-1234-1234-1234-123456789abc",
        ...     "name": "AI Project",
        ...     "code": "AI-001",
        ...     "description": "AI development project",
        ...     "is_active": true,
        ...     "created_by": "87654321-4321-4321-4321-cba987654321",
        ...     "created_at": "2024-01-15T10:30:00Z",
        ...     "updated_at": "2024-01-15T10:30:00Z"
        ... }
    """
    logger.info(
        "プロジェクトコード検索",
        user_id=str(current_user.id),
        code=code,
        action="get_project_by_code",
    )

    # プロジェクト取得
    project = await project_service.get_project_by_code(code)

    # アクセス権チェック
    has_access = await project_service.check_user_access(
        project_id=project.id,
        user_id=current_user.id,
    )
    if not has_access:
        logger.warning(
            "プロジェクトへのアクセス権がありません",
            user_id=str(current_user.id),
            project_id=str(project.id),
            code=code,
        )
        raise AuthorizationError(
            "このプロジェクトへのアクセス権限がありません",
            details={"code": code},
        )

    logger.info(
        "プロジェクトをコードで検索しました",
        user_id=str(current_user.id),
        project_id=str(project.id),
        code=code,
    )

    return ProjectResponse.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="プロジェクト情報更新",
    description="""
    プロジェクト情報を更新します。

    **OWNER/ADMINロールが必要です。**

    更新可能なフィールド:
        - name: プロジェクト名
        - description: プロジェクト説明
        - is_active: アクティブフラグ

    注意:
        - code（プロジェクトコード）は更新できません
        - 指定されたフィールドのみが更新されます（PATCH）
    """,
)
@handle_service_errors
async def update_project(
    project_id: uuid.UUID,
    update_data: ProjectUpdate,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAzureDep,
) -> ProjectResponse:
    """プロジェクト情報を更新します（OWNER/ADMINのみ）。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        update_data (ProjectUpdate): 更新データ
        project_service (ProjectService): プロジェクトサービス（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        ProjectResponse: 更新されたプロジェクト情報

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: OWNER/ADMINロールがない
            - 404: プロジェクトが見つからない
            - 422: バリデーションエラー
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> PATCH /api/v1/projects/12345678-1234-1234-1234-123456789abc
        >>> Authorization: Bearer <Azure_AD_Token>
        >>> {
        ...     "name": "Updated Project Name",
        ...     "description": "Updated description"
        ... }
        >>>
        >>> # レスポンス (200 OK)
        >>> {
        ...     "id": "12345678-1234-1234-1234-123456789abc",
        ...     "name": "Updated Project Name",
        ...     "code": "AI-001",
        ...     "description": "Updated description",
        ...     "is_active": true,
        ...     "created_by": "87654321-4321-4321-4321-cba987654321",
        ...     "created_at": "2024-01-15T10:30:00Z",
        ...     "updated_at": "2024-01-15T12:00:00Z"
        ... }

    Note:
        - OWNER/ADMINロールのみが更新を実行できます
        - プロジェクトコード（code）は更新できません
    """
    logger.info(
        "プロジェクト情報更新",
        user_id=str(current_user.id),
        project_id=str(project_id),
        update_fields=update_data.model_dump(exclude_unset=True),
        action="update_project",
    )

    updated_project = await project_service.update_project(
        project_id=project_id,
        update_data=update_data,
        user_id=current_user.id,
    )

    logger.info(
        "プロジェクト情報を更新しました",
        user_id=str(current_user.id),
        project_id=str(updated_project.id),
        project_code=updated_project.code,
    )

    return ProjectResponse.model_validate(updated_project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="プロジェクト削除",
    description="""
    プロジェクトを削除します。

    **OWNERロールが必要です。**

    パスパラメータ:
        - project_id: プロジェクトID（UUID形式）

    注意:
        - 削除は物理削除です（データベースから完全に削除されます）
        - CASCADE設定により、関連する ProjectMember と ProjectFile も自動削除されます
        - この操作は取り消せません
    """,
)
@handle_service_errors
async def delete_project(
    project_id: uuid.UUID,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAzureDep,
) -> None:
    """プロジェクトを削除します（OWNERのみ）。

    Args:
        project_id (uuid.UUID): プロジェクトのUUID
        project_service (ProjectService): プロジェクトサービス（自動注入）
        current_user (User): 認証済みユーザー（自動注入）

    Returns:
        None: 204 No Content（削除成功）

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 403: OWNERロールがない
            - 404: プロジェクトが見つからない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> DELETE /api/v1/projects/12345678-1234-1234-1234-123456789abc
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (204 No Content)
        >>> # レスポンスボディなし

    Note:
        - OWNERロールのみが削除を実行できます
        - CASCADE設定により、関連するメンバーとファイルも削除されます
        - 削除操作は監査ログに記録されます
        - この操作は取り消せません（物理削除）
    """
    logger.info(
        "プロジェクト削除",
        user_id=str(current_user.id),
        project_id=str(project_id),
        action="delete_project",
    )

    await project_service.delete_project(
        project_id=project_id,
        user_id=current_user.id,
    )

    logger.info(
        "プロジェクトを削除しました",
        user_id=str(current_user.id),
        project_id=str(project_id),
    )
