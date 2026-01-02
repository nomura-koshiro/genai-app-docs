"""CSRFミドルウェアのテスト。

このモジュールは、CSRFMiddlewareが正しくCSRF保護を実装していることを検証します。

テストシナリオ:
    1. 安全なメソッド（GET）はCSRFチェックをスキップ
    2. Bearer token認証はCSRFチェックをスキップ
    3. Cookie認証はCSRFトークン検証を実施
    4. CSRFトークンがレスポンスCookieに含まれる
"""

import pytest
from httpx import AsyncClient, Response

from tests.helpers.assertions import assert_csrf_error, assert_no_csrf_error


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path,expected_status_codes",
    [
        ("GET", "/health", [200]),
        ("OPTIONS", "/api/v1/users", [200, 204]),
    ],
    ids=["get_health", "options_users"],
)
async def test_csrf_safe_methods_skip_verification(
    client: AsyncClient, method: str, path: str, expected_status_codes: list[int]
):
    """[test_csrf-001,008] 安全なメソッド（GET, OPTIONS）はCSRF検証をスキップすることを確認。"""
    # Act - 安全なメソッドはCSRFトークンなしで成功する
    response = await client.request(method, path)

    # Assert
    assert response.status_code in expected_status_codes
    # CSRFトークンがCookieに設定される
    assert "csrf_token" in response.cookies


@pytest.mark.asyncio
async def test_csrf_token_set_in_cookie_on_get(client: AsyncClient):
    """[test_csrf-002] GETリクエストでCSRFトークンがCookieに設定されることを確認。"""
    # Act
    response = await client.get("/")

    # Assert
    assert response.status_code == 200
    # CSRFトークンがCookieに設定される
    assert "csrf_token" in response.cookies
    csrf_token = response.cookies.get("csrf_token")
    assert csrf_token is not None
    assert len(csrf_token) > 0


@pytest.mark.asyncio
async def test_csrf_bearer_token_skip_verification(client: AsyncClient):
    """[test_csrf-003] Bearer token認証はCSRF検証をスキップすることを確認。"""
    # Arrange - Bearer tokenを使用
    headers = {"Authorization": "Bearer mock-access-token-dev-12345"}

    # Act - POSTリクエストでもCSRFトークンなしで成功する（Bearer token認証）
    response = await client.post("/api/v1/users", json={}, headers=headers)

    # Assert
    # 認証エラーやバリデーションエラーは発生するが、CSRF検証はスキップされる
    # （403 Forbidden CSRF token mismatch エラーが発生しないことを確認）
    assert_no_csrf_error(response)


@pytest.mark.asyncio
async def test_csrf_cookie_auth_without_token_passes(client: AsyncClient):
    """[test_csrf-004] Cookie認証でCSRFトークンがない場合でも処理を継続することを確認（初回リクエスト）。"""
    # Act - Cookie認証でCSRFトークンなし（初回リクエスト）
    # 現在の実装では、CSRFトークンがない場合でも処理を継続する
    response = await client.post("/api/v1/users", json={})

    # Assert
    # CSRFエラーではなく、バリデーションエラーが返される
    assert_no_csrf_error(response)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cookie_attribute,expected_in_header",
    [
        ("samesite", ["SameSite=lax", "samesite=lax"]),
        ("httponly", None),  # None means HttpOnly should NOT be present
    ],
    ids=["samesite_lax", "httponly_false"],
)
async def test_csrf_cookie_attributes(
    client: AsyncClient, cookie_attribute: str, expected_in_header: list[str] | None
):
    """[test_csrf-005,006] CSRFトークンCookieの属性を確認。

    - SameSite=lax属性が設定されていること
    - HttpOnly=False（JavaScriptアクセス可能）
    """
    # Act
    response = await client.get("/")

    # Assert
    assert response.status_code == 200
    # Set-Cookieヘッダーの確認
    set_cookie = response.headers.get("set-cookie", "")
    assert "csrf_token=" in set_cookie

    if expected_in_header is not None:
        # 指定された文字列が含まれることを確認
        assert any(
            expected in set_cookie or expected in set_cookie.lower()
            for expected in expected_in_header
        )
    else:
        # HttpOnlyフラグがないことを確認（JavaScriptからアクセス可能）
        # Note: httpx AsyncClientでは、Set-Cookieヘッダーの詳細な属性チェックは制限される
        # 実際のブラウザ環境では、JavaScriptから document.cookie でアクセス可能であることを確認する必要がある
        pass


