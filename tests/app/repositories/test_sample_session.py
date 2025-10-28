"""セッションリポジトリのテスト。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sample_user import SampleUser
from app.repositories.sample_session import SampleSessionRepository


class TestSampleSessionRepository:
    """SampleSessionRepositoryのテストクラス。"""

    @pytest.mark.asyncio
    async def test_create_session(self, db_session: AsyncSession):
        """セッションの作成が成功すること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)

        # Act
        session = await repository.create_session(
            session_id="test-session-123",
            metadata={"source": "web"},
        )

        # Assert
        assert session.id is not None
        assert session.session_id == "test-session-123"
        assert session.session_metadata == {"source": "web"}
        assert session.user_id is None

    @pytest.mark.asyncio
    async def test_create_session_with_user(self, db_session: AsyncSession):
        """ユーザー所有のセッションの作成が成功すること。"""
        # Arrange
        user = SampleUser(
            email="session@example.com",
            username="sessionuser",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repository = SampleSessionRepository(db_session)

        # Act
        session = await repository.create_session(
            session_id="user-session-123",
            user_id=user.id,
        )

        # Assert
        assert session.user_id == user.id

    @pytest.mark.asyncio
    async def test_get_by_session_id(self, db_session: AsyncSession):
        """session_idでセッションを取得できること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)
        created_session = await repository.create_session(session_id="get-session-test")
        await db_session.commit()

        # Act
        session = await repository.get_by_session_id("get-session-test")

        # Assert
        assert session is not None
        assert session.id == created_session.id
        assert session.session_id == "get-session-test"

    @pytest.mark.asyncio
    async def test_get_by_session_id_not_found(self, db_session: AsyncSession):
        """存在しないsession_idでNoneが返されること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)

        # Act
        session = await repository.get_by_session_id("non-existent-session")

        # Assert
        assert session is None

    @pytest.mark.asyncio
    async def test_add_message(self, db_session: AsyncSession):
        """メッセージの追加が成功すること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)
        session = await repository.create_session(session_id="message-session")
        await db_session.commit()

        # Act
        message = await repository.add_message(
            session_id=session.id,
            role="user",
            content="Hello, AI!",
            tokens_used=10,
            model="gpt-4",
        )
        await db_session.commit()

        # Assert
        assert message.id is not None
        assert message.session_id == session.id
        assert message.role == "user"
        assert message.content == "Hello, AI!"
        assert message.tokens_used == 10
        assert message.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_add_multiple_messages(self, db_session: AsyncSession):
        """複数のメッセージを追加できること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)
        session = await repository.create_session(session_id="multi-message-session")
        await db_session.commit()

        # Act
        messages_data = [
            ("user", "First message"),
            ("assistant", "First response"),
            ("user", "Second message"),
            ("assistant", "Second response"),
        ]

        for role, content in messages_data:
            await repository.add_message(
                session_id=session.id,
                role=role,
                content=content,
            )
        await db_session.commit()

        # Assert - セッションからメッセージを取得
        loaded_session = await repository.get_by_session_id("multi-message-session")
        assert loaded_session is not None
        assert len(loaded_session.messages) == 4

    @pytest.mark.asyncio
    async def test_get_session_with_messages(self, db_session: AsyncSession):
        """セッション取得時にメッセージも一緒に取得されること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)
        session = await repository.create_session(session_id="session-with-messages")
        await db_session.commit()

        # メッセージを追加
        await repository.add_message(
            session_id=session.id,
            role="user",
            content="Message 1",
        )
        await repository.add_message(
            session_id=session.id,
            role="assistant",
            content="Message 2",
        )
        await db_session.commit()

        # Act
        loaded_session = await repository.get_by_session_id("session-with-messages")

        # Assert
        assert loaded_session is not None
        assert len(loaded_session.messages) == 2
        assert loaded_session.messages[0].role == "user"
        assert loaded_session.messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_delete_session(self, db_session: AsyncSession):
        """セッションの削除が成功すること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)
        await repository.create_session(session_id="delete-session-test")
        await db_session.commit()

        # Act
        result = await repository.delete_session("delete-session-test")
        await db_session.commit()

        # Assert
        assert result is True
        deleted_session = await repository.get_by_session_id("delete-session-test")
        assert deleted_session is None

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, db_session: AsyncSession):
        """存在しないセッションの削除でFalseが返されること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)

        # Act
        result = await repository.delete_session("non-existent-session")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_session_cascades_messages(self, db_session: AsyncSession):
        """セッション削除時にメッセージもカスケード削除されること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)
        session = await repository.create_session(session_id="cascade-delete-session")
        await db_session.commit()

        await repository.add_message(
            session_id=session.id,
            role="user",
            content="Message to be deleted",
        )
        await db_session.commit()

        # Act - セッションを削除
        await repository.delete_session("cascade-delete-session")
        await db_session.commit()

        # Assert - セッションが削除されている
        deleted_session = await repository.get_by_session_id("cascade-delete-session")
        assert deleted_session is None

    @pytest.mark.asyncio
    async def test_add_message_optional_fields(self, db_session: AsyncSession):
        """オプショナルフィールドなしでメッセージを追加できること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)
        session = await repository.create_session(session_id="optional-fields-session")
        await db_session.commit()

        # Act - tokens_usedとmodelを省略
        message = await repository.add_message(
            session_id=session.id,
            role="user",
            content="Message without optional fields",
        )
        await db_session.commit()

        # Assert
        assert message.tokens_used is None
        assert message.model is None
        assert message.content == "Message without optional fields"

    @pytest.mark.asyncio
    async def test_session_with_metadata(self, db_session: AsyncSession):
        """メタデータ付きセッションの作成が成功すること。"""
        # Arrange
        repository = SampleSessionRepository(db_session)
        metadata = {
            "source": "mobile",
            "device": "iPhone",
            "version": "1.0.0",
        }

        # Act
        _session = await repository.create_session(
            session_id="metadata-session",
            metadata=metadata,
        )
        await db_session.commit()

        # Assert
        loaded_session = await repository.get_by_session_id("metadata-session")
        assert loaded_session is not None
        assert loaded_session.session_metadata == metadata
