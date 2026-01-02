"""メトリクスエンドポイントのテスト。

対象: src/app/api/routes/system/metrics.py
"""

import pytest
from httpx import AsyncClient


class TestMetricsEndpoint:
    """メトリクスエンドポイント(/metrics)のテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "check_type",
        ["prometheus_format", "no_auth_required"],
        ids=["prometheus_format", "no_auth_required"],
    )
    async def test_metrics_endpoint(self, client: AsyncClient, check_type):
        """[test_metrics-001-002] メトリクスエンドポイントのテストケース。"""
        # Act
        response = await client.get("/metrics")

        # Assert
        assert response.status_code == 200
        if check_type == "prometheus_format":
            assert "text/plain" in response.headers["content-type"]
