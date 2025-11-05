# モックとフィクスチャ

## 概要

モックとフィクスチャは、テストを効率的かつ信頼性高く実行するための重要な技術です。このドキュメントでは、`unittest.mock`、`pytest-mock`、pytestのフィクスチャを使用した高度なテスト技法を説明します。

## モック（Mock）の基礎

### モックとは

モックは、実際のオブジェクトの代わりに使用する偽のオブジェクトです。外部依存（データベース、API、ファイルシステムなど）を置き換えて、テストを高速化し、制御可能にします。

### unittest.mock の基本

```python
from unittest.mock import Mock, MagicMock, patch

def test_basic_mock():
    """基本的なモックの使用"""
    # Mockオブジェクトの作成
    mock_obj = Mock()

    # 任意の属性やメソッドを持てる
    mock_obj.method.return_value = "mocked value"

    # 呼び出し
    result = mock_obj.method()
    assert result == "mocked value"

    # 呼び出しの検証
    mock_obj.method.assert_called_once()

def test_magic_mock():
    """マジックメソッドをサポートするモック"""
    mock_obj = MagicMock()

    # マジックメソッドも使用可能
    mock_obj.__len__.return_value = 5
    assert len(mock_obj) == 5

    mock_obj.__getitem__.return_value = "item"
    assert mock_obj[0] == "item"
```

### pytest-mock の使用

pytest-mockは、pytestとunittest.mockを統合したプラグインです。

```powershell
# インストール
pip install pytest-mock
```

```python
# tests/unit/test_with_mocker.py
import pytest

def test_with_mocker(mocker):
    """mockerフィクスチャの使用"""
    # 関数をモック
    mock_function = mocker.Mock(return_value="mocked")

    result = mock_function("arg1", "arg2")

    assert result == "mocked"
    mock_function.assert_called_once_with("arg1", "arg2")

def test_patch_with_mocker(mocker):
    """モジュールの関数をパッチ"""
    # datetime.now をモック
    from datetime import datetime
    mock_now = datetime(2024, 1, 1, 12, 0, 0)
    mocker.patch("datetime.datetime.now", return_value=mock_now)

    # テスト対象の関数
    def get_current_time():
        from datetime import datetime
        return datetime.now()

    result = get_current_time()
    assert result == mock_now
```

## 外部サービスのモック

### データベースのモック

```python
# tests/unit/services/test_user_service.py
import pytest
from unittest.mock import AsyncMock
from app.services.sample_user import SampleUserService
from app.models.sample_user import SampleUser

class TestSampleUserService:
    """ユーザーサービスのユニットテスト（モック使用）"""

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, mocker):
        """IDでユーザーを取得"""
        # データベースセッションをモック
        mock_db = mocker.Mock()

        # クエリ結果をモック
        mock_user = SampleUser(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
        )

        # execute().scalar_one_or_none() をモック
        mock_result = mocker.Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        # サービスのテスト
        service = SampleUserService(mock_db)
        user = await service.get_user(1)

        assert user.id == 1
        assert user.email == "test@example.com"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user(self, mocker):
        """ユーザーの作成"""
        mock_db = mocker.Mock()
        mock_db.add = mocker.Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = SampleUserService(mock_db)

        # ユーザーデータ
        user_data = {
            "email": "new@example.com",
            "username": "newuser",
            "password": "password123",
        }

        # パスワードハッシュ化をモック
        mocker.patch(
            "app.core.security.password.hash_password",
            return_value="hashed_password"
        )

        user = await service.create_user(**user_data)

        # 検証
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
```

### 外部APIのモック

```python
# tests/unit/services/test_external_api.py
import pytest
from unittest.mock import AsyncMock
import httpx

class TestExternalAPI:
    """外部APIのモックテスト"""

    @pytest.mark.asyncio
    async def test_fetch_data_from_api(self, mocker):
        """外部APIからデータを取得"""
        # httpx.AsyncClient をモック
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": "mocked data",
            "status": "success"
        }

        mock_client = mocker.Mock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # AsyncClient のコンテキストマネージャをモック
        mocker.patch(
            "httpx.AsyncClient",
            return_value=mocker.MagicMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(),
            )
        )

        # テスト対象の関数
        async def fetch_external_data():
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.example.com/data")
                return response.json()

        result = await fetch_external_data()

        assert result["data"] == "mocked data"
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mocker):
        """APIエラーの処理"""
        # エラーレスポンスをモック
        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=mocker.Mock(),
            response=mock_response
        )

        mock_client = mocker.Mock()
        mock_client.get = AsyncMock(return_value=mock_response)

        mocker.patch(
            "httpx.AsyncClient",
            return_value=mocker.MagicMock(
                __aenter__=AsyncMock(return_value=mock_client),
                __aexit__=AsyncMock(),
            )
        )

        # エラーハンドリングをテスト
        async def fetch_with_error_handling():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError:
                return {"error": "API request failed"}

        result = await fetch_with_error_handling()
        assert "error" in result
```

