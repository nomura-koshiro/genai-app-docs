"""分析テンプレートAPIエンドポイント。

このモジュールは、分析テンプレート（施策・課題の組み合わせ）のRESTful APIエンドポイントを定義します。
validation.ymlから自動的にインポートされたテンプレートデータの取得を提供します。

主な機能:
    - テンプレート一覧取得（GET /api/v1/analysis/templates）
    - テンプレート詳細取得（GET /api/v1/analysis/templates/{template_id}）
    - 施策別テンプレート一覧（GET /api/v1/analysis/templates/policy/{policy}）
    - 施策・課題による検索（GET /api/v1/analysis/templates/search）

認証:
    - 認証不要（公開データ）
    - アクティブなテンプレートのみ返却

使用例:
    >>> # テンプレート一覧取得
    >>> GET /api/v1/analysis/templates?skip=0&limit=20
    >>>
    >>> # 施策別一覧
    >>> GET /api/v1/analysis/templates/policy/市場拡大
    >>>
    >>> # 施策・課題で検索
    >>> GET /api/v1/analysis/templates/search?policy=市場拡大&issue=新規参入
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import handle_service_errors
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.analysis_template import AnalysisTemplateRepository
from app.schemas.analysis_template import (
    AnalysisTemplateDetailResponse,
    AnalysisTemplateResponse,
)

logger = get_logger(__name__)

router = APIRouter()


# ================================================================================
# 依存性注入ヘルパー
# ================================================================================


def get_template_repository(db: AsyncSession = Depends(get_db)) -> AnalysisTemplateRepository:
    """テンプレートリポジトリインスタンスを生成します。

    Args:
        db: データベースセッション（自動注入）

    Returns:
        AnalysisTemplateRepository: 初期化されたリポジトリ
    """
    return AnalysisTemplateRepository(db)


# ================================================================================
# GET Endpoints
# ================================================================================


@router.get(
    "",
    response_model=list[AnalysisTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="テンプレート一覧取得",
    description="アクティブな分析テンプレート一覧を取得します。ページネーション対応。",
)
@handle_service_errors
async def list_templates(
    skip: int = Query(default=0, ge=0, description="スキップする件数"),
    limit: int = Query(default=100, ge=1, le=100, description="取得する最大件数"),
    template_repo: AnalysisTemplateRepository = Depends(get_template_repository),
):
    """アクティブな分析テンプレート一覧を取得します。

    Args:
        skip: スキップする件数（デフォルト: 0）
        limit: 取得する最大件数（デフォルト: 100）
        template_repo: テンプレートリポジトリ（自動注入）

    Returns:
        list[AnalysisTemplateResponse]: テンプレート一覧

    Example:
        >>> GET /api/v1/analysis/templates?skip=0&limit=20
        [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "policy": "市場拡大",
                "issue": "新規参入",
                "description": "新規市場への参入効果を分析します",
                "agent_prompt": "...",
                "initial_msg": "分析を開始します",
                "initial_axis": [...],
                "dummy_formula": null,
                "dummy_input": null,
                "dummy_hint": null,
                "is_active": true,
                "display_order": 0,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }
        ]
    """
    logger.info("list_templates_requested", skip=skip, limit=limit)

    templates = await template_repo.list_active(skip=skip, limit=limit)

    logger.info("list_templates_success", count=len(templates))
    return templates


@router.get(
    "/{template_id}",
    response_model=AnalysisTemplateDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="テンプレート詳細取得",
    description="指定されたテンプレートの詳細情報を取得します（チャートデータを含む）。",
)
@handle_service_errors
async def get_template_detail(
    template_id: uuid.UUID,
    template_repo: AnalysisTemplateRepository = Depends(get_template_repository),
):
    """テンプレートの詳細情報（チャートデータを含む）を取得します。

    Args:
        template_id: テンプレートID
        template_repo: テンプレートリポジトリ（自動注入）

    Returns:
        AnalysisTemplateDetailResponse: チャートデータを含むテンプレート詳細

    Raises:
        NotFoundError: テンプレートが見つからない場合

    Example:
        >>> GET /api/v1/analysis/templates/123e4567-e89b-12d3-a456-426614174000
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "policy": "市場拡大",
            "issue": "新規参入",
            "description": "...",
            "agent_prompt": "...",
            "initial_msg": "...",
            "initial_axis": [...],
            "dummy_formula": [...],
            "dummy_input": [...],
            "dummy_hint": "...",
            "is_active": true,
            "display_order": 0,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "charts": [
                {
                    "id": "223e4567-e89b-12d3-a456-426614174000",
                    "template_id": "123e4567-e89b-12d3-a456-426614174000",
                    "chart_name": "利益改善効果グラフ",
                    "chart_data": {"data": [...], "layout": {...}},
                    "chart_order": 0,
                    "chart_type": "scatter",
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z"
                }
            ]
        }
    """
    logger.info("get_template_detail_requested", template_id=str(template_id))

    template = await template_repo.get_with_charts(template_id)

    if not template:
        raise NotFoundError(f"テンプレートが見つかりません: {template_id}")

    logger.info(
        "get_template_detail_success",
        template_id=str(template_id),
        chart_count=len(template.charts),
    )
    return template


@router.get(
    "/policy/{policy}",
    response_model=list[AnalysisTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="施策別テンプレート一覧取得",
    description="指定された施策に紐づくテンプレート一覧を取得します。",
)
@handle_service_errors
async def list_templates_by_policy(
    policy: str,
    skip: int = Query(default=0, ge=0, description="スキップする件数"),
    limit: int = Query(default=100, ge=1, le=100, description="取得する最大件数"),
    template_repo: AnalysisTemplateRepository = Depends(get_template_repository),
):
    """指定された施策に紐づくテンプレート一覧を取得します。

    Args:
        policy: 施策名（例: "市場拡大"）
        skip: スキップする件数（デフォルト: 0）
        limit: 取得する最大件数（デフォルト: 100）
        template_repo: テンプレートリポジトリ（自動注入）

    Returns:
        list[AnalysisTemplateResponse]: テンプレート一覧

    Example:
        >>> GET /api/v1/analysis/templates/policy/市場拡大
        [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "policy": "市場拡大",
                "issue": "新規参入",
                "description": "...",
                ...
            }
        ]
    """
    logger.info("list_templates_by_policy_requested", policy=policy, skip=skip, limit=limit)

    templates = await template_repo.list_by_policy(policy, skip=skip, limit=limit)

    logger.info("list_templates_by_policy_success", policy=policy, count=len(templates))
    return templates


@router.get(
    "/search/by-policy-issue",
    response_model=AnalysisTemplateDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="施策・課題による検索",
    description="施策と課題の組み合わせでテンプレートを検索します（チャートデータを含む）。",
)
@handle_service_errors
async def search_template(
    policy: str = Query(..., description="施策名"),
    issue: str = Query(..., description="課題名"),
    template_repo: AnalysisTemplateRepository = Depends(get_template_repository),
):
    """施策と課題の組み合わせでテンプレートを検索します。

    Args:
        policy: 施策名（必須）
        issue: 課題名（必須）
        template_repo: テンプレートリポジトリ（自動注入）

    Returns:
        AnalysisTemplateDetailResponse: チャートデータを含むテンプレート詳細

    Raises:
        NotFoundError: 該当するテンプレートが見つからない場合

    Example:
        >>> GET /api/v1/analysis/templates/search/by-policy-issue?policy=市場拡大&issue=新規参入
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "policy": "市場拡大",
            "issue": "新規参入",
            "description": "...",
            "agent_prompt": "...",
            "initial_msg": "...",
            "initial_axis": [...],
            "dummy_formula": [...],
            "dummy_input": [...],
            "dummy_hint": "...",
            "is_active": true,
            "display_order": 0,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "charts": [...]
        }
    """
    logger.info("search_template_requested", policy=policy, issue=issue)

    template = await template_repo.get_by_policy_issue(policy, issue)

    if not template:
        raise NotFoundError(f"テンプレートが見つかりません: policy={policy}, issue={issue}")

    # チャートデータを含む詳細情報を再取得
    template_with_charts = await template_repo.get_with_charts(template.id)

    if not template_with_charts:
        raise NotFoundError(f"テンプレート詳細の取得に失敗しました: {template.id}")

    logger.info(
        "search_template_success",
        policy=policy,
        issue=issue,
        template_id=str(template.id),
        chart_count=len(template_with_charts.charts),
    )
    return template_with_charts
