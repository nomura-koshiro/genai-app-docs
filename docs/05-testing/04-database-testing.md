# データベーステスト

## 概要

データベーステストは、データベース層の操作（CRUD操作、クエリ、リレーション）が正しく動作するかを検証します。このドキュメントでは、SQLAlchemyを使用した非同期データベーステストの方法を、実践的な例とともに説明します。

## テストデータベースのセットアップ

### インメモリデータベースの使用

テストでは、本番データベースとは別のテストデータベースを使用します。最も簡単な方法は、SQLiteのインメモリデータベースを使用することです。

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from app.database import Base

# テスト用データベースURL（インメモリ）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """イベントループをセッションスコープで提供"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_engine():
    """テスト用データベースエンジンを提供"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # SQLログを表示しない
        future=True,
    )

    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # クリーンアップ
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """テスト用データベースセッションを提供"""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session
        # 各テスト後にロールバック
        await session.rollback()
```

### PostgreSQL テストデータベース

本番環境と同じPostgreSQLを使用する場合：

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base

TEST_DATABASE_URL = "postgresql+asyncpg://testuser:testpass@localhost:5432/test_db"

@pytest.fixture(scope="session")
async def test_engine():
    """PostgreSQLテストエンジン"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 全テーブル削除
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """各テストでトランザクションをロールバック"""
    connection = await test_engine.connect()
    transaction = await connection.begin()

    TestSessionLocal = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session

    # ロールバック
    await transaction.rollback()
    await connection.close()
```

## モデルのテスト

### 基本的なCRUD操作

```python
# tests/integration/models/test_user_model.py
import pytest
from app.models.user import User
from app.core.security import hash_password

