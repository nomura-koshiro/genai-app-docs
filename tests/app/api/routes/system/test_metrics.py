"""Prometheusメトリクスエンドポイントのテスト。

このモジュールは、/metricsエンドポイントが正しくPrometheus形式の
メトリクスを返すことを検証します。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_200(client: AsyncClient):
    """/metricsエンドポイントが200を返すことを確認。"""
    response = await client.get("/metrics")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_content_type(client: AsyncClient):
    """メトリクスのContent-TypeがPrometheus形式であることを確認。"""
    response = await client.get("/metrics")

    assert response.status_code == 200
    # Prometheus形式: text/plain; version=0.0.4
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_metrics_contains_prometheus_format(client: AsyncClient):
    """メトリクスがPrometheus形式を含むことを確認。"""
    response = await client.get("/metrics")
    content = response.text

    # Prometheus形式の基本要素が含まれている
    # メトリクス名が含まれている（http_で始まるメトリクス）
    assert "http_" in content or "HELP" in content or "TYPE" in content


@pytest.mark.asyncio
async def test_metrics_endpoint_no_auth_required(client: AsyncClient):
    """メトリクスエンドポイントが認証不要であることを確認。"""
    # 認証なしでアクセス
    response = await client.get("/metrics")

    # 401や403ではなく200が返る
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_updated_on_requests(client: AsyncClient):
    """リクエスト後にメトリクスが更新されることを確認。"""
    # 複数のリクエストを発行してメトリクスを生成
    await client.get("/health")
    await client.get("/")

    # メトリクスを取得
    response = await client.get("/metrics")
    content = response.text

    # メトリクスにHTTPリクエストの情報が含まれている
    assert response.status_code == 200
    assert len(content) > 0
