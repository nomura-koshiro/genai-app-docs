# テストデータベースのセットアップ

このドキュメントでは、データベーステストのセットアップ方法について説明します。

[← データベーステストに戻る](./04-database-testing.md)

## 目次

- [テスト専用データベースの自動作成](#テスト専用データベースの自動作成)
- [環境設定](#環境設定)
- [conftest.pyの実装例](#conftestpyの実装例)
- [テストの実行](#テストの実行)

## テスト専用データベースの自動作成

このプロジェクトでは、PostgreSQL（Docker）を使用した自動テストデータベース管理システムを採用しています。

テストデータベースは`tests/conftest.py`で自動的に管理されます：

1. **テストセッション開始時**: `test_db`データベースを作成
2. **各テスト関数の前**: 全テーブルを作成
3. **各テスト関数の後**: 全テーブルを削除
4. **テストセッション終了時**: `test_db`データベースを削除

```mermaid
graph TB
    subgraph "1. テストセッション開始"
        A[pytest起動] --> B[setup_test_database fixture]
        B --> C[管理者接続:<br/>postgres DB]
        C --> D[DROP DATABASE<br/>IF EXISTS test_db]
        D --> E[CREATE DATABASE<br/>test_db]
    end

    subgraph "2. 各テスト関数"
        F[テスト関数開始] --> G[db_engine fixture]
        G --> H[test_db接続]
        H --> I[CREATE ALL TABLES<br/>Base.metadata.create_all]
        I --> J[テスト実行]
        J --> K[DROP ALL TABLES<br/>Base.metadata.drop_all]
        K --> L{次のテストあり?}
    end

    subgraph "3. テストセッション終了"
        M[全テスト完了] --> N[teardown_test_database]
        N --> O[管理者接続:<br/>postgres DB]
        O --> P[DROP DATABASE<br/>test_db]
        P --> Q[完了]
    end

    E --> F
    L -->|Yes| F
    L -->|No| M

    style B fill:#ef5350,stroke:#b71c1c,stroke-width:3px,color:#fff,stroke-width:3px
    style G fill:#81c784,stroke:#1b5e20,stroke-width:3px,color:#000,stroke-width:3px
    style N fill:#ccccff,stroke:#1976d2,stroke-width:3px
    style I fill:#ffffcc,stroke:#f57c00,stroke-width:3px
    style K fill:#ffe0cc,stroke:#e64a19,stroke-width:3px
```

この仕組みにより、各テストは完全に独立した環境で実行され、テスト間のデータ干渉を防ぎます。

## 環境設定

`.env`ファイルに以下の設定が必要です：

```bash
# Test Database (PostgreSQL via Docker)
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
TEST_DATABASE_ADMIN_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
TEST_DATABASE_NAME=test_db
```

## conftest.pyの実装例

```python
# tests/conftest.py
import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app


async def create_test_database() -> None:
    """テスト用PostgreSQLデータベースを作成します。"""
    admin_engine = create_async_engine(
        settings.TEST_DATABASE_ADMIN_URL,
        isolation_level="AUTOCOMMIT",
        echo=False,
    )

    try:
        async with admin_engine.connect() as conn:
            # 既存のデータベースを削除（存在する場合）
            await conn.execute(
                text(f"DROP DATABASE IF EXISTS {settings.TEST_DATABASE_NAME}")
            )
            # 新しいデータベースを作成
            await conn.execute(
                text(f"CREATE DATABASE {settings.TEST_DATABASE_NAME}")
            )
    finally:
        await admin_engine.dispose()


async def drop_test_database() -> None:
    """テスト用PostgreSQLデータベースを削除します。"""
    admin_engine = create_async_engine(
        settings.TEST_DATABASE_ADMIN_URL,
        isolation_level="AUTOCOMMIT",
        echo=False,
    )

    try:
        async with admin_engine.connect() as conn:
            await conn.execute(
                text(f"DROP DATABASE IF EXISTS {settings.TEST_DATABASE_NAME}")
            )
    finally:
        await admin_engine.dispose()


@pytest.fixture(scope="session")
def event_loop():
    """セッションスコープのイベントループ。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database(event_loop):
    """テストセッション全体でデータベースを作成・削除します。"""
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
```

### フィクスチャの活用

プロジェクト共通のフィクスチャを作成：

```python
# tests/conftest.py に追加

@pytest.fixture
async def test_user(db_session):
    """テスト用ユーザー"""
    from app.models.sample_user import SampleUser
    from app.core.security import hash_password

    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password=hash_password("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session):
    """テスト用管理者"""
    from app.models.sample_user import SampleUser
    from app.core.security import hash_password

    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password=hash_password("admin123"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_file(db_session, test_user):
    """テスト用ファイル"""
    from app.models.sample_file import SampleFile

    file = File(
        file_id="test-file-id",
        filename="stored_test.txt",
        original_filename="test.txt",
        content_type="text/plain",
        size=1024,
        storage_path="/uploads/test-file-id.txt",
        user_id=test_user.id,
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)
    return file
```

## テストの実行

```bash
# PostgreSQLコンテナを起動
docker-compose up -d postgres

# すべてのテストを実行
uv run pytest

# 詳細出力付き
uv run pytest -v

# 特定のテストファイルを実行
uv run pytest tests/test_models.py

# 特定のテスト関数を実行
uv run pytest tests/test_models.py::test_create_user

# カバレッジレポート付き
uv run pytest --cov=app --cov-report=html
```

## 次のステップ

テストデータベースのセットアップが完了したら、次は具体的なテストパターンを学びます。

**[→ 次へ: テストパターンとベストプラクティス](./04-database-testing-patterns.md)**

## 参考リンク

- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [データベーステスト](./04-database-testing.md)
