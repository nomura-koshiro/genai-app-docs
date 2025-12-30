"""ドライバーツリーカテゴリマスタリポジトリ。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver_tree.driver_tree_category import DriverTreeCategory
from app.schemas.admin.category import DriverTreeCategoryCreate, DriverTreeCategoryUpdate


class DriverTreeCategoryRepository:
    """ドライバーツリーカテゴリマスタリポジトリ。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, category_id: int) -> DriverTreeCategory | None:
        """IDでカテゴリを取得。"""
        result = await self.db.execute(select(DriverTreeCategory).where(DriverTreeCategory.id == category_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DriverTreeCategory]:
        """カテゴリ一覧を取得。"""
        result = await self.db.execute(
            select(DriverTreeCategory).order_by(DriverTreeCategory.category_id, DriverTreeCategory.industry_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """カテゴリ件数を取得。"""
        result = await self.db.execute(select(func.count(DriverTreeCategory.id)))
        return result.scalar_one()

    async def create(self, category_create: DriverTreeCategoryCreate) -> DriverTreeCategory:
        """カテゴリを作成。"""
        category = DriverTreeCategory(**category_create.model_dump())
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, category: DriverTreeCategory, category_update: DriverTreeCategoryUpdate) -> DriverTreeCategory:
        """カテゴリを更新。"""
        update_data = category_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete(self, category: DriverTreeCategory) -> None:
        """カテゴリを削除。"""
        await self.db.delete(category)
        await self.db.flush()

    async def has_trees(self, category_id: int) -> bool:
        """カテゴリにドライバーツリーが紐づいているか確認。"""
        from app.models.driver_tree.driver_tree import DriverTree

        result = await self.db.execute(select(func.count(DriverTree.id)).where(DriverTree.category_id == category_id))
        return result.scalar_one() > 0

    async def get_with_formula_count(self, category_id: int) -> dict | None:
        """関連数式数を含めてカテゴリを取得します。"""
        from app.models.driver_tree.driver_tree_formula import DriverTreeFormula

        stmt = (
            select(
                DriverTreeCategory,
                func.count(DriverTreeFormula.id).label("formula_count"),
            )
            .outerjoin(DriverTreeFormula, DriverTreeFormula.category_id == DriverTreeCategory.id)
            .where(DriverTreeCategory.id == category_id)
            .group_by(DriverTreeCategory.id)
        )

        result = await self.db.execute(stmt)
        row = result.first()

        if not row:
            return None

        category, formula_count = row
        return {
            "category": category,
            "formula_count": formula_count,
        }

    async def get_list_with_formula_counts(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """関連数式数を含めてカテゴリ一覧を取得します。"""
        from app.models.driver_tree.driver_tree_formula import DriverTreeFormula

        # カウント
        count_stmt = select(func.count(DriverTreeCategory.id))
        total = await self.db.scalar(count_stmt) or 0

        # データ取得
        stmt = (
            select(
                DriverTreeCategory,
                func.count(DriverTreeFormula.id).label("formula_count"),
            )
            .outerjoin(DriverTreeFormula, DriverTreeFormula.category_id == DriverTreeCategory.id)
            .group_by(DriverTreeCategory.id)
            .order_by(DriverTreeCategory.category_id, DriverTreeCategory.industry_id)
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [{"category": row[0], "formula_count": row[1]} for row in rows], total
