"""共通テストフィクスチャとセットアップ。"""

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.base import Base

# passlibのbcryptバグチェックをスキップ（テスト環境でのエラー回避）
os.environ["PASSLIB_SKIP_BCRYPT_BUG_TESTS"] = "1"


async def create_test_database() -> None:
    """テスト用PostgreSQLデータベースを作成します。"""
    # 管理者接続でデータベースを作成
    admin_engine = create_async_engine(
        settings.TEST_DATABASE_ADMIN_URL,
        isolation_level="AUTOCOMMIT",
        echo=False,
    )

    try:
        async with admin_engine.connect() as conn:
            # 既存のデータベースを削除（存在する場合）
            await conn.execute(text(f"DROP DATABASE IF EXISTS {settings.TEST_DATABASE_NAME}"))
            # 新しいデータベースを作成
            await conn.execute(text(f"CREATE DATABASE {settings.TEST_DATABASE_NAME}"))
    finally:
        await admin_engine.dispose()


async def drop_test_database() -> None:
    """テスト用PostgreSQLデータベースを削除します。"""
    # 管理者接続でデータベースを削除
    admin_engine = create_async_engine(
        settings.TEST_DATABASE_ADMIN_URL,
        isolation_level="AUTOCOMMIT",
        echo=False,
    )

    try:
        async with admin_engine.connect() as conn:
            await conn.execute(text(f"DROP DATABASE IF EXISTS {settings.TEST_DATABASE_NAME}"))
    finally:
        await admin_engine.dispose()


@pytest.fixture(scope="session")
def event_loop():
    """セッションスコープのイベントループ。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database(event_loop, request):
    """テストセッション全体でデータベースを作成・削除します。"""
    # skip_dbマーカーがついているテストではデータベースセットアップをスキップ
    if request.node.get_closest_marker("skip_db"):
        yield
        return

    # テストデータベースを作成
    await create_test_database()

    yield

    # テストデータベースを削除
    await drop_test_database()


@pytest.fixture(scope="function")
async def db_engine():
    """テスト用データベースエンジン。

    環境変数TEST_DATABASE_URLから接続先を取得します。
    各テスト関数の前にテーブルを作成し、後に削除します。
    """
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # テーブルを作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # テーブルを削除
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession]:
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
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """テスト用HTTPクライアント。"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
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
        "session_metadata": {"key": "value"},
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


@pytest.fixture
def mock_azure_user():
    """Azure ADユーザーのモックデータ。"""
    return {
        "oid": "test-azure-oid-12345",
        "email": "test@example.com",
        "name": "Test User",
        "preferred_username": "testuser",
    }


@pytest.fixture
def override_auth(request):
    """認証依存性をオーバーライドするヘルパーfixture。

    使用例:
        def test_example(client, override_auth, mock_user):
            override_auth(mock_user)
            response = client.get("/api/v1/users")
            # テスト処理

    Args:
        request: pytestリクエストオブジェクト（クリーンアップ用）

    Yields:
        callable: ユーザーオブジェクトを受け取り、認証をオーバーライドする関数
    """
    from app.api.core.dependencies import get_current_active_user_azure
    from app.main import app

    def _override(user):
        """指定されたユーザーで認証をオーバーライド。

        Args:
            user: モックユーザーオブジェクト（User model instance）

        Returns:
            User: 渡されたユーザーオブジェクト（チェーン可能）
        """
        app.dependency_overrides[get_current_active_user_azure] = lambda: user
        return user

    yield _override

    # クリーンアップ: テスト終了後に自動的にオーバーライドをクリア
    app.dependency_overrides.clear()
