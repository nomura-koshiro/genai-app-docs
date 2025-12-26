"""ドライバーツリーサービス共通ベース。

このモジュールは、ツリーサービスの共通機能を提供します。
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.driver_tree import (
    DriverTree,
    DriverTreeNode,
    DriverTreeRelationship,
    DriverTreeRelationshipChild,
)
from app.repositories.driver_tree import (
    DriverTreeCategoryRepository,
    DriverTreeFormulaRepository,
    DriverTreeNodeRepository,
    DriverTreeRepository,
)

logger = get_logger(__name__)


class DriverTreeServiceBase:
    """ドライバーツリーサービスの共通ベースクラス。"""

    def __init__(self, db: AsyncSession):
        """ドライバーツリーサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.tree_repository = DriverTreeRepository(db)
        self.category_repository = DriverTreeCategoryRepository(db)
        self.formula_repository = DriverTreeFormulaRepository(db)
        self.node_repository = DriverTreeNodeRepository(db)

    async def _get_tree_with_validation(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
    ) -> DriverTree:
        """ツリーを取得し、プロジェクトとの整合性を検証します。

        Args:
            project_id: プロジェクトID
            tree_id: ツリーID

        Returns:
            DriverTree: ツリー

        Raises:
            NotFoundError: ツリーが見つからない、またはプロジェクトに属していない場合
        """
        tree = await self.tree_repository.get_with_relations(tree_id)
        if not tree:
            raise NotFoundError(
                "ツリーが見つかりません",
                details={"tree_id": str(tree_id)},
            )

        if tree.project_id != project_id:
            raise NotFoundError(
                "このプロジェクトにツリーが見つかりません",
                details={"tree_id": str(tree_id), "project_id": str(project_id)},
            )

        return tree

    async def _build_tree_response(self, tree: DriverTree) -> dict[str, Any]:
        """ツリーレスポンスを構築します。

        Args:
            tree: ツリーモデル

        Returns:
            dict[str, Any]: ツリーレスポンス
        """
        # ツリーをリレーションシップ含めて再取得
        result = await self.db.execute(
            select(DriverTree)
            .where(DriverTree.id == tree.id)
            .options(
                selectinload(DriverTree.root_node),
                selectinload(DriverTree.relationships)
                .selectinload(DriverTreeRelationship.children)
                .selectinload(DriverTreeRelationshipChild.child_node),
                selectinload(DriverTree.relationships).selectinload(DriverTreeRelationship.parent_node),
            )
        )
        tree = result.scalar_one()

        # ノード情報を収集
        nodes = []
        node_ids: set[uuid.UUID] = set()

        # ルートノードを追加
        if tree.root_node:
            nodes.append(self._node_to_dict(tree.root_node))
            node_ids.add(tree.root_node.id)

        # リレーションシップからノードを収集
        relationships = []
        for rel in tree.relationships:
            # 親ノード
            if rel.parent_node and rel.parent_node.id not in node_ids:
                nodes.append(self._node_to_dict(rel.parent_node))
                node_ids.add(rel.parent_node.id)

            # 子ノード
            child_id_list = []
            for child in rel.children:
                child_id_list.append(child.child_node_id)
                if child.child_node and child.child_node_id not in node_ids:
                    nodes.append(self._node_to_dict(child.child_node))
                    node_ids.add(child.child_node_id)

            relationships.append(
                {
                    "parent_id": rel.parent_node_id,
                    "operator": rel.operator,
                    "child_id_list": child_id_list,
                }
            )

        return {
            "tree_id": tree.id,
            "name": tree.root_node.label if tree.root_node else "",
            "description": "",
            "root": self._node_to_dict(tree.root_node) if tree.root_node else None,
            "nodes": nodes,
            "relationship": relationships,
        }

    def _node_to_dict(self, node: DriverTreeNode) -> dict[str, Any]:
        """ノードを辞書形式に変換します。

        Args:
            node: ノードモデル

        Returns:
            dict[str, Any]: ノード辞書
        """
        return {
            "node_id": node.id,
            "label": node.label,
            "node_type": node.node_type,
            "position_x": node.position_x or 0,
            "position_y": node.position_y or 0,
        }
