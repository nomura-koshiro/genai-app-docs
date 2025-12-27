"""カテゴリマスタ管理サービス。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
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
        """カテゴリマスタ一覧を取得。"""
        categories = await self.repository.list(skip=skip, limit=limit)
        total = await self.repository.count()

        return DriverTreeCategoryListResponse(
            categories=[DriverTreeCategoryResponse.model_validate(category) for category in categories],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_category(self, category_id: int) -> DriverTreeCategoryResponse:
        """カテゴリマスタ詳細を取得。"""
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"カテゴリマスタが見つかりません: {category_id}")

        return DriverTreeCategoryResponse.model_validate(category)

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
        if await self.repository.has_trees(category_id):
            raise ConflictError("このカテゴリにはドライバーツリーが紐づいているため削除できません")

        await self.repository.delete(category)
        await self.db.commit()

        logger.info(f"カテゴリマスタ削除: id={category_id}")
