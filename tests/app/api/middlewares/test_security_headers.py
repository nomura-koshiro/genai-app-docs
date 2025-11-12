"""セキュリティヘッダーミドルウェアのテスト。

このモジュールは、SecurityHeadersMiddlewareが正しくセキュリティヘッダーを
追加することを検証します。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_headers_on_root(client: AsyncClient):
    """ルートエンドポイントにセキュリティヘッダーが追加されることを確認。"""
    response = await client.get("/")

    # 基本的なセキュリティヘッダーの存在を確認
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

    assert "X-XSS-Protection" in response.headers
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


@pytest.mark.asyncio
async def test_security_headers_on_health(client: AsyncClient):
    """ヘルスチェックエンドポイントにセキュリティヘッダーが追加されることを確認。"""
    response = await client.get("/health")

    # すべてのエンドポイントにセキュリティヘッダーが追加される
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


@pytest.mark.asyncio
async def test_hsts_header_present(client: AsyncClient):
    """HSTSヘッダーが追加されることを確認（本番環境のみ）。"""
    response = await client.get("/")

    # 開発環境ではHSTSヘッダーは追加されない（DEBUG=Trueのため）
    # 本番環境（DEBUG=False）でのみHSTSヘッダーが追加される
    # テスト環境ではDEBUG=Trueなので、HSTSヘッダーがないことを確認
    from app.core.config import settings

    if settings.DEBUG:
        # 開発/テスト環境: HSTSヘッダーなし
        assert "Strict-Transport-Security" not in response.headers
    else:
        # 本番環境: HSTSヘッダーあり
        assert "Strict-Transport-Security" in response.headers
        hsts_value = response.headers["Strict-Transport-Security"]
        assert "max-age=" in hsts_value


@pytest.mark.asyncio
async def test_security_headers_on_api_endpoints(client: AsyncClient):
    """APIエンドポイントにもセキュリティヘッダーが追加されることを確認。"""
    # ユーザー作成エンドポイントにPOST
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
        },
    )

    # セキュリティヘッダーの存在を確認
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
