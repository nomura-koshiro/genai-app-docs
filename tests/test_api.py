"""APIエンドポイントのテスト。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """ルートエンドポイントのテスト。"""
    # Act
    response = await client.get("/")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """ヘルスチェックエンドポイントのテスト。"""
    # Act
    response = await client.get("/health")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_chat_endpoint_guest(client: AsyncClient):
    """ゲストユーザーでのチャットエンドポイントのテスト。"""
    # Arrange
    chat_request = {
        "message": "Hello, agent!",
        "context": {"source": "test"},
    }

    # Act
    response = await client.post("/api/agents/chat", json=chat_request)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    assert data["session_id"] is not None


@pytest.mark.asyncio
async def test_chat_endpoint_with_session_id(client: AsyncClient):
    """既存セッションIDでのチャットエンドポイントのテスト。"""
    # Arrange - 最初のメッセージでセッションを作成
    first_request = {
        "message": "First message",
        "context": {},
    }
    first_response = await client.post("/api/agents/chat", json=first_request)
    session_id = first_response.json()["session_id"]

    # Act - 同じセッションIDで2つ目のメッセージ
    second_request = {
        "message": "Second message",
        "session_id": session_id,
        "context": {},
    }
    response = await client.post("/api/agents/chat", json=second_request)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id


@pytest.mark.asyncio
async def test_chat_endpoint_validation_error(client: AsyncClient):
    """バリデーションエラーのテスト。"""
    # Arrange - メッセージフィールドが欠けている
    invalid_request = {
        "context": {},
    }

    # Act
    response = await client.post("/api/agents/chat", json=invalid_request)

    # Assert
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_file_upload_endpoint(client: AsyncClient):
    """ファイルアップロードエンドポイントのテスト。"""
    # Arrange
    files = {"file": ("test.txt", b"Test file content", "text/plain")}

    # Act
    response = await client.post("/api/files/upload", files=files)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "filepath" in data
    assert "size" in data
    assert data["filename"] == "test.txt"


@pytest.mark.asyncio
async def test_file_upload_no_file(client: AsyncClient):
    """ファイルなしでのアップロード失敗のテスト。"""
    # Act
    response = await client.post("/api/files/upload")

    # Assert
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_openapi_schema(client: AsyncClient):
    """OpenAPIスキーマの取得テスト。"""
    # Act
    response = await client.get("/openapi.json")

    # Assert
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema


@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient):
    """CORS ヘッダーのテスト。"""
    # Act
    response = await client.options(
        "/api/agents/chat",
        headers={"Origin": "http://localhost:3000"},
    )

    # Assert
    assert response.status_code == 200
    # CORSヘッダーが設定されていることを確認
    assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient):
    """レート制限のテスト（簡易版）。"""
    # Act - 連続してリクエスト
    responses = []
    for _ in range(5):
        response = await client.get("/health")
        responses.append(response)

    # Assert - すべて成功（実際のレート制限は100req/60sなので）
    for response in responses:
        assert response.status_code == 200
