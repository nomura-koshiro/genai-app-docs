"""ドライバーツリーノードサービス共通ベース。

このモジュールは、ノードサービスの共通機能を提供します。
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
    DriverTreeNodeRepository,
    DriverTreePolicyRepository,
    DriverTreeRepository,
)

logger = get_logger(__name__)


class DriverTreeNodeServiceBase:
    """ドライバーツリーノードサービスの共通ベースクラス。"""

    def __init__(self, db: AsyncSession):
        """ドライバーツリーノードサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.node_repository = DriverTreeNodeRepository(db)
        self.policy_repository = DriverTreePolicyRepository(db)
        self.tree_repository = DriverTreeRepository(db)

    async def _get_node_with_validation(
        self,
        node_id: uuid.UUID,
    ) -> DriverTreeNode:
        """ノードを取得し検証します。

        Args:
            node_id: ノードID

        Returns:
            DriverTreeNode: ノード

        Raises:
            NotFoundError: ノードが見つからない場合
        """
        node = await self.node_repository.get_with_relations(node_id)
        if not node:
            raise NotFoundError(
                "ノードが見つかりません",
                details={"node_id": str(node_id)},
            )
        return node

    async def _get_tree_by_node(
        self,
        node_id: uuid.UUID,
    ) -> DriverTree | None:
        """ノードが属するツリーを取得します。

        Args:
            node_id: ノードID

        Returns:
            DriverTree | None: ツリー
        """
        # ルートノードとしてツリーを検索
        result = await self.db.execute(select(DriverTree).where(DriverTree.root_node_id == node_id))
        tree = result.scalar_one_or_none()
        if tree:
            return tree

        # リレーションシップの親ノードまたは子ノードとして検索
        result = await self.db.execute(
            select(DriverTree)
            .join(DriverTreeRelationship, DriverTree.id == DriverTreeRelationship.driver_tree_id)
            .where(DriverTreeRelationship.parent_node_id == node_id)
        )
        tree = result.scalar_one_or_none()
        if tree:
            return tree

        result = await self.db.execute(
            select(DriverTree)
            .join(DriverTreeRelationship, DriverTree.id == DriverTreeRelationship.driver_tree_id)
            .join(DriverTreeRelationshipChild, DriverTreeRelationship.id == DriverTreeRelationshipChild.relationship_id)
            .where(DriverTreeRelationshipChild.child_node_id == node_id)
        )
        return result.scalar_one_or_none()

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

    async def _build_policies_response(self, node_id: uuid.UUID) -> dict[str, Any]:
        """施策レスポンスを構築します。

        Args:
            node_id: ノードID

        Returns:
            dict[str, Any]: 施策レスポンス
        """
        policies = await self.policy_repository.list_by_node(node_id)
        return {
            "node_id": node_id,
            "policies": [
                {
                    "policy_id": p.id,
                    "name": p.label,
                    "value": p.value,
                }
                for p in policies
            ],
        }
