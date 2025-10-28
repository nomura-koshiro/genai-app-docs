"""エージェントAPIのテスト。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_endpoint_guest(client: AsyncClient):
    """ゲストユーザーでのチャットエンドポイントのテスト。"""
    # Arrange
    chat_request = {
        "message": "Hello, agent!",
        "context": {"source": "test"},
    }

    # Act
    response = await client.post("/api/v1/agents/chat", json=chat_request)

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
    first_response = await client.post("/api/v1/agents/chat", json=first_request)
    session_id = first_response.json()["session_id"]

    # Act - 同じセッションIDで2つ目のメッセージ
    second_request = {
        "message": "Second message",
        "session_id": session_id,
        "context": {},
    }
    response = await client.post("/api/v1/agents/chat", json=second_request)

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
    response = await client.post("/api/v1/agents/chat", json=invalid_request)

    # Assert
    assert response.status_code == 422  # Validation error
