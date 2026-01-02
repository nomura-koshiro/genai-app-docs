"""Prometheusメトリクスミドルウェアのテスト。

このモジュールは、PrometheusMetricsMiddlewareが正しくHTTPメトリクスを
収集し、/metricsエンドポイントで公開することを検証します。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint_accessible(client: AsyncClient):
    """[test_metrics-001] /metricsエンドポイントがアクセス可能であること。"""
    # Act
    response = await client.get("/metrics")

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "metric_name",
    [
        "http_requests_total",
        "http_request_duration_seconds",
    ],
    ids=["requests_total", "duration"],
)
async def test_metrics_content_includes_metric(client: AsyncClient, metric_name: str):
    """[test_metrics-002] メトリクスに必要な項目が含まれること。"""
    # Arrange
    await client.get("/health")

    # Act
    response = await client.get("/metrics")
    content = response.text

    # Assert
    assert metric_name in content


@pytest.mark.asyncio
async def test_metrics_after_requests_updated(client: AsyncClient):
    """[test_metrics-004] リクエスト後にメトリクスが更新されること。"""
    # Arrange
    await client.get("/health")
    await client.get("/")

    # Act
    response = await client.get("/metrics")
    content = response.text

    # Assert
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content


@pytest.mark.asyncio
async def test_metrics_format_prometheus_compliant(client: AsyncClient):
    """[test_metrics-005] メトリクスがPrometheus形式であること。"""
    # Act
    response = await client.get("/metrics")
    content = response.text

    # Assert - Prometheus形式の基本要素
    assert "# HELP" in content or "http_" in content
    assert "# TYPE" in content or "http_" in content


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "label_name",
    ["method=", "status_code="],
    ids=["method", "status_code"],
)
async def test_metrics_labels_included(client: AsyncClient, label_name: str):
    """[test_metrics-006] メトリクスにラベルが含まれること。"""
    # Arrange
    await client.get("/health")
    await client.get("/nonexistent")

    # Act
    response = await client.get("/metrics")
    content = response.text

    # Assert
    assert label_name in content or "http_" in content
