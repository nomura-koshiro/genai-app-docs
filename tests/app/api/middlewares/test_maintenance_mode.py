"""メンテナンスモードミドルウェアのテスト。

MaintenanceModeMiddlewareが正しくメンテナンスモード時のアクセス制御を
行うことを検証します。
"""

from unittest.mock import MagicMock

import pytest


class TestMaintenanceModeMiddleware:
    """メンテナンスモードミドルウェアのユニットテスト。"""

    @pytest.mark.parametrize(
        "path",
        [
            # ヘルスチェック
            "/health",
            "/healthz",
            "/ready",
            # ドキュメント
            "/docs",
            "/openapi.json",
            "/redoc",
        ],
        ids=["health", "healthz", "ready", "docs", "openapi", "redoc"],
    )
    def test_allowed_paths_included(self, path: str):
        """[test_maintenance_mode-001] 常にアクセス可能なパスが設定されていること。"""
        # Arrange
        from app.api.middlewares.maintenance_mode import MaintenanceModeMiddleware

        middleware = MaintenanceModeMiddleware(app=MagicMock())

        # Act & Assert
        assert path in middleware.ALWAYS_ALLOWED_PATHS

    @pytest.mark.parametrize(
        "path,should_match",
        [
            # 管理者パス（マッチする）
            ("/api/v1/admin/settings", True),
            ("/api/v1/admin/statistics", True),
            ("/api/v1/admin/audit-logs", True),
            # 非管理者パス（マッチしない）
            ("/api/v1/projects", False),
            ("/api/v1/user_accounts", False),
            ("/health", False),
        ],
        ids=["admin_settings", "admin_stats", "admin_audit", "projects", "users", "health"],
    )
    def test_admin_path_pattern_match(self, path: str, should_match: bool):
        """[test_maintenance_mode-003] 管理者パスパターンが正しく判定されること。"""
        # Arrange
        from app.api.middlewares.maintenance_mode import MaintenanceModeMiddleware

        middleware = MaintenanceModeMiddleware(app=MagicMock())

        # Act & Assert
        if should_match:
            assert middleware.ADMIN_PATH_PATTERN.match(path)
        else:
            assert not middleware.ADMIN_PATH_PATTERN.match(path)

    def test_cache_clear_operation_resets_cache(self):
        """[test_maintenance_mode-005] キャッシュクリアが正しく動作すること。"""
        # Arrange
        from app.api.middlewares.maintenance_mode import MaintenanceModeMiddleware

        middleware = MaintenanceModeMiddleware(app=MagicMock())
        middleware._maintenance_cache = {"enabled": True}
        middleware._cache_ttl = 9999999999

        # Act
        middleware.clear_cache()

        # Assert
        assert middleware._maintenance_cache is None
        assert middleware._cache_ttl == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint,expected_status",
    [
        ("/health", 200),
        ("/docs", [200, 307]),  # リダイレクトまたは200
    ],
    ids=["health", "docs"],
)
async def test_maintenance_mode_allowed_endpoints(client, endpoint: str, expected_status):
    """[test_maintenance_mode-006] メンテナンスモードでも許可エンドポイントはアクセス可能。"""
    # Act
    response = await client.get(endpoint)

    # Assert
    if isinstance(expected_status, list):
        assert response.status_code in expected_status
    else:
        assert response.status_code == expected_status
