# APIテスト

## 概要

APIテストは、FastAPIのエンドポイントが正しく動作するかを検証します。このドキュメントでは、FastAPIのTestClientを使用したAPIテストの方法を、実践的な例とともに説明します。

## FastAPI TestClient

### TestClientとは

TestClientは、FastAPIアプリケーションをテストするための専用クライアントです。実際のHTTPサーバーを起動せずに、APIエンドポイントをテストできます。

### 基本的なセットアップ

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db

# テスト用データベース
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def test_db():
    """テスト用データベースセッションを提供"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # セッションファクトリ
    TestSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session

    # クリーンアップ
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
def client(test_db):
    """TestClientインスタンスを提供"""
    # データベース依存関係をオーバーライド
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # クリーンアップ
    app.dependency_overrides.clear()
```

## 基本的なAPIテスト

### GETリクエストのテスト

```python
# tests/integration/api/test_basic_endpoints.py
import pytest
from fastapi import status

def test_root_endpoint(client):
    """ルートエンドポイントのテスト"""
    response = client.get("/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data

def test_health_check(client):
    """ヘルスチェックエンドポイントのテスト"""
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data

def test_not_found_endpoint(client):
    """存在しないエンドポイントのテスト"""
    response = client.get("/nonexistent")

    assert response.status_code == status.HTTP_404_NOT_FOUND
```

### POSTリクエストのテスト

```python
# tests/integration/api/test_files_routes.py
import pytest
from fastapi import status
from io import BytesIO

class TestFileUpload:
    """ファイルアップロードAPIのテストスイート"""

    def test_upload_file_success(self, client):
        """ファイルアップロードの成功"""
        # テストファイルの準備
        file_content = b"test file content"
        file = BytesIO(file_content)

        response = client.post(
            "/api/sample-files/upload",
            files={"file": ("test.txt", file, "text/plain")}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test.txt"
        assert data["size"] == len(file_content)
        assert data["content_type"] == "text/plain"
        assert data["message"] == "File uploaded successfully"

    def test_upload_file_without_file(self, client):
        """ファイルなしでのアップロード（エラー）"""
        response = client.post("/api/sample-files/upload")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_large_file(self, client):
        """大きなファイルのアップロード"""
        # 5MBのファイル
        file_content = b"x" * (5 * 1024 * 1024)
        file = BytesIO(file_content)

        response = client.post(
            "/api/sample-files/upload",
            files={"file": ("large.txt", file, "text/plain")}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["size"] == len(file_content)

    @pytest.mark.parametrize("filename,content_type", [
        ("document.pdf", "application/pdf"),
        ("image.jpg", "image/jpeg"),
        ("data.json", "application/json"),
        ("script.py", "text/x-python"),
    ])
    def test_upload_different_file_types(self, client, filename, content_type):
        """様々なファイルタイプのアップロード"""
        file_content = b"test content"
        file = BytesIO(file_content)

        response = client.post(
            "/api/sample-files/upload",
            files={"file": (filename, file, content_type)}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["filename"] == filename
        assert data["content_type"] == content_type
```

### PUTリクエストのテスト

```python
def test_update_user(client, test_user):
    """ユーザー情報の更新"""
    update_data = {
        "username": "updated_user",
        "email": "updated@example.com",
    }

    response = client.put(
        f"/api/sample-users/{test_user.id}",
        json=update_data
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == update_data["username"]
    assert data["email"] == update_data["email"]
```

### DELETEリクエストのテスト

```python
class TestFileDelete:
    """ファイル削除APIのテストスイート"""

    @pytest.fixture
    def uploaded_file(self, client):
        """テスト用にファイルをアップロード"""
        file_content = b"test content"
        file = BytesIO(file_content)

        response = client.post(
            "/api/sample-files/upload",
            files={"file": ("test.txt", file, "text/plain")}
        )
        return response.json()

    def test_delete_file_success(self, client, uploaded_file):
        """ファイル削除の成功"""
        file_id = uploaded_file["file_id"]

        response = client.delete(f"/api/sample-files/{file_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["file_id"] == file_id
        assert "deleted successfully" in data["message"]

    def test_delete_nonexistent_file(self, client):
        """存在しないファイルの削除"""
        response = client.delete("/api/sample-files/nonexistent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_access_deleted_file(self, client, uploaded_file):
        """削除されたファイルにアクセスできない"""
        file_id = uploaded_file["file_id"]

        # ファイルを削除
        client.delete(f"/api/sample-files/{file_id}")

        # ダウンロードを試みる
        response = client.get(f"/api/sample-files/download/{file_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
```

## クエリパラメータとパスパラメータ

### クエリパラメータのテスト

```python
class TestFileList:
    """ファイル一覧APIのテストスイート"""

    @pytest.fixture
    async def sample_files(self, client):
        """テスト用ファイルを複数アップロード"""
        files = []
        for i in range(5):
            file_content = f"content {i}".encode()
            file = BytesIO(file_content)
            response = client.post(
                "/api/sample-files/upload",
                files={"file": (f"test_{i}.txt", file, "text/plain")}
            )
            files.append(response.json())
        return files

    def test_list_all_files(self, client, sample_files):
        """全ファイルの一覧取得"""
        response = client.get("/api/sample-files/list")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "files" in data
        assert "total" in data
        assert len(data["files"]) == 5

    def test_list_files_with_pagination(self, client, sample_files):
        """ページネーション付きファイル一覧"""
        # 最初の2件
        response = client.get("/api/sample-files/list?skip=0&limit=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["files"]) == 2

        # 次の2件
        response = client.get("/api/sample-files/list?skip=2&limit=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["files"]) == 2

    @pytest.mark.parametrize("skip,limit,expected_count", [
        (0, 10, 5),  # 全件取得
        (0, 2, 2),   # 最初の2件
        (2, 2, 2),   # 3-4件目
        (4, 2, 1),   # 5件目のみ
        (5, 2, 0),   # 範囲外
    ])
    def test_list_files_pagination_variations(
        self, client, sample_files, skip, limit, expected_count
    ):
        """様々なページネーションパターン"""
        response = client.get(f"/api/sample-files/list?skip={skip}&limit={limit}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["files"]) == expected_count
```

### パスパラメータのテスト

```python
def test_download_file_with_valid_id(client, uploaded_file):
    """有効なIDでファイルダウンロード"""
    file_id = uploaded_file["file_id"]

    response = client.get(f"/api/sample-files/download/{file_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "content-disposition" in response.headers

def test_download_file_with_invalid_id(client):
    """無効なIDでファイルダウンロード"""
    response = client.get("/api/sample-files/download/invalid-id")

    assert response.status_code == status.HTTP_404_NOT_FOUND
```

## 認証テスト

### 認証トークンの生成

```python
# tests/conftest.py
import pytest
from app.core.security import create_access_token

@pytest.fixture
def test_user_data():
    """テストユーザーデータ"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
    }

