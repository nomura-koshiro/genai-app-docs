"""分析検証マスタリポジトリ。"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis.analysis_validation_master import AnalysisValidationMaster
from app.schemas.admin.validation import AnalysisValidationCreate, AnalysisValidationUpdate


class AnalysisValidationRepository:
    """分析検証マスタリポジトリ。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, validation_id: uuid.UUID) -> AnalysisValidationMaster | None:
        """IDで検証マスタを取得。"""
        result = await self.db.execute(select(AnalysisValidationMaster).where(AnalysisValidationMaster.id == validation_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AnalysisValidationMaster]:
        """検証マスタ一覧を取得。"""
        result = await self.db.execute(
            select(AnalysisValidationMaster).order_by(AnalysisValidationMaster.validation_order).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """検証マスタ件数を取得。"""
        result = await self.db.execute(select(func.count(AnalysisValidationMaster.id)))
        return result.scalar_one()

    async def create(self, validation_create: AnalysisValidationCreate) -> AnalysisValidationMaster:
        """検証マスタを作成。"""
        validation = AnalysisValidationMaster(**validation_create.model_dump())
        self.db.add(validation)
        await self.db.flush()
        await self.db.refresh(validation)
        return validation

    async def update(
        self,
        validation: AnalysisValidationMaster,
        validation_update: AnalysisValidationUpdate,
    ) -> AnalysisValidationMaster:
        """検証マスタを更新。"""
        update_data = validation_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(validation, key, value)
        await self.db.flush()
        await self.db.refresh(validation)
        return validation

    async def delete(self, validation: AnalysisValidationMaster) -> None:
        """検証マスタを削除。"""
        await self.db.delete(validation)
        await self.db.flush()

    async def has_issues(self, validation_id: uuid.UUID) -> bool:
        """検証マスタに課題が紐づいているか確認。"""
        from app.models.analysis.analysis_issue_master import AnalysisIssueMaster

        result = await self.db.execute(select(func.count(AnalysisIssueMaster.id)).where(AnalysisIssueMaster.validation_id == validation_id))
        return result.scalar_one() > 0
