"""セッションAPIのテスト。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_sessions_endpoint(client: AsyncClient):
    """セッション一覧取得エンドポイントのテスト。"""
    # Act
    response = await client.get("/api/v1/sample-sessions")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "total" in data
    assert isinstance(data["sessions"], list)


@pytest.mark.asyncio
async def test_list_sessions_with_pagination(client: AsyncClient):
    """ページネーション付きセッション一覧取得のテスト。"""
    # Act
    response = await client.get("/api/v1/sample-sessions?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) <= 10


@pytest.mark.asyncio
async def test_list_sessions_invalid_pagination(client: AsyncClient):
    """不正なページネーションパラメータのテスト。"""
    # Act - limitが大きすぎる
    response = await client.get("/api/v1/sample-sessions?limit=10000")

    # Assert - バリデーションエラー
    assert response.status_code == 422
