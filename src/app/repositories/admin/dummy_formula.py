"""分析ダミー数式マスタリポジトリ。"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis.analysis_dummy_formula_master import AnalysisDummyFormulaMaster
from app.schemas.analysis.analysis_template import (
    AnalysisDummyFormulaCreate,
    AnalysisDummyFormulaUpdate,
)


class AnalysisDummyFormulaRepository:
    """分析ダミー数式マスタリポジトリ。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, formula_id: uuid.UUID) -> AnalysisDummyFormulaMaster | None:
        """IDでダミー数式マスタを取得。"""
        result = await self.db.execute(select(AnalysisDummyFormulaMaster).where(AnalysisDummyFormulaMaster.id == formula_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        issue_id: uuid.UUID | None = None,
    ) -> list[AnalysisDummyFormulaMaster]:
        """ダミー数式マスタ一覧を取得。"""
        query = select(AnalysisDummyFormulaMaster).order_by(AnalysisDummyFormulaMaster.formula_order)

        if issue_id:
            query = query.where(AnalysisDummyFormulaMaster.issue_id == issue_id)

        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self, issue_id: uuid.UUID | None = None) -> int:
        """ダミー数式マスタ件数を取得。"""
        query = select(func.count(AnalysisDummyFormulaMaster.id))
        if issue_id:
            query = query.where(AnalysisDummyFormulaMaster.issue_id == issue_id)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, formula_create: AnalysisDummyFormulaCreate) -> AnalysisDummyFormulaMaster:
        """ダミー数式マスタを作成。"""
        formula = AnalysisDummyFormulaMaster(**formula_create.model_dump())
        self.db.add(formula)
        await self.db.flush()
        await self.db.refresh(formula)
        return formula

    async def update(
        self,
        formula: AnalysisDummyFormulaMaster,
        formula_update: AnalysisDummyFormulaUpdate,
    ) -> AnalysisDummyFormulaMaster:
        """ダミー数式マスタを更新。"""
        update_data = formula_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(formula, key, value)
        await self.db.flush()
        await self.db.refresh(formula)
        return formula

    async def delete(self, formula: AnalysisDummyFormulaMaster) -> None:
        """ダミー数式マスタを削除。"""
        await self.db.delete(formula)
        await self.db.flush()
