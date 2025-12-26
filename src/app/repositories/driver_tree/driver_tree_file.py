"""ドライバーツリーファイルリポジトリ。

このモジュールは、DriverTreeFileモデルに特化したデータベース操作を提供します。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.driver_tree import DriverTreeFile
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class DriverTreeFileRepository(BaseRepository[DriverTreeFile, uuid.UUID]):
    """DriverTreeFileモデル用のリポジトリクラス。

    BaseRepositoryの共通CRUD操作に加えて、
    ドライバーツリーファイル管理に特化したクエリメソッドを提供します。
    """

    def __init__(self, db: AsyncSession):
        """ファイルリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(DriverTreeFile, db)

    async def get_with_project_file(self, file_id: uuid.UUID) -> DriverTreeFile | None:
        """プロジェクトファイル情報を含めて取得します。

        Args:
            file_id: ファイルID

        Returns:
            DriverTreeFile | None: ドライバーツリーファイル（プロジェクトファイル情報含む）
        """
        result = await self.db.execute(
            select(DriverTreeFile).where(DriverTreeFile.id == file_id).options(selectinload(DriverTreeFile.project_file))
        )
        return result.scalar_one_or_none()

    async def list_by_project_file(self, project_file_id: uuid.UUID) -> list[DriverTreeFile]:
        """プロジェクトファイルに紐づくファイル一覧を取得します。

        Args:
            project_file_id: プロジェクトファイルID

        Returns:
            list[DriverTreeFile]: ファイル一覧
        """
        result = await self.db.execute(
            select(DriverTreeFile).where(DriverTreeFile.project_file_id == project_file_id).order_by(DriverTreeFile.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_project_file_and_sheet(
        self,
        project_file_id: uuid.UUID,
        sheet_name: str,
    ) -> DriverTreeFile | None:
        """プロジェクトファイルIDとシート名で検索します。

        Args:
            project_file_id: プロジェクトファイルID
            sheet_name: シート名

        Returns:
            DriverTreeFile | None: ドライバーツリーファイル
        """
        result = await self.db.execute(
            select(DriverTreeFile).where(DriverTreeFile.project_file_id == project_file_id).where(DriverTreeFile.sheet_name == sheet_name)
        )
        return result.scalar_one_or_none()

    async def list_with_data_frames(self, project_file_id: uuid.UUID) -> list[DriverTreeFile]:
        """データフレームを含むファイル一覧を取得します。

        Args:
            project_file_id: プロジェクトファイルID

        Returns:
            list[DriverTreeFile]: ファイル一覧（データフレーム含む）
        """
        result = await self.db.execute(
            select(DriverTreeFile)
            .where(DriverTreeFile.project_file_id == project_file_id)
            .options(selectinload(DriverTreeFile.data_frames))
            .order_by(DriverTreeFile.created_at.desc())
        )
        return list(result.scalars().all())
