"""カテゴリマスタ管理サービス。"""

from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models.driver_tree.driver_tree_category import DriverTreeCategory
from app.repositories.admin import DriverTreeCategoryRepository
from app.schemas.admin.category import (
    DriverTreeCategoryCreate,
    DriverTreeCategoryListResponse,
    DriverTreeCategoryResponse,
    DriverTreeCategoryUpdate,
)

logger = get_logger(__name__)


class AdminCategoryService:
    """カテゴリマスタ管理サービス。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = DriverTreeCategoryRepository(db)

    async def list_categories(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> DriverTreeCategoryListResponse:
        """カテゴリマスタ一覧を取得（関連数式数含む）。"""
        categories_with_counts, total = await self.repository.get_list_with_formula_counts(skip=skip, limit=limit)

        category_responses = []
        for item in categories_with_counts:
            category = cast(DriverTreeCategory, item["category"])
            formula_count = cast(int, item["formula_count"])

            category_responses.append(
                DriverTreeCategoryResponse(
                    id=category.id,
                    category_id=category.category_id,
                    category_name=category.category_name,
                    industry_id=category.industry_id,
                    industry_name=category.industry_name,
                    driver_type_id=category.driver_type_id,
                    driver_type=category.driver_type,
                    formula_count=formula_count,
                    created_at=category.created_at,
                    updated_at=category.updated_at,
                )
            )

        return DriverTreeCategoryListResponse(
            categories=category_responses,
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_category(self, category_id: int) -> DriverTreeCategoryResponse:
        """カテゴリマスタ詳細を取得（関連数式数含む）。"""
        result = await self.repository.get_with_formula_count(category_id)
        if not result:
            raise NotFoundError(f"カテゴリマスタが見つかりません: {category_id}")

        category = result["category"]
        formula_count = result["formula_count"]

        return DriverTreeCategoryResponse(
            id=category.id,
            category_id=category.category_id,
            category_name=category.category_name,
            industry_id=category.industry_id,
            industry_name=category.industry_name,
            driver_type_id=category.driver_type_id,
            driver_type=category.driver_type,
            formula_count=formula_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )

    async def create_category(self, category_create: DriverTreeCategoryCreate) -> DriverTreeCategoryResponse:
        """カテゴリマスタを作成。"""
        category = await self.repository.create(category_create)
        await self.db.commit()

        logger.info(f"カテゴリマスタ作成: id={category.id}")
        return DriverTreeCategoryResponse.model_validate(category)

    async def update_category(
        self,
        category_id: int,
        category_update: DriverTreeCategoryUpdate,
    ) -> DriverTreeCategoryResponse:
        """カテゴリマスタを更新。"""
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"カテゴリマスタが見つかりません: {category_id}")

        category = await self.repository.update(category, category_update)
        await self.db.commit()

        logger.info(f"カテゴリマスタ更新: id={category.id}")
        return DriverTreeCategoryResponse.model_validate(category)

    async def delete_category(self, category_id: int) -> None:
        """カテゴリマスタを削除。"""
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"カテゴリマスタが見つかりません: {category_id}")

        # 参照チェック
        if await self.repository.has_formulas(category_id):
            raise ConflictError("このカテゴリには数式が紐づいているため削除できません")

        await self.repository.delete(category)
        await self.db.commit()

        logger.info(f"カテゴリマスタ削除: id={category_id}")
