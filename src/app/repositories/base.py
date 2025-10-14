"""共通のCRUD操作用のベースリポジトリ。"""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """共通のCRUD操作を持つベースリポジトリ。"""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            model: SQLAlchemyモデルクラス
            db: データベースセッション
        """
        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        """IDによってレコードを取得します。

        Args:
            id: レコードID

        Returns:
            モデルインスタンス、見つからない場合はNone
        """
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        """オプションのフィルタリングで複数のレコードを取得します。

        Args:
            skip: スキップするレコード数
            limit: 返す最大レコード数
            filters: フィルタ条件

        Returns:
            モデルインスタンスのリスト
        """
        query = select(self.model)

        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **obj_in: Any) -> ModelType:
        """新しいレコードを作成します。

        Args:
            obj_in: オブジェクトデータ

        Returns:
            作成されたモデルインスタンス
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, **update_data: Any) -> ModelType:
        """レコードを更新します。

        Args:
            db_obj: 更新するデータベースオブジェクト
            update_data: 更新データ

        Returns:
            更新されたモデルインスタンス
        """
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        """レコードを削除します。

        Args:
            id: レコードID

        Returns:
            削除された場合はTrue、見つからない場合はFalse
        """
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
            return True
        return False

    async def count(self, **filters: Any) -> int:
        """オプションのフィルタリングでレコードを数えます。

        Args:
            filters: フィルタ条件

        Returns:
            レコード数
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)

        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar_one()