### ファイルシステムのモック

```python
# tests/unit/services/test_file_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, mock_open
from pathlib import Path

class TestFileOperations:
    """ファイル操作のモック"""

    def test_read_file(self, mocker):
        """ファイル読み取りのモック"""
        mock_file_content = "mocked file content"

        # open() をモック
        m = mock_open(read_data=mock_file_content)
        mocker.patch("builtins.open", m)

        # テスト対象
        def read_file(path):
            with open(path, "r") as f:
                return f.read()

        result = read_file("/path/to/file.txt")

        assert result == mock_file_content
        m.assert_called_once_with("/path/to/file.txt", "r")

    def test_write_file(self, mocker):
        """ファイル書き込みのモック"""
        m = mock_open()
        mocker.patch("builtins.open", m)

        # テスト対象
        def write_file(path, content):
            with open(path, "w") as f:
                f.write(content)

        write_file("/path/to/file.txt", "content")

        m.assert_called_once_with("/path/to/file.txt", "w")
        m().write.assert_called_once_with("content")

    @pytest.mark.asyncio
    async def test_azure_blob_storage_mock(self, mocker):
        """Azure Blob Storageのモック"""
        # BlobServiceClient をモック
        mock_blob_client = mocker.Mock()
        mock_blob_client.upload_blob = AsyncMock()

        mock_container_client = mocker.Mock()
        mock_container_client.get_blob_client.return_value = mock_blob_client

        mock_blob_service = mocker.Mock()
        mock_blob_service.get_container_client.return_value = mock_container_client

        mocker.patch(
            "azure.storage.blob.BlobServiceClient.from_connection_string",
            return_value=mock_blob_service
        )

        # テスト対象の関数
        from azure.storage.blob import BlobServiceClient

        async def upload_to_blob(container, blob_name, data):
            blob_service = BlobServiceClient.from_connection_string("connection_string")
            container_client = blob_service.get_container_client(container)
            blob_client = container_client.get_blob_client(blob_name)
            await blob_client.upload_blob(data)

        await upload_to_blob("test-container", "test.txt", b"data")

        # 検証
        mock_blob_client.upload_blob.assert_called_once_with(b"data")
```

## pytestフィクスチャの高度な使用

### スコープの使い分け

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def app_config():
    """アプリケーション設定（セッション全体で1回）"""
    return {
        "app_name": "Test App",
        "version": "1.0.0",
    }

@pytest.fixture(scope="module")
def database_connection():
    """データベース接続（モジュールごと）"""
    print("データベース接続を確立")
    connection = "db_connection"
    yield connection
    print("データベース接続を閉じる")

@pytest.fixture(scope="class")
def api_client():
    """APIクライアント（クラスごと）"""
    print("APIクライアントを初期化")
    client = "api_client"
    yield client
    print("APIクライアントをクリーンアップ")

@pytest.fixture(scope="function")
def temp_data():
    """一時データ（各テストごと）"""
    print("一時データを作成")
    data = {"temp": "data"}
    yield data
    print("一時データをクリーンアップ")
```

### パラメータ化されたフィクスチャ

```python
import pytest

@pytest.fixture(params=[
    "sqlite+aiosqlite:///:memory:",
    "postgresql+asyncpg://localhost/test_db",
])
def database_url(request):
    """複数のデータベースURLでテスト"""
    return request.param

def test_with_different_databases(database_url):
    """異なるデータベースでテスト"""
    print(f"Testing with: {database_url}")
    assert "://" in database_url

# IDを指定
@pytest.fixture(params=[
    pytest.param("admin", id="admin_user"),
    pytest.param("user", id="regular_user"),
    pytest.param("guest", id="guest_user"),
])
def user_role(request):
    """異なるユーザーロールでテスト"""
    return request.param

def test_authorization(user_role):
    """ロールごとの認可をテスト"""
    if user_role == "admin":
        assert True  # 管理者は全アクセス可能
    elif user_role == "user":
        assert True  # ユーザーは制限付きアクセス
    else:
        assert True  # ゲストは最小限のアクセス
```

### フィクスチャのファクトリパターン

```python
import pytest
from app.models.sample_user import SampleUser
from app.core.security import hash_password

