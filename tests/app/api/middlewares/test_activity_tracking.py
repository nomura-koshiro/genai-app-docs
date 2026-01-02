"""操作履歴記録ミドルウェアのテスト。

ActivityTrackingMiddlewareが正しく操作履歴を記録することを検証します。
"""

from unittest.mock import MagicMock

import pytest


class TestActivityTrackingMiddleware:
    """操作履歴記録ミドルウェアのユニットテスト。"""

    @pytest.mark.parametrize(
        "path,should_skip",
        [
            # 除外パス（固定）
            ("/health", True),
            ("/healthz", True),
            ("/ready", True),
            ("/docs", True),
            ("/openapi.json", True),
            # 除外パス（パターン）
            ("/static/css/style.css", True),
            ("/assets/images/logo.png", True),
            ("/_next/static/chunks/main.js", True),
            # 記録対象パス
            ("/api/v1/projects", False),
            ("/api/v1/admin/settings", False),
            ("/api/v1/user_accounts", False),
        ],
        ids=[
            "health", "healthz", "ready", "docs", "openapi",
            "static_css", "assets_img", "next_static",
            "api_projects", "api_admin", "api_users",
        ],
    )
    def test_should_skip_path(self, path: str, should_skip: bool):
        """[test_activity_tracking-001] パスの除外判定が正しいこと。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._should_skip(path) is should_skip

    @pytest.mark.parametrize(
        "method,status_code,expected_action",
        [
            ("GET", 200, "READ"),
            ("POST", 201, "CREATE"),
            ("PUT", 200, "UPDATE"),
            ("PATCH", 200, "UPDATE"),
            ("DELETE", 204, "DELETE"),
            # エラーステータス
            ("GET", 404, "ERROR"),
            ("POST", 400, "ERROR"),
            ("GET", 500, "ERROR"),
        ],
        ids=["get_read", "post_create", "put_update", "patch_update", "delete",
             "error_404", "error_400", "error_500"],
    )
    def test_infer_action_type(self, method: str, status_code: int, expected_action: str):
        """[test_activity_tracking-012] HTTPメソッドとステータスからアクション種別が推定されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._infer_action_type(method, status_code) == expected_action

    @pytest.mark.parametrize(
        "path,expected_type,expected_id",
        [
            ("/api/v1/projects/550e8400-e29b-41d4-a716-446655440000", "PROJECT", "550e8400-e29b-41d4-a716-446655440000"),
            ("/api/v1/user_accounts/12345678-1234-1234-1234-123456789012", "USER", "12345678-1234-1234-1234-123456789012"),
            ("/api/v1/unknown/path", None, None),
        ],
        ids=["project", "user", "unknown"],
    )
    def test_extract_resource_info(self, path: str, expected_type: str | None, expected_id: str | None):
        """[test_activity_tracking-009] パスからリソース情報が抽出されること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act
        resource_type, resource_id = middleware._extract_resource_info(path)

        # Assert
        assert resource_type == expected_type
        if expected_id:
            assert str(resource_id) == expected_id
        else:
            assert resource_id is None


class TestMaskSensitiveData:
    """機密情報マスキングのテスト。"""

    @pytest.mark.parametrize(
        "data,expected_masked_keys",
        [
            # パスワード
            ({"email": "test@example.com", "password": "secret123"}, ["password"]),
            # トークン類
            ({"access_token": "jwt...", "refresh_token": "ref...", "api_key": "sk-..."}, ["access_token", "refresh_token", "api_key"]),
        ],
        ids=["password", "tokens"],
    )
    def test_mask_sensitive_fields(self, data: dict, expected_masked_keys: list[str]):
        """[test_activity_tracking-004] 機密フィールドがマスクされること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())

        # Act
        masked = middleware._mask_sensitive_data(data)

        # Assert
        for key in expected_masked_keys:
            assert masked[key] == "***MASKED***"

    def test_mask_nested_sensitive_data(self):
        """[test_activity_tracking-006] ネストされた機密情報もマスクされること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())
        data = {
            "user": {
                "email": "test@example.com",
                "credentials": {"password": "secret123", "token": "jwt_token"},
            },
        }

        # Act
        masked = middleware._mask_sensitive_data(data)

        # Assert
        assert masked["user"]["email"] == "test@example.com"
        assert masked["user"]["credentials"]["password"] == "***MASKED***"
        assert masked["user"]["credentials"]["token"] == "***MASKED***"

    def test_mask_list_items(self):
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
        for i, item in enumerate(masked):
            assert item["password"] == "***MASKED***"
            assert item["name"] == f"User{i + 1}"

    def test_mask_deep_nested_truncated(self):
        """[test_activity_tracking-008] 深くネストされたデータは打ち切られること。"""
        # Arrange
        from app.api.middlewares.activity_tracking import ActivityTrackingMiddleware

        middleware = ActivityTrackingMiddleware(app=MagicMock())
        data: dict = {"level": 0}
        current = data
        for i in range(15):
            current["nested"] = {"level": i + 1}
            current = current["nested"]

        # Act
        masked = middleware._mask_sensitive_data(data)

        # Assert
        assert "***NESTED***" in str(masked)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint",
    ["/health", "/"],
    ids=["health", "root"],
)
async def test_activity_tracking_endpoint_success(client, endpoint: str):
    """[test_activity_tracking-017] リクエストが正常に処理されること。"""
    # Act
    response = await client.get(endpoint)

    # Assert
    assert response.status_code == 200
