"""Driver Treeサービス。

このモジュールは、ドライバーツリー機能のビジネスロジックを提供します。
"""

import re
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import async_timeout, measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.models.driver_tree import DriverTree, DriverTreeNode
from app.repositories.driver_tree import (
    DriverTreeCategoryRepository,
    DriverTreeNodeRepository,
    DriverTreeRepository,
)
from app.schemas.driver_tree.driver_tree import DriverTreeNodeResponse, DriverTreeResponse

logger = structlog.get_logger(__name__)


class DriverTreeService:
    """Driver Treeサービス。

    ドライバーツリー機能のビジネスロジックを提供します。

    Args:
        db: データベースセッション

    Example:
        >>> service = DriverTreeService(db)
        >>> tree = await service.create_tree_from_formulas(["粗利 = 売上 - 原価"])
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。

        Args:
            db: データベースセッション
        """
        self.db = db
        self.node_repo = DriverTreeNodeRepository(db)
        self.tree_repo = DriverTreeRepository(db)
        self.category_repo = DriverTreeCategoryRepository(db)

    @measure_performance
    @transactional
    async def create_node(
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

        Raises:
            ValidationError: ラベルが無効な場合

        Example:
            >>> node = await service.create_node(tree_id, "売上", parent_id=root_id, operator="-")
        """
        logger.info("node_create_started", label=label, tree_id=str(tree_id))

        if not label or len(label) > 100:
            raise ValidationError("ラベルは1～100文字で指定してください")

        node = await self.node_repo.create(
            tree_id=tree_id,
            label=label,
            parent_id=parent_id,
            operator=operator,
            x=x,
            y=y,
        )

        logger.info("node_created", node_id=str(node.id), label=label)
        return node

    @measure_performance
    async def get_node(self, node_id: uuid.UUID) -> DriverTreeNode:
        """ノードを取得します。

        Args:
            node_id: ノードID

        Returns:
            DriverTreeNode: ノード

        Raises:
            NotFoundError: ノードが見つからない場合
        """
        logger.debug("node_get_started", node_id=str(node_id))

        node = await self.node_repo.get(node_id)
        if not node:
            logger.warning("node_not_found", node_id=str(node_id))
            raise NotFoundError(f"ノードが見つかりません: {node_id}")

        logger.debug("node_retrieved", node_id=str(node_id), label=node.label)
        return node

    @measure_performance
    @transactional
    async def update_node(
        self,
        node_id: uuid.UUID,
        label: str | None = None,
        parent_id: uuid.UUID | None = None,
        operator: str | None = None,
        x: int | None = None,
        y: int | None = None,
    ) -> DriverTreeNode:
        """ノードを更新します。

        Args:
            node_id: ノードID
            label: 新しいラベル
            parent_id: 新しい親ノードID
            operator: 新しい演算子
            x: 新しいX座標
            y: 新しいY座標

        Returns:
            DriverTreeNode: 更新されたノード

        Raises:
            NotFoundError: ノードが見つからない場合
        """
        logger.info("node_update_started", node_id=str(node_id))

        node = await self.get_node(node_id)

        if label is not None:
            node.label = label
        if parent_id is not None:
            node.parent_id = parent_id
        if operator is not None:
            node.operator = operator
        if x is not None:
            node.x = x
        if y is not None:
            node.y = y

        await self.db.flush()
        logger.info("node_updated", node_id=str(node_id))
        return node

    @measure_performance
    @transactional
    async def create_tree_from_formulas(self, formulas: list[str], tree_name: str | None = None) -> DriverTree:
        """数式からツリーを作成します。

        Args:
            formulas: 数式のリスト（例: ["粗利 = 売上 - 原価", "売上 = 数量 * 単価"]）
            tree_name: ツリー名（任意）

        Returns:
            DriverTree: 作成されたツリー

        Raises:
            ValidationError: 数式が無効な場合

        Example:
            >>> tree = await service.create_tree_from_formulas([
            ...     "粗利 = 売上 - 原価",
            ...     "売上 = 数量 * 単価"
            ... ], "粗利分析")
        """
        logger.info("tree_creation_started", formula_count=len(formulas))

        if not formulas:
            raise ValidationError("数式が指定されていません")

        # 数式をパースして親子関係を構築
        formula_dict: dict[str, tuple[list[str], str]] = {}
        for formula in formulas:
            if "=" not in formula:
                continue

            left, right = [x.strip() for x in formula.split("=", 1)]
            parts, operator = self._parse_expression(right)
            formula_dict[left] = (parts, operator)

        # ルートノードを特定（右辺に出現しないノード）
        all_nodes = set(formula_dict.keys())
        child_nodes = set()
        for parts, _ in formula_dict.values():
            child_nodes.update(parts)

        root_labels = all_nodes - child_nodes
        if not root_labels:
            raise ValidationError("ルートノードを特定できません")
        if len(root_labels) > 1:
            raise ValidationError(f"ルートノードが複数あります: {root_labels}")

        root_label = root_labels.pop()

        # ツリーを作成
        tree = await self.tree_repo.create(name=tree_name)

        # ノードを再帰的に作成
        node_map: dict[str, DriverTreeNode] = {}
        root_node = await self._create_node_recursive(
            tree_id=tree.id,
            label=root_label,
            formula_dict=formula_dict,
            node_map=node_map,
            parent_id=None,
            operator=None,
        )

        # ツリーにルートノードを設定
        await self.tree_repo.update_root_node(tree.id, root_node.id)

        # Y座標を計算して設定
        await self._calculate_y_coordinates(root_node, 0)

        await self.db.flush()

        logger.info("tree_created", tree_id=str(tree.id), node_count=len(node_map))
        return tree

    async def _create_node_recursive(
        self,
        tree_id: uuid.UUID,
        label: str,
        formula_dict: dict[str, tuple[list[str], str]],
        node_map: dict[str, DriverTreeNode],
        parent_id: uuid.UUID | None,
        operator: str | None,
    ) -> DriverTreeNode:
        """ノードを再帰的に作成します。

        Args:
            tree_id: ツリーID
            label: ノードのラベル
            formula_dict: 数式の辞書
            node_map: 作成済みノードのマップ
            parent_id: 親ノードID
            operator: 親ノードとの演算子

        Returns:
            DriverTreeNode: 作成されたノード
        """
        # 既に作成済みの場合はそのノードを返す
        if label in node_map:
            return node_map[label]

        # X座標を計算（深さ = parent_idから辿った深さ）
        x = 0
        if parent_id:
            parent_node = next((n for n in node_map.values() if n.id == parent_id), None)
            if parent_node and parent_node.x is not None:
                x = parent_node.x + 1

        # ノードを作成
        node = await self.node_repo.create(
            tree_id=tree_id,
            label=label,
            parent_id=parent_id,
            operator=operator,
            x=x,
            y=None,  # Y座標は後で設定
        )
        node_map[label] = node

        # 子ノードがある場合は再帰的に作成
        if label in formula_dict:
            child_labels, child_operator = formula_dict[label]
            for child_label in child_labels:
                await self._create_node_recursive(
                    tree_id=tree_id,
                    label=child_label,
                    formula_dict=formula_dict,
                    node_map=node_map,
                    parent_id=node.id,
                    operator=child_operator,
                )

        return node

    async def _calculate_y_coordinates(self, node: DriverTreeNode, current_y: int) -> int:
        """Y座標を再帰的に計算します。

        Args:
            node: 対象ノード
            current_y: 現在のY座標

        Returns:
            int: 次のY座標
        """
        node.y = current_y
        await self.db.flush()

        # 子ノードのY座標を計算
        children = await self.node_repo.find_children(node.id)
        next_y = current_y + 1
        for child in children:
            next_y = await self._calculate_y_coordinates(child, next_y)

        return next_y if children else current_y + 1

    @measure_performance
    async def get_tree(self, tree_id: uuid.UUID) -> DriverTree:
        """ツリーを取得します。

        Args:
            tree_id: ツリーID

        Returns:
            DriverTree: ツリー

        Raises:
            NotFoundError: ツリーが見つからない場合
        """
        logger.debug("tree_get_started", tree_id=str(tree_id))

        tree = await self.tree_repo.get_with_tree_structure(tree_id)
        if not tree:
            logger.warning("tree_not_found", tree_id=str(tree_id))
            raise NotFoundError(f"ツリーが見つかりません: {tree_id}")

        logger.debug("tree_retrieved", tree_id=str(tree_id), name=tree.name)
        return tree

    @measure_performance
    async def get_tree_response(self, tree_id: uuid.UUID) -> DriverTreeResponse:
        """ツリーのレスポンスを取得します。

        Args:
            tree_id: ツリーID

        Returns:
            DriverTreeResponse: ツリーのレスポンス

        Raises:
            NotFoundError: ツリーが見つからない場合
        """
        logger.debug("tree_response_get_started", tree_id=str(tree_id))

        try:
            tree = await self.get_tree(tree_id)

            root_node_response = None
            if tree.root_node:
                root_node_response = await self._build_node_response(tree.root_node)

            logger.debug("tree_response_built", tree_id=str(tree_id), has_root=bool(tree.root_node))

            return DriverTreeResponse(
                id=tree.id,
                name=tree.name,
                root_node_id=tree.root_node_id,
                root_node=root_node_response,
            )

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error("tree_response_get_failed", tree_id=str(tree_id), error=str(e), exc_info=True)
            raise

    async def _build_node_response(self, node: DriverTreeNode) -> DriverTreeNodeResponse:
        """ノードのレスポンスを再帰的に構築します。

        Args:
            node: ノード

        Returns:
            DriverTreeNodeResponse: ノードのレスポンス
        """
        children = await self.node_repo.find_children(node.id)
        children_responses = [await self._build_node_response(child) for child in children]

        return DriverTreeNodeResponse(
            id=node.id,
            tree_id=node.tree_id,
            label=node.label,
            parent_id=node.parent_id,
            operator=node.operator,
            x=node.x,
            y=node.y,
            children=children_responses,
        )

    def _parse_expression(self, expression: str) -> tuple[list[str], str]:
        """数式から演算子とオペランドを抽出します。

        Args:
            expression: 数式の右辺（例: "売上 - 原価"）

        Returns:
            tuple[list[str], str]: (オペランドのリスト, 演算子)
        """
        pattern = r"[\+\-\*/%]"
        match = re.search(pattern, expression)

        if match:
            operator = match.group()
            parts = [p.strip() for p in re.split(rf"\s*{re.escape(operator)}\s*", expression)]
            return parts, operator

        return [expression.strip()], ""

    @measure_performance
    @async_timeout(10.0)
    async def get_categories(self) -> dict[str, dict[str, list[str]]]:
        """カテゴリー一覧を取得します。

        Returns:
            dict: カテゴリーの辞書

        Example:
            >>> categories = await service.get_categories()
            >>> print(categories["製造業"]["自動車製造"])
        """
        logger.debug("categories_get_started")

        all_categories = await self.category_repo.find_by_criteria()

        result: dict[str, dict[str, list[str]]] = {}

        for category in all_categories:
            if category.industry_class not in result:
                result[category.industry_class] = {}

            if category.industry not in result[category.industry_class]:
                result[category.industry_class][category.industry] = []

            if category.tree_type not in result[category.industry_class][category.industry]:
                result[category.industry_class][category.industry].append(category.tree_type)

        logger.info("categories_retrieved", count=len(all_categories))
        return result

    @measure_performance
    @async_timeout(10.0)
    async def get_formulas(self, tree_type: str, kpi: str) -> list[str]:
        """指定されたツリータイプとKPIの数式を取得します。

        Args:
            tree_type: ツリータイプ
            kpi: KPI名

        Returns:
            list[str]: 数式のリスト

        Raises:
            NotFoundError: 数式が見つかりません場合
        """
        logger.info("formulas_get_started", tree_type=tree_type, kpi=kpi)

        try:
            categories = await self.category_repo.find_by_criteria(tree_type=tree_type, kpi=kpi)

            if not categories:
                logger.warning("formulas_not_found", tree_type=tree_type, kpi=kpi)
                raise NotFoundError(f"数式が見つかりません: tree_type={tree_type}, kpi={kpi}")

            logger.info("formulas_retrieved", tree_type=tree_type, kpi=kpi, formula_count=len(categories[0].formulas))
            return categories[0].formulas

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error("formulas_get_failed", tree_type=tree_type, kpi=kpi, error=str(e), exc_info=True)
            raise
