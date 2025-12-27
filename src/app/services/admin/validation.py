"""検証マスタ管理サービス。"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.repositories.admin import AnalysisValidationRepository
from app.schemas.admin.validation import (
    AnalysisValidationCreate,
    AnalysisValidationListResponse,
    AnalysisValidationResponse,
    AnalysisValidationUpdate,
)

logger = get_logger(__name__)


class AdminValidationService:
    """検証マスタ管理サービス。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = AnalysisValidationRepository(db)

    async def list_validations(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> AnalysisValidationListResponse:
        """検証マスタ一覧を取得。"""
        validations = await self.repository.list(skip=skip, limit=limit)
        total = await self.repository.count()

        return AnalysisValidationListResponse(
            validations=[AnalysisValidationResponse.model_validate(validation) for validation in validations],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_validation(self, validation_id: uuid.UUID) -> AnalysisValidationResponse:
        """検証マスタ詳細を取得。"""
        validation = await self.repository.get_by_id(validation_id)
        if not validation:
            raise NotFoundError(f"検証マスタが見つかりません: {validation_id}")

        return AnalysisValidationResponse.model_validate(validation)

    async def create_validation(self, validation_create: AnalysisValidationCreate) -> AnalysisValidationResponse:
        """検証マスタを作成。"""
        validation = await self.repository.create(validation_create)
        await self.db.commit()

        logger.info(f"検証マスタ作成: id={validation.id}")
        return AnalysisValidationResponse.model_validate(validation)

    async def update_validation(
        self,
        validation_id: uuid.UUID,
        validation_update: AnalysisValidationUpdate,
    ) -> AnalysisValidationResponse:
        """検証マスタを更新。"""
        validation = await self.repository.get_by_id(validation_id)
        if not validation:
            raise NotFoundError(f"検証マスタが見つかりません: {validation_id}")

        validation = await self.repository.update(validation, validation_update)
        await self.db.commit()

        logger.info(f"検証マスタ更新: id={validation.id}")
        return AnalysisValidationResponse.model_validate(validation)

    async def delete_validation(self, validation_id: uuid.UUID) -> None:
        """検証マスタを削除。"""
        validation = await self.repository.get_by_id(validation_id)
        if not validation:
            raise NotFoundError(f"検証マスタが見つかりません: {validation_id}")

        # 参照チェック
        if await self.repository.has_issues(validation_id):
            raise ConflictError("この検証マスタには課題が紐づいているため削除できません")

        await self.repository.delete(validation)
        await self.db.commit()

        logger.info(f"検証マスタ削除: id={validation_id}")
