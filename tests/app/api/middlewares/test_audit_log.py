"""監査ログミドルウェアのテスト。

AuditLogMiddlewareが正しく監査ログを記録することを検証します。
"""

import re
from unittest.mock import MagicMock

import pytest

from app.models import AuditEventType, AuditSeverity


class TestAuditLogMiddleware:
    """監査ログミドルウェアのユニットテスト。"""

    @pytest.mark.parametrize(
        "resource_type,expected_event_type,expected_severity,expected_methods",
        [
            ("PROJECT", AuditEventType.DATA_CHANGE, AuditSeverity.INFO, {"PUT", "PATCH", "DELETE"}),
            ("USER", AuditEventType.DATA_CHANGE, AuditSeverity.INFO, {"PUT", "PATCH", "DELETE"}),
            ("SYSTEM_SETTING", AuditEventType.DATA_CHANGE, AuditSeverity.WARNING, {"PATCH", "POST"}),
            ("IMPERSONATION", AuditEventType.SECURITY, AuditSeverity.CRITICAL, {"POST"}),
            ("DATA_CLEANUP", AuditEventType.DATA_CHANGE, AuditSeverity.CRITICAL, {"POST"}),
        ],
        ids=["project", "user", "system_setting", "impersonation", "data_cleanup"],
    )
    def test_audit_targets_config(
        self,
        resource_type: str,
        expected_event_type: AuditEventType,
        expected_severity: AuditSeverity,
        expected_methods: set[str],
    ):
        """[test_audit_log-001] 各リソースタイプの監査設定が正しいこと。"""
        # Arrange
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        # Act
        config = None
        for c in middleware.AUDIT_TARGETS:
            if c["resource_type"] == resource_type:
                config = c
                break

        # Assert
        assert config is not None, f"{resource_type} の設定が見つからない"
        assert config["event_type"] == expected_event_type
        assert config["severity"] == expected_severity
        for method in expected_methods:
            assert method in config["methods"]

    @pytest.mark.parametrize(
        "path,method,expected_resource_type",
        [
            ("/api/v1/admin/settings/general", "PATCH", "SYSTEM_SETTING"),
            ("/api/v1/admin/settings", "GET", None),  # GET は対象外
            ("/api/v1/health", "GET", None),  # 対象外パス
        ],
        ids=["system_setting_patch", "system_setting_get", "health"],
    )
    def test_get_audit_config(self, path: str, method: str, expected_resource_type: str | None):
        """[test_audit_log-006] パスとメソッドから監査設定が取得できること。"""
        # Arrange
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        # Act
        config = middleware._get_audit_config(path, method)

        # Assert
        if expected_resource_type:
            assert config is not None
            assert config["resource_type"] == expected_resource_type
        else:
            assert config is None

    @pytest.mark.parametrize(
        "path,expected_id",
        [
            ("/api/v1/projects/550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440000"),
            ("/api/v1/projects", None),  # IDなし
        ],
        ids=["with_id", "without_id"],
    )
    def test_extract_resource_id(self, path: str, expected_id: str | None):
        """[test_audit_log-008] パスからリソースIDが抽出できること。"""
        # Arrange
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())
        pattern = re.compile(r"^/api/v1/projects?/([0-9a-f-]{36})$")

        # Act
        resource_id = middleware._extract_resource_id(path, pattern)

        # Assert
        assert resource_id == expected_id

    @pytest.mark.parametrize(
        "method,expected_action",
        [
            ("POST", "CREATE"),
            ("PUT", "UPDATE"),
            ("PATCH", "UPDATE"),
            ("DELETE", "DELETE"),
            ("GET", "OTHER"),
            ("HEAD", "OTHER"),
            ("OPTIONS", "OTHER"),
        ],
        ids=["post", "put", "patch", "delete", "get", "head", "options"],
    )
    def test_infer_action(self, method: str, expected_action: str):
        """[test_audit_log-010] HTTPメソッドからアクションが推定されること。"""
        # Arrange
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        # Act & Assert
        assert middleware._infer_action(method) == expected_action

    @pytest.mark.parametrize(
        "old_value,new_value,expected_changed",
        [
            ({"name": "Old", "status": "active", "count": 10}, {"name": "New", "status": "active", "count": 20}, ["name", "count"]),
            ({"name": "Same", "status": "active"}, {"name": "Same", "status": "active"}, []),
            (None, None, []),
            ({"name": "Test"}, None, []),
        ],
        ids=["changed", "unchanged", "both_none", "new_none"],
    )
    def test_get_changed_fields(
        self,
        old_value: dict | None,
        new_value: dict | None,
        expected_changed: list[str],
    ):
        """[test_audit_log-014] 変更フィールドが正しく検出されること。"""
        # Arrange
        from app.api.middlewares.audit_log import AuditLogMiddleware

        middleware = AuditLogMiddleware(app=MagicMock())

        # Act
        changed = middleware._get_changed_fields(old_value, new_value)

        # Assert
        if expected_changed:
            for field in expected_changed:
                assert field in changed
            assert "status" not in changed  # 変更なしフィールド
        else:
            assert changed == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint",
    ["/health", "/"],
    ids=["health", "root"],
)
async def test_audit_log_endpoint_success(client, endpoint: str):
    """[test_audit_log-017] ミドルウェアが正常動作すること。"""
    # Act
    response = await client.get(endpoint)

    # Assert
    assert response.status_code == 200
