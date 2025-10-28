"""セッションモデルのテスト。"""

from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sample_session import SampleMessage, SampleSession
from app.models.sample_user import SampleUser


class TestSampleSessionModel:
    """SampleSessionモデルのテストクラス。"""

    @pytest.mark.asyncio
    async def test_create_session_success(self, db_session: AsyncSession):
        """セッションの作成が成功すること。"""
        # Arrange
        session = SampleSession(
            session_id="session-123",
            session_metadata={"source": "web", "device": "desktop"},
        )

        # Act
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Assert
        assert session.id is not None
        assert session.session_id == "session-123"
        assert session.user_id is None  # ゲストセッション
        assert session.session_metadata == {"source": "web", "device": "desktop"}
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_session_with_user(self, db_session: AsyncSession):
        """ユーザー所有のセッションの作成が成功すること。"""
        # Arrange - まずユーザーを作成
        user = SampleUser(
            email="session@example.com",
            username="sessionuser",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        session = SampleSession(
            session_id="user-session-123",
            user_id=user.id,
        )

        # Act
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Assert
        assert session.user_id == user.id

    @pytest.mark.asyncio
    async def test_session_id_unique_constraint(self, db_session: AsyncSession):
        """session_idのユニーク制約が機能すること。"""
        # Arrange - 同じsession_idで2つのセッションを作成
        session1 = SampleSession(session_id="duplicate-session")
        db_session.add(session1)
        await db_session.commit()

        session2 = SampleSession(session_id="duplicate-session")  # 重複
        db_session.add(session2)

        # Act & Assert
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_session_repr(self, db_session: AsyncSession):
        """__repr__メソッドが正しく動作すること。"""
        # Arrange
        session = SampleSession(session_id="repr-session")
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Act
        repr_str = repr(session)

        # Assert
        assert "SampleSession" in repr_str
        assert f"id={session.id}" in repr_str
        assert "session_id=repr-session" in repr_str

    @pytest.mark.asyncio
    async def test_user_deletion_cascades_to_session(self, db_session: AsyncSession):
        """ユーザー削除時にセッションもカスケード削除されること。"""
        # Arrange
        user = SampleUser(
            email="cascade@example.com",
            username="cascadeuser",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        session = SampleSession(session_id="cascade-session", user_id=user.id)
        db_session.add(session)
        await db_session.commit()

        # Act - ユーザーを削除
        await db_session.delete(user)
        await db_session.commit()

        # Assert - セッションも削除されている
        result = await db_session.execute(select(SampleSession).filter_by(session_id="cascade-session"))
        deleted_session = result.scalar_one_or_none()
        assert deleted_session is None


class TestSampleMessageModel:
    """SampleMessageモデルのテストクラス。"""

    @pytest.mark.asyncio
    async def test_create_message_success(self, db_session: AsyncSession):
        """メッセージの作成が成功すること。"""
        # Arrange - まずセッションを作成
        session = SampleSession(session_id="msg-session")
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        message = SampleMessage(
            session_id=session.id,
            role="user",
            content="Hello, AI!",
            tokens_used=10,
            model="gpt-4",
        )

        # Act
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        # Assert
        assert message.id is not None
        assert message.session_id == session.id
        assert message.role == "user"
        assert message.content == "Hello, AI!"
        assert message.tokens_used == 10
        assert message.model == "gpt-4"
        assert isinstance(message.created_at, datetime)

    @pytest.mark.asyncio
    async def test_message_roles(self, db_session: AsyncSession):
        """様々なロールのメッセージを作成できること。"""
        # Arrange
        session = SampleSession(session_id="roles-session")
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        messages = [
            SampleMessage(session_id=session.id, role="user", content="User message"),
            SampleMessage(session_id=session.id, role="assistant", content="Assistant message"),
            SampleMessage(session_id=session.id, role="system", content="System message"),
        ]

        # Act
        for message in messages:
            db_session.add(message)
        await db_session.commit()

        # Assert
        result = await db_session.execute(select(SampleMessage).filter_by(session_id=session.id))
        saved_messages = result.scalars().all()
        assert len(saved_messages) == 3
        roles = [msg.role for msg in saved_messages]
        assert "user" in roles
        assert "assistant" in roles
        assert "system" in roles

    @pytest.mark.asyncio
    async def test_session_deletion_cascades_to_messages(self, db_session: AsyncSession):
        """セッション削除時にメッセージもカスケード削除されること。"""
        # Arrange
        session = SampleSession(session_id="cascade-msg-session")
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        message1 = SampleMessage(session_id=session.id, role="user", content="Message 1")
        message2 = SampleMessage(session_id=session.id, role="assistant", content="Message 2")
        db_session.add_all([message1, message2])
        await db_session.commit()

        # Act - セッションを削除
        await db_session.delete(session)
        await db_session.commit()

        # Assert - メッセージも削除されている
        result = await db_session.execute(select(SampleMessage).filter_by(session_id=session.id))
        deleted_messages = result.scalars().all()
        assert len(deleted_messages) == 0

    @pytest.mark.asyncio
    async def test_message_repr(self, db_session: AsyncSession):
        """__repr__メソッドが正しく動作すること。"""
        # Arrange
        session = SampleSession(session_id="repr-msg-session")
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        message = SampleMessage(
            session_id=session.id,
            role="user",
            content="Test content",
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        # Act
        repr_str = repr(message)

        # Assert
        assert "SampleMessage" in repr_str
        assert f"id={message.id}" in repr_str
        assert "role=user" in repr_str
        assert f"session_id={session.id}" in repr_str

    @pytest.mark.asyncio
    async def test_session_relationship_with_messages(self, db_session: AsyncSession):
        """セッションとメッセージのリレーションシップが正しく動作すること。"""
        # Arrange
        session = SampleSession(session_id="relationship-session")
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        messages = [SampleMessage(session_id=session.id, role="user", content=f"Message {i}") for i in range(3)]
        for message in messages:
            db_session.add(message)
        await db_session.commit()

        # Act - セッションからメッセージを取得
        result = await db_session.execute(select(SampleSession).filter_by(session_id="relationship-session"))
        session_with_messages = result.scalar_one()
        await db_session.refresh(session_with_messages, ["messages"])

        # Assert
        assert len(session_with_messages.messages) == 3
        assert all(msg.session_id == session.id for msg in session_with_messages.messages)

    @pytest.mark.asyncio
    async def test_message_optional_fields(self, db_session: AsyncSession):
        """オプショナルフィールド（tokens_used, model）がNoneでも作成できること。"""
        # Arrange
        session = SampleSession(session_id="optional-fields-session")
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        message = SampleMessage(
            session_id=session.id,
            role="user",
            content="Message without optional fields",
            # tokens_used と model を省略
        )

        # Act
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        # Assert
        assert message.tokens_used is None
        assert message.model is None
