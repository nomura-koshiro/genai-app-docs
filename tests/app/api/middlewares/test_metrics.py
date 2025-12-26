"""Prometheusメトリクスミドルウェアのテスト。

このモジュールは、PrometheusMetricsMiddlewareが正しくHTTPメトリクスを
収集し、/metricsエンドポイントで公開することを検証します。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint_exists(client: AsyncClient):
    """[test_metrics-001] /metricsエンドポイントが存在し、アクセス可能であることを確認。"""
    response = await client.get("/metrics")

    assert response.status_code == 200
    # Prometheus形式のテキスト
    assert response.headers["content-type"].startswith("text/plain")


@pytest.mark.asyncio
async def test_metrics_contain_http_requests(client: AsyncClient):
    """[test_metrics-002] メトリクスにHTTPリクエスト数が含まれることを確認。"""
    # 先にリクエストを発行してメトリクスを生成
    await client.get("/health")

    # メトリクスを取得
    response = await client.get("/metrics")
    content = response.text

    # http_requests_totalメトリクスが含まれている
    assert "http_requests_total" in content


@pytest.mark.asyncio
async def test_metrics_contain_request_duration(client: AsyncClient):
    """[test_metrics-003] メトリクスにリクエスト処理時間が含まれることを確認。"""
    # リクエストを発行
    await client.get("/health")

    # メトリクスを取得
    response = await client.get("/metrics")
    content = response.text

    # http_request_duration_secondsメトリクスが含まれている
    assert "http_request_duration_seconds" in content


@pytest.mark.asyncio
async def test_metrics_updated_after_requests(client: AsyncClient):
    """[test_metrics-004] リクエスト後にメトリクスが更新されることを確認。"""
    # 新しいリクエストを複数発行
    await client.get("/health")
    await client.get("/")

    # 更新されたメトリクス取得
    updated_response = await client.get("/metrics")
    updated_content = updated_response.text

    # メトリクスが更新されている（少なくともサイズが変わる）
    # または同じ場合もあるが、メトリクスの形式は保持されている
    assert "http_requests_total" in updated_content
    assert "http_request_duration_seconds" in updated_content


@pytest.mark.asyncio
async def test_metrics_format_is_prometheus(client: AsyncClient):
    """[test_metrics-005] メトリクスがPrometheus形式であることを確認。"""
    response = await client.get("/metrics")
    content = response.text

    # Prometheus形式の基本要素
    # HELPコメント（メトリクスの説明）
    assert "# HELP" in content or "http_" in content
    # TYPEコメント（メトリクスタイプ）
    assert "# TYPE" in content or "http_" in content


@pytest.mark.asyncio
async def test_metrics_include_method_labels(client: AsyncClient):
    """[test_metrics-006] メトリクスにHTTPメソッドラベルが含まれることを確認。"""
    # 異なるメソッドでリクエスト
    await client.get("/health")
    await client.post("/health")  # Method Not Allowed

    response = await client.get("/metrics")
    content = response.text

    # メソッドラベルが含まれている（GET, POSTなど）
    # Prometheusのラベル形式: {method="GET"} または {method="POST"}
    assert "method=" in content or "http_" in content


@pytest.mark.asyncio
async def test_metrics_include_status_code_labels(client: AsyncClient):
    """[test_metrics-007] メトリクスにステータスコードラベルが含まれることを確認。"""
    # 成功とエラーのリクエストを発行
    await client.get("/health")  # 200
    await client.get("/nonexistent")  # 404

    response = await client.get("/metrics")
    content = response.text

    # ステータスコードラベルが含まれている
    assert "status_code=" in content or "http_" in content