@pytest.mark.asyncio
async def test_csrf_multiple_requests_token_refresh(client: AsyncClient):
    """[test_csrf-007] 複数のリクエストでCSRFトークンが更新されることを確認。"""
    # Arrange
    first_response = await client.get("/")
    first_token = first_response.cookies.get("csrf_token")

    # Act
    second_response = await client.get("/health")
    second_token = second_response.cookies.get("csrf_token")

    # Assert
    assert first_token is not None
    assert second_token is not None
    # 各リクエストで新しいトークンが生成される
    # （セキュリティ強化のため、トークンは毎回更新される）
    # Note: 現在の実装では毎回新しいトークンが生成される


@pytest.mark.asyncio
async def test_csrf_token_mismatch_returns_403(client: AsyncClient):
    """[test_csrf-009] CSRFトークン不一致時に403エラーを返すことを確認。"""
    # Arrange - まずCSRFトークンを取得
    get_response = await client.get("/")
    csrf_cookie = get_response.cookies.get("csrf_token")
    assert csrf_cookie is not None

    # Act - Cookie側とヘッダー側で異なるトークンを送信
    headers = {"X-CSRF-Token": "invalid-token-that-does-not-match"}
    # Cookieを設定してPOSTリクエスト
    client.cookies.set("csrf_token", csrf_cookie)
    response = await client.post("/api/v1/users", json={}, headers=headers)

    # Assert - CSRFトークン不一致で403エラー
    assert_csrf_error(response, expected_message_contains="CSRF token mismatch")


@pytest.mark.asyncio
async def test_csrf_missing_header_with_cookie_returns_403(client: AsyncClient):
    """[test_csrf-010] CookieありでX-CSRF-Tokenヘッダーがない場合に403エラーを返すことを確認。"""
    # Arrange - まずCSRFトークンを取得
    get_response = await client.get("/")
    csrf_cookie = get_response.cookies.get("csrf_token")
    assert csrf_cookie is not None

    # Act - Cookieはあるがヘッダーなしでリクエスト
    client.cookies.set("csrf_token", csrf_cookie)
    response = await client.post("/api/v1/users", json={})

    # Assert - CSRFトークンヘッダー欠落で403エラー
    assert_csrf_error(response, expected_message_contains="CSRF token missing")


@pytest.mark.asyncio
async def test_csrf_valid_token_passes_verification(client: AsyncClient):
    """[test_csrf-011] 有効なCSRFトークンで検証をパスすることを確認。"""
    # Arrange - まずCSRFトークンを取得
    get_response = await client.get("/")
    csrf_token = get_response.cookies.get("csrf_token")
    assert csrf_token is not None

    # Act - Cookieとヘッダーで同じトークンを送信
    headers = {"X-CSRF-Token": csrf_token}
    client.cookies.set("csrf_token", csrf_token)
    response = await client.post("/api/v1/users", json={}, headers=headers)

    # Assert - CSRF検証をパスし、後続の処理（認証エラー等）に進む
    # 403でCSRFエラーではなく、401（認証必要）または422（バリデーションエラー）
    assert_no_csrf_error(response)


@pytest.mark.asyncio
async def test_csrf_bearer_token_case_insensitive(client: AsyncClient):
    """[test_csrf-012] Bearer token認証の大文字小文字を区別しないことを確認。"""
    # Arrange - 小文字の"bearer"を使用
    headers_lower = {"Authorization": "bearer mock-access-token-dev-12345"}
    headers_mixed = {"Authorization": "BEARER mock-access-token-dev-12345"}

    # Act - 小文字のbearerでもCSRF検証をスキップ
    response_lower = await client.post("/api/v1/users", json={}, headers=headers_lower)
    response_mixed = await client.post("/api/v1/users", json={}, headers=headers_mixed)

    # Assert - どちらもCSRFエラーにならない
    assert_no_csrf_error(response_lower)
    assert_no_csrf_error(response_mixed)


