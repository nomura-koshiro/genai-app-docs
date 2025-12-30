"""分析セッションリポジトリ。

このモジュールは、AnalysisSessionモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.analysis import AnalysisFile, AnalysisSession, AnalysisSnapshot
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class AnalysisSessionRepository(BaseRepository[AnalysisSession, uuid.UUID]):
    """AnalysisSessionモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    分析セッション管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """分析セッションリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(AnalysisSession, db)

    async def get_with_relations(self, session_id: uuid.UUID) -> AnalysisSession | None:
        """リレーションシップを含めてセッションを取得します。

        Args:
            session_id: セッションID

        Returns:
            AnalysisSession | None: セッション（スナップショット、ファイル含む）
        """
        from app.models.analysis.analysis_issue_master import AnalysisIssueMaster

        result = await self.db.execute(
            select(AnalysisSession)
            .where(AnalysisSession.id == session_id)
            .options(
                selectinload(AnalysisSession.snapshots),
                selectinload(AnalysisSession.files),
                selectinload(AnalysisSession.issue).selectinload(AnalysisIssueMaster.validation),
                selectinload(AnalysisSession.creator),
                selectinload(AnalysisSession.input_file),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AnalysisSession]:
        """プロジェクトに属するセッション一覧を取得します。

        Args:
            project_id: プロジェクトID
            skip: スキップするレコード数
            limit: 取得する最大レコード数

        Returns:
            list[AnalysisSession]: セッション一覧（作成日時降順）
        """
        from app.models.analysis.analysis_issue_master import AnalysisIssueMaster

        result = await self.db.execute(
            select(AnalysisSession)
            .where(AnalysisSession.project_id == project_id)
            .options(
                selectinload(AnalysisSession.issue).selectinload(AnalysisIssueMaster.validation),
                selectinload(AnalysisSession.creator),
                selectinload(AnalysisSession.input_file).selectinload(AnalysisFile.project_file),
                selectinload(AnalysisSession.current_snapshot),
            )
            .order_by(AnalysisSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        """プロジェクトに属するセッション数を取得します。

        Args:
            project_id: プロジェクトID

        Returns:
            int: セッション数
        """
        from sqlalchemy import func

        result = await self.db.execute(select(func.count()).select_from(AnalysisSession).where(AnalysisSession.project_id == project_id))
        return result.scalar_one()

    async def get_latest_snapshot(self, session_id: uuid.UUID) -> AnalysisSnapshot | None:
        """セッションの最新スナップショットを取得します。

        Args:
            session_id: セッションID

        Returns:
            AnalysisSnapshot | None: 最新スナップショット
        """
        result = await self.db.execute(
            select(AnalysisSnapshot)
            .where(AnalysisSnapshot.session_id == session_id)
            .order_by(AnalysisSnapshot.snapshot_order.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
