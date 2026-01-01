"""分析ステップリポジトリ。

このモジュールは、AnalysisStepモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analysis import AnalysisStep
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class AnalysisStepRepository(BaseRepository[AnalysisStep, uuid.UUID]):
    """AnalysisStepモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    分析ステップ管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """分析ステップリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(AnalysisStep, db)

    async def list_by_snapshot(self, snapshot_id: uuid.UUID) -> list[AnalysisStep]:
        """スナップショットのステップ一覧を取得します。

        Args:
            snapshot_id: スナップショットID

        Returns:
            list[AnalysisStep]: ステップ一覧（順序順）
        """
        result = await self.db.execute(
            select(AnalysisStep).where(AnalysisStep.snapshot_id == snapshot_id).order_by(AnalysisStep.step_order.asc())
        )
        return list(result.scalars().all())

    async def get_by_type(
        self,
        snapshot_id: uuid.UUID,
        step_type: str,
    ) -> list[AnalysisStep]:
        """スナップショット内の特定タイプのステップを取得します。

        Args:
            snapshot_id: スナップショットID
            step_type: ステップタイプ（filter/aggregate/transform/summary）

        Returns:
            list[AnalysisStep]: ステップ一覧
        """
        result = await self.db.execute(
            select(AnalysisStep)
            .where(AnalysisStep.snapshot_id == snapshot_id)
            .where(AnalysisStep.type == step_type)
            .order_by(AnalysisStep.step_order.asc())
        )
        return list(result.scalars().all())

    async def get_max_order(self, snapshot_id: uuid.UUID) -> int:
        """スナップショットの最大ステップ順序を取得します。

        Args:
            snapshot_id: スナップショットID

        Returns:
            int: 最大順序（存在しない場合は-1）
        """
        from sqlalchemy import func

        result = await self.db.execute(select(func.max(AnalysisStep.step_order)).where(AnalysisStep.snapshot_id == snapshot_id))
        max_order = result.scalar_one()
        return max_order if max_order is not None else -1

    async def get_summary_steps(self, snapshot_id: uuid.UUID) -> list[AnalysisStep]:
        """スナップショットのsummaryステップを取得します。

        Args:
            snapshot_id: スナップショットID

        Returns:
            list[AnalysisStep]: summaryステップ一覧
        """
        return await self.get_by_type(snapshot_id, "summary")

    async def delete_by_snapshot(self, snapshot_id: uuid.UUID) -> int:
        """スナップショットのステップをすべて削除します。

        Args:
            snapshot_id: スナップショットID

        Returns:
            int: 削除件数
        """
        # 削除前にカウントを取得
        count_result = await self.db.scalar(select(func.count()).select_from(AnalysisStep).where(AnalysisStep.snapshot_id == snapshot_id))
        count = count_result or 0

        # 削除を実行
        await self.db.execute(delete(AnalysisStep).where(AnalysisStep.snapshot_id == snapshot_id))
        return count
