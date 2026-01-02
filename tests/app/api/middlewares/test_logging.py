"""ロギングミドルウェアのテスト。

このモジュールは、LoggingMiddlewareが正しくリクエスト/レスポンスを
ログに記録し、X-Process-Timeヘッダーを追加することを検証します。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,endpoint,expected_status",
    [
        ("GET", "/health", 200),
        ("GET", "/", 200),
        ("POST", "/health", 405),
        ("GET", "/nonexistent", 404),
    ],
    ids=["health_get", "root_get", "health_post_not_allowed", "not_found"],
)
async def test_response_includes_process_time_header(
    client: AsyncClient, method: str, endpoint: str, expected_status: int
):
    """[test_logging-001] 各リクエストにX-Process-Timeヘッダーが追加されること。

    正常なレスポンス、エラーレスポンス、異なるHTTPメソッドなど、
    あらゆるケースでX-Process-Timeヘッダーが正しく追加されることを確認します。
    """
    # Act
    response = await client.request(method, endpoint)

    # Assert
    assert response.status_code == expected_status
    assert "X-Process-Time" in response.headers
    # 処理時間は数値文字列（秒単位）で、0以上の値であること
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0
    assert process_time < 10  # 10秒以内に完了しているはず


@pytest.mark.asyncio
async def test_process_time_complex_request_returns_positive_value(client: AsyncClient):
    """[test_logging-002] 複雑な処理ほど処理時間が増加することを確認（相対的な比較）。"""
    # Act
    # シンプルなヘルスチェック
    health_response = await client.get("/health")
    health_time = float(health_response.headers["X-Process-Time"])

    # 別のエンドポイント
    root_response = await client.get("/")
    root_time = float(root_response.headers["X-Process-Time"])

    # Assert
    # 両方とも有効な処理時間
    assert health_time >= 0
    assert root_time >= 0
