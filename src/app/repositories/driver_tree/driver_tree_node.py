"""ドライバーツリーノードリポジトリ。

このモジュールは、DriverTreeNodeモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.driver_tree import DriverTreeNode
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class DriverTreeNodeRepository(BaseRepository[DriverTreeNode, uuid.UUID]):
    """DriverTreeNodeモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    ノード管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """ノードリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(DriverTreeNode, db)

    async def get_with_relations(self, node_id: uuid.UUID) -> DriverTreeNode | None:
        """リレーションシップを含めてノードを取得します。

        Args:
            node_id: ノードID

        Returns:
            DriverTreeNode | None: ノード（データフレーム、施策含む）
        """
        result = await self.db.execute(
            select(DriverTreeNode)
            .where(DriverTreeNode.id == node_id)
            .options(
                selectinload(DriverTreeNode.data_frame),
                selectinload(DriverTreeNode.policies),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_type(self, node_type: str) -> list[DriverTreeNode]:
        """ノードタイプでノード一覧を取得します。

        Args:
            node_type: ノードタイプ（計算/入力/定数）

        Returns:
            list[DriverTreeNode]: ノード一覧
        """
        result = await self.db.execute(
            select(DriverTreeNode).where(DriverTreeNode.node_type == node_type).order_by(DriverTreeNode.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_policies(self, node_id: uuid.UUID) -> DriverTreeNode | None:
        """施策一覧を含めてノードを取得します。

        Args:
            node_id: ノードID

        Returns:
            DriverTreeNode | None: ノード（施策含む）
        """
        result = await self.db.execute(
            select(DriverTreeNode).where(DriverTreeNode.id == node_id).options(selectinload(DriverTreeNode.policies))
        )
        return result.scalar_one_or_none()

    async def get_many_with_policies(self, node_ids: list[uuid.UUID]) -> dict[uuid.UUID, DriverTreeNode]:
        """複数のノードを施策付きで一括取得します。

        N+1クエリを回避するため、selectinloadを使用して一括取得します。

        Args:
            node_ids: ノードIDリスト

        Returns:
            dict[uuid.UUID, DriverTreeNode]: ノードIDをキーとした辞書
        """
        if not node_ids:
            return {}

        result = await self.db.execute(
            select(DriverTreeNode).where(DriverTreeNode.id.in_(node_ids)).options(selectinload(DriverTreeNode.policies))
        )
        return {node.id: node for node in result.scalars().all()}
