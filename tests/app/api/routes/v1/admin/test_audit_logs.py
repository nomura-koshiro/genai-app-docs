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


@pytest.mark.asyncio
async def test_list_audit_logs_unauthorized(client: AsyncClient):
    """[test_audit_logs-003] 認証なしでの監査ログ一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/audit-logs")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_audit_logs_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_audit_logs-004] 一般ユーザーでの監査ログ一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/audit-logs/changes - データ変更履歴取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_data_changes_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-005] データ変更履歴取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/changes")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_data_changes_unauthorized(client: AsyncClient):
    """[test_audit_logs-006] 認証なしでのデータ変更履歴取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/audit-logs/changes")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_data_changes_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_audit_logs-007] 一般ユーザーでのデータ変更履歴取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/changes")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/audit-logs/access - アクセスログ取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_access_logs_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-008] アクセスログ取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/access")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_access_logs_unauthorized(client: AsyncClient):
    """[test_audit_logs-009] 認証なしでのアクセスログ取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/audit-logs/access")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_access_logs_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_audit_logs-010] 一般ユーザーでのアクセスログ取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/access")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/audit-logs/security - セキュリティイベント取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_security_events_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-011] セキュリティイベント取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/security")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_security_events_unauthorized(client: AsyncClient):
    """[test_audit_logs-012] 認証なしでのセキュリティイベント取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/audit-logs/security")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_security_events_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_audit_logs-013] 一般ユーザーでのセキュリティイベント取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/security")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/audit-logs/resource/{type}/{id} - リソース変更履歴追跡
# ================================================================================


@pytest.mark.asyncio
async def test_get_resource_history_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-014] リソース変更履歴追跡の成功ケース。"""
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


@pytest.mark.asyncio
async def test_get_resource_history_unauthorized(client: AsyncClient):
    """[test_audit_logs-015] 認証なしでのリソース変更履歴追跡拒否。"""
    # Arrange
    resource_type = "PROJECT"
    resource_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/audit-logs/resource/{resource_type}/{resource_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_resource_history_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_audit_logs-016] 一般ユーザーでのリソース変更履歴追跡拒否。"""
    # Arrange
    override_auth(regular_user)
    resource_type = "PROJECT"
    resource_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/audit-logs/resource/{resource_type}/{resource_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/audit-logs/export - 監査ログエクスポート
# ================================================================================


@pytest.mark.asyncio
async def test_export_audit_logs_csv_success(client: AsyncClient, override_auth, admin_user):
    """[test_audit_logs-017] 監査ログCSVエクスポートの成功ケース。"""
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
    """[test_audit_logs-018] 監査ログJSONエクスポートの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/export", params={"format": "json"})

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_export_audit_logs_unauthorized(client: AsyncClient):
    """[test_audit_logs-019] 認証なしでのエクスポート拒否。"""
    # Act
    response = await client.get("/api/v1/admin/audit-logs/export")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_export_audit_logs_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_audit_logs-020] 一般ユーザーでのエクスポート拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/audit-logs/export")

    # Assert
    assert response.status_code == 403