@pytest.fixture
def auth_token(test_user_data):
    """認証トークンを生成"""
    return create_access_token(data={"sub": str(test_user_data["id"])})

@pytest.fixture
def auth_headers(auth_token):
    """認証ヘッダーを生成"""
    return {"Authorization": f"Bearer {auth_token}"}
```

### 認証が必要なエンドポイントのテスト

```python
# tests/integration/api/test_auth_routes.py
import pytest
from fastapi import status

class TestAuthenticatedEndpoints:
    """認証が必要なエンドポイントのテストスイート"""

    def test_access_protected_endpoint_without_token(self, client):
        """トークンなしで保護されたエンドポイントにアクセス"""
        response = client.get("/api/sample-users/sample-me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_invalid_token(self, client):
        """無効なトークンで保護されたエンドポイントにアクセス"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/sample-users/sample-me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_valid_token(
        self, client, auth_headers, test_user_data
    ):
        """有効なトークンで保護されたエンドポイントにアクセス"""
        response = client.get("/api/sample-users/sample-me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user_data["email"]

    def test_upload_file_with_authentication(self, client, auth_headers):
        """認証付きファイルアップロード"""
        file_content = b"authenticated upload"
        file = BytesIO(file_content)

        response = client.post(
            "/api/sample-files/upload",
            files={"file": ("auth_test.txt", file, "text/plain")},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        # ファイルがユーザーに紐付けられているか確認
        data = response.json()
        assert "file_id" in data
```

### 異なる権限レベルのテスト

```python
@pytest.fixture
def admin_token():
    """管理者トークンを生成"""
    return create_access_token(data={"sub": "1", "role": "admin"})

@pytest.fixture
def user_token():
    """一般ユーザートークンを生成"""
    return create_access_token(data={"sub": "2", "role": "user"})

class TestRoleBasedAccess:
    """ロールベースアクセス制御のテスト"""

    def test_admin_can_access_admin_endpoint(self, client, admin_token):
        """管理者が管理者エンドポイントにアクセス可能"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/users", headers=headers)

        assert response.status_code == status.HTTP_200_OK

    def test_user_cannot_access_admin_endpoint(self, client, user_token):
        """一般ユーザーが管理者エンドポイントにアクセス不可"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/admin/users", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_can_access_own_resources(self, client, user_token):
        """ユーザーが自身のリソースにアクセス可能"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/sample-users/sample-me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
