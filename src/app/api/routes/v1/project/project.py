"""Azure AD認証用プロジェクト管理APIエンドポイント。

このモジュールは、Azure AD認証に対応したプロジェクト管理のRESTful APIエンドポイントを定義します。
プロジェクトのCRUD操作、メンバーシップ管理、権限制御を提供します。

主な機能:
    - プロジェクト作成（POST /api/v1/project - 認証必須、自動的にOWNERとして追加）
    - プロジェクト一覧取得（GET /api/v1/project - 自分がメンバーのプロジェクトのみ）
    - プロジェクト詳細取得（GET /api/v1/project/{project_id} - メンバーのみ）
    - プロジェクトコード検索（GET /api/v1/project/code/{code} - メンバーのみ）
    - プロジェクト更新（PATCH /api/v1/project/{project_id} - OWNER/ADMINのみ）
    - プロジェクト削除（DELETE /api/v1/project/{project_id} - OWNERのみ）

セキュリティ:
    - Azure AD Bearer認証（本番環境）
    - モック認証（開発環境）
    - プロジェクトレベルのロールベースアクセス制御（RBAC）

使用例:
    >>> # プロジェクト作成
    >>> POST /api/v1/project
    >>> Authorization: Bearer <Azure_AD_Token>
    >>> {
    ...     "name": "AI Development Project",
    ...     "code": "AI-001",
    ...     "description": "Project for AI model development"
    ... }
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.core import CurrentUserAccountDep, ProjectServiceDep
from app.core.decorators import handle_service_errors
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.schemas import ProjectCreate, ProjectDetailResponse, ProjectListResponse, ProjectResponse, ProjectUpdate

logger = get_logger(__name__)

projects_router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@projects_router.get(
    "/project",
    response_model=ProjectListResponse,
    summary="プロジェクト一覧取得",
    description="""
    プロジェクト一覧を取得します（ユーザーが所属するプロジェクトのみ）。

    **認証が必要です。**

    パスパラメータ:
        - なし

    クエリパラメータ:
        - skip: int - スキップ数（デフォルト: 0）
        - limit: int - 取得件数（デフォルト: 100）
        - is_active: bool - アクティブフィルタ（オプション）

    レスポンス:
        - ProjectListResponse: プロジェクト一覧レスポンス
            - projects (list[ProjectResponse]): プロジェクト情報リスト（統計情報を含む）
                - stats (ProjectStatsResponse): プロジェクト統計情報
                    - member_count (int): メンバー数
                    - file_count (int): ファイル数
                    - session_count (int): 分析セッション数
                    - tree_count (int): ドライバーツリー数
            - total (int): 総件数
            - skip (int): スキップ数
            - limit (int): 取得件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
