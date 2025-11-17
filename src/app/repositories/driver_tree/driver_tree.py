"""DriverTreeリポジトリ。

このモジュールは、DriverTreeモデルのデータアクセスを提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import DriverTree
from app.repositories.base import BaseRepository


class DriverTreeRepository(BaseRepository[DriverTree, uuid.UUID]):
    """DriverTreeリポジトリ。

    ツリーと関連ノードに対するデータアクセスを提供します。

    Args:
        db: データベースセッション

    Example:
        >>> repo = DriverTreeRepository(db)
        >>> tree = await repo.create(name="粗利分析")
    """

    def __init__(self, db: AsyncSession):
        """リポジトリを初期化します。

        Args:
            db: データベースセッション
        """
        super().__init__(DriverTree, db)

    async def create(
        self,
        name: str | None = None,
        root_node_id: uuid.UUID | None = None,
    ) -> DriverTree:
        """ツリーを作成します。

        Args:
            name: ツリー名（任意）
            root_node_id: ルートノードID（任意、後で設定可能）

        Returns:
            DriverTree: 作成されたツリー

        Example:
            >>> tree = await repo.create(name="粗利分析")
        """
        tree = DriverTree(name=name, root_node_id=root_node_id)
        self.db.add(tree)
        await self.db.flush()
        await self.db.refresh(tree)
        return tree

    async def get_with_nodes(self, id: uuid.UUID) -> DriverTree | None:
        """ツリーをすべてのノードと共に取得します。

        Args:
            id: ツリーID

        Returns:
            DriverTree | None: ツリー、または None

        Example:
            >>> tree = await repo.get_with_nodes(tree_id)
            >>> print(len(tree.nodes))
        """
        result = await self.db.execute(
            select(DriverTree)
            .where(DriverTree.id == id)
            .options(
                selectinload(DriverTree.nodes),
                selectinload(DriverTree.root_node),
            )
        )
        return result.scalar_one_or_none()

    async def get_with_tree_structure(self, id: uuid.UUID) -> DriverTree | None:
        """ツリーを木構造（ルートノードと再帰的な子ノード）と共に取得します。

        Args:
            id: ツリーID

        Returns:
            DriverTree | None: ツリー、または None

        Example:
            >>> tree = await repo.get_with_tree_structure(tree_id)
            >>> if tree.root_node:
            ...     print(tree.root_node.label)
            ...     for child in tree.root_node.children:
            ...         print(f"  - {child.label}")
        """
        result = await self.db.execute(
            select(DriverTree)
            .where(DriverTree.id == id)
            .options(selectinload(DriverTree.root_node).selectinload(DriverTree.root_node.property.mapper.class_.children))
        )
        tree = result.scalar_one_or_none()

        # 再帰的に子ノードをロード
        if tree and tree.root_node:
            await self._load_children_recursive(tree.root_node)

        return tree

    async def _load_children_recursive(self, node) -> None:
        """ノードの子を再帰的にロードします（内部メソッド）。

        Args:
            node: ノード
        """
        # 子ノードをロード
        await self.db.refresh(node, ["children"])

        # 各子ノードについて再帰的にロード
        for child in node.children:
            await self._load_children_recursive(child)

    async def update_root_node(self, tree_id: uuid.UUID, root_node_id: uuid.UUID) -> DriverTree | None:
        """ツリーのルートノードを更新します。

        Args:
            tree_id: ツリーID
            root_node_id: 新しいルートノードID

        Returns:
            DriverTree | None: 更新されたツリー、または None

        Example:
            >>> tree = await repo.update_root_node(tree_id, new_root_id)
        """
        tree = await self.get(tree_id)
        if tree:
            tree.root_node_id = root_node_id
            await self.db.flush()
            await self.db.refresh(tree)
        return tree
