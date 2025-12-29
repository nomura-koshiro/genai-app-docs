"""分析スナップショットリポジトリ。

このモジュールは、AnalysisSnapshotモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.analysis import AnalysisSnapshot
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class AnalysisSnapshotRepository(BaseRepository[AnalysisSnapshot, uuid.UUID]):
    """AnalysisSnapshotモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    スナップショット管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """スナップショットリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(AnalysisSnapshot, db)

    async def get_with_relations(self, snapshot_id: uuid.UUID) -> AnalysisSnapshot | None:
        """リレーションシップを含めてスナップショットを取得します。

        Args:
            snapshot_id: スナップショットID

        Returns:
            AnalysisSnapshot | None: スナップショット（ステップ、チャット含む）
        """
        result = await self.db.execute(
            select(AnalysisSnapshot)
            .where(AnalysisSnapshot.id == snapshot_id)
            .options(
                selectinload(AnalysisSnapshot.steps),
                selectinload(AnalysisSnapshot.chats),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_session(self, session_id: uuid.UUID) -> list[AnalysisSnapshot]:
        """セッションのスナップショット一覧を取得します。

        Args:
            session_id: セッションID

        Returns:
            list[AnalysisSnapshot]: スナップショット一覧（順序順）
        """
        result = await self.db.execute(
            select(AnalysisSnapshot).where(AnalysisSnapshot.session_id == session_id).order_by(AnalysisSnapshot.snapshot_order.asc())
        )
        return list(result.scalars().all())

    async def get_by_order(
        self,
        session_id: uuid.UUID,
        snapshot_order: int,
    ) -> AnalysisSnapshot | None:
        """セッションIDとスナップショット順序で取得します。

        Args:
            session_id: セッションID
            snapshot_order: スナップショット順序

        Returns:
            AnalysisSnapshot | None: スナップショット
        """
        result = await self.db.execute(
            select(AnalysisSnapshot)
            .where(AnalysisSnapshot.session_id == session_id)
            .where(AnalysisSnapshot.snapshot_order == snapshot_order)
        )
        return result.scalar_one_or_none()

    async def get_max_order(self, session_id: uuid.UUID) -> int:
        """セッションの最大スナップショット順序を取得します。

        Args:
            session_id: セッションID

        Returns:
            int: 最大順序（存在しない場合は-1）
        """
        result = await self.db.execute(
            select(func.max(AnalysisSnapshot.snapshot_order)).where(AnalysisSnapshot.session_id == session_id)
        )
        max_order = result.scalar_one()
        return max_order if max_order is not None else -1

    async def list_by_session_with_relations(self, session_id: uuid.UUID) -> list[AnalysisSnapshot]:
        """セッションのスナップショット一覧をリレーションシップ付きで取得します。

        N+1クエリを回避するため、selectinloadを使用して一括取得します。

        Args:
            session_id: セッションID

        Returns:
            list[AnalysisSnapshot]: スナップショット一覧（ステップ、チャット含む）
        """
        result = await self.db.execute(
            select(AnalysisSnapshot)
            .where(AnalysisSnapshot.session_id == session_id)
            .options(
                selectinload(AnalysisSnapshot.steps),
                selectinload(AnalysisSnapshot.chats),
            )
            .order_by(AnalysisSnapshot.snapshot_order.asc())
        )
        return list(result.scalars().all())
