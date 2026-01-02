"""セキュリティヘッダーミドルウェアのテスト。

このモジュールは、SecurityHeadersMiddlewareが正しくセキュリティヘッダーを
追加することを検証します。
"""

import pytest
from httpx import AsyncClient


# 期待されるセキュリティヘッダーと値
EXPECTED_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint,method",
    [
        ("/", "GET"),
        ("/health", "GET"),
    ],
    ids=["root", "health"],
)
async def test_security_headers_included(client: AsyncClient, endpoint: str, method: str):
    """[test_security_headers-001] 各エンドポイントにセキュリティヘッダーが追加されることを確認。"""
    # Act
    response = await client.request(method, endpoint)

    # Assert
    for header_name, expected_value in EXPECTED_SECURITY_HEADERS.items():
        assert header_name in response.headers, f"{header_name} が存在しない"
        assert response.headers[header_name] == expected_value


@pytest.mark.asyncio
async def test_hsts_header_production_mode_includes_header(client: AsyncClient):
    """[test_security_headers-003] HSTSヘッダーが追加されることを確認（本番環境のみ）。"""
    # Arrange
    from app.core.config import settings

    # Act
    response = await client.get("/")

    # Assert
    if settings.DEBUG:
        # 開発/テスト環境: HSTSヘッダーなし
        assert "Strict-Transport-Security" not in response.headers
    else:
        # 本番環境: HSTSヘッダーあり
        assert "Strict-Transport-Security" in response.headers
        hsts_value = response.headers["Strict-Transport-Security"]
        assert "max-age=" in hsts_value


@pytest.mark.asyncio
async def test_security_headers_api_endpoint_include_headers(client: AsyncClient):
    """[test_security_headers-004] APIエンドポイントにもセキュリティヘッダーが追加されることを確認。"""
    # Act
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
        },
    )

    # Assert
    for header_name in EXPECTED_SECURITY_HEADERS:
        assert header_name in response.headers
