"""ルートエンドポイントのテスト。

対象: src/app/api/routes/system/root.py
"""

import pytest
from httpx import AsyncClient


class TestRootEndpoint:
    """ルートエンドポイント(/)のテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "check_structure",
        [True, False],
        ids=["with_structure_validation", "status_only"],
    )
    async def test_root_endpoint(self, client: AsyncClient, check_structure):
        """[test_root-001-002] ルートエンドポイントのテストケース。"""
        # Act
        response = await client.get("/")

        # Assert
        assert response.status_code == 200

        if check_structure:
            data = response.json()
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
