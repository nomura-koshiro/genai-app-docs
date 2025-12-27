"""課題マスタ管理サービス。"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.repositories.admin import AnalysisIssueRepository
from app.schemas.admin.issue import (
    AnalysisIssueCreate,
    AnalysisIssueListResponse,
    AnalysisIssueResponse,
    AnalysisIssueUpdate,
)

logger = get_logger(__name__)


class AdminIssueService:
    """課題マスタ管理サービス。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = AnalysisIssueRepository(db)

    async def list_issues(
        self,
        skip: int = 0,
        limit: int = 100,
        validation_id: uuid.UUID | None = None,
    ) -> AnalysisIssueListResponse:
        """課題マスタ一覧を取得。"""
        issues = await self.repository.list(skip=skip, limit=limit, validation_id=validation_id)
        total = await self.repository.count(validation_id=validation_id)

        return AnalysisIssueListResponse(
            issues=[AnalysisIssueResponse.model_validate(issue) for issue in issues],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_issue(self, issue_id: uuid.UUID) -> AnalysisIssueResponse:
        """課題マスタ詳細を取得。"""
        issue = await self.repository.get_by_id(issue_id)
        if not issue:
            raise NotFoundError(f"課題マスタが見つかりません: {issue_id}")

        return AnalysisIssueResponse.model_validate(issue)

    async def create_issue(self, issue_create: AnalysisIssueCreate) -> AnalysisIssueResponse:
        """課題マスタを作成。"""
        issue = await self.repository.create(issue_create)
        await self.db.commit()

        logger.info(f"課題マスタ作成: id={issue.id}")
        return AnalysisIssueResponse.model_validate(issue)

    async def update_issue(
        self,
        issue_id: uuid.UUID,
        issue_update: AnalysisIssueUpdate,
    ) -> AnalysisIssueResponse:
        """課題マスタを更新。"""
        issue = await self.repository.get_by_id(issue_id)
        if not issue:
            raise NotFoundError(f"課題マスタが見つかりません: {issue_id}")

        issue = await self.repository.update(issue, issue_update)
        await self.db.commit()

        logger.info(f"課題マスタ更新: id={issue.id}")
        return AnalysisIssueResponse.model_validate(issue)

    async def delete_issue(self, issue_id: uuid.UUID) -> None:
        """課題マスタを削除。"""
        issue = await self.repository.get_by_id(issue_id)
        if not issue:
            raise NotFoundError(f"課題マスタが見つかりません: {issue_id}")

        # 参照チェック
        if await self.repository.has_sessions(issue_id):
            raise ConflictError("この課題マスタにはセッションが紐づいているため削除できません")

        await self.repository.delete(issue)
        await self.db.commit()

        logger.info(f"課題マスタ削除: id={issue_id}")
