"""分析テンプレートAPI v2エンドポイント。

パス変更: /project/{id}/analysis/template → /project/{id}/template
"""

import uuid

from fastapi import APIRouter, Path, Query, status

from app.api.core import AnalysisTemplateServiceDep, ProjectMemberDep
from app.api.decorators import handle_service_errors
from app.core.logging import get_logger
from app.schemas.analysis import (
    AnalysisTemplateListResponse,
    AnalysisTemplateResponse,
)

logger = get_logger(__name__)

template_router = APIRouter()


@template_router.get(
    "/project/{project_id}/template",
    response_model=AnalysisTemplateListResponse,
    status_code=status.HTTP_200_OK,
    summary="テンプレート一覧取得",
    description="プロジェクトで使用可能な分析テンプレート（課題マスタ）一覧を取得します。",
)
@handle_service_errors
async def list_templates(
    member: ProjectMemberDep,
    template_service: AnalysisTemplateServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    skip: int = Query(0, ge=0, description="スキップ数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
) -> AnalysisTemplateListResponse:
    """テンプレート一覧を取得します。"""
    logger.info(f"テンプレート一覧取得: project_id={project_id}, user_id={member.user_id}")
    return await template_service.list_templates(skip=skip, limit=limit)


@template_router.get(
    "/project/{project_id}/template/{issue_id}",
    response_model=AnalysisTemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="テンプレート詳細取得",
    description="指定された課題IDのテンプレート詳細を取得します。",
)
@handle_service_errors
async def get_template(
    member: ProjectMemberDep,
    template_service: AnalysisTemplateServiceDep,
    project_id: uuid.UUID = Path(..., description="プロジェクトID"),
    issue_id: uuid.UUID = Path(..., description="課題ID"),
) -> AnalysisTemplateResponse:
    """テンプレート詳細を取得します。"""
    logger.info(f"テンプレート詳細取得: issue_id={issue_id}, user_id={member.user_id}")
    return await template_service.get_template(issue_id)


__all__ = ["template_router"]