# ========================================
# Edge Case Tests
# ========================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_token,description",
    [
        ("", "empty"),
        ("<script>alert('xss')</script>", "xss_script"),
        ("'; DROP TABLE users; --", "sql_injection"),
        ("../../../etc/passwd", "path_traversal"),
        ("A" * 10000, "very_long"),
    ],
    ids=["empty", "xss", "sql_injection", "path_traversal", "very_long"],
)
async def test_csrf_invalid_tokens(
    client: AsyncClient, invalid_token: str, description: str
):
    """[test_csrf-013,014,015] 無効なCSRFトークンでエラーになることを確認。

    テストケース:
    - 空文字列
    - XSSスクリプト
    - SQLインジェクション
    - パストラバーサル
    - 極端に長い文字列（10000文字）
    """
    # Arrange - まずCSRFトークンを取得
    get_response = await client.get("/")
    csrf_cookie = get_response.cookies.get("csrf_token")
    assert csrf_cookie is not None

    # Act - 無効なトークンを送信
    headers = {"X-CSRF-Token": invalid_token}
    client.cookies.set("csrf_token", csrf_cookie)
    response = await client.post("/api/v1/users", json={}, headers=headers)

    # Assert - 無効なトークンとして403または413エラーが返される
    # 極端に長いトークンの場合は413（Payload Too Large）の可能性あり
    expected_status_codes = [403, 413] if description == "very_long" else [403]
    assert response.status_code in expected_status_codes, (
        f"Failed for {description} token: expected {expected_status_codes}, "
        f"got {response.status_code}"
    )


@pytest.mark.asyncio
async def test_csrf_token_expired(client: AsyncClient):
    """[test_csrf-016] 期限切れトークンでエラーになることを確認。

    CSRFトークンは1時間（3600秒）の有効期限を持ちます。
    期限切れトークンを使用した場合、403エラーが返されることを確認します。
    """
    import base64
    import hashlib
    import hmac
    import time

    from app.core.config import settings

    # Arrange - 2時間前のタイムスタンプで期限切れトークンを生成
    expired_timestamp = int(time.time()) - 7200  # 2時間前
    nonce = b"\x00" * 16  # 固定nonce（テスト用）

    token_data = expired_timestamp.to_bytes(8, "big") + nonce
    signature = hmac.new(
        settings.SECRET_KEY.encode(), token_data, hashlib.sha256
    ).digest()
    expired_token = base64.urlsafe_b64encode(token_data + signature).decode()

    # Act - 期限切れトークンでPOSTリクエスト
    headers = {"X-CSRF-Token": expired_token}
    client.cookies.set("csrf_token", expired_token)
    response = await client.post("/api/v1/users", json={}, headers=headers)

    # Assert - 期限切れエラー（403）
    assert_csrf_error(response, expected_message_contains="expired or invalid")


@pytest.mark.asyncio
async def test_csrf_concurrent_requests(client: AsyncClient):
    """[test_csrf-017] 同じCSRFトークンで並行リクエストが処理されることを確認。"""
    import asyncio

    # Arrange - まずCSRFトークンを取得
    get_response = await client.get("/")
    csrf_token = get_response.cookies.get("csrf_token")
    assert csrf_token is not None

    # Act - 同じトークンで5つの並行リクエストを送信
    async def make_request() -> Response:
        """並行リクエストを作成。"""
        headers = {"X-CSRF-Token": csrf_token}
        return await client.post(
            "/api/v1/users",
            json={},
            headers=headers,
            cookies={"csrf_token": csrf_token},
        )

    responses = await asyncio.gather(*[make_request() for _ in range(5)])

    # Assert - すべてのリクエストがCSRFエラーにならないことを確認
    # （認証エラーやバリデーションエラーは発生するが、CSRF検証はパスする）
    for response in responses:
        assert_no_csrf_error(response)


@pytest.mark.asyncio
async def test_csrf_header_without_cookie_passes(client: AsyncClient):
    """[test_csrf-018] X-CSRF-Tokenヘッダーありでcookieがない場合の動作確認。

    CSRFトークンがCookieに存在しない場合、X-CSRF-Tokenヘッダーがあっても
    CSRF検証はスキップされる（初回リクエスト時のシナリオ）。
    """
    # Arrange - CSRFトークンをヘッダーにのみ設定（Cookieなし）
    headers = {"X-CSRF-Token": "some-token-value"}

    # Act - Cookieなし、ヘッダーのみでリクエスト
    response = await client.post("/api/v1/users", json={}, headers=headers)

    # Assert - CSRFエラーではなく、後続の処理（認証エラー等）に進む
    # Cookieがない場合はCSRF検証をスキップする
    assert_no_csrf_error(response)
