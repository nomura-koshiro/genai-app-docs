"""DriverTree シーダー。"""

from typing import Any

from app.models.driver_tree import (
    DriverTree,
    DriverTreeNode,
    DriverTreePolicy,
    DriverTreeRelationship,
    DriverTreeRelationshipChild,
)
from app.models.project import Project

from .project import ProjectSeederMixin


class DriverTreeSeederMixin(ProjectSeederMixin):
    """DriverTree作成用Mixin。"""

    async def create_driver_tree_node(
        self,
        *,
        driver_tree: DriverTree,
        label: str = "テストノード",
        node_type: str = "計算",
        position_x: int = 0,
        position_y: int = 0,
    ) -> DriverTreeNode:
        """テスト用ドライバーツリーノードを作成。

        Args:
            driver_tree: 所属するドライバーツリー
            label: ノードラベル
            node_type: ノードタイプ（計算/入力/定数）
            position_x: X座標
            position_y: Y座標

        Returns:
            DriverTreeNode: 作成されたノード
        """
        node = DriverTreeNode(
            driver_tree_id=driver_tree.id,
            label=label,
            node_type=node_type,
            position_x=position_x,
            position_y=position_y,
        )
        self.db.add(node)
        await self.db.flush()
        await self.db.refresh(node)
        return node

    async def create_driver_tree(
        self,
        *,
        project: Project,
        name: str = "テストツリー",
        description: str = "",
    ) -> DriverTree:
        """テスト用ドライバーツリーを作成。

        Args:
            project: プロジェクト
            name: ツリー名
            description: ツリー説明

        Returns:
            DriverTree: 作成されたツリー
        """
        tree = DriverTree(
            project_id=project.id,
            name=name,
            description=description,
            root_node_id=None,
            formula_id=None,
        )
        self.db.add(tree)
        await self.db.flush()
        await self.db.refresh(tree)
        return tree

    async def create_driver_tree_relationship(
        self,
        *,
        tree: DriverTree,
        parent_node: DriverTreeNode,
        child_nodes: list[DriverTreeNode],
        operator: str = "+",
    ) -> DriverTreeRelationship:
        """テスト用ドライバーツリーリレーションシップを作成。

        Args:
            tree: ツリー
            parent_node: 親ノード
            child_nodes: 子ノードリスト
            operator: 演算子

        Returns:
            DriverTreeRelationship: 作成されたリレーションシップ
        """
        relationship = DriverTreeRelationship(
            driver_tree_id=tree.id,
            parent_node_id=parent_node.id,
            operator=operator,
        )
        self.db.add(relationship)
        await self.db.flush()
        await self.db.refresh(relationship)

        # 子ノードを追加
        for i, child_node in enumerate(child_nodes):
            child_rel = DriverTreeRelationshipChild(
                relationship_id=relationship.id,
                child_node_id=child_node.id,
                order_index=i,
            )
            self.db.add(child_rel)

        await self.db.flush()
        await self.db.refresh(relationship)
        return relationship

    async def create_driver_tree_policy(
        self,
        *,
        node: DriverTreeNode,
        label: str = "テスト施策",
        value: float = 10.0,
    ) -> DriverTreePolicy:
        """テスト用ドライバーツリー施策を作成。

        Args:
            node: ノード
            label: 施策名
            value: 施策値

        Returns:
            DriverTreePolicy: 作成された施策
        """
        policy = DriverTreePolicy(
            node_id=node.id,
            label=label,
            value=value,
        )
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def create_driver_tree_with_structure(
        self,
        *,
        project: Project,
        name: str = "テストツリー",
        description: str = "",
    ) -> dict[str, Any]:
        """構造を持つテスト用ドライバーツリーを作成。

        1. ツリーを作成（root_node_id は NULL）
        2. ルートノードと子ノードを作成
        3. リレーションシップを設定
        4. ツリーの root_node_id を更新

        Args:
            project: プロジェクト
            name: ツリー名
            description: ツリー説明

        Returns:
            dict: {tree, root_node, child_nodes, relationship}
        """
        # 1. ツリー作成（root_node_id は NULL）
        tree = await self.create_driver_tree(
            project=project,
            name=name,
            description=description,
        )

        # 2. ルートノード（計算ノード）
        root_node = await self.create_driver_tree_node(
            driver_tree=tree,
            label=name,
            node_type="計算",
            position_x=0,
            position_y=0,
        )

        # 3. 子ノード（入力ノード）
        child_node1 = await self.create_driver_tree_node(
            driver_tree=tree,
            label="子ノード1",
            node_type="入力",
            position_x=200,
            position_y=100,
        )
        child_node2 = await self.create_driver_tree_node(
            driver_tree=tree,
            label="子ノード2",
            node_type="入力",
            position_x=400,
            position_y=100,
        )

        # 4. リレーションシップ作成
        relationship = await self.create_driver_tree_relationship(
            tree=tree,
            parent_node=root_node,
            child_nodes=[child_node1, child_node2],
            operator="+",
        )

        # 5. root_node_id を更新
        tree.root_node_id = root_node.id
        await self.db.flush()
        await self.db.refresh(tree)

        return {
            "tree": tree,
            "root_node": root_node,
            "child_nodes": [child_node1, child_node2],
            "relationship": relationship,
        }

    async def seed_driver_tree_dataset(self) -> dict[str, Any]:
        """ドライバーツリー用テストデータセットをシード。

        Returns:
            dict: {project, owner, tree, root_node, child_nodes, relationship, policy}
        """
        project, owner = await self.create_project_with_owner()

        tree_data = await self.create_driver_tree_with_structure(
            project=project,
            name="シードツリー",
        )

        # 子ノードに施策を追加
        policy = await self.create_driver_tree_policy(
            node=tree_data["child_nodes"][0],
            label="テスト施策",
            value=15.0,
        )

        await self.db.commit()

        return {
            "project": project,
            "owner": owner,
            "tree": tree_data["tree"],
            "root_node": tree_data["root_node"],
            "child_nodes": tree_data["child_nodes"],
            "relationship": tree_data["relationship"],
            "policy": policy,
        }
