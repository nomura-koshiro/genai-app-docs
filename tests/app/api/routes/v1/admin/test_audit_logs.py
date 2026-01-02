"""監査ログ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/audit-logs - 監査ログ一覧取得
    - GET /api/v1/admin/audit-logs/changes - データ変更履歴取得
    - GET /api/v1/admin/audit-logs/access - アクセスログ取得
    - GET /api/v1/admin/audit-logs/security - セキュリティイベント取得
    - GET /api/v1/admin/audit-logs/resource/{type}/{id} - リソース変更履歴追跡
    - GET /api/v1/admin/audit-logs/export - 監査ログエクスポート
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/audit-logs - 監査ログ一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_audit_logs_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-001] 監査ログ一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_list_audit_logs_with_filters(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-002] フィルタ付き監査ログ一覧取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get(
        "/api/v1/admin/audit-logs",
        params={
            "event_type": "DATA_CHANGE",
            "severity": "INFO",
            "page": 1,
            "limit": 20,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 20


# ================================================================================
# GET /api/v1/admin/audit-logs/{type} - 各種監査ログ取得
# ================================================================================


@pytest.mark.parametrize(
    "endpoint,expected_keys",
    [
        ("/api/v1/admin/audit-logs/changes", ["items", "total"]),
        ("/api/v1/admin/audit-logs/access", ["items", "total"]),
        ("/api/v1/admin/audit-logs/security", ["items", "total"]),
    ],
    ids=["data_changes", "access_logs", "security_events"],
)
@pytest.mark.asyncio
async def test_list_specific_audit_logs_success(
    client: AsyncClient, override_auth, admin_user, endpoint, expected_keys
):
    """[test_audit_logs-003-005] 各種監査ログ取得の成功ケース（データ変更/アクセス/セキュリティ）。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get(endpoint)

    # Assert
    assert response.status_code == 200
    data = response.json()
    for key in expected_keys:
        assert key in data


# ================================================================================
# GET /api/v1/admin/audit-logs/resource/{type}/{id} - リソース変更履歴追跡
# ================================================================================


@pytest.mark.asyncio
async def test_get_resource_history_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-006] リソース変更履歴追跡の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    resource_type = "PROJECT"
    resource_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/audit-logs/resource/{resource_type}/{resource_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


# ================================================================================
# GET /api/v1/admin/audit-logs/export - 監査ログエクスポート
# ================================================================================


@pytest.mark.parametrize(
    "export_format,expected_content_type",
    [
        ("csv", "text/csv; charset=utf-8"),
        ("json", "application/json"),
    ],
    ids=["csv_format", "json_format"],
)
@pytest.mark.asyncio
async def test_export_audit_logs_success(
    client: AsyncClient, override_auth, admin_user, export_format, expected_content_type
):
    """[test_audit_logs-007-008] 監査ログエクスポートの成功ケース（CSV/JSON）。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/export", params={"format": export_format})

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == expected_content_type
    assert "attachment" in response.headers["content-disposition"]
