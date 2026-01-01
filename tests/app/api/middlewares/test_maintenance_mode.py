"""メンテナンスモードミドルウェアのテスト。

MaintenanceModeMiddlewareが正しくメンテナンスモード時のアクセス制御を
行うことを検証します。
"""

from unittest.mock import MagicMock

import pytest


class TestMaintenanceModeMiddleware:
    """メンテナンスモードミドルウェアのユニットテスト。"""

    def test_always_allowed_paths_health(self):
        """[test_maintenance_mode-001] ヘルスチェックパスは常にアクセス可能であること。"""
        # Arrange
        from app.api.middlewares.maintenance_mode import MaintenanceModeMiddleware

        middleware = MaintenanceModeMiddleware(app=MagicMock())

        # Act & Assert
        assert "/health" in middleware.ALWAYS_ALLOWED_PATHS
        assert "/healthz" in middleware.ALWAYS_ALLOWED_PATHS
        assert "/ready" in middleware.ALWAYS_ALLOWED_PATHS

    def test_always_allowed_paths_docs(self):
        """[test_maintenance_mode-002] ドキュメントパスは常にアクセス可能であること。"""
        # Arrange
        from app.api.middlewares.maintenance_mode import MaintenanceModeMiddleware

        middleware = MaintenanceModeMiddleware(app=MagicMock())

        # Act & Assert
        assert "/docs" in middleware.ALWAYS_ALLOWED_PATHS
        assert "/openapi.json" in middleware.ALWAYS_ALLOWED_PATHS
        assert "/redoc" in middleware.ALWAYS_ALLOWED_PATHS

    def test_admin_path_pattern_matches(self):
        """[test_maintenance_mode-003] 管理者パスパターンが正しく一致すること。"""
        # Arrange
        from app.api.middlewares.maintenance_mode import MaintenanceModeMiddleware

        middleware = MaintenanceModeMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware.ADMIN_PATH_PATTERN.match("/api/v1/admin/settings")
        assert middleware.ADMIN_PATH_PATTERN.match("/api/v1/admin/statistics")
        assert middleware.ADMIN_PATH_PATTERN.match("/api/v1/admin/audit-logs")

    def test_admin_path_pattern_not_matches(self):
        """[test_maintenance_mode-004] 非管理者パスはパターンに一致しないこと。"""
        # Arrange
        from app.api.middlewares.maintenance_mode import MaintenanceModeMiddleware

        middleware = MaintenanceModeMiddleware(app=MagicMock())

        # Act & Assert
        assert not middleware.ADMIN_PATH_PATTERN.match("/api/v1/projects")
        assert not middleware.ADMIN_PATH_PATTERN.match("/api/v1/user_accounts")
        assert not middleware.ADMIN_PATH_PATTERN.match("/health")

    def test_cache_clear(self):
        """[test_maintenance_mode-005] キャッシュクリアが正しく動作すること。"""
        # Arrange
        from app.api.middlewares.maintenance_mode import MaintenanceModeMiddleware

        middleware = MaintenanceModeMiddleware(app=MagicMock())

        # キャッシュを設定
        middleware._maintenance_cache = {"enabled": True}
        middleware._cache_ttl = 9999999999

        # Act
        # キャッシュをクリア
        middleware.clear_cache()

        # Assert
        assert middleware._maintenance_cache is None
        assert middleware._cache_ttl == 0


@pytest.mark.asyncio
async def test_maintenance_mode_allows_health_endpoint(client):
    """[test_maintenance_mode-006] メンテナンスモードでもヘルスチェックはアクセス可能であること。"""
    # Act
    response = await client.get("/health")

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_maintenance_mode_allows_docs(client):
    """[test_maintenance_mode-007] メンテナンスモードでもドキュメントはアクセス可能であること。"""
    # Act
    response = await client.get("/docs")

    # Assert
    # docsへのリダイレクトまたは200を期待
    assert response.status_code in [200, 307]
