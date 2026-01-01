"""ルートエンドポイントのテスト。

対象: src/app/api/routes/system/root.py
"""

import pytest
from httpx import AsyncClient


class TestRootEndpoint:
    """ルートエンドポイント(/)のテスト。"""

    @pytest.mark.asyncio
    async def test_root_returns_200(self, client: AsyncClient):
        """[test_root-001] ルートエンドポイントが200を返すこと。"""
        # Act
        response = await client.get("/")

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_root_endpoint_returns_valid_structure(self, client: AsyncClient):
        """[test_root-002] レスポンスが期待される構造を持つこと。"""
        # Act
        response = await client.get("/")
        data = response.json()

        # Assert
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert data["docs"] == "/docs"


class TestOpenAPISchema:
    """OpenAPIスキーマのテスト。"""

    @pytest.mark.asyncio
    async def test_openapi_schema_returns_200(self, client: AsyncClient):
        """[test_root-003] OpenAPIスキーマが取得できること。"""
        # Act
        response = await client.get("/openapi.json")

        # Assert
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
