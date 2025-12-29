"""ドライバーツリーリポジトリ。

このモジュールは、DriverTreeモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.driver_tree import DriverTree, DriverTreeNode, DriverTreePolicy
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class DriverTreeRepository(BaseRepository[DriverTree, uuid.UUID]):
    """DriverTreeモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    ドライバーツリー管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """ドライバーツリーリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(DriverTree, db)

    async def get_with_relations(self, tree_id: uuid.UUID) -> DriverTree | None:
        """リレーションシップを含めてツリーを取得します。

        Args:
            tree_id: ツリーID

        Returns:
            DriverTree | None: ツリー（ルートノード、リレーションシップ含む）
        """
        result = await self.db.execute(
            select(DriverTree)
            .where(DriverTree.id == tree_id)
            .options(
                selectinload(DriverTree.root_node),
                selectinload(DriverTree.relationships),
                selectinload(DriverTree.formula),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DriverTree]:
        """プロジェクトに属するツリー一覧を取得します。

        Args:
            project_id: プロジェクトID
            skip: スキップするレコード数
            limit: 取得する最大レコード数

        Returns:
            list[DriverTree]: ツリー一覧（作成日時降順、数式マスタ含む）
        """
        result = await self.db.execute(
            select(DriverTree)
            .where(DriverTree.project_id == project_id)
            .options(selectinload(DriverTree.formula))
            .order_by(DriverTree.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        """プロジェクトに属するツリー数を取得します。

        Args:
            project_id: プロジェクトID

        Returns:
            int: ツリー数
        """
        from sqlalchemy import func

        result = await self.db.execute(select(func.count()).select_from(DriverTree).where(DriverTree.project_id == project_id))
        return result.scalar_one()

    async def count_nodes_by_tree(self, tree_id: uuid.UUID) -> int:
        """ツリーに含まれるノード数を取得します。

        Args:
            tree_id: ツリーID

        Returns:
            int: ノード数
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count()).select_from(DriverTreeNode).where(DriverTreeNode.driver_tree_id == tree_id)
        )
        return result.scalar_one()

    async def count_policies_by_tree(self, tree_id: uuid.UUID) -> int:
        """ツリーに関連する施策数を取得します。

        ツリーに属する全ノードの施策数の合計を返します。

        Args:
            tree_id: ツリーID

        Returns:
            int: 施策数
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count())
            .select_from(DriverTreePolicy)
            .join(DriverTreeNode, DriverTreePolicy.node_id == DriverTreeNode.id)
            .where(DriverTreeNode.driver_tree_id == tree_id)
        )
        return result.scalar_one()

    async def get_aggregate_counts(
        self, tree_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, dict[str, int]]:
        """複数ツリーのノード数・施策数を一括取得します。

        N+1クエリを回避するため、一括でカウントを取得します。

        Args:
            tree_ids: ツリーIDリスト

        Returns:
            dict[uuid.UUID, dict[str, int]]: ツリーIDをキーとした集計結果
                - node_count: ノード数
                - policy_count: 施策数
        """
        from sqlalchemy import func

        if not tree_ids:
            return {}

        # ノード数を一括取得
        node_counts_result = await self.db.execute(
            select(
                DriverTreeNode.driver_tree_id,
                func.count(DriverTreeNode.id).label("node_count"),
            )
            .where(DriverTreeNode.driver_tree_id.in_(tree_ids))
            .group_by(DriverTreeNode.driver_tree_id)
        )
        node_counts = {row[0]: row[1] for row in node_counts_result.all()}

        # 施策数を一括取得
        policy_counts_result = await self.db.execute(
            select(
                DriverTreeNode.driver_tree_id,
                func.count(DriverTreePolicy.id).label("policy_count"),
            )
            .join(DriverTreeNode, DriverTreePolicy.node_id == DriverTreeNode.id)
            .where(DriverTreeNode.driver_tree_id.in_(tree_ids))
            .group_by(DriverTreeNode.driver_tree_id)
        )
        policy_counts = {row[0]: row[1] for row in policy_counts_result.all()}

        # 結果をマージ
        result: dict[uuid.UUID, dict[str, int]] = {}
        for tree_id in tree_ids:
            result[tree_id] = {
                "node_count": node_counts.get(tree_id, 0),
                "policy_count": policy_counts.get(tree_id, 0),
            }

        return result
