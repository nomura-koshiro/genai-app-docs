"""ドライバーツリーリポジトリ。

このモジュールは、DriverTreeモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.driver_tree import DriverTree
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class DriverTreeRepository(BaseRepository[DriverTree, uuid.UUID]):
    """DriverTreeモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    ドライバーツリー管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """ドライバーツリーリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(DriverTree, db)

    async def get_with_relations(self, tree_id: uuid.UUID) -> DriverTree | None:
        """リレーションシップを含めてツリーを取得します。

        Args:
            tree_id: ツリーID

        Returns:
            DriverTree | None: ツリー（ルートノード、リレーションシップ含む）
        """
        result = await self.db.execute(
            select(DriverTree)
            .where(DriverTree.id == tree_id)
            .options(
                selectinload(DriverTree.root_node),
                selectinload(DriverTree.relationships),
                selectinload(DriverTree.formula),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DriverTree]:
        """プロジェクトに属するツリー一覧を取得します。

        Args:
            project_id: プロジェクトID
            skip: スキップするレコード数
            limit: 取得する最大レコード数

        Returns:
            list[DriverTree]: ツリー一覧（作成日時降順）
        """
        result = await self.db.execute(
            select(DriverTree).where(DriverTree.project_id == project_id).order_by(DriverTree.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        """プロジェクトに属するツリー数を取得します。

        Args:
            project_id: プロジェクトID

        Returns:
            int: ツリー数
        """
        from sqlalchemy import func

        result = await self.db.execute(select(func.count()).select_from(DriverTree).where(DriverTree.project_id == project_id))
        return result.scalar_one()
