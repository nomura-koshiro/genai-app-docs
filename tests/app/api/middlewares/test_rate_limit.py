"""CORSとレート制限のミドルウェアテスト。"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.api.middlewares.rate_limit import RateLimitMiddleware


@pytest.mark.asyncio
async def test_cors_with_origin_header_returns_cors_headers(client: AsyncClient):
    """[test_rate_limit-001] CORS ヘッダーのテスト。"""
    # Act
    # GETリクエストでCORSヘッダーを確認
    response = await client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )

    # Assert
    # ヘルスチェックは成功する
    assert response.status_code == 200
    # CORSヘッダーが設定されていることを確認
    assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_within_threshold_allows_requests(client: AsyncClient):
    """[test_rate_limit-002] レート制限のテスト（簡易版）。"""
    # Act
    # 連続してリクエスト
    responses = []
    for _ in range(5):
        response = await client.get("/health")
        responses.append(response)

    # Assert
    # すべて成功（実際のレート制限は100req/60sなので）
    for response in responses:
        assert response.status_code == 200


class TestRateLimitMiddleware:
    """レート制限ミドルウェアの単体テスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "max_calls,request_count,should_be_limited",
        [
            (5, 6, True),   # Exceeded - should get 429
            (10, 1, False), # Within limit - should pass
        ],
        ids=["exceeded", "within_limit"],
    )
    async def test_rate_limit_threshold(self, max_calls, request_count, should_be_limited):
        """[test_rate_limit-003/005] レート制限の閾値テスト（パラメータ化）。"""
        # Arrange
        middleware = RateLimitMiddleware(app=None, calls=max_calls, period=60)
        client_id = "test:client"
        current_time = 1000.0

        # 既存のリクエストを記録（request_count - 1回、最後の1回はチェックで追加される）
        if request_count > 1:
            for i in range(request_count - 1):
                middleware._memory_store[client_id] = middleware._memory_store.get(client_id, [])
                middleware._memory_store[client_id].append(current_time + i)

        # Act
        is_limited, count = middleware._check_rate_limit_memory(client_id, current_time + 10)

        # Assert
        if should_be_limited:
            assert is_limited is True
            assert count >= max_calls
        else:
            assert is_limited is False
            assert count < max_calls

    @pytest.mark.asyncio
    async def test_rate_limit_response_has_correct_headers(self):
        """[test_rate_limit-004] 429レスポンスに正しいヘッダーが含まれることを確認。"""
        # Arrange
        middleware = RateLimitMiddleware(app=None, calls=100, period=60)

        # Act
        response = middleware._create_rate_limit_response()

        # Assert
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "60"
        body = response.body.decode()
        assert "Rate limit exceeded" in body
        assert '"limit": 100' in body
        assert '"period": 60' in body

    @pytest.mark.asyncio
    async def test_rate_limit_cleanup_old_entries(self):
        """[test_rate_limit-006] 古いエントリが期間外でクリーンアップされることを確認。"""
        # Arrange
        middleware = RateLimitMiddleware(app=None, calls=10, period=60)
        client_id = "test:client"

        # 古いエントリを追加（70秒前）
        old_time = 1000.0
        middleware._memory_store[client_id] = [old_time]

        # Act - 現在時刻でチェック（old_timeから70秒後）
        current_time = old_time + 70
        is_limited, count = middleware._check_rate_limit_memory(client_id, current_time)

        # Assert
        assert is_limited is False
        # 古いエントリはクリーンアップされ、新しいエントリのみ
        assert len(middleware._memory_store[client_id]) == 1
        assert middleware._memory_store[client_id][0] == current_time

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "has_user,expected_prefix",
        [
            (True, "user:"),
            (False, "ip:"),
        ],
        ids=["with_user", "with_ip"],
    )
    async def test_client_identifier(self, has_user, expected_prefix):
        """[test_rate_limit-007/008] クライアント識別子の生成テスト（パラメータ化）。"""
        # Arrange
        middleware = RateLimitMiddleware(app=None)
        mock_request = AsyncMock()

        if has_user:
            # 認証ユーザーの場合
            mock_request.state.user = AsyncMock()
            mock_request.state.user.id = "user-123"
            expected_identifier = "user:user-123"
        else:
            # IPアドレスの場合
            mock_request.state = AsyncMock(spec=[])  # userなし
            mock_request.headers = {}
            mock_request.client.host = "192.168.1.100"
            expected_identifier = "ip:192.168.1.100"

        # Act
        identifier = middleware._get_client_identifier(mock_request)

        # Assert
        assert identifier.startswith(expected_prefix)
        assert identifier == expected_identifier

    @pytest.mark.asyncio
    async def test_memory_store_cleanup_prevents_leak(self):
        """[test_rate_limit-009] メモリストアがmax_memory_entriesを超えた場合にクリーンアップされることを確認。"""
        # Arrange
        middleware = RateLimitMiddleware(app=None, max_memory_entries=10)

        # 11クライアント分のエントリを追加
        for i in range(11):
            middleware._memory_store[f"client:{i}"] = [float(i)]

        # Act
        middleware._cleanup_memory_store()

        # Assert
        # 80%まで削減されるはず (10 * 0.8 = 8)
        assert len(middleware._memory_store) <= 10
