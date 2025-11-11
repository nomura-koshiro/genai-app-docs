"""DriverTreeNodeリポジトリ。

このモジュールは、DriverTreeNodeモデルのデータアクセスを提供します。
木構造の親子関係を考慮したCRUD操作をサポートします。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.driver_tree_node import DriverTreeNode
from app.repositories.base import BaseRepository


class DriverTreeNodeRepository(BaseRepository[DriverTreeNode, uuid.UUID]):
    """DriverTreeNodeリポジトリ。

    木構造のノードに対するデータアクセスを提供します。

    Args:
        db: データベースセッション

    Example:
        >>> repo = DriverTreeNodeRepository(db)
        >>> # ルートノード作成
        >>> root = await repo.create(tree_id=tree_id, label="粗利")
        >>> # 子ノード作成
        >>> child = await repo.create(
        ...     tree_id=tree_id,
        ...     label="売上",
        ...     parent_id=root.id,
        ...     operator="-"
        ... )
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            db: データベースセッション
        """
        super().__init__(DriverTreeNode, db)

    async def create(
        self,
        tree_id: uuid.UUID,
        label: str,
        parent_id: uuid.UUID | None = None,
        operator: str | None = None,
        x: int | None = None,
        y: int | None = None,
    ) -> DriverTreeNode:
        """ノードを作成します。

        Args:
            tree_id: 所属するツリーのID
            label: ノードのラベル
            parent_id: 親ノードID（Noneの場合はルートノード）
            operator: 親ノードとの演算子
            x: X座標
            y: Y座標

        Returns:
            DriverTreeNode: 作成されたノード

        Example:
            >>> # ルートノード
            >>> root = await repo.create(tree_id=tree_id, label="粗利")
            >>> # 子ノード
            >>> child = await repo.create(
            ...     tree_id=tree_id,
            ...     label="売上",
            ...     parent_id=root.id,
            ...     operator="-"
            ... )
        """
        node = DriverTreeNode(
            tree_id=tree_id,
            label=label,
            parent_id=parent_id,
            operator=operator,
            x=x,
            y=y,
        )
        self.db.add(node)
        await self.db.flush()
        await self.db.refresh(node)
        return node

    async def find_by_tree_id(self, tree_id: uuid.UUID) -> list[DriverTreeNode]:
        """指定されたツリーに属するすべてのノードを取得します。

        Args:
            tree_id: ツリーID

        Returns:
            list[DriverTreeNode]: ノードのリスト

        Example:
            >>> nodes = await repo.find_by_tree_id(tree_id)
        """
        result = await self.db.execute(
            select(DriverTreeNode).where(DriverTreeNode.tree_id == tree_id)
        )
        return list(result.scalars().all())

    async def find_root_by_tree_id(self, tree_id: uuid.UUID) -> DriverTreeNode | None:
        """指定されたツリーのルートノードを取得します。

        Args:
            tree_id: ツリーID

        Returns:
            DriverTreeNode | None: ルートノード、または None

        Example:
            >>> root = await repo.find_root_by_tree_id(tree_id)
        """
        result = await self.db.execute(
            select(DriverTreeNode)
            .where(DriverTreeNode.tree_id == tree_id)
            .where(DriverTreeNode.parent_id.is_(None))
        )
        return result.scalar_one_or_none()

    async def find_children(self, parent_id: uuid.UUID) -> list[DriverTreeNode]:
        """指定された親ノードの子ノードを取得します。

        Args:
            parent_id: 親ノードID

        Returns:
            list[DriverTreeNode]: 子ノードのリスト

        Example:
            >>> children = await repo.find_children(parent_id)
        """
        result = await self.db.execute(
            select(DriverTreeNode).where(DriverTreeNode.parent_id == parent_id)
        )
        return list(result.scalars().all())

    async def get_with_children(self, id: uuid.UUID) -> DriverTreeNode | None:
        """ノードを子ノードと共に取得します（再帰的）。

        Args:
            id: ノードID

        Returns:
            DriverTreeNode | None: ノード、または None

        Example:
            >>> node = await repo.get_with_children(node_id)
            >>> for child in node.children:
            ...     print(child.label)
        """
        result = await self.db.execute(
            select(DriverTreeNode)
            .where(DriverTreeNode.id == id)
            .options(selectinload(DriverTreeNode.children))
        )
        return result.scalar_one_or_none()

    async def find_by_label_and_tree(
        self, tree_id: uuid.UUID, label: str
    ) -> DriverTreeNode | None:
        """ツリー内でラベルからノードを検索します。

        Args:
            tree_id: ツリーID
            label: ノードのラベル

        Returns:
            DriverTreeNode | None: 見つかったノード、または None

        Example:
            >>> node = await repo.find_by_label_and_tree(tree_id, "粗利")
        """
        result = await self.db.execute(
            select(DriverTreeNode)
            .where(DriverTreeNode.tree_id == tree_id)
            .where(DriverTreeNode.label == label)
        )
        return result.scalar_one_or_none()
