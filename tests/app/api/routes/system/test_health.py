"""ヘルスチェックエンドポイントのテスト。

対象: src/app/api/routes/system/health.py
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """ヘルスチェックエンドポイント(/health)のテスト。"""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client: AsyncClient):
        """[test_health-001] ヘルスチェックエンドポイントが200を返すこと。"""
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_with_db_connection_returns_valid_structure(self, client: AsyncClient, db_session):
        """[test_health-002] レスポンスが期待される構造を持つこと。"""
        # Arrange
        # get_dbをモックしてテスト用セッションを返す
        async def mock_get_db():
            yield db_session

        # Act
        with patch("app.api.routes.system.health.get_db", mock_get_db):
            response = await client.get("/health")
            data = response.json()

            # Assert
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data
            assert "environment" in data
