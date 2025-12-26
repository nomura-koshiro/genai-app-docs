"""分析ファイルリポジトリ。

このモジュールは、AnalysisFileモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.analysis import AnalysisFile
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class AnalysisFileRepository(BaseRepository[AnalysisFile, uuid.UUID]):
    """AnalysisFileモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    分析ファイル管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """分析ファイルリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(AnalysisFile, db)

    async def get_with_project_file(self, file_id: uuid.UUID) -> AnalysisFile | None:
        """プロジェクトファイル情報を含めて取得します。

        Args:
            file_id: ファイルID

        Returns:
            AnalysisFile | None: 分析ファイル（プロジェクトファイル情報含む）
        """
        result = await self.db.execute(
            select(AnalysisFile).where(AnalysisFile.id == file_id).options(selectinload(AnalysisFile.project_file))
        )
        return result.scalar_one_or_none()

    async def list_by_session(self, session_id: uuid.UUID) -> list[AnalysisFile]:
        """セッションに紐づくファイル一覧を取得します。

        Args:
            session_id: セッションID

        Returns:
            list[AnalysisFile]: ファイル一覧
        """
        result = await self.db.execute(
            select(AnalysisFile)
            .join(AnalysisFile.session)
            .where(AnalysisFile.session.has(id=session_id))
            .options(selectinload(AnalysisFile.project_file))
            .order_by(AnalysisFile.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_project_file(
        self,
        project_file_id: uuid.UUID,
        sheet_name: str,
    ) -> AnalysisFile | None:
        """プロジェクトファイルIDとシート名で検索します。

        Args:
            project_file_id: プロジェクトファイルID
            sheet_name: シート名

        Returns:
            AnalysisFile | None: 分析ファイル
        """
        result = await self.db.execute(
            select(AnalysisFile).where(AnalysisFile.project_file_id == project_file_id).where(AnalysisFile.sheet_name == sheet_name)
        )
        return result.scalar_one_or_none()
