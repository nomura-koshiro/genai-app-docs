"""CORSとレート制限のミドルウェアテスト。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient):
    """[test_rate_limit-001] CORS ヘッダーのテスト。"""
    # GETリクエストでCORSヘッダーを確認
    response = await client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )

    # Assert - ヘルスチェックは成功する
    assert response.status_code == 200
    # CORSヘッダーが設定されていることを確認
    assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient):
    """[test_rate_limit-002] レート制限のテスト（簡易版）。"""
    # Act - 連続してリクエスト
    responses = []
    for _ in range(5):
        response = await client.get("/health")
        responses.append(response)

    # Assert - すべて成功（実際のレート制限は100req/60sなので）
    for response in responses:
        assert response.status_code == 200
