"""データベースモデルのテスト。"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models import File, Message, Session, User


@pytest.mark.asyncio
async def test_create_user(db_session, user_data):
    """ユーザー作成のテスト。"""
    # Arrange & Act
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed_password_here",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Assert
    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.username == user_data["username"]
    assert user.is_active is True
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_user_relationships(db_session, user_data):
    """ユーザーのリレーションシップのテスト。"""
    # Arrange
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Act - セッションを作成
    session = Session(
        session_id="test-session",
        user_id=user.id,
        metadata={"test": "data"},
    )
    db_session.add(session)
    await db_session.commit()

    # Assert - リレーションシップが正しく動作
    result = await db_session.execute(
        select(User).where(User.id == user.id)
    )
    user_with_sessions = result.scalar_one()
    assert len(user_with_sessions.sessions) == 1
    assert user_with_sessions.sessions[0].session_id == "test-session"


@pytest.mark.asyncio
async def test_create_session(db_session):
    """セッション作成のテスト。"""
    # Arrange & Act
    session = Session(
        session_id="test-session-123",
        user_id=None,  # ゲストユーザー
        metadata={"key": "value"},
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    # Assert
    assert session.id is not None
    assert session.session_id == "test-session-123"
    assert session.user_id is None
    assert session.metadata == {"key": "value"}
    assert session.created_at is not None


@pytest.mark.asyncio
async def test_create_message(db_session):
    """メッセージ作成のテスト。"""
    # Arrange - セッションを先に作成
    session = Session(session_id="test-session", metadata={})
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    # Act - メッセージを作成
    message = Message(
        session_id=session.id,
        role="user",
        content="Hello, world!",
        tokens_used=10,
        model="gpt-4",
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)

    # Assert
    assert message.id is not None
    assert message.session_id == session.id
    assert message.role == "user"
    assert message.content == "Hello, world!"
    assert message.tokens_used == 10
    assert message.model == "gpt-4"


@pytest.mark.asyncio
async def test_session_cascade_delete(db_session):
    """セッション削除時のカスケード動作のテスト。"""
    # Arrange - セッションとメッセージを作成
    session = Session(session_id="test-session", metadata={})
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    message = Message(
        session_id=session.id,
        role="user",
        content="Test message",
    )
    db_session.add(message)
    await db_session.commit()

    # Act - セッションを削除
    await db_session.delete(session)
    await db_session.commit()

    # Assert - メッセージも削除されている
    result = await db_session.execute(
        select(Message).where(Message.session_id == session.id)
    )
    messages = result.scalars().all()
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_create_file(db_session, user_data):
    """ファイル作成のテスト。"""
    # Arrange - ユーザーを作成
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Act - ファイルを作成
    file = File(
        filename="test.txt",
        filepath="/uploads/test.txt",
        content_type="text/plain",
        size=1024,
        user_id=user.id,
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)

    # Assert
    assert file.id is not None
    assert file.filename == "test.txt"
    assert file.filepath == "/uploads/test.txt"
    assert file.content_type == "text/plain"
    assert file.size == 1024
    assert file.user_id == user.id
    assert file.uploaded_at is not None


@pytest.mark.asyncio
async def test_timezone_aware_timestamps(db_session):
    """タイムゾーン対応タイムスタンプのテスト。"""
    # Arrange & Act
    session = Session(session_id="test-session", metadata={})
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    # Assert - タイムゾーン情報が含まれている
    assert session.created_at.tzinfo is not None
    assert session.updated_at.tzinfo is not None
    # UTCタイムゾーンであることを確認
    assert session.created_at.tzinfo == timezone.utc
