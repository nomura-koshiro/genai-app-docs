"""分析課題マスタリポジトリ。"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis.analysis_issue_master import AnalysisIssueMaster
from app.schemas.admin.issue import AnalysisIssueCreate, AnalysisIssueUpdate


class AnalysisIssueRepository:
    """分析課題マスタリポジトリ。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, issue_id: uuid.UUID) -> AnalysisIssueMaster | None:
        """IDで課題マスタを取得。"""
        result = await self.db.execute(select(AnalysisIssueMaster).where(AnalysisIssueMaster.id == issue_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        validation_id: uuid.UUID | None = None,
    ) -> list[AnalysisIssueMaster]:
        """課題マスタ一覧を取得。"""
        query = select(AnalysisIssueMaster).order_by(AnalysisIssueMaster.issue_order)

        if validation_id:
            query = query.where(AnalysisIssueMaster.validation_id == validation_id)

        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self, validation_id: uuid.UUID | None = None) -> int:
        """課題マスタ件数を取得。"""
        query = select(func.count(AnalysisIssueMaster.id))
        if validation_id:
            query = query.where(AnalysisIssueMaster.validation_id == validation_id)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, issue_create: AnalysisIssueCreate) -> AnalysisIssueMaster:
        """課題マスタを作成。"""
        issue = AnalysisIssueMaster(**issue_create.model_dump())
        self.db.add(issue)
        await self.db.flush()
        await self.db.refresh(issue)
        return issue

    async def update(
        self,
        issue: AnalysisIssueMaster,
        issue_update: AnalysisIssueUpdate,
    ) -> AnalysisIssueMaster:
        """課題マスタを更新。"""
        update_data = issue_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(issue, key, value)
        await self.db.flush()
        await self.db.refresh(issue)
        return issue

    async def delete(self, issue: AnalysisIssueMaster) -> None:
        """課題マスタを削除。"""
        await self.db.delete(issue)
        await self.db.flush()

    async def has_sessions(self, issue_id: uuid.UUID) -> bool:
        """課題マスタにセッションが紐づいているか確認。"""
        from app.models.analysis.analysis_session import AnalysisSession

        result = await self.db.execute(select(func.count(AnalysisSession.id)).where(AnalysisSession.issue_id == issue_id))
        return result.scalar_one() > 0
