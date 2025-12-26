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
    DriverTreeRelationship,
    DriverTreeRelationshipChild,
)
from app.services.driver_tree.driver_tree.base import DriverTreeServiceBase

logger = get_logger(__name__)


class DriverTreeCrudService(DriverTreeServiceBase):
    """ドライバーツリーのCRUD操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """ドライバーツリーCRUDサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

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

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: ツリー一覧
                - trees: list[dict] - ツリー一覧
        """
        trees = await self.tree_repository.list_by_project(project_id)

        tree_list = []
        for tree in trees:
            tree_list.append(
                {
                    "tree_id": tree.id,
                    "name": tree.name,
                    "description": tree.description,
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
        # 簡易的な数式パーサー
        if "=" not in formula:
            raise ValidationError(
                "数式のフォーマットが不正です",
                details={"formula": formula},
            )

        parts = formula.split("=")
        if len(parts) != 2:
            raise ValidationError(
                "数式のフォーマットが不正です",
                details={"formula": formula},
            )

        result_name = parts[0].strip()
        expression = parts[1].strip()

        # 演算子を検出
        operator = None
        operands = []
        for op in ["+", "-", "*", "/"]:
            if op in expression:
                operator = op
                operands = [o.strip() for o in expression.split(op)]
                break

        if not operator or len(operands) < 2:
            # 単純な代入の場合
            operands = [expression]
            operator = None

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
            # 数値かどうか判定
            try:
                float(operand)
                node_type = "定数"
            except ValueError:
                node_type = "入力"

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
