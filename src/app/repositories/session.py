"""Session repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import Message, Session
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Repository for Session model."""

    def __init__(self, db: AsyncSession):
        """Initialize session repository.

        Args:
            db: Database session
        """
        super().__init__(Session, db)

    async def get_by_session_id(self, session_id: str) -> Session | None:
        """Get session by session_id.

        Args:
            session_id: Session identifier

        Returns:
            Session instance or None if not found
        """
        result = await self.db.execute(
            select(Session)
            .where(Session.session_id == session_id)
            .options(selectinload(Session.messages))
        )
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Session]:
        """Get sessions for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user sessions
        """
        result = await self.db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .options(selectinload(Session.messages))
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        tokens_used: int | None = None,
        model: str | None = None,
    ) -> Message:
        """Add a message to a session.

        Args:
            session_id: Session ID
            role: Message role (user/assistant/system)
            content: Message content
            tokens_used: Number of tokens used
            model: Model used for generation

        Returns:
            Created message instance
        """
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            model=model,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model."""

    def __init__(self, db: AsyncSession):
        """Initialize message repository.

        Args:
            db: Database session
        """
        super().__init__(Message, db)

    async def get_session_messages(
        self, session_id: int, skip: int = 0, limit: int = 100
    ) -> list[Message]:
        """Get messages for a session.

        Args:
            session_id: Session ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of session messages
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
