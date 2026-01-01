"""監査ログミドルウェアのテスト。

AuditLogMiddlewareが正しく監査ログを記録することを検証します。
"""

import re
from unittest.mock import MagicMock

import pytest

from app.models import AuditEventType, AuditSeverity


class TestAuditLogMiddleware:
    """監査ログミドルウェアのユニットテスト。"""

    def test_audit_targets_contains_project(self):
        """[test_audit_log-001] プロジェクト変更が監査対象に含まれること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        project_config = None
        for config in middleware.AUDIT_TARGETS:
            if config["resource_type"] == "PROJECT":
                project_config = config
                break

        assert project_config is not None
        assert "PUT" in project_config["methods"]
        assert "PATCH" in project_config["methods"]
        assert "DELETE" in project_config["methods"]

    def test_audit_targets_contains_user(self):
        """[test_audit_log-002] ユーザー変更が監査対象に含まれること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        user_config = None
        for config in middleware.AUDIT_TARGETS:
            if config["resource_type"] == "USER":
                user_config = config
                break

        assert user_config is not None
        assert user_config["event_type"] == AuditEventType.DATA_CHANGE

    def test_audit_targets_contains_system_setting(self):
        """[test_audit_log-003] システム設定変更が監査対象に含まれること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        setting_config = None
        for config in middleware.AUDIT_TARGETS:
            if config["resource_type"] == "SYSTEM_SETTING":
                setting_config = config
                break

        assert setting_config is not None
        assert setting_config["severity"] == AuditSeverity.WARNING

    def test_audit_targets_contains_impersonation(self):
        """[test_audit_log-004] 代行操作が監査対象に含まれること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        impersonation_config = None
        for config in middleware.AUDIT_TARGETS:
            if config["resource_type"] == "IMPERSONATION":
                impersonation_config = config
                break

        assert impersonation_config is not None
        assert impersonation_config["event_type"] == AuditEventType.SECURITY
        assert impersonation_config["severity"] == AuditSeverity.CRITICAL

    def test_audit_targets_contains_data_cleanup(self):
        """[test_audit_log-005] データクリーンアップが監査対象に含まれること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        cleanup_config = None
        for config in middleware.AUDIT_TARGETS:
            if config["resource_type"] == "DATA_CLEANUP":
                cleanup_config = config
                break

        assert cleanup_config is not None
        assert cleanup_config["severity"] == AuditSeverity.CRITICAL

    def test_get_audit_config_matches(self):
        """[test_audit_log-006] パスとメソッドから監査設定が取得できること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        # システム設定変更
        config = middleware._get_audit_config("/api/v1/admin/settings/general", "PATCH")
        assert config is not None
        assert config["resource_type"] == "SYSTEM_SETTING"

    def test_get_audit_config_no_match(self):
        """[test_audit_log-007] 監査対象外のパスではNoneが返ること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        # GETリクエストは監査対象外
        config = middleware._get_audit_config("/api/v1/admin/settings", "GET")
        assert config is None

        # 対象外のパス
        config = middleware._get_audit_config("/api/v1/health", "GET")
        assert config is None

    def test_extract_resource_id(self):
        """[test_audit_log-008] パスからリソースIDが抽出できること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        pattern = re.compile(r"^/api/v1/projects?/([0-9a-f-]{36})$")
        resource_id = middleware._extract_resource_id(
            "/api/v1/projects/550e8400-e29b-41d4-a716-446655440000",
            pattern,
        )

        assert resource_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_extract_resource_id_no_match(self):
        """[test_audit_log-009] パターンに一致しないパスではNoneが返ること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        pattern = re.compile(r"^/api/v1/projects?/([0-9a-f-]{36})$")
        resource_id = middleware._extract_resource_id(
            "/api/v1/projects",  # IDなし
            pattern,
        )

        assert resource_id is None

    def test_infer_action_post(self):
        """[test_audit_log-010] POSTはCREATEと推定されること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        assert middleware._infer_action("POST") == "CREATE"

    def test_infer_action_put(self):
        """[test_audit_log-011] PUT/PATCHはUPDATEと推定されること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        assert middleware._infer_action("PUT") == "UPDATE"
        assert middleware._infer_action("PATCH") == "UPDATE"

    def test_infer_action_delete(self):
        """[test_audit_log-012] DELETEはDELETEと推定されること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        assert middleware._infer_action("DELETE") == "DELETE"

    def test_infer_action_other(self):
        """[test_audit_log-013] その他のメソッドはOTHERと推定されること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        assert middleware._infer_action("GET") == "OTHER"
        assert middleware._infer_action("HEAD") == "OTHER"
        assert middleware._infer_action("OPTIONS") == "OTHER"

    def test_get_changed_fields(self):
        """[test_audit_log-014] 変更フィールドが正しく検出されること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        old_value = {"name": "Old Name", "status": "active", "count": 10}
        new_value = {"name": "New Name", "status": "active", "count": 20}

        changed = middleware._get_changed_fields(old_value, new_value)

        assert "name" in changed
        assert "count" in changed
        assert "status" not in changed

    def test_get_changed_fields_empty(self):
        """[test_audit_log-015] 変更がない場合は空リストが返ること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        old_value = {"name": "Same", "status": "active"}
        new_value = {"name": "Same", "status": "active"}

        changed = middleware._get_changed_fields(old_value, new_value)

        assert changed == []

    def test_get_changed_fields_none_values(self):
        """[test_audit_log-016] None値の場合は空リストが返ること。"""
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        changed = middleware._get_changed_fields(None, None)
        assert changed == []

        changed = middleware._get_changed_fields({"name": "Test"}, None)
        assert changed == []


@pytest.mark.asyncio
async def test_audit_log_on_normal_request(client):
    """[test_audit_log-017] 通常のリクエストでミドルウェアが正常動作すること。"""
    response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_audit_log_on_api_endpoint(client):
    """[test_audit_log-018] APIエンドポイントでミドルウェアが正常動作すること。"""
    response = await client.get("/")

    assert response.status_code == 200
