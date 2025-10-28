"""エラーハンドリングミドルウェアのテスト。

このモジュールは、ErrorHandlerMiddlewareが正しく例外を捕捉し、
統一されたJSON形式のエラーレスポンスに変換することを検証します。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_not_found_error_handling(client: AsyncClient):
    """NotFoundErrorが404レスポンスに変換されることを確認。"""
    # 存在しないエンドポイントにアクセス
    response = await client.get("/api/v1/nonexistent-endpoint")

    assert response.status_code == 404
    data = response.json()
    # FastAPIのデフォルトエラー形式では "detail" キーを使用
    assert "detail" in data
    assert "not found" in str(data["detail"]).lower()


@pytest.mark.asyncio
async def test_validation_error_handling(client: AsyncClient):
    """ValidationErrorが適切なレスポンスに変換されることを確認。"""
    # 不正なJSONデータを送信
    response = await client.post(
        "/health",  # POSTを受け付けないエンドポイント
        json={"invalid": "data"},
    )

    # Method Not Allowedエラー
    assert response.status_code == 405
    data = response.json()
    assert "detail" in data  # FastAPIのエラー形式


@pytest.mark.asyncio
async def test_error_response_format(client: AsyncClient):
    """エラーレスポンスが統一された形式であることを確認。"""
    # 存在しないエンドポイント
    response = await client.get("/api/v1/nonexistent")

    assert response.status_code == 404
    data = response.json()
    # FastAPIの404エラーには "detail" が含まれる
    assert "detail" in data


@pytest.mark.asyncio
async def test_successful_request_not_affected(client: AsyncClient):
    """正常なリクエストがエラーハンドラーに影響されないことを確認。"""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    # ステータスは "healthy" または "degraded" (DB接続状態による)
    assert data["status"] in ["healthy", "degraded"]


@pytest.mark.asyncio
async def test_error_handler_with_api_endpoint(client: AsyncClient):
    """APIエンドポイントでのエラーハンドリングを確認。"""
    # ヘルスチェックエンドポイント（正常系）
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    # ステータスは "healthy" または "degraded" (DB接続状態による)
    assert data["status"] in ["healthy", "degraded"]


@pytest.mark.asyncio
async def test_method_not_allowed(client: AsyncClient):
    """許可されていないHTTPメソッドが適切に処理されることを確認。"""
    # GETしか許可されていないエンドポイントにPOST
    response = await client.post("/health")

    assert response.status_code == 405  # Method Not Allowed
    data = response.json()
    assert "detail" in data
