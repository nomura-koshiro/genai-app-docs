"""分析テンプレートAPIエンドポイント。

このモジュールは、分析テンプレート(施策・課題)の取得に関するAPIエンドポイントを定義します。

主な機能:
    - テンプレート一覧取得（GET /api/v1/project/{project_id}/analysis/template）
    - テンプレート詳細取得（GET /api/v1/project/{project_id}/analysis/template/{issue_id}）

"""

import uuid

from fastapi import APIRouter, Path, status

from app.api.core import AnalysisTemplateServiceDep, CurrentUserAccountDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.analysis import (
    AnalysisIssueCatalogListResponse,
    AnalysisIssueDetailResponse,
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
