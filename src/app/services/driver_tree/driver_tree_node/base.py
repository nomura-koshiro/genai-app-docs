"""ドライバーツリーノードサービス共通ベース。

このモジュールは、ノードサービスの共通機能を提供します。
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
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

    async def _validate_no_circular_reference(
        self,
        parent_node_id: uuid.UUID,
        child_node_ids: list[uuid.UUID],
    ) -> None:
        """循環参照がないことを検証します。

        親ノードが子孫ノードに含まれていないかをチェックします。
        親→子→孫→親のような循環が発生する場合はValidationErrorを発生させます。

        Args:
            parent_node_id: 親ノードID
            child_node_ids: 子ノードIDリスト

        Raises:
            ValidationError: 循環参照が検出された場合
        """
        # 親ノードが子ノードリストに含まれていないかチェック
        if parent_node_id in child_node_ids:
            raise ValidationError(
                "循環参照が検出されました: 親ノードを子ノードとして設定することはできません",
                details={
                    "parent_node_id": str(parent_node_id),
                    "child_node_ids": [str(cid) for cid in child_node_ids],
                },
            )

        # 子ノードの子孫をたどって親ノードが含まれていないかチェック
        visited: set[uuid.UUID] = set()
        to_check: list[uuid.UUID] = list(child_node_ids)

        while to_check:
            current_id = to_check.pop()
            if current_id in visited:
                continue
            visited.add(current_id)

            # このノードの子ノードを取得
            result = await self.db.execute(
                select(DriverTreeRelationshipChild.child_node_id)
                .join(
                    DriverTreeRelationship,
                    DriverTreeRelationshipChild.relationship_id == DriverTreeRelationship.id,
                )
                .where(DriverTreeRelationship.parent_node_id == current_id)
            )
            descendant_ids = [row[0] for row in result.fetchall()]

            for descendant_id in descendant_ids:
                if descendant_id == parent_node_id:
                    raise ValidationError(
                        "循環参照が検出されました: 親ノードが子孫ノードに存在します",
                        details={
                            "parent_node_id": str(parent_node_id),
                            "circular_path_via": str(current_id),
                        },
                    )
                to_check.append(descendant_id)

        logger.debug(
            "循環参照チェック完了",
            parent_node_id=str(parent_node_id),
            checked_nodes=len(visited),
        )

    async def _validate_order_index_uniqueness(
        self,
        relationship_id: uuid.UUID,
        order_indices: list[int],
        exclude_child_ids: list[uuid.UUID] | None = None,
    ) -> None:
        """order_indexの一意性を検証します。

        同一リレーションシップ内でorder_indexが重複していないかチェックします。

        Args:
            relationship_id: リレーションシップID
            order_indices: 設定しようとしているorder_indexのリスト
            exclude_child_ids: 除外する子ノードIDリスト（更新時に既存のものを除外）

        Raises:
            ValidationError: order_indexが重複している場合
        """
        # 入力リスト内での重複チェック
        if len(order_indices) != len(set(order_indices)):
            duplicates = [idx for idx in order_indices if order_indices.count(idx) > 1]
            raise ValidationError(
                "order_indexが重複しています",
                details={
                    "relationship_id": str(relationship_id),
                    "duplicate_indices": list(set(duplicates)),
                },
            )

        # 既存のorder_indexとの重複チェック
        query = select(DriverTreeRelationshipChild.order_index).where(DriverTreeRelationshipChild.relationship_id == relationship_id)
        if exclude_child_ids:
            query = query.where(DriverTreeRelationshipChild.child_node_id.notin_(exclude_child_ids))

        result = await self.db.execute(query)
        existing_indices = {row[0] for row in result.fetchall()}

        conflicts = set(order_indices) & existing_indices
        if conflicts:
            raise ValidationError(
                "order_indexが既存のエントリと重複しています",
                details={
                    "relationship_id": str(relationship_id),
                    "conflicting_indices": list(conflicts),
                },
            )

        logger.debug(
            "order_index一意性チェック完了",
            relationship_id=str(relationship_id),
            checked_indices=order_indices,
        )

    def _normalize_order_indices(self, children_count: int) -> list[int]:
        """order_indexを正規化します。

        0から連番のorder_indexリストを生成します。

        Args:
            children_count: 子ノード数

        Returns:
            list[int]: 正規化されたorder_indexリスト
        """
        return list(range(children_count))
