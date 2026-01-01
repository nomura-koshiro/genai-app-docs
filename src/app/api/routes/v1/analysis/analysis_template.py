"""分析テンプレートAPIエンドポイント。

このモジュールは、分析テンプレート(施策・課題)の取得・作成・削除に関するAPIエンドポイントを定義します。

主な機能:
    - テンプレート一覧取得（GET /api/v1/project/{project_id}/analysis/template）
    - テンプレート詳細取得（GET /api/v1/project/{project_id}/analysis/template/{issue_id}）
    - テンプレート作成（POST /api/v1/project/{project_id}/analysis/template）
    - テンプレート削除（DELETE /api/v1/project/{project_id}/analysis/template/{template_id}）

"""

import uuid

from fastapi import APIRouter, Path, status

from app.api.core import AnalysisTemplateServiceDep, CurrentUserAccountDep, ProjectMemberDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.analysis import (
    AnalysisIssueCatalogListResponse,
    AnalysisIssueDetailResponse,
    AnalysisTemplateCreateRequest,
    AnalysisTemplateCreateResponse,
    AnalysisTemplateDeleteResponse,
)

logger = get_logger(__name__)

analysis_templates_router = APIRouter()


# ================================================================================
# GET Endpoints
# ================================================================================


@analysis_templates_router.get(
    "/project/{project_id}/analysis/template",
    response_model=AnalysisIssueCatalogListResponse,
    status_code=status.HTTP_200_OK,
    summary="テンプレート一覧取得",
    description="""
    施策課題テンプレート一覧を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    レスポンス:
        - AnalysisIssueCatalogListResponse: 施策課題カタログ一覧レスポンス
            - issues (list[AnalysisIssueCatalogResponse]): 課題カタログリスト
            - total (int): 総件数

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
    """,
)
@handle_service_errors
async def list_templates(
    current_user: CurrentUserAccountDep,
    template_service: AnalysisTemplateServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
) -> AnalysisIssueCatalogListResponse:
    """テンプレート一覧を取得します。

    Args:
        current_user (CurrentUserAccountDep): 認証済みユーザー
        template_service (AnalysisTemplateServiceDep): 分析テンプレートサービス

    Returns:
        AnalysisIssueCatalogListResponse: テンプレート一覧
            - issues (list[AnalysisIssueCatalogResponse]): 課題カタログリスト
                - validation_id (uuid): 施策ID
                - validation (str): 施策名
                - validation_order (int): 施策表示順序
                - id (uuid): 課題ID
                - name (str): 課題名
                - issue_order (int): 課題表示順序
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            - total (int): 総件数
    """
    logger.info(
        "テンプレート一覧取得",
        user_id=str(current_user.id),
        action="list_templates",
    )

    templates = await template_service.list_templates(project_id=project_id)

    logger.info(
        "テンプレート一覧を取得しました",
        user_id=str(current_user.id),
        count=len(templates),
    )

    return AnalysisIssueCatalogListResponse(
        issues=templates,
        total=len(templates),
    )


@analysis_templates_router.get(
    "/project/{project_id}/analysis/template/{issue_id}",
    response_model=AnalysisIssueDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="テンプレート詳細取得",
    description="""
    指定した施策課題の分析テンプレート詳細を取得します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - issue_id: uuid - 課題ID（必須）

    レスポンス:
        - AnalysisIssueDetailResponse: 施策課題詳細情報
            - id (uuid): 課題ID
            - name (str): 課題名
            - issue_order (int): 課題表示順序
            - validation_id (uuid): 施策ID
            - validation (str): 施策名
            - validation_order (int): 施策表示順序
            - description (str): 課題説明
            - agent_prompt (str): エージェントプロンプト
            - initial_axis (list[AnalysisGraphAxisResponse]): 初期軸設定
            - dummy_input (list[dict]): ダミー入力データ(pandas.to_dict, orient='records'形式)
            - dummy_hint (str): ダミー入力ヒント
            - dummy_formula (list[AnalysisDummyFormulaResponse]): ダミー計算式
            - dummy_chart (list[AnalysisDummyChartResponse]): ダミーチャート
            - created_at (datetime): 作成日時
            - updated_at (datetime): 更新日時

    ステータスコード:
        - 200: 成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない）
        - 404: テンプレートが見つからない
    """,
)
@handle_service_errors
async def get_template(
    current_user: CurrentUserAccountDep,
    template_service: AnalysisTemplateServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    issue_id: uuid.UUID = Path(..., description="課題ID"),
) -> AnalysisIssueDetailResponse:
    """テンプレート詳細を取得します。

    Args:
        issue_id: 課題ID
        current_user: 認証済みユーザー
        template_service: 分析テンプレートサービス

    Returns:
        AnalysisIssueDetailResponse: テンプレート詳細
    """
    logger.info(
        "テンプレート詳細取得",
        user_id=str(current_user.id),
        issue_id=str(issue_id),
        action="get_template",
    )

    template = await template_service.get_template(issue_id=issue_id, project_id=project_id)

    logger.info(
        "テンプレート詳細を取得しました",
        user_id=str(current_user.id),
        issue_id=str(issue_id),
    )

    return template


