"""File repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.repositories.base import BaseRepository


class FileRepository(BaseRepository[File]):
    """Repository for File model."""

    def __init__(self, db: AsyncSession):
        """Initialize file repository.

        Args:
            db: Database session
        """
        super().__init__(File, db)

    async def get_by_file_id(self, file_id: str) -> File | None:
        """Get file by file_id.

        Args:
            file_id: File identifier

        Returns:
            File instance or None if not found
        """
        result = await self.db.execute(select(File).where(File.file_id == file_id))
        return result.scalar_one_or_none()

    async def get_user_files(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[File]:
        """Get files for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user files
        """
        result = await self.db.execute(
            select(File)
            .where(File.user_id == user_id)
            .order_by(File.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_files(self, skip: int = 0, limit: int = 100) -> list[File]:
        """Get all files.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of all files
        """
        result = await self.db.execute(
            select(File).order_by(File.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