class TestUserModel:
    """ユーザーモデルのテストスイート"""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """ユーザーの作成"""
        # Arrange
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password123"),
            is_active=True,
        )

        # Act
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Assert
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_read_user(self, db_session):
        """ユーザーの読み取り"""
        # ユーザーを作成
        user = User(
            email="read@example.com",
            username="readuser",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()

        # IDで取得
        from sqlalchemy import select
        stmt = select(User).where(User.id == user.id)
        result = await db_session.execute(stmt)
        retrieved_user = result.scalar_one_or_none()

        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.email == user.email

    @pytest.mark.asyncio
    async def test_update_user(self, db_session):
        """ユーザーの更新"""
        # ユーザーを作成
        user = User(
            email="update@example.com",
            username="updateuser",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()

        # 更新
        user.username = "updated_user"
        user.email = "updated@example.com"
        await db_session.commit()
        await db_session.refresh(user)

        # 検証
        assert user.username == "updated_user"
        assert user.email == "updated@example.com"
        assert user.updated_at > user.created_at

    @pytest.mark.asyncio
    async def test_delete_user(self, db_session):
        """ユーザーの削除"""
        # ユーザーを作成
        user = User(
            email="delete@example.com",
            username="deleteuser",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        user_id = user.id

        # 削除
        await db_session.delete(user)
        await db_session.commit()

        # 存在しないことを確認
        from sqlalchemy import select
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        deleted_user = result.scalar_one_or_none()

        assert deleted_user is None
```

### ユニーク制約のテスト

```python
class TestUserConstraints:
    """ユーザーモデルの制約テスト"""

    @pytest.mark.asyncio
    async def test_email_unique_constraint(self, db_session):
        """メールアドレスのユニーク制約"""
        # 最初のユーザー
        user1 = User(
            email="unique@example.com",
            username="user1",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user1)
        await db_session.commit()

        # 同じメールアドレスで2番目のユーザー
        user2 = User(
            email="unique@example.com",  # 重複
            username="user2",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user2)

        # 例外が発生することを確認
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_username_unique_constraint(self, db_session):
        """ユーザー名のユニーク制約"""
        # 最初のユーザー
        user1 = User(
            email="user1@example.com",
            username="uniqueuser",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user1)
        await db_session.commit()

        # 同じユーザー名で2番目のユーザー
        user2 = User(
            email="user2@example.com",
            username="uniqueuser",  # 重複
            hashed_password=hash_password("password123"),
        )
        db_session.add(user2)

        # 例外が発生することを確認
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            await db_session.commit()
```

## リレーションシップのテスト

### 1対多のリレーション

```python
# tests/integration/models/test_relationships.py
import pytest
from app.models.user import User
from app.models.file import File
from app.core.security import hash_password

class TestUserFileRelationship:
    """ユーザーとファイルのリレーションシップテスト"""

    @pytest.mark.asyncio
    async def test_user_files_relationship(self, db_session):
        """ユーザーが複数のファイルを持つ"""
        # ユーザーを作成
        user = User(
            email="fileowner@example.com",
            username="fileowner",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # ファイルを作成
        file1 = File(
            file_id="file-1",
            filename="stored_1.txt",
            original_filename="file1.txt",
            content_type="text/plain",
            size=100,
            storage_path="/uploads/file-1",
            user_id=user.id,
        )
        file2 = File(
            file_id="file-2",
            filename="stored_2.txt",
            original_filename="file2.txt",
            content_type="text/plain",
            size=200,
            storage_path="/uploads/file-2",
            user_id=user.id,
        )

        db_session.add_all([file1, file2])
        await db_session.commit()

        # ユーザーのファイルを取得
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        stmt = select(User).where(User.id == user.id).options(selectinload(User.files))
        result = await db_session.execute(stmt)
        user_with_files = result.scalar_one()

        # 検証
        assert len(user_with_files.files) == 2
        assert user_with_files.files[0].original_filename in ["file1.txt", "file2.txt"]
        assert user_with_files.files[1].original_filename in ["file1.txt", "file2.txt"]

    @pytest.mark.asyncio
    async def test_cascade_delete(self, db_session):
        """ユーザー削除時にファイルも削除される"""
        # ユーザーとファイルを作成
        user = User(
            email="cascade@example.com",
            username="cascadeuser",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        file = File(
            file_id="cascade-file",
            filename="cascade.txt",
            original_filename="cascade.txt",
            content_type="text/plain",
            size=100,
            storage_path="/uploads/cascade-file",
            user_id=user.id,
        )
        db_session.add(file)
        await db_session.commit()
        file_id = file.id

        # ユーザーを削除
        await db_session.delete(user)
        await db_session.commit()

        # ファイルも削除されていることを確認
        from sqlalchemy import select
        stmt = select(File).where(File.id == file_id)
        result = await db_session.execute(stmt)
        deleted_file = result.scalar_one_or_none()

        assert deleted_file is None
```

### 多対多のリレーション

```python
# 例: ユーザーとロールの多対多リレーション
@pytest.mark.asyncio
async def test_many_to_many_relationship(self, db_session):
    """多対多リレーションのテスト"""
    # ユーザーを作成
    user = User(
        email="roles@example.com",
        username="roleuser",
        hashed_password=hash_password("password123"),
    )

    # ロールを作成
    from app.models.role import Role
    admin_role = Role(name="admin")
    user_role = Role(name="user")

    # ユーザーにロールを割り当て
    user.roles.extend([admin_role, user_role])

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 検証
    assert len(user.roles) == 2
    role_names = [role.name for role in user.roles]
    assert "admin" in role_names
    assert "user" in role_names
```

## クエリのテスト

### 基本的なクエリ

```python
# tests/integration/database/test_queries.py
import pytest
from sqlalchemy import select, func
from app.models.user import User
from app.core.security import hash_password

class TestDatabaseQueries:
    """データベースクエリのテストスイート"""

    @pytest.fixture
    async def sample_users(self, db_session):
        """テスト用ユーザーを複数作成"""
        users = [
            User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                hashed_password=hash_password("password123"),
                is_active=i % 2 == 0,  # 偶数番号のみアクティブ
            )
            for i in range(5)
        ]
        db_session.add_all(users)
        await db_session.commit()
        return users

    @pytest.mark.asyncio
    async def test_select_all_users(self, db_session, sample_users):
        """全ユーザーの取得"""
        stmt = select(User)
        result = await db_session.execute(stmt)
        users = result.scalars().all()

        assert len(users) == 5

    @pytest.mark.asyncio
    async def test_filter_active_users(self, db_session, sample_users):
        """アクティブユーザーのフィルタリング"""
        stmt = select(User).where(User.is_active == True)
        result = await db_session.execute(stmt)
        active_users = result.scalars().all()

        # user0, user2, user4 がアクティブ
        assert len(active_users) == 3
        for user in active_users:
            assert user.is_active is True

    @pytest.mark.asyncio
    async def test_count_users(self, db_session, sample_users):
        """ユーザー数のカウント"""
        stmt = select(func.count()).select_from(User)
        result = await db_session.execute(stmt)
        count = result.scalar()

        assert count == 5

    @pytest.mark.asyncio
    async def test_pagination(self, db_session, sample_users):
        """ページネーション"""
        # 最初の2件
        stmt = select(User).limit(2).offset(0)
        result = await db_session.execute(stmt)
        page1 = result.scalars().all()

        assert len(page1) == 2

        # 次の2件
        stmt = select(User).limit(2).offset(2)
        result = await db_session.execute(stmt)
        page2 = result.scalars().all()

        assert len(page2) == 2
        # 異なるユーザー
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_order_by(self, db_session, sample_users):
        """ソート"""
        # メールアドレスで昇順
        stmt = select(User).order_by(User.email.asc())
        result = await db_session.execute(stmt)
        users_asc = result.scalars().all()

        # メールアドレスで降順
        stmt = select(User).order_by(User.email.desc())
        result = await db_session.execute(stmt)
        users_desc = result.scalars().all()

        # 逆順であることを確認
        assert users_asc[0].email == users_desc[-1].email
        assert users_asc[-1].email == users_desc[0].email
```

### 複雑なクエリ

```python
class TestComplexQueries:
    """複雑なクエリのテスト"""

    @pytest.mark.asyncio
    async def test_join_query(self, db_session):
        """JOIN クエリ"""
        from sqlalchemy.orm import joinedload

        # ユーザーとファイルを作成
        user = User(
            email="join@example.com",
            username="joinuser",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()

        file = File(
            file_id="join-file",
            filename="join.txt",
            original_filename="join.txt",
            content_type="text/plain",
            size=100,
            storage_path="/uploads/join-file",
            user_id=user.id,
        )
        db_session.add(file)
        await db_session.commit()

        # JOINでユーザーとファイルを同時取得
        stmt = select(User).options(joinedload(User.files)).where(User.id == user.id)
        result = await db_session.execute(stmt)
        user_with_files = result.unique().scalar_one()

        assert len(user_with_files.files) == 1
        assert user_with_files.files[0].file_id == "join-file"

    @pytest.mark.asyncio
    async def test_aggregate_query(self, db_session):
        """集計クエリ"""
        # 複数のユーザーとファイルを作成
        for i in range(3):
            user = User(
                email=f"agg{i}@example.com",
                username=f"agguser{i}",
                hashed_password=hash_password("password123"),
            )
            db_session.add(user)
            await db_session.commit()

            # 各ユーザーに異なる数のファイルを追加
            for j in range(i + 1):
                file = File(
                    file_id=f"agg-file-{i}-{j}",
                    filename=f"agg_{i}_{j}.txt",
                    original_filename=f"agg_{i}_{j}.txt",
                    content_type="text/plain",
                    size=100,
                    storage_path=f"/uploads/agg-file-{i}-{j}",
                    user_id=user.id,
                )
                db_session.add(file)
            await db_session.commit()

        # ユーザーごとのファイル数を集計
        from sqlalchemy import select, func
        stmt = (
            select(User.id, func.count(File.id).label("file_count"))
            .join(File)
            .group_by(User.id)
        )
        result = await db_session.execute(stmt)
        counts = result.all()

        # user0: 1ファイル, user1: 2ファイル, user2: 3ファイル
        assert len(counts) == 3
```

## トランザクションのテスト

### ロールバックのテスト

```python
class TestTransactions:
    """トランザクションのテスト"""

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session):
        """トランザクションのロールバック"""
        # ユーザーを作成
        user = User(
            email="rollback@example.com",
            username="rollbackuser",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.flush()  # DBに書き込むがコミットしない

        user_id = user.id
        assert user_id is not None

        # ロールバック
        await db_session.rollback()

        # ロールバック後はIDでアクセスできない
        from sqlalchemy import select
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        rolled_back_user = result.scalar_one_or_none()

        assert rolled_back_user is None

    @pytest.mark.asyncio
    async def test_transaction_commit(self, db_session):
        """トランザクションのコミット"""
        # ユーザーを作成
        user = User(
            email="commit@example.com",
            username="commituser",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()

        # 新しいセッションでもアクセス可能
        await db_session.refresh(user)
        assert user.id is not None
        assert user.email == "commit@example.com"
```

## テストデータの管理

### ファクトリパターン

```python
# tests/factories.py
from app.models.user import User
from app.models.file import File
from app.core.security import hash_password
import random

class UserFactory:
    """ユーザーのテストデータファクトリ"""

    @staticmethod
    def create(**kwargs):
        """ユーザーインスタンスを作成"""
        defaults = {
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "username": f"user{random.randint(1000, 9999)}",
            "hashed_password": hash_password("password123"),
            "is_active": True,
            "is_superuser": False,
        }
        defaults.update(kwargs)
        return User(**defaults)

    @staticmethod
    async def create_and_save(db_session, **kwargs):
        """ユーザーを作成してDBに保存"""
        user = UserFactory.create(**kwargs)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

class FileFactory:
    """ファイルのテストデータファクトリ"""

    @staticmethod
    def create(**kwargs):
        """ファイルインスタンスを作成"""
        file_id = f"file-{random.randint(1000, 9999)}"
        defaults = {
            "file_id": file_id,
            "filename": f"stored_{file_id}.txt",
            "original_filename": f"test_{random.randint(1000, 9999)}.txt",
            "content_type": "text/plain",
            "size": random.randint(100, 10000),
            "storage_path": f"/uploads/{file_id}",
        }
        defaults.update(kwargs)
        return File(**defaults)

    @staticmethod
    async def create_and_save(db_session, **kwargs):
        """ファイルを作成してDBに保存"""
        file = FileFactory.create(**kwargs)
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)
        return file

# 使用例
@pytest.mark.asyncio
async def test_with_factory(db_session):
    """ファクトリを使用したテスト"""
    # ユーザーを作成
    user = await UserFactory.create_and_save(
        db_session,
        email="factory@example.com"
    )

    # ファイルを作成
    file = await FileFactory.create_and_save(
        db_session,
        user_id=user.id
    )

    assert file.user_id == user.id
```

### フィクスチャの活用

```python
# tests/conftest.py
@pytest.fixture
async def test_user(db_session):
    """テスト用ユーザー"""
    user = UserFactory.create(email="testuser@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_admin(db_session):
    """テスト用管理者"""
    admin = UserFactory.create(
        email="admin@example.com",
        is_superuser=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin

@pytest.fixture
async def test_file(db_session, test_user):
    """テスト用ファイル"""
    file = FileFactory.create(user_id=test_user.id)
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)
    return file
```

## よくある間違いとその対処法

### 1. セッションの再利用

❌ **悪い例**:
```python
def test_multiple_operations(db_session):
    user1 = User(email="user1@example.com", ...)
    db_session.add(user1)
    await db_session.commit()

    # セッションが期限切れの可能性
    user1.username = "updated"  # エラーが発生する可能性
```

✅ **良い例**:
```python
async def test_multiple_operations(db_session):
    user1 = User(email="user1@example.com", ...)
    db_session.add(user1)
    await db_session.commit()
    await db_session.refresh(user1)  # リフレッシュ

    user1.username = "updated"
    await db_session.commit()
```

### 2. トランザクションの管理

❌ **悪い例**:
```python
async def test_without_cleanup(db_session):
    user = User(email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
    # クリーンアップなし - 他のテストに影響
```

✅ **良い例**:
```python
@pytest.fixture
async def db_session(test_engine):
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()  # 自動クリーンアップ
```

### 3. 非同期処理の誤用

❌ **悪い例**:
```python
def test_async_operation(db_session):  # asyncがない
    user = User(email="test@example.com", ...)
    db_session.add(user)
    db_session.commit()  # awaitがない
```

✅ **良い例**:
```python
@pytest.mark.asyncio
async def test_async_operation(db_session):
    user = User(email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
```

## ベストプラクティス

### 1. テストの独立性を保つ

```python
@pytest.fixture(autouse=True)
async def cleanup(db_session):
    """各テスト後に自動クリーンアップ"""
    yield
    await db_session.rollback()
```

### 2. テストデータの最小化

```python
# 必要最小限のデータのみ作成
async def test_user_creation(db_session):
    user = User(
        email="test@example.com",
        username="test",
        hashed_password="hashed",
    )
    # 不要なリレーションデータは作成しない
```

### 3. 明確なアサーション

```python
async def test_user_properties(db_session):
    user = UserFactory.create(email="test@example.com")
    db_session.add(user)
    await db_session.commit()

    # 複数の具体的なアサーション
    assert user.id is not None, "IDが設定されていない"
    assert user.email == "test@example.com", "メールアドレスが一致しない"
    assert user.created_at is not None, "作成日時が設定されていない"
```

## 参考リンク

- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Database Testing](https://fastapi.tiangolo.com/advanced/testing-database/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

## 次のステップ

- [モックとフィクスチャ](./05-mocks-fixtures.md) - 高度なモックとフィクスチャの使用
- [ベストプラクティス](./06-best-practices.md) - より良いテストを書くために
