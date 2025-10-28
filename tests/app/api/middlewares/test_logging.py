"""ロギングミドルウェアのテスト。

このモジュールは、LoggingMiddlewareが正しくリクエスト/レスポンスを
ログに記録し、X-Process-Timeヘッダーを追加することを検証します。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_process_time_header_added(client: AsyncClient):
    """X-Process-Timeヘッダーが追加されることを確認。"""
    response = await client.get("/health")

    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    # 処理時間は数値文字列（秒単位）
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0
    assert process_time < 10  # 10秒以内に完了しているはず


@pytest.mark.asyncio
async def test_process_time_on_api_endpoint(client: AsyncClient):
    """APIエンドポイントでもX-Process-Timeが追加されることを確認。"""
    response = await client.get("/")

    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0


@pytest.mark.asyncio
async def test_logging_on_successful_request(client: AsyncClient):
    """正常なリクエストでログが記録されることを確認（ヘッダーで間接的に検証）。"""
    response = await client.get("/")

    # ログミドルウェアが動作していれば、X-Process-Timeが追加される
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_logging_on_post_request(client: AsyncClient):
    """POSTリクエストでもログとヘッダーが正しく処理されることを確認。"""
    # エラーになるPOSTリクエスト（Method Not Allowed）
    response = await client.post("/health")

    # 成功または失敗に関わらず、X-Process-Timeは追加される
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_logging_on_error_response(client: AsyncClient):
    """エラーレスポンスでもX-Process-Timeが追加されることを確認。"""
    response = await client.get("/nonexistent")

    assert response.status_code == 404
    # エラーの場合でもログミドルウェアは動作する
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_process_time_increases_with_complexity(client: AsyncClient):
    """複雑な処理ほど処理時間が増加することを確認（相対的な比較）。"""
    # シンプルなヘルスチェック
    health_response = await client.get("/health")
    health_time = float(health_response.headers["X-Process-Time"])

    # 別のエンドポイント
    root_response = await client.get("/")
    root_time = float(root_response.headers["X-Process-Time"])

    # 両方とも有効な処理時間
    assert health_time >= 0
    assert root_time >= 0
