"""ドライバーツリー施策リポジトリ。

このモジュールは、DriverTreePolicyモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.driver_tree import DriverTreePolicy
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class DriverTreePolicyRepository(BaseRepository[DriverTreePolicy, uuid.UUID]):
    """DriverTreePolicyモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    施策管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """施策リポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(DriverTreePolicy, db)

    async def list_by_node(self, node_id: uuid.UUID) -> list[DriverTreePolicy]:
        """ノードに紐づく施策一覧を取得します。

        Args:
            node_id: ノードID

        Returns:
            list[DriverTreePolicy]: 施策一覧（作成日時順）
        """
        result = await self.db.execute(
            select(DriverTreePolicy).where(DriverTreePolicy.node_id == node_id).order_by(DriverTreePolicy.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_node_and_label(
        self,
        node_id: uuid.UUID,
        label: str,
    ) -> DriverTreePolicy | None:
        """ノードIDとラベルで施策を検索します。

        Args:
            node_id: ノードID
            label: 施策ラベル

        Returns:
            DriverTreePolicy | None: 施策
        """
        result = await self.db.execute(
            select(DriverTreePolicy).where(DriverTreePolicy.node_id == node_id).where(DriverTreePolicy.label == label)
        )
        return result.scalar_one_or_none()

    async def count_by_node(self, node_id: uuid.UUID) -> int:
        """ノードに紐づく施策数を取得します。

        Args:
            node_id: ノードID

        Returns:
            int: 施策数
        """
        from sqlalchemy import func

        result = await self.db.execute(select(func.count()).select_from(DriverTreePolicy).where(DriverTreePolicy.node_id == node_id))
        return result.scalar_one()

    async def list_by_tree(self, tree_id: uuid.UUID) -> list[DriverTreePolicy]:
        """ツリーに紐づくすべての施策を取得します。

        Args:
            tree_id: ツリーID

        Returns:
            list[DriverTreePolicy]: 施策一覧（ノードとの関連を含む）
        """
        from sqlalchemy.orm import selectinload

        from app.models.driver_tree import DriverTreeNode

        result = await self.db.execute(
            select(DriverTreePolicy)
            .join(DriverTreeNode, DriverTreePolicy.node_id == DriverTreeNode.id)
            .where(DriverTreeNode.tree_id == tree_id)
            .options(selectinload(DriverTreePolicy.node))
            .order_by(DriverTreeNode.label, DriverTreePolicy.created_at.asc())
        )
        return list(result.scalars().all())
