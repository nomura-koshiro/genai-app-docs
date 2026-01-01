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
# GET /api/v1/admin/audit-logs/changes - データ変更履歴取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_data_changes_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-003] データ変更履歴取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/changes")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


# ================================================================================
# GET /api/v1/admin/audit-logs/access - アクセスログ取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_access_logs_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-004] アクセスログ取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/access")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


# ================================================================================
# GET /api/v1/admin/audit-logs/security - セキュリティイベント取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_security_events_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-005] セキュリティイベント取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/security")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


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


@pytest.mark.asyncio
async def test_export_audit_logs_csv_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-007] 監査ログCSVエクスポートの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/export", params={"format": "csv"})

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_export_audit_logs_json_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-008] 監査ログJSONエクスポートの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/export", params={"format": "json"})

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]
