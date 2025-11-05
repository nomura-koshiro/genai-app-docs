"""DriverTreeCategoryリポジトリ。"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver_tree_category import DriverTreeCategory
from app.repositories.base import BaseRepository


class DriverTreeCategoryRepository(BaseRepository[DriverTreeCategory, uuid.UUID]):
    """DriverTreeCategoryリポジトリ。"""

    def __init__(self, db: AsyncSession):
        super().__init__(DriverTreeCategory, db)

    async def find_by_criteria(
        self,
        industry_class: str | None = None,
        industry: str | None = None,
        tree_type: str | None = None,
        kpi: str | None = None,
    ) -> list[DriverTreeCategory]:
        """条件でカテゴリーを検索します。

        Args:
            industry_class: 業種大分類
            industry: 業種
            tree_type: ツリータイプ
            kpi: KPI名

        Returns:
            list[DriverTreeCategory]: カテゴリーのリスト
        """
        query = select(DriverTreeCategory)

        if industry_class:
            query = query.where(DriverTreeCategory.industry_class == industry_class)
        if industry:
            query = query.where(DriverTreeCategory.industry == industry)
        if tree_type:
            query = query.where(DriverTreeCategory.tree_type == tree_type)
        if kpi:
            query = query.where(DriverTreeCategory.kpi == kpi)

        result = await self.db.execute(query)
        return list(result.scalars().all())
