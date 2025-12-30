"""ドライバーツリーCRUDサービス。

このモジュールは、ドライバーツリーのCRUD操作を提供します。
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import transactional
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.models.driver_tree import (
    DriverTree,
    DriverTreePolicy,
    DriverTreeRelationship,
    DriverTreeRelationshipChild,
)
from app.services.driver_tree.driver_tree.base import DriverTreeServiceBase
from app.services.driver_tree.formula_parser import FormulaParser

logger = get_logger(__name__)


class DriverTreeCrudService(DriverTreeServiceBase):
    """ドライバーツリーのCRUD操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """ドライバーツリーCRUDサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)
        self.formula_parser = FormulaParser()

    @transactional
    async def create_tree(
        self,
        project_id: uuid.UUID,
        name: str,
        description: str | None,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """新規ツリーを作成します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            name: ツリー名
            description: 説明（オプション）
            user_id: 作成者のユーザーID

        Returns:
            dict[str, Any]: 作成結果
                - tree_id: uuid - ツリーID
                - name: str - ツリー名
                - description: str - 説明
                - created_at: datetime - 作成日時
        """
        logger.info(
            "ツリーを作成中",
            project_id=str(project_id),
            name=name,
            user_id=str(user_id),
        )

        # ツリーを作成（root_nodeは作成しない）
        tree = await self.tree_repository.create(
            project_id=project_id,
            name=name,
            description=description or "",
            root_node_id=None,
            formula_id=None,
        )

        logger.info(
            "ツリーを作成しました",
            tree_id=str(tree.id),
            project_id=str(project_id),
            name=name,
        )

        return {
            "tree_id": tree.id,
            "name": name,
            "description": description or "",
            "created_at": tree.created_at,
        }

    async def list_trees(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーの一覧を取得します。

        数式マスタ名、ノード数、施策数を含む詳細情報を返します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: ツリー一覧
                - trees: list[dict] - ツリー一覧（集計情報含む）
        """
        trees = await self.tree_repository.list_by_project(project_id)

        # 一括で集計情報を取得（N+1クエリ回避）
        tree_ids = [tree.id for tree in trees]
        aggregate_counts = await self.tree_repository.get_aggregate_counts(tree_ids)

        tree_list = []
        for tree in trees:
            counts = aggregate_counts.get(tree.id, {"node_count": 0, "policy_count": 0})

            # 数式マスタ名を取得
            formula_master_name = None
            if tree.formula:
                formula_master_name = tree.formula.driver_type

            tree_list.append(
                {
                    "tree_id": tree.id,
                    "name": tree.name,
                    "description": tree.description,
                    "status": tree.status,
                    "formula_master_name": formula_master_name,
                    "node_count": counts["node_count"],
                    "policy_count": counts["policy_count"],
                    "created_at": tree.created_at,
                    "updated_at": tree.updated_at,
                }
            )

        return {"trees": tree_list}

    async def get_tree(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーの全体構造を取得します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            tree_id: ツリーID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: ツリー情報

        Raises:
            NotFoundError: ツリーが見つからない場合
        """
        tree = await self._get_tree_with_validation(project_id, tree_id)
        return await self._build_tree_response(tree)

    @transactional
    async def import_formula(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        position_x: int,
        position_y: int,
        formulas: list[str],
        sheet_id: uuid.UUID | None,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーに数式データをインポートします。

        数式を解析してツリー構造を構築します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            tree_id: ツリーID
            position_x: ルートノードX座標
            position_y: ルートノードY座標
            formulas: 数式リスト
            sheet_id: 入力シートID（オプション）
            user_id: ユーザーID

        Returns:
            dict[str, Any]: インポート結果（ツリー全体の最新構造）

        Raises:
            NotFoundError: ツリーが見つからない場合
            ValidationError: 数式の解析に失敗した場合
        """
        logger.info(
            "数式をインポート中",
            tree_id=str(tree_id),
            formula_count=len(formulas),
        )

        tree = await self._get_tree_with_validation(project_id, tree_id)

        if not formulas:
            raise ValidationError(
                "数式が指定されていません",
                details={"formulas": formulas},
            )

        # 数式を解析してノードとリレーションシップを作成
        for formula in formulas:
            await self._parse_and_create_nodes(tree, formula, position_x, position_y)

        # ルートノードの位置を更新（root_node_idで存在確認し、リポジトリから取得）
        if tree.root_node_id:
            root_node = await self.node_repository.get(tree.root_node_id)
            if root_node:
                await self.node_repository.update(
                    root_node,
                    position_x=position_x,
                    position_y=position_y,
                )

        logger.info(
            "数式をインポートしました",
            tree_id=str(tree_id),
            formula_count=len(formulas),
        )

        return await self._build_tree_response(tree)

    async def _parse_and_create_nodes(
        self,
        tree: DriverTree,
        formula: str,
        base_x: int,
        base_y: int,
    ) -> None:
        """数式を解析してノードとリレーションシップを作成します。

        Args:
            tree: ツリー
            formula: 数式（例: "売上高 = 単価 * 数量"）
            base_x: ベースX座標
            base_y: ベースY座標
        """
        # 数式を解析（FormulaParserに委譲）
        parsed = self.formula_parser.parse(formula)
        result_name = parsed.result_name
        operator = parsed.operator
        operands = parsed.operands

        # 結果ノードの作成または更新（ルートノードを使用）
        # lazy loadを避けるため、root_node_idでチェックしリポジトリから取得
        root_node = None
        if tree.root_node_id:
            root_node = await self.node_repository.get(tree.root_node_id)

        if root_node and root_node.label == result_name:
            result_node = root_node
        else:
            # ルートノードのラベルを更新
            if root_node:
                await self.node_repository.update(root_node, label=result_name)
                result_node = root_node
            else:
                result_node = await self.node_repository.create(
                    label=result_name,
                    node_type="計算",
                    position_x=base_x,
                    position_y=base_y,
                )
                await self.tree_repository.update(tree, root_node_id=result_node.id)

        # 子ノードの作成
        child_nodes = []
        for i, operand in enumerate(operands):
            # ノードタイプを判定（FormulaParserに委譲）
            node_type = self.formula_parser.determine_node_type(operand)

            child_node = await self.node_repository.create(
                label=operand,
                node_type=node_type,
                position_x=base_x + (i + 1) * 200,
                position_y=base_y + 100,
            )
            child_nodes.append(child_node)

        # リレーションシップの作成
        if operator and child_nodes:
            relationship = DriverTreeRelationship(
                driver_tree_id=tree.id,
                parent_node_id=result_node.id,
                operator=operator,
            )
            self.db.add(relationship)
            await self.db.flush()
            await self.db.refresh(relationship)

            # 子ノードをリレーションシップに追加
            for i, child_node in enumerate(child_nodes):
                child_rel = DriverTreeRelationshipChild(
                    relationship_id=relationship.id,
                    child_node_id=child_node.id,
                    order_index=i,
                )
                self.db.add(child_rel)

            await self.db.flush()

    @transactional
    async def reset_tree(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーを初期状態にリセットします。

        全ノードのデータがクリアされます（構造は維持）。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            tree_id: ツリーID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: リセット結果
                - tree: dict - リセット後のツリー全体構造
                - reset_at: datetime - リセット日時

        Raises:
            NotFoundError: ツリーが見つからない場合
        """
        logger.info(
            "ツリーをリセット中",
            tree_id=str(tree_id),
            user_id=str(user_id),
        )

        tree = await self._get_tree_with_validation(project_id, tree_id)

        # 全リレーションシップを削除（ルートノード以外のノードは残る）
        for relationship in tree.relationships:
            await self.db.delete(relationship)

        await self.db.flush()

        reset_at = datetime.now(UTC)

        logger.info(
            "ツリーをリセットしました",
            tree_id=str(tree_id),
        )

        tree_response = await self._build_tree_response(tree)

        return {
            "tree": tree_response,
            "reset_at": reset_at,
        }

    @transactional
    async def delete_tree(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーを完全に削除します。

        全関連ノード、施策、計算結果も削除されます。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            tree_id: ツリーID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 削除結果
                - success: bool - 成功フラグ
                - deleted_at: datetime - 削除日時

        Raises:
            NotFoundError: ツリーが見つからない場合
        """
        logger.info(
            "ツリーを削除中",
            tree_id=str(tree_id),
            user_id=str(user_id),
        )

        await self._get_tree_with_validation(project_id, tree_id)

        # ツリーを削除（CASCADEで関連データも削除される）
        await self.tree_repository.delete(tree_id)

        deleted_at = datetime.now(UTC)

        logger.info(
            "ツリーを削除しました",
            tree_id=str(tree_id),
        )

        return {
            "success": True,
            "deleted_at": deleted_at,
        }

    @transactional
    async def duplicate_tree(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
        new_name: str | None = None,
    ) -> dict[str, Any]:
        """ドライバーツリーを複製します。

        ツリーとその関連データ（ノード、リレーションシップ）を深いコピーで複製します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            tree_id: 複製元ツリーID
            user_id: 複製実行者のユーザーID
            new_name: 新しいツリー名（オプション、未指定の場合は「(コピー)」を追加）

        Returns:
            dict[str, Any]: 複製されたツリー情報

        Raises:
            NotFoundError: ツリーが見つからない場合
        """
        logger.info(
            "ツリーを複製中",
            tree_id=str(tree_id),
            user_id=str(user_id),
        )

        original_tree = await self._get_tree_with_validation(project_id, tree_id)

        # 新しいツリー名を生成
        duplicated_name = new_name or f"{original_tree.name} (コピー)"

        # 新しいツリーを作成
        new_tree = await self.tree_repository.create(
            project_id=project_id,
            name=duplicated_name,
            description=original_tree.description,
            root_node_id=None,
            formula_id=original_tree.formula_id,
            status=original_tree.status if hasattr(original_tree, "status") else "draft",
        )

        # ノードIDのマッピング（元ID -> 新ID）
        node_id_mapping: dict[uuid.UUID, uuid.UUID] = {}

        # 元ツリーの全ノードIDを収集（リレーションシップから）
        original_node_ids: set[uuid.UUID] = set()
        for relationship in original_tree.relationships:
            original_node_ids.add(relationship.parent_node_id)
            for child in relationship.children:
                original_node_ids.add(child.child_node_id)

        # ルートノードも含める
        if original_tree.root_node_id:
            original_node_ids.add(original_tree.root_node_id)

        # 全ノードを施策付きで一括取得（N+1回避）
        original_nodes = await self.node_repository.get_many_with_policies(list(original_node_ids))

        # ノードを複製（施策も含む）
        for node_id, original_node in original_nodes.items():
            new_node = await self.node_repository.create(
                label=original_node.label,
                node_type=original_node.node_type,
                position_x=original_node.position_x,
                position_y=original_node.position_y,
                data_frame_id=original_node.data_frame_id,
            )
            node_id_mapping[node_id] = new_node.id

            # ノードに紐づく施策（ポリシー）を複製（既に読み込み済み）
            for policy in original_node.policies:
                new_policy = DriverTreePolicy(
                    node_id=new_node.id,
                    label=policy.label,
                    value=policy.value,
                    description=policy.description,
                    cost=policy.cost,
                    duration_months=policy.duration_months,
                    status=policy.status,
                )
                self.db.add(new_policy)

        # ルートノードを更新
        if original_tree.root_node_id and original_tree.root_node_id in node_id_mapping:
            await self.tree_repository.update(
                new_tree,
                root_node_id=node_id_mapping[original_tree.root_node_id],
            )

        # リレーションシップを複製
        for relationship in original_tree.relationships:
            if relationship.parent_node_id in node_id_mapping:
                new_relationship = DriverTreeRelationship(
                    driver_tree_id=new_tree.id,
                    parent_node_id=node_id_mapping[relationship.parent_node_id],
                    operator=relationship.operator,
                )
                self.db.add(new_relationship)
                await self.db.flush()
                await self.db.refresh(new_relationship)

                # 子ノードをリレーションシップに追加
                for child in relationship.children:
                    if child.child_node_id in node_id_mapping:
                        child_rel = DriverTreeRelationshipChild(
                            relationship_id=new_relationship.id,
                            child_node_id=node_id_mapping[child.child_node_id],
                            order_index=child.order_index,
                        )
                        self.db.add(child_rel)

                await self.db.flush()

        logger.info(
            "ツリーを複製しました",
            original_tree_id=str(tree_id),
            new_tree_id=str(new_tree.id),
        )

        return await self._build_tree_response(new_tree)

    async def get_tree_policies(
        self,
        project_id: uuid.UUID,
        tree_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """ツリーに紐づくすべての施策を取得します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            tree_id: ツリーID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: ツリー施策一覧
                - tree_id: uuid - ツリーID
                - policies: list[dict] - 施策一覧
                - total_count: int - 施策総数
        """
        logger.info(
            "ツリー施策一覧取得中",
            project_id=str(project_id),
            tree_id=str(tree_id),
            user_id=str(user_id),
        )

        # ツリーの存在確認
        tree = await self.tree_repository.get(tree_id)
        if not tree or tree.project_id != project_id:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(
                "ツリーが見つかりません",
                details={"tree_id": str(tree_id)},
            )

        # ツリーに紐づくすべての施策を取得
        policies = await self.policy_repository.list_by_tree(tree_id)

        # レスポンスを構築
        policy_items = []
        for policy in policies:
            policy_items.append(
                {
                    "policy_id": policy.id,
                    "node_id": policy.node_id,
                    "node_label": policy.node.label if policy.node else "",
                    "label": policy.label,
                    "description": policy.description,
                    "impact_type": policy.impact_type,
                    "impact_value": policy.impact_value,
                    "status": policy.status,
                }
            )

        logger.info(
            "ツリー施策一覧を取得しました",
            project_id=str(project_id),
            tree_id=str(tree_id),
            total_count=len(policy_items),
        )

        return {
            "tree_id": tree_id,
            "policies": policy_items,
            "total_count": len(policy_items),
        }
