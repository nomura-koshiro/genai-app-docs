"""操作履歴記録ミドルウェアのテスト。

ActivityTrackingMiddlewareが正しく操作履歴を記録することを検証します。
"""

from unittest.mock import MagicMock

import pytest


class TestActivityTrackingMiddleware:
    """操作履歴記録ミドルウェアのユニットテスト。"""

    def test_should_skip_health_endpoint(self):
        """[test_activity_tracking-001] ヘルスチェックエンドポイントは除外されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._should_skip("/health") is True
        assert middleware._should_skip("/healthz") is True
        assert middleware._should_skip("/ready") is True
        assert middleware._should_skip("/docs") is True
        assert middleware._should_skip("/openapi.json") is True

    def test_should_not_skip_api_endpoint(self):
        """[test_activity_tracking-002] APIエンドポイントは記録されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._should_skip("/api/v1/projects") is False
        assert middleware._should_skip("/api/v1/admin/settings") is False
        assert middleware._should_skip("/api/v1/user_accounts") is False

    def test_should_skip_static_patterns(self):
        """[test_activity_tracking-003] 静的リソースパターンは除外されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._should_skip("/static/css/style.css") is True
        assert middleware._should_skip("/assets/images/logo.png") is True
        assert middleware._should_skip("/_next/static/chunks/main.js") is True

    def test_mask_sensitive_data_password(self):
        """[test_activity_tracking-004] パスワードがマスクされること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        data = {
            "email": "test@example.com",
            "password": "secret123",
            "username": "testuser",
        }

        # Act
        masked = middleware._mask_sensitive_data(data)

        # Assert
        assert masked["email"] == "test@example.com"
        assert masked["password"] == "***MASKED***"
        assert masked["username"] == "testuser"

    def test_mask_sensitive_data_tokens(self):
        """[test_activity_tracking-005] トークン類がマスクされること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "refresh_abc123",
            "api_key": "sk-1234567890",
            "name": "Test User",
        }

        # Act
        masked = middleware._mask_sensitive_data(data)

        # Assert
        assert masked["access_token"] == "***MASKED***"
        assert masked["refresh_token"] == "***MASKED***"
        assert masked["api_key"] == "***MASKED***"
        assert masked["name"] == "Test User"

    def test_mask_sensitive_data_nested(self):
        """[test_activity_tracking-006] ネストされた機密情報もマスクされること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        data = {
            "user": {
                "email": "test@example.com",
                "credentials": {
                    "password": "secret123",
                    "token": "jwt_token",
                },
            },
        }

        # Act
        masked = middleware._mask_sensitive_data(data)

        # Assert
        assert masked["user"]["email"] == "test@example.com"
        assert masked["user"]["credentials"]["password"] == "***MASKED***"
        assert masked["user"]["credentials"]["token"] == "***MASKED***"

    def test_mask_sensitive_data_list(self):
        """[test_activity_tracking-007] リスト内の機密情報もマスクされること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        data = [
            {"password": "secret1", "name": "User1"},
            {"password": "secret2", "name": "User2"},
        ]

        # Act
        masked = middleware._mask_sensitive_data(data)

        # Assert
        assert masked[0]["password"] == "***MASKED***"
        assert masked[0]["name"] == "User1"
        assert masked[1]["password"] == "***MASKED***"
        assert masked[1]["name"] == "User2"

    def test_mask_sensitive_data_deep_nested(self):
        """[test_activity_tracking-008] 深くネストされたデータは打ち切られること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # 15レベルのネストを作成
        data: dict = {"level": 0}
        current = data
        for i in range(15):
            current["nested"] = {"level": i + 1}
            current = current["nested"]

        # Act
        masked = middleware._mask_sensitive_data(data)

        # Assert
        # 10レベル以上は打ち切られる
        assert "***NESTED***" in str(masked)

    def test_extract_resource_info_project(self):
        """[test_activity_tracking-009] プロジェクトリソース情報が抽出されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act
        resource_type, resource_id = middleware._extract_resource_info("/api/v1/projects/550e8400-e29b-41d4-a716-446655440000")

        # Assert
        assert resource_type == "PROJECT"
        assert str(resource_id) == "550e8400-e29b-41d4-a716-446655440000"

    def test_extract_resource_info_user(self):
        """[test_activity_tracking-010] ユーザーリソース情報が抽出されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act
        resource_type, resource_id = middleware._extract_resource_info("/api/v1/user_accounts/12345678-1234-1234-1234-123456789012")

        # Assert
        assert resource_type == "USER"
        assert str(resource_id) == "12345678-1234-1234-1234-123456789012"

    def test_extract_resource_info_no_match(self):
        """[test_activity_tracking-011] パターンに一致しないパスではNoneが返ること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act
        resource_type, resource_id = middleware._extract_resource_info("/api/v1/unknown/path")

        # Assert
        assert resource_type is None
        assert resource_id is None

    def test_infer_action_type_get(self):
        """[test_activity_tracking-012] GETリクエストはREADと推定されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._infer_action_type("GET", 200) == "READ"

    def test_infer_action_type_post(self):
        """[test_activity_tracking-013] POSTリクエストはCREATEと推定されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._infer_action_type("POST", 201) == "CREATE"

    def test_infer_action_type_patch(self):
        """[test_activity_tracking-014] PATCHリクエストはUPDATEと推定されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._infer_action_type("PATCH", 200) == "UPDATE"
        assert middleware._infer_action_type("PUT", 200) == "UPDATE"

    def test_infer_action_type_delete(self):
        """[test_activity_tracking-015] DELETEリクエストはDELETEと推定されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._infer_action_type("DELETE", 204) == "DELETE"

    def test_infer_action_type_error(self):
        """[test_activity_tracking-016] 4xx/5xxエラーはERRORと推定されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._infer_action_type("GET", 404) == "ERROR"
        assert middleware._infer_action_type("POST", 400) == "ERROR"
        assert middleware._infer_action_type("GET", 500) == "ERROR"


@pytest.mark.asyncio
async def test_activity_tracking_header_added(client):
    """[test_activity_tracking-017] リクエストが正常に処理されること。"""
    # Act
    response = await client.get("/health")

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_activity_tracking_on_api_endpoint(client):
    """[test_activity_tracking-018] APIエンドポイントでも正常に動作すること。"""
    # Act
    response = await client.get("/")

    # Assert
    assert response.status_code == 200