@handle_service_errors
async def list_projects(
    project_service: ProjectServiceDep,
    current_user: CurrentUserAccountDep,
    skip: int = Query(0, ge=0, description="スキップするレコード数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大レコード数"),
    is_active: bool | None = Query(None, description="アクティブフラグフィルタ"),
) -> ProjectListResponse:
    """プロジェクト一覧を取得します（ユーザーが所属するプロジェクトのみ）。"""
    logger.info(
        "プロジェクト一覧取得",
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        is_active=is_active,
        action="list_projects",
    )

    projects, total = await project_service.list_user_projects(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )

    # 統計情報を一括取得
    project_ids = [project.id for project in projects]
    stats_dict = await project_service.get_projects_stats_bulk(project_ids)

    # プロジェクトレスポンスを構築（統計情報を含む）
    project_responses = []
    for project in projects:
        project_response = ProjectResponse.model_validate(project)
        # 統計情報を追加
        project_response.stats = stats_dict.get(project.id)
        project_responses.append(project_response)

    logger.info(
        "プロジェクト一覧を取得しました",
        user_id=str(current_user.id),
        count=len(projects),
        total=total,
    )

    return ProjectListResponse(
        projects=project_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@projects_router.get(
    "/project/{project_id}",
    response_model=ProjectDetailResponse,
    summary="プロジェクト詳細取得",
    description="""
    プロジェクト情報を取得します（メンバーのみ）。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    レスポンス:
        - ProjectDetailResponse: プロジェクト詳細情報
            - id (uuid): プロジェクトID
            - name (str): プロジェクト名
            - code (str): プロジェクトコード
            - description (str): プロジェクト説明
            - is_active (bool): アクティブフラグ
            - created_by (uuid): 作成者のユーザーID
            - start_date (date | None): プロジェクト開始日
            - end_date (date | None): プロジェクト終了日
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時
            - stats (ProjectStatsResponse): プロジェクト統計情報
                - member_count (int): メンバー数
                - file_count (int): ファイル数
                - session_count (int): 分析セッション数
                - tree_count (int): ドライバーツリー数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: プロジェクトが見つからない
    """,
)
@handle_service_errors
async def get_project(
    project_id: uuid.UUID,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectDetailResponse:
    """プロジェクト情報を取得します（メンバーのみ）。"""
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

    # 統計情報を取得
    stats = await project_service.get_project_stats(project_id)

    logger.info(
        "プロジェクト詳細を取得しました",
        user_id=str(current_user.id),
        project_id=str(project.id),
        project_code=project.code,
    )

    # ProjectDetailResponseを構築
    project_response = ProjectResponse.model_validate(project)
    return ProjectDetailResponse(
        **project_response.model_dump(),
        stats=stats,
    )


@projects_router.get(
    "/project/code/{code}",
    response_model=ProjectResponse,
    summary="プロジェクトコード検索",
    description="""
    プロジェクトコードで検索します（メンバーのみ）。

    **認証が必要です。**

    パスパラメータ:
        - code: str - プロジェクトコード（必須）

    レスポンス:
        - ProjectResponse: プロジェクト情報
            - id (uuid): プロジェクトID
            - name (str): プロジェクト名
            - code (str): プロジェクトコード
            - description (str): プロジェクト説明
            - is_active (bool): アクティブフラグ
            - created_by (uuid): 作成者のユーザーID
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
    """,
)
@handle_service_errors
async def get_project_by_code(
    code: str,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectResponse:
    """プロジェクトコードで検索します（メンバーのみ）。"""
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


# ================================================================================
# POST Endpoints
# ================================================================================


@projects_router.post(
    "/project",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="プロジェクト作成",
    description="""
    プロジェクトを作成します。

    **認証が必要です。**

    リクエストボディ:
        - ProjectCreate: プロジェクト作成データ
            - name (str): プロジェクト名（必須、最大255文字）
            - code (str): プロジェクトコード（必須、最大50文字、一意）
            - description (str): プロジェクト説明（オプション）

    レスポンス:
        - ProjectResponse: プロジェクト情報
            - id (uuid): プロジェクトID
            - name (str): プロジェクト名
            - code (str): プロジェクトコード
            - description (str): プロジェクト説明
            - is_active (bool): アクティブフラグ
            - created_by (uuid): 作成者のユーザーID
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 422: バリデーションエラー
    """,
)
@handle_service_errors
async def create_project(
    project_data: ProjectCreate,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectResponse:
    """プロジェクトを作成します。"""
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


# ================================================================================
# PATCH Endpoints
# ================================================================================


@projects_router.patch(
    "/project/{project_id}",
    response_model=ProjectResponse,
    summary="プロジェクト情報更新",
    description="""
    プロジェクト情報を更新します（OWNER/ADMINのみ）。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    リクエストボディ:
        - ProjectUpdate: プロジェクト更新データ
            - name (str): プロジェクト名（オプション、最大255文字）
            - description (str): プロジェクト説明（オプション）
            - is_active (bool): アクティブフラグ（オプション）

    レスポンス:
        - ProjectResponse: プロジェクト情報
            - id (uuid): プロジェクトID
            - name (str): プロジェクト名
            - code (str): プロジェクトコード
            - description (str): プロジェクト説明
            - is_active (bool): アクティブフラグ
            - created_by (uuid): 作成者のユーザーID
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 200: 更新成功
        - 401: 認証されていない
        - 404: リソースが見つからない
    """,
)
@handle_service_errors
async def update_project(
    project_id: uuid.UUID,
    update_data: ProjectUpdate,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAccountDep,
) -> ProjectResponse:
    """プロジェクト情報を更新します（OWNER/ADMINのみ）。"""
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


# ================================================================================
# DELETE Endpoints
# ================================================================================


@projects_router.delete(
    "/project/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="プロジェクト削除",
    description="""
    プロジェクトを削除します（OWNERのみ）。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    レスポンス:
        - None（204 No Content）

    ステータスコード:
        - 204: 削除成功
        - 401: 認証されていない
        - 404: リソースが見つからない
    """,
)
@handle_service_errors
async def delete_project(
    project_id: uuid.UUID,
    project_service: ProjectServiceDep,
    current_user: CurrentUserAccountDep,
) -> None:
    """プロジェクトを削除します（OWNERのみ）。"""
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
