"""メトリクスエンドポイントのテスト。

対象: src/app/api/routes/system/metrics.py
"""

import pytest
from httpx import AsyncClient


class TestMetricsEndpoint:
    """メトリクスエンドポイント(/metrics)のテスト。"""

    @pytest.mark.asyncio
    async def test_metrics_returns_prometheus_format(self, client: AsyncClient):
        """[test_metrics-001] メトリクスがPrometheus形式で返されること。"""
        response = await client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_metrics_no_auth_required(self, client: AsyncClient):
        """[test_metrics-002] メトリクスエンドポイントが認証不要であること。"""
        response = await client.get("/metrics")
        # 401や403ではなく200が返る
        assert response.status_code == 200