@pytest.fixture
def user_factory(db_session):
    """ユーザー作成ファクトリ"""
    created_users = []

    async def _create_user(**kwargs):
        defaults = {
            "email": f"user{len(created_users)}@example.com",
            "username": f"user{len(created_users)}",
            "hashed_password": hash_password("password123"),
            "is_active": True,
        }
        defaults.update(kwargs)

        user = SampleUser(**defaults)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        created_users.append(user)
        return user

    yield _create_user

    # クリーンアップ
    for user in created_users:
        await db_session.delete(user)
    await db_session.commit()

@pytest.mark.asyncio
async def test_with_user_factory(user_factory):
    """ファクトリを使用して複数のユーザーを作成"""
    user1 = await user_factory(email="user1@example.com")
    user2 = await user_factory(email="user2@example.com")
    admin = await user_factory(email="admin@example.com", is_superuser=True)

    assert user1.email == "user1@example.com"
    assert user2.email == "user2@example.com"
    assert admin.is_superuser is True
```

### フィクスチャの依存関係

```python
@pytest.fixture
async def test_user(db_session):
    """テストユーザーを作成"""
    user = SampleUser(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def auth_token(test_user):
    """認証トークン（test_userに依存）"""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": str(test_user.id)})

@pytest.fixture
def auth_headers(auth_token):
    """認証ヘッダー（auth_tokenに依存）"""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.mark.asyncio
async def test_with_dependencies(client, test_user, auth_headers):
    """依存関係のあるフィクスチャを使用"""
    response = client.get("/api/v1/sample-users/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
```

### 自動使用フィクスチャ（autouse）

```python
@pytest.fixture(autouse=True)
def reset_database(db_session):
    """各テスト後にデータベースをリセット"""
    yield
    # テスト後に自動実行
    await db_session.rollback()

@pytest.fixture(autouse=True)
def setup_logging():
    """テスト前にロギングを設定"""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    yield
    # クリーンアップ
    logging.shutdown()
```

## 高度なモック技法

### 副作用（side_effect）の使用

```python
def test_side_effect(mocker):
    """副作用を使用したモック"""
    # 複数の戻り値
    mock_func = mocker.Mock(side_effect=[1, 2, 3])
    assert mock_func() == 1
    assert mock_func() == 2
    assert mock_func() == 3

    # 例外を発生させる
    mock_func = mocker.Mock(side_effect=ValueError("Error"))
    with pytest.raises(ValueError):
        mock_func()

    # カスタム関数を実行
    def custom_side_effect(arg):
        return arg * 2

    mock_func = mocker.Mock(side_effect=custom_side_effect)
    assert mock_func(5) == 10
```

### 呼び出しの検証

```python
def test_call_verification(mocker):
    """呼び出しの詳細な検証"""
    mock_func = mocker.Mock()

    # 関数を複数回呼び出し
    mock_func(1, 2)
    mock_func(3, 4, key="value")
    mock_func(5)

    # 呼び出し回数の検証
    assert mock_func.call_count == 3

    # 特定の引数で呼び出されたか
    mock_func.assert_any_call(1, 2)
    mock_func.assert_any_call(3, 4, key="value")

    # 最後の呼び出しの検証
    mock_func.assert_called_with(5)

    # 呼び出しのリスト
    from unittest.mock import call
    expected_calls = [
        call(1, 2),
        call(3, 4, key="value"),
        call(5),
    ]
    mock_func.assert_has_calls(expected_calls)
```

### スパイ（Spy）パターン

```python
def test_spy_pattern(mocker):
    """実際の関数を呼び出しつつ、呼び出しを監視"""
    # 実際の関数
    def original_function(x):
        return x * 2

    # スパイでラップ
    spy = mocker.spy(original_function.__class__, original_function.__name__)

    # 実際の関数が呼び出される
    result = original_function(5)
    assert result == 10

    # 呼び出しを検証
    spy.assert_called_once_with(5)
```

### パッチのコンテキストマネージャ

```python
def test_patch_context_manager(mocker):
    """パッチをコンテキストマネージャとして使用"""
    from datetime import datetime

    original_now = datetime.now()

    with mocker.patch("datetime.datetime.now") as mock_now:
        mock_now.return_value = datetime(2024, 1, 1, 12, 0, 0)

        # パッチが適用されている
        assert datetime.now() == datetime(2024, 1, 1, 12, 0, 0)

    # パッチが解除されている
    assert datetime.now() != datetime(2024, 1, 1, 12, 0, 0)
```

## テストデータ管理のベストプラクティス

### テストデータビルダー

```python
# tests/builders.py
class UserBuilder:
    """ユーザーのテストデータビルダー"""

    def __init__(self):
        self._email = "default@example.com"
        self._username = "defaultuser"
        self._password = "password123"
        self._is_active = True
        self._is_superuser = False

    def with_email(self, email):
        self._email = email
        return self

    def with_username(self, username):
        self._username = username
        return self

    def as_admin(self):
        self._is_superuser = True
        return self

    def as_inactive(self):
        self._is_active = False
        return self

    def build(self):
        from app.models.sample_user import SampleUser
        from app.core.security.password import hash_password

        return SampleUser(
            email=self._email,
            username=self._username,
            hashed_password=hash_password(self._password),
            is_active=self._is_active,
            is_superuser=self._is_superuser,
        )

# 使用例
def test_with_builder():
    """ビルダーパターンの使用"""
    # 通常のユーザー
    user = UserBuilder().with_email("user@example.com").build()
    assert user.email == "user@example.com"
    assert user.is_superuser is False

    # 管理者
    admin = UserBuilder().with_email("admin@example.com").as_admin().build()
    assert admin.is_superuser is True

    # 非アクティブユーザー
    inactive = UserBuilder().as_inactive().build()
    assert inactive.is_active is False
```

### フィクスチャのカスタマイズ

```python
@pytest.fixture
def custom_user(request):
    """カスタマイズ可能なユーザーフィクスチャ"""
    # マーカーからパラメータを取得
    marker = request.node.get_closest_marker("user_config")
    if marker:
        config = marker.kwargs
    else:
        config = {}

    # デフォルト設定
    defaults = {
        "email": "default@example.com",
        "username": "defaultuser",
        "is_superuser": False,
    }
    defaults.update(config)

    return UserBuilder().with_email(defaults["email"]).build()

# 使用例
@pytest.mark.user_config(email="custom@example.com", is_superuser=True)
def test_with_custom_user(custom_user):
    assert custom_user.email == "custom@example.com"
    assert custom_user.is_superuser is True
```

## よくある間違いとその対処法

### 1. モックの過剰使用

❌ **悪い例**:

```python
def test_simple_calculation(mocker):
    # 単純な計算をモック（不要）
    mocker.patch("builtins.sum", return_value=10)
    assert sum([1, 2, 3, 4]) == 10  # 実際の動作をテストしていない
```

✅ **良い例**:

```python
def test_simple_calculation():
    # 実際の動作をテスト
    assert sum([1, 2, 3, 4]) == 10
```

### 2. モックの適切なスコープ

❌ **悪い例**:

```python
# グローバルなモック（他のテストに影響）
mock_func = Mock(return_value="global")

def test_a():
    assert mock_func() == "global"

def test_b():
    # 前のテストの影響を受ける
    assert mock_func.call_count == 1  # 期待: 0, 実際: 1
```

✅ **良い例**:

```python
@pytest.fixture
def mock_func(mocker):
    """各テストで新しいモック"""
    return mocker.Mock(return_value="mocked")

def test_a(mock_func):
    assert mock_func() == "mocked"

def test_b(mock_func):
    assert mock_func.call_count == 0  # 期待通り
```

### 3. 非同期関数のモック

❌ **悪い例**:

```python
def test_async_function(mocker):
    # 非同期関数を同期的にモック
    mocker.patch("app.service.async_func", return_value="value")
    # await が必要な場所でエラーが発生
```

✅ **良い例**:

```python
@pytest.mark.asyncio
async def test_async_function(mocker):
    # AsyncMock を使用
    mocker.patch("app.service.async_func", new=AsyncMock(return_value="value"))
    result = await async_func()
    assert result == "value"
```

## ベストプラクティス

### 1. モックは最小限に

```python
# 外部依存のみモック
@pytest.mark.asyncio
async def test_user_service(mocker):
    # データベースはモック（外部依存）
    mock_db = mocker.Mock()

    # ビジネスロジックは実際のコード
    service = SampleUserService(mock_db)
    # ...
```

### 2. フィクスチャの再利用

```python
# tests/conftest.py - プロジェクト全体で共有
@pytest.fixture
def test_user():
    return UserBuilder().build()

# tests/unit/conftest.py - unitテストで共有
@pytest.fixture
def mock_db(mocker):
    return mocker.Mock()
```

### 3. 明確な命名

```python
# 明確なフィクスチャ名
@pytest.fixture
def authenticated_admin_user():
    """認証済み管理者ユーザー"""
    pass

@pytest.fixture
def mock_azure_blob_client():
    """Azure Blob Storageクライアントのモック"""
    pass
```

## 参考リンク

- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Effective Python Testing With Pytest](https://realpython.com/pytest-python-testing/)
- [Mock Testing Best Practices](https://martinfowler.com/articles/mocksArentStubs.html)

## 次のステップ

- [ベストプラクティス](./06-best-practices.md) - より良いテストを書くために
- [テスト戦略](./01-testing-strategy.md) - 全体的なテスト戦略に戻る
