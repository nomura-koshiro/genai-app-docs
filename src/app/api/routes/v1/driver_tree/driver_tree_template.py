"""ドライバーツリーテンプレートAPIエンドポイント。

このモジュールは、ドライバーツリーテンプレートの取得・作成・削除に関するAPIエンドポイントを定義します。

主な機能:
    - テンプレート一覧取得（GET /api/v1/project/{project_id}/driver-tree/template）
    - テンプレート作成（POST /api/v1/project/{project_id}/driver-tree/template）
    - テンプレート削除（DELETE /api/v1/project/{project_id}/driver-tree/template/{template_id}）
"""

import uuid

from fastapi import APIRouter, Path, Query, status

from app.api.core import CurrentUserAccountDep, DatabaseDep, ProjectMemberDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.driver_tree import (
    DriverTreeTemplateCreateRequest,
    DriverTreeTemplateCreateResponse,
    DriverTreeTemplateDeleteResponse,
    DriverTreeTemplateListResponse,
)
from app.services.driver_tree.driver_tree_template import DriverTreeTemplateService

logger = get_logger(__name__)

driver_tree_templates_router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@driver_tree_templates_router.get(
    "/project/{project_id}/driver-tree/template",
    response_model=DriverTreeTemplateListResponse,
    status_code=status.HTTP_200_OK,
    summary="テンプレート一覧取得",
    description="""
    ドライバーツリーテンプレート一覧を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    クエリパラメータ:
        - include_public: bool - 公開テンプレートを含めるか（デフォルト: true）
        - category: str - カテゴリでフィルタ（任意）

    レスポンス:
        - DriverTreeTemplateListResponse: テンプレート一覧
            - templates (list[DriverTreeTemplateInfo]): テンプレート一覧
            - total (int): 総件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
    """,
)
@handle_service_errors
async def list_templates(
    project_id: uuid.UUID,
    current_user: CurrentUserAccountDep,
    member: ProjectMemberDep,  # 権限チェック
    db: DatabaseDep,
    include_public: bool = Query(True, description="公開テンプレートを含めるか"),
    category: str | None = Query(None, description="カテゴリでフィルタ"),
) -> DriverTreeTemplateListResponse:
    """テンプレート一覧を取得します。

    Args:
        project_id: プロジェクトID
        current_user: 認証済みユーザー
        member: プロジェクトメンバー（権限チェック用）
        db: データベースセッション
        include_public: 公開テンプレートを含めるか
        category: カテゴリでフィルタ

    Returns:
        DriverTreeTemplateListResponse: テンプレート一覧
    """
    logger.info(
        "ドライバーツリーテンプレート一覧取得",
        user_id=str(current_user.id),
        project_id=str(project_id),
        action="list_driver_tree_templates",
    )

    template_service = DriverTreeTemplateService(db)
    templates = await template_service.list_templates(
        project_id=project_id, include_public=include_public, category=category
    )

    logger.info(
        "ドライバーツリーテンプレート一覧を取得しました",
        user_id=str(current_user.id),
        count=templates.total,
    )

    return templates


# ================================================================================
# POST Endpoints
# ================================================================================


@driver_tree_templates_router.post(
    "/project/{project_id}/driver-tree/template",
    response_model=DriverTreeTemplateCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="テンプレート作成",
    description="""
    ツリーからテンプレートを作成します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    リクエストボディ:
        - DriverTreeTemplateCreateRequest: テンプレート作成リクエスト
            - name (str): テンプレート名（必須）
            - description (str | None): 説明
            - category (str | None): カテゴリ（業種）
            - sourceTreeId (UUID): 元ツリーID（必須）
            - isPublic (bool): 公開フラグ（デフォルト: false）

    レスポンス:
        - DriverTreeTemplateCreateResponse: 作成されたテンプレート情報
            - templateId (UUID): テンプレートID
            - name (str): テンプレート名
            - description (str | None): 説明
            - category (str | None): カテゴリ
            - templateConfig (dict): テンプレート設定
            - nodeCount (int): ノード数
            - createdAt (datetime): 作成日時

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない、または他プロジェクトのツリー）
        - 404: 元ツリーが見つからない
    """,
)
@handle_service_errors
async def create_template(
    project_id: uuid.UUID,
    request: DriverTreeTemplateCreateRequest,
    current_user: CurrentUserAccountDep,
    member: ProjectMemberDep,  # 権限チェック
    db: DatabaseDep,
) -> DriverTreeTemplateCreateResponse:
    """テンプレートを作成します。

    Args:
        project_id: プロジェクトID
        request: テンプレート作成リクエスト
        current_user: 認証済みユーザー
        member: プロジェクトメンバー（権限チェック用）
        db: データベースセッション

    Returns:
        DriverTreeTemplateCreateResponse: 作成されたテンプレート情報
    """
    logger.info(
        "ドライバーツリーテンプレート作成",
        user_id=str(current_user.id),
        project_id=str(project_id),
        action="create_driver_tree_template",
    )

    template_service = DriverTreeTemplateService(db)
    template = await template_service.create_template(project_id=project_id, request=request, user_id=current_user.id)

    logger.info(
        "ドライバーツリーテンプレートを作成しました",
        user_id=str(current_user.id),
        template_id=str(template.template_id),
    )

    return template


# ================================================================================
# DELETE Endpoints
# ================================================================================


@driver_tree_templates_router.delete(
    "/project/{project_id}/driver-tree/template/{template_id}",
    response_model=DriverTreeTemplateDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="テンプレート削除",
    description="""
    テンプレートを削除します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - template_id: uuid - テンプレートID（必須）

    レスポンス:
        - DriverTreeTemplateDeleteResponse: 削除結果
            - success (bool): 削除成功フラグ
            - deletedAt (datetime): 削除日時

    ステータスコード:
        - 200: 削除成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない、または作成者ではない）
        - 404: テンプレートが見つからない
    """,
)
@handle_service_errors
async def delete_template(
    project_id: uuid.UUID,
    template_id: uuid.UUID,
    current_user: CurrentUserAccountDep,
    member: ProjectMemberDep,  # 権限チェック
    db: DatabaseDep,
) -> DriverTreeTemplateDeleteResponse:
    """テンプレートを削除します。

    Args:
        project_id: プロジェクトID
        template_id: テンプレートID
        current_user: 認証済みユーザー
        member: プロジェクトメンバー（権限チェック用）
        db: データベースセッション

    Returns:
        DriverTreeTemplateDeleteResponse: 削除結果
    """
    logger.info(
        "ドライバーツリーテンプレート削除",
        user_id=str(current_user.id),
        project_id=str(project_id),
        template_id=str(template_id),
        action="delete_driver_tree_template",
    )

    template_service = DriverTreeTemplateService(db)
    result = await template_service.delete_template(project_id=project_id, template_id=template_id, user_id=current_user.id)

    logger.info(
        "ドライバーツリーテンプレートを削除しました",
        user_id=str(current_user.id),
        template_id=str(template_id),
    )

    return result
