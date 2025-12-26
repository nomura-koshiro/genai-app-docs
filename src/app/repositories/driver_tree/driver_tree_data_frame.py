"""DriverTreeDataFrame リポジトリ。

このモジュールは、DriverTreeDataFrameのデータベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.driver_tree import DriverTreeDataFrame
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class DriverTreeDataFrameRepository(BaseRepository[DriverTreeDataFrame, uuid.UUID]):
    """DriverTreeDataFrame リポジトリ。

    DriverTreeDataFrameテーブルへのアクセスを提供します。

    BaseRepositoryの共通CRUD操作に加えて、
    データフレーム管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """データフレームリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(DriverTreeDataFrame, db)

    async def list_by_file(self, driver_tree_file_id: uuid.UUID) -> list[DriverTreeDataFrame]:
        """ドライバーツリーファイルに紐づくデータフレーム一覧を取得します。

        Args:
            driver_tree_file_id: ドライバーツリーファイルID

        Returns:
            list[DriverTreeDataFrame]: データフレーム一覧
        """
        result = await self.db.execute(
            select(DriverTreeDataFrame)
            .where(DriverTreeDataFrame.driver_tree_file_id == driver_tree_file_id)
            .order_by(DriverTreeDataFrame.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_file_and_column(
        self,
        driver_tree_file_id: uuid.UUID,
        column_name: str,
    ) -> DriverTreeDataFrame | None:
        """ファイルIDと列名でデータフレームを検索します。

        Args:
            driver_tree_file_id: ドライバーツリーファイルID
            column_name: 列名

        Returns:
            DriverTreeDataFrame | None: データフレーム
        """
        result = await self.db.execute(
            select(DriverTreeDataFrame)
            .where(DriverTreeDataFrame.driver_tree_file_id == driver_tree_file_id)
            .where(DriverTreeDataFrame.column_name == column_name)
        )
        return result.scalar_one_or_none()
