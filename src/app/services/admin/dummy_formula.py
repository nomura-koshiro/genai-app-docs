"""ダミー数式マスタ管理サービス。"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.admin import AnalysisDummyFormulaRepository
from app.schemas.admin.dummy_formula import (
    AnalysisDummyFormulaListResponse,
)
from app.schemas.analysis.analysis_template import (
    AnalysisDummyFormulaCreate,
    AnalysisDummyFormulaResponse,
    AnalysisDummyFormulaUpdate,
)

logger = get_logger(__name__)


class AdminDummyFormulaService:
    """ダミー数式マスタ管理サービス。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = AnalysisDummyFormulaRepository(db)

    async def list_formulas(
        self,
        skip: int = 0,
        limit: int = 100,
        issue_id: uuid.UUID | None = None,
    ) -> AnalysisDummyFormulaListResponse:
        """ダミー数式マスタ一覧を取得。"""
        formulas = await self.repository.list(skip=skip, limit=limit, issue_id=issue_id)
        total = await self.repository.count(issue_id=issue_id)

        return AnalysisDummyFormulaListResponse(
            formulas=[AnalysisDummyFormulaResponse.model_validate(formula) for formula in formulas],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_formula(self, formula_id: uuid.UUID) -> AnalysisDummyFormulaResponse:
        """ダミー数式マスタ詳細を取得。"""
        formula = await self.repository.get_by_id(formula_id)
        if not formula:
            raise NotFoundError(f"ダミー数式マスタが見つかりません: {formula_id}")

        return AnalysisDummyFormulaResponse.model_validate(formula)

    async def create_formula(self, formula_create: AnalysisDummyFormulaCreate) -> AnalysisDummyFormulaResponse:
        """ダミー数式マスタを作成。"""
        formula = await self.repository.create(formula_create)
        await self.db.commit()

        logger.info(f"ダミー数式マスタ作成: id={formula.id}")
        return AnalysisDummyFormulaResponse.model_validate(formula)

    async def update_formula(
        self,
        formula_id: uuid.UUID,
        formula_update: AnalysisDummyFormulaUpdate,
    ) -> AnalysisDummyFormulaResponse:
        """ダミー数式マスタを更新。"""
        formula = await self.repository.get_by_id(formula_id)
        if not formula:
            raise NotFoundError(f"ダミー数式マスタが見つかりません: {formula_id}")

        formula = await self.repository.update(formula, formula_update)
        await self.db.commit()

        logger.info(f"ダミー数式マスタ更新: id={formula.id}")
        return AnalysisDummyFormulaResponse.model_validate(formula)

    async def delete_formula(self, formula_id: uuid.UUID) -> None:
        """ダミー数式マスタを削除。"""
        formula = await self.repository.get_by_id(formula_id)
        if not formula:
            raise NotFoundError(f"ダミー数式マスタが見つかりません: {formula_id}")

        await self.repository.delete(formula)
        await self.db.commit()

        logger.info(f"ダミー数式マスタ削除: id={formula_id}")
