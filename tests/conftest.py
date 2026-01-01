"""共通テストフィクスチャとセットアップ。"""

import asyncio
import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.base import Base
from tests.fixtures.excel_helper import create_multi_sheet_excel_bytes

# ストレージサービスのモックパス（統一: app.services.storage.get_storage_service）
STORAGE_SERVICE_MOCK_PATH = "app.services.storage.get_storage_service"

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

    # テーブルを削除（循環依存を避けるため、PostgreSQLのCASCADEを使用）
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))

    # 接続のクリーンアップを待機してからdispose
    await asyncio.sleep(0.1)
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
        # 非同期操作の完了を待機
        await asyncio.sleep(0)


@pytest.fixture(scope="function")
def mock_storage_service():
    """モックストレージサービスを提供するフィクスチャ。

    テスト用のExcelファイルを返すモックを作成します。

    Returns:
        AsyncMock: モック化されたストレージサービス
    """
    storage_mock = AsyncMock()
    # デフォルトでテスト用Excelファイルを返す
    storage_mock.download.return_value = create_multi_sheet_excel_bytes()
    storage_mock.upload.return_value = True
    storage_mock.exists.return_value = True
    storage_mock.delete.return_value = True
    return storage_mock


@pytest.fixture(scope="function")
def mock_analysis_agent():
    """モック分析エージェントを提供するフィクスチャ。

    AnalysisAgentのモックを作成します。
    テスト内でchat_historyやall_stepsをカスタマイズ可能です。

    Returns:
        tuple: (mock_agent_class, mock_agent_instance)

    使用例:
        def test_example(client, mock_analysis_agent):
            mock_class, mock_instance = mock_analysis_agent
            mock_instance.state.chat_history = [("user", "msg"), ("assistant", "response")]
            mock_instance.state.all_steps = []
            with patch("app.services.analysis.analysis_session.service.AnalysisAgent", mock_class):
                response = await client.post(...)
    """
    from unittest.mock import MagicMock

    mock_agent = MagicMock()

    def chat_side_effect(user_message):
        # userの発言を履歴に追加
        if not hasattr(mock_agent.state, "chat_history") or mock_agent.state.chat_history is None:
            mock_agent.state.chat_history = []
        mock_agent.state.chat_history.append(("user", user_message))
        # assistantの返答を履歴に追加
        mock_agent.state.chat_history.append(("assistant", "分析を開始します。"))
        return "分析を開始します。"

    mock_agent.chat.side_effect = chat_side_effect

    # デフォルトのchat_historyとall_stepsはstateにセットされる
    def agent_init(state):
        # テストが事前に初期チャット履歴やall_stepsを指定している場合はそれをstateに反映
        if hasattr(mock_agent, "initial_chat_history"):
            try:
                state.chat_history = list(mock_agent.initial_chat_history)
            except Exception:
                state.chat_history = mock_agent.initial_chat_history
        if hasattr(mock_agent, "initial_all_steps"):
            try:
                state.all_steps = list(mock_agent.initial_all_steps)
            except Exception:
                state.all_steps = mock_agent.initial_all_steps
        # stateをmock_agent.stateとして保持
        mock_agent.state = state
        return mock_agent

    mock_agent_class = MagicMock(side_effect=agent_init)
    return mock_agent_class, mock_agent


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession, mock_storage_service) -> AsyncGenerator[AsyncClient]:
    """テスト用HTTPクライアント。

    Note:
        mock_storage_serviceは自動的にストレージサービスとして注入されます。
        テスト内でモックの戻り値を変更したい場合は、mock_storage_serviceフィクスチャを
        直接引数として受け取り、return_valueを変更してください。
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # ストレージサービスをモック（統一パス: app.services.storage.get_storage_service）
    with patch(STORAGE_SERVICE_MOCK_PATH, return_value=mock_storage_service):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client

    app.dependency_overrides.clear()
    # 非同期操作の完了を待機（Connection._cancel警告を防止）
    await asyncio.sleep(0.1)


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
    from app.api.core.dependencies import get_current_active_user_account
    from app.main import app

    def _override(user):
        """指定されたユーザーで認証をオーバーライド。

        Args:
            user: モックユーザーオブジェクト（User model instance）

        Returns:
            User: 渡されたユーザーオブジェクト（チェーン可能）
        """
        app.dependency_overrides[get_current_active_user_account] = lambda: user
        return user

    yield _override

    # クリーンアップ: テスト終了後に自動的にオーバーライドをクリア
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """テスト用ユーザーを作成します。"""
    from app.models import UserAccount

    user = UserAccount(
        azure_oid="test-azure-oid",
        email="test@example.com",
        display_name="Test User",
        roles=["User"],
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_project(db_session, test_user):
    """テスト用プロジェクトを作成します。"""
    from app.models import Project, ProjectMember, ProjectRole

    project = Project(
        name="テストプロジェクト",
        code="TEST001",
        description="テスト用プロジェクト",
    )
    db_session.add(project)
    await db_session.flush()

    # プロジェクトマネージャーとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(project)

    return project


# =============================================================================
# テストデータシーダー関連フィクスチャ
# =============================================================================


@pytest.fixture
def test_data_seeder(db_session):
    """テストデータシーダーを提供。

    使用例:
        async def test_example(test_data_seeder):
            user = await test_data_seeder.create_user(display_name="Test")
            project, owner = await test_data_seeder.create_project_with_owner()
    """
    from tests.fixtures.seeders import TestDataSeeder

    return TestDataSeeder(db_session)


@pytest.fixture
async def project_with_owner(test_data_seeder):
    """オーナー付きプロジェクトを作成。

    Returns:
        tuple[Project, UserAccount]: (project, owner)
    """
    project, owner = await test_data_seeder.create_project_with_owner()
    await test_data_seeder.db.commit()
    return project, owner
