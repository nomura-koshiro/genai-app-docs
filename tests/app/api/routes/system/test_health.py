"""システムエンドポイントのテスト。"""

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
