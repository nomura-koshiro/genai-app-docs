"""プロジェクトファイルリポジトリ。

このモジュールは、プロジェクトファイルのCRUD操作を提供します。

主な機能:
    - ファイルメタデータの作成・取得・削除
    - プロジェクト別ファイル一覧取得
    - ファイル数・合計サイズの集計

使用例:
    >>> from app.repositories.project.file import ProjectFileRepository
    >>> repo = ProjectFileRepository(db_session)
    >>> file = await repo.create({
    ...     "project_id": project_id,
    ...     "filename": "document.pdf",
    ...     "file_size": 1024000
    ... })
"""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models import ProjectFile
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class ProjectFileRepository(BaseRepository[ProjectFile, uuid.UUID]):
    """プロジェクトファイルリポジトリ。

    プロジェクトファイルのデータベース操作を提供します。
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトファイルリポジトリを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(ProjectFile, db)

    async def create(self, **file_data: Any) -> ProjectFile:
        """ファイルメタデータを作成します。

        Args:
            file_data: ファイルメタデータ
                - project_id (UUID): プロジェクトID
                - filename (str): 保存ファイル名
                - original_filename (str): 元のファイル名
                - file_path (str): ファイルパス
                - file_size (int): ファイルサイズ（バイト）
                - mime_type (str | None): MIMEタイプ
                - uploaded_by (UUID): アップロード者のユーザーID

        Returns:
            ProjectFile: 作成されたファイルメタデータ

        Example:
            >>> file = await repo.create({
            ...     "project_id": project_id,
            ...     "filename": "doc_12345.pdf",
            ...     "original_filename": "document.pdf",
            ...     "file_path": "uploads/projects/proj-id/doc_12345.pdf",
            ...     "file_size": 1024000,
            ...     "mime_type": "application/pdf",
            ...     "uploaded_by": user_id
            ... })
        """
        file = ProjectFile(**file_data)
        self.db.add(file)
        await self.db.flush()
        await self.db.refresh(file)
        return file

    async def get(self, file_id: uuid.UUID) -> ProjectFile | None:
        """ファイルメタデータを取得します（uploader情報含む）。

        Args:
            file_id: ファイルID

        Returns:
            ProjectFile | None: ファイルメタデータ、存在しない場合はNone

        Example:
            >>> file = await repo.get(file_id)
            >>> if file:
            ...     print(file.uploader.display_name)  # アップロード者の名前
        """
        result = await self.db.execute(
            select(ProjectFile)
            .options(selectinload(ProjectFile.uploader))  # uploader情報を含める
            .where(ProjectFile.id == file_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        mime_type: str | None = None,
    ) -> list[ProjectFile]:
        """プロジェクトのファイル一覧を取得します（uploader情報含む）。

        Args:
            project_id: プロジェクトID
            skip: スキップするレコード数
            limit: 取得する最大レコード数
            mime_type: MIMEタイプでフィルタ（部分一致、例: "image/", "application/pdf"）

        Returns:
            list[ProjectFile]: ファイルのリスト（アップロード日時の降順）

        Example:
            >>> files = await repo.list_by_project(project_id, skip=0, limit=10)
            >>> for file in files:
            ...     print(f"{file.original_filename} - {file.uploader.display_name}")
            >>> # MIMEタイプでフィルタ
            >>> images = await repo.list_by_project(project_id, mime_type="image/")
        """
        query = select(ProjectFile).options(selectinload(ProjectFile.uploader)).where(ProjectFile.project_id == project_id)

        if mime_type:
            query = query.where(ProjectFile.mime_type.ilike(f"{mime_type}%"))

        query = query.order_by(ProjectFile.uploaded_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_project_with_filter(
        self,
        project_id: uuid.UUID,
        mime_type: str | None = None,
    ) -> int:
        """プロジェクトのファイル数をカウントします（フィルタ対応）。

        Args:
            project_id: プロジェクトID
            mime_type: MIMEタイプでフィルタ（部分一致）

        Returns:
            int: ファイル数
        """
        query = select(func.count(ProjectFile.id)).where(ProjectFile.project_id == project_id)

        if mime_type:
            query = query.where(ProjectFile.mime_type.ilike(f"{mime_type}%"))

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def delete(self, file_id: uuid.UUID) -> bool:
        """ファイルメタデータを削除します。

        Args:
            file_id: ファイルID

        Returns:
            bool: 削除成功の場合True、ファイルが存在しない場合False

        Example:
            >>> success = await repo.delete(file_id)
            >>> if success:
            ...     print("File deleted")
        """
        file = await self.get(file_id)
        if not file:
            return False

        await self.db.delete(file)
        await self.db.flush()
        return True

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        """プロジェクトのファイル数をカウントします。

        Args:
            project_id: プロジェクトID

        Returns:
            int: ファイル数

        Example:
            >>> count = await repo.count_by_project(project_id)
            >>> print(f"Total files: {count}")
        """
        result = await self.db.execute(select(func.count(ProjectFile.id)).where(ProjectFile.project_id == project_id))
        return result.scalar() or 0

    async def get_total_size_by_project(self, project_id: uuid.UUID) -> int:
        """プロジェクトの合計ファイルサイズを取得します。

        Args:
            project_id: プロジェクトID

        Returns:
            int: 合計ファイルサイズ（バイト）

        Example:
            >>> total_size = await repo.get_total_size_by_project(project_id)
            >>> print(f"Total size: {total_size / 1024 / 1024:.2f} MB")
        """
        result = await self.db.execute(select(func.sum(ProjectFile.file_size)).where(ProjectFile.project_id == project_id))
        return result.scalar() or 0

    async def get_with_usage(self, file_id: uuid.UUID) -> ProjectFile | None:
        """ファイルメタデータと使用情報を取得します。

        Args:
            file_id: ファイルID

        Returns:
            ProjectFile | None: ファイルメタデータ（analysis_files, driver_tree_files含む）
        """
        result = await self.db.execute(
            select(ProjectFile)
            .options(
                selectinload(ProjectFile.uploader),
                selectinload(ProjectFile.analysis_files),
                selectinload(ProjectFile.driver_tree_files),
            )
            .where(ProjectFile.id == file_id)
        )
        return result.scalar_one_or_none()
