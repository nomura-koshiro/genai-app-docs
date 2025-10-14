"""User repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    def __init__(self, db: AsyncSession):
        """Initialize user repository.

        Args:
            db: Database session
        """
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get active users.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active users
        """
        return await self.get_multi(skip=skip, limit=limit, is_active=True)