# ================================================================================
# POST Endpoints
# ================================================================================


@analysis_templates_router.post(
    "/project/{project_id}/analysis/template",
    response_model=AnalysisTemplateCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="テンプレート作成",
    description="""
    セッションからテンプレートを作成します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）

    リクエストボディ:
        - AnalysisTemplateCreateRequest: テンプレート作成リクエスト
            - name (str): テンプレート名（必須）
            - description (str | None): 説明
            - sourceSessionId (UUID): 元セッションID（必須）
            - isPublic (bool): 公開フラグ（デフォルト: false）

    レスポンス:
        - AnalysisTemplateCreateResponse: 作成されたテンプレート情報
            - templateId (UUID): テンプレートID
            - name (str): テンプレート名
            - description (str | None): 説明
            - templateType (str): テンプレートタイプ
            - templateConfig (dict): テンプレート設定
            - createdAt (datetime): 作成日時

    ステータスコード:
        - 201: 作成成功
        - 401: 認証されていない
        - 403: 権限なし（メンバーではない、または他プロジェクトのセッション）
        - 404: 元セッションが見つからない
    """,
)
@handle_service_errors
async def create_template(
    project_id: uuid.UUID,
    request: AnalysisTemplateCreateRequest,
    current_user: CurrentUserAccountDep,
    member: ProjectMemberDep,  # 権限チェック
    template_service: AnalysisTemplateServiceDep,
) -> AnalysisTemplateCreateResponse:
    """テンプレートを作成します。

    Args:
        project_id: プロジェクトID
        request: テンプレート作成リクエスト
        current_user: 認証済みユーザー
        member: プロジェクトメンバー（権限チェック用）
        template_service: 分析テンプレートサービス

    Returns:
        AnalysisTemplateCreateResponse: 作成されたテンプレート情報
    """
    logger.info(
        "テンプレート作成",
        user_id=str(current_user.id),
        project_id=str(project_id),
        action="create_template",
    )

    template = await template_service.create_template(
        project_id=project_id, request=request, user_id=current_user.id
    )

    logger.info(
        "テンプレートを作成しました",
        user_id=str(current_user.id),
        template_id=str(template.template_id),
    )

    return template


# ================================================================================
# DELETE Endpoints
# ================================================================================


@analysis_templates_router.delete(
    "/project/{project_id}/analysis/template/{template_id}",
    response_model=AnalysisTemplateDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="テンプレート削除",
    description="""
    テンプレートを削除します。

    **認証が必要です。**

    パスパラメータ:
        - project_id: uuid - プロジェクトID（必須）
        - template_id: uuid - テンプレートID（必須）

    レスポンス:
        - AnalysisTemplateDeleteResponse: 削除結果
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
    template_id: uuid.UUID = Path(..., description="テンプレートID"),
    current_user: CurrentUserAccountDep,
    member: ProjectMemberDep,  # 権限チェック
    template_service: AnalysisTemplateServiceDep,
) -> AnalysisTemplateDeleteResponse:
    """テンプレートを削除します。

    Args:
        project_id: プロジェクトID
        template_id: テンプレートID
        current_user: 認証済みユーザー
        member: プロジェクトメンバー（権限チェック用）
        template_service: 分析テンプレートサービス

    Returns:
        AnalysisTemplateDeleteResponse: 削除結果
    """
    logger.info(
        "テンプレート削除",
        user_id=str(current_user.id),
        project_id=str(project_id),
        template_id=str(template_id),
        action="delete_template",
    )

    result = await template_service.delete_template(
        project_id=project_id, template_id=template_id, user_id=current_user.id
    )

    logger.info(
        "テンプレートを削除しました",
        user_id=str(current_user.id),
        template_id=str(template_id),
    )

    return result
