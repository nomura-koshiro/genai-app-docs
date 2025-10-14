"""共通テストフィクスチャとセットアップ。"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app


# テスト用のインメモリデータベース
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """セッションスコープのイベントループ。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """テスト用データベースエンジン。"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """テスト用データベースセッション。"""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """テスト用HTTPクライアント。"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# サンプルデータフィクスチャ
@pytest.fixture
def user_data():
    """テスト用ユーザーデータ。"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
    }


@pytest.fixture
def session_data():
    """テスト用セッションデータ。"""
    return {
        "session_id": "test-session-123",
        "metadata": {"key": "value"},
    }


@pytest.fixture
def file_data():
    """テスト用ファイルデータ。"""
    return {
        "filename": "test.txt",
        "filepath": "/uploads/test.txt",
        "content_type": "text/plain",
        "size": 1024,
    }