```

## レスポンスの検証

### JSONレスポンスの検証

```python
def test_response_structure(client):
    """レスポンス構造の検証"""
    response = client.get("/api/sample-files/list")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # 必須フィールドの存在確認
    assert "files" in data
    assert "total" in data

    # データ型の確認
    assert isinstance(data["files"], list)
    assert isinstance(data["total"], int)

    # ファイルがある場合、各ファイルの構造を確認
    if data["files"]:
        file = data["files"][0]
        assert "file_id" in file
        assert "filename" in file
        assert "size" in file
        assert "content_type" in file
        assert "created_at" in file
```

### ヘッダーの検証

```python
def test_response_headers(client, uploaded_file):
    """レスポンスヘッダーの検証"""
    file_id = uploaded_file["file_id"]
    response = client.get(f"/api/sample-files/download/{file_id}")

    assert response.status_code == status.HTTP_200_OK

    # Content-Typeヘッダー
    assert "content-type" in response.headers
    assert response.headers["content-type"].startswith("text/plain")

    # Content-Dispositionヘッダー
    assert "content-disposition" in response.headers
    assert "attachment" in response.headers["content-disposition"]
    assert uploaded_file["filename"] in response.headers["content-disposition"]
```

### エラーレスポンスの検証

```python
class TestErrorResponses:
    """エラーレスポンスのテスト"""

    def test_validation_error_response(self, client):
        """バリデーションエラーのレスポンス"""
        # 不正なデータでリクエスト
        response = client.post(
            "/api/sample-users",
            json={"email": "invalid-email"}  # 無効なメール形式
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    def test_not_found_error_response(self, client):
        """NotFoundエラーのレスポンス"""
        response = client.get("/api/sample-files/download/nonexistent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "error" in data or "detail" in data

    def test_unauthorized_error_response(self, client):
        """認証エラーのレスポンス"""
        response = client.get("/api/sample-users/sample-me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data
```

## 非同期エンドポイントのテスト

### 非同期テストのセットアップ

```python
# tests/integration/api/test_async_endpoints.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def async_client():
    """非同期TestClientを提供"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_async_file_upload(async_client):
    """非同期ファイルアップロード"""
    file_content = b"async test content"

    response = await async_client.post(
        "/api/sample-files/upload",
        files={"file": ("async_test.txt", file_content, "text/plain")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data

@pytest.mark.asyncio
async def test_concurrent_requests(async_client):
    """並行リクエストのテスト"""
    import asyncio

    async def upload_file(i):
        file_content = f"file {i}".encode()
        return await async_client.post(
            "/api/sample-files/upload",
            files={"file": (f"file_{i}.txt", file_content, "text/plain")}
        )

    # 5つのファイルを同時にアップロード
    responses = await asyncio.gather(*[upload_file(i) for i in range(5)])

    # 全てのリクエストが成功
    for response in responses:
        assert response.status_code == 200
```

## ミドルウェアのテスト

### エラーハンドラーミドルウェア

```python
# tests/integration/middleware/test_error_handler.py
import pytest
from fastapi import status

def test_error_handler_middleware(client):
    """エラーハンドラーミドルウェアのテスト"""
    # 意図的にエラーを発生させるエンドポイント（テスト用）
    response = client.get("/api/test/error")

    # エラーが適切に処理されている
    assert response.status_code in [
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        status.HTTP_404_NOT_FOUND
    ]
```

### レート制限ミドルウェア

```python
# tests/integration/middleware/test_rate_limit.py
import pytest
from fastapi import status
import time

def test_rate_limiting(client):
    """レート制限のテスト"""
    # 制限を超えるリクエストを送信
    responses = []
    for _ in range(101):  # 制限が100/分の場合
        response = client.get("/health")
        responses.append(response)

    # 最後のリクエストがレート制限エラー
    assert responses[-1].status_code == status.HTTP_429_TOO_MANY_REQUESTS

def test_rate_limit_reset(client):
    """レート制限のリセット"""
    # 制限を超える
    for _ in range(101):
        client.get("/health")

    # 時間経過後にリセット
    time.sleep(61)  # 1分以上待機

    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
```

## よくある間違いとその対処法

### 1. データベーストランザクションの管理

❌ **悪い例**:

```python
def test_create_user(client):
    # データベースのクリーンアップなし
    response = client.post("/api/sample-users", json={"email": "test@example.com"})
    # テスト後もデータが残る
```

✅ **良い例**:

```python
@pytest.fixture
async def test_db():
    """各テスト後にロールバック"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()
```

### 2. 非同期処理の誤用

❌ **悪い例**:

```python
def test_async_endpoint(client):
    # 非同期エンドポイントを同期的にテスト
    response = client.get("/api/async-endpoint")
```

✅ **良い例**:

```python
@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    response = await async_client.get("/api/async-endpoint")
```

### 3. テストデータの漏洩

❌ **悪い例**:

```python
def test_upload_file(client):
    # ファイルがクリーンアップされない
    response = client.post(
        "/api/sample-files/upload",
        files={"file": ("test.txt", b"content", "text/plain")}
    )
```

✅ **良い例**:

```python
@pytest.fixture
def uploaded_file(client):
    response = client.post(
        "/api/sample-files/upload",
        files={"file": ("test.txt", b"content", "text/plain")}
    )
    file_id = response.json()["file_id"]
    yield response.json()
    # クリーンアップ
    client.delete(f"/api/sample-files/{file_id}")
```

## ベストプラクティス

### 1. テストの構造化

```python
class TestFileAPI:
    """ファイルAPIのテストスイート"""

    class TestUpload:
        """アップロード機能のテスト"""

        def test_success(self, client):
            """正常系"""
            pass

        def test_validation_error(self, client):
            """バリデーションエラー"""
            pass

    class TestDownload:
        """ダウンロード機能のテスト"""

        def test_success(self, client, uploaded_file):
            """正常系"""
            pass

        def test_not_found(self, client):
            """ファイルが見つからない"""
            pass
```

### 2. フィクスチャの再利用

```python
# tests/conftest.py
@pytest.fixture
def sample_file():
    """テスト用ファイルデータ"""
    return {
        "filename": "test.txt",
        "content": b"test content",
        "content_type": "text/plain"
    }

@pytest.fixture
def uploaded_file(client, sample_file):
    """アップロード済みファイル"""
    response = client.post(
        "/api/sample-files/upload",
        files={"file": (
            sample_file["filename"],
            sample_file["content"],
            sample_file["content_type"]
        )}
    )
    return response.json()
```

### 3. 明確なアサーション

```python
def test_file_upload_response(client):
    """ファイルアップロードのレスポンス検証"""
    file_content = b"test content"
    filename = "test.txt"

    response = client.post(
        "/api/sample-files/upload",
        files={"file": (filename, file_content, "text/plain")}
    )

    # ステータスコード
    assert response.status_code == 200, "ファイルアップロードが失敗"

    data = response.json()

    # 各フィールドの検証
    assert "file_id" in data, "file_idが含まれていない"
    assert data["filename"] == filename, f"ファイル名が一致しない: {data['filename']}"
    assert data["size"] == len(file_content), f"サイズが一致しない: {data['size']}"
```

## 参考リンク

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [TestClient Documentation](https://fastapi.tiangolo.com/reference/testclient/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [HTTPX AsyncClient](https://www.python-httpx.org/async/)
- [API Testing Best Practices](https://testdriven.io/blog/fastapi-crud/)

## 次のステップ

- [データベーステスト](./04-database-testing.md) - データベース層のテスト
- [モックとフィクスチャ](./05-mocks-fixtures.md) - 高度なモックとフィクスチャの使用
- [ベストプラクティス](./06-best-practices.md) - より良いテストを書くために
