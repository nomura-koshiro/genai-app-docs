"""操作履歴管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/activity-logs - 操作履歴一覧取得
    - GET /api/v1/admin/activity-logs/errors - エラー履歴取得
    - GET /api/v1/admin/activity-logs/export - 操作履歴エクスポート
    - GET /api/v1/admin/activity-logs/{activity_id} - 操作履歴詳細取得
"""

import uuid

import pytest
from httpx import AsyncClient


# ================================================================================
# GET /api/v1/admin/activity-logs - 操作履歴一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_activity_logs_success(client: AsyncClient, override_auth, admin_user):
    """[test_activity_logs-001] 操作履歴一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/activity-logs")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_list_activity_logs_with_filters(client: AsyncClient, override_auth, admin_user):
    """[test_activity_logs-002] フィルタ付き操作履歴一覧取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get(
        "/api/v1/admin/activity-logs",
        params={
            "action_type": "CREATE",
            "page": 1,
            "limit": 10,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 10


@pytest.mark.asyncio
async def test_list_activity_logs_unauthorized(client: AsyncClient):
    """[test_activity_logs-003] 認証なしでの操作履歴一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/activity-logs")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_activity_logs_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_activity_logs-004] 一般ユーザーでの操作履歴一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/activity-logs")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/activity-logs/errors - エラー履歴取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_error_logs_success(client: AsyncClient, override_auth, admin_user):
    """[test_activity_logs-005] エラー履歴取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/activity-logs/errors")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_error_logs_unauthorized(client: AsyncClient):
    """[test_activity_logs-006] 認証なしでのエラー履歴取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/activity-logs/errors")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_error_logs_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_activity_logs-007] 一般ユーザーでのエラー履歴取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/activity-logs/errors")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/activity-logs/export - 操作履歴エクスポート
# ================================================================================


@pytest.mark.asyncio
async def test_export_activity_logs_success(client: AsyncClient, override_auth, admin_user):
    """[test_activity_logs-008] 操作履歴エクスポートの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/activity-logs/export")

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_export_activity_logs_unauthorized(client: AsyncClient):
    """[test_activity_logs-009] 認証なしでのエクスポート拒否。"""
    # Act
    response = await client.get("/api/v1/admin/activity-logs/export")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_export_activity_logs_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_activity_logs-010] 一般ユーザーでのエクスポート拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/activity-logs/export")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/activity-logs/{activity_id} - 操作履歴詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_activity_log_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_activity_logs-011] 存在しない操作履歴の取得。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/activity-logs/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_activity_log_unauthorized(client: AsyncClient):
    """[test_activity_logs-012] 認証なしでの操作履歴詳細取得拒否。"""
    # Arrange
    activity_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/activity-logs/{activity_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_activity_log_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_activity_logs-013] 一般ユーザーでの操作履歴詳細取得拒否。"""
    # Arrange
    override_auth(regular_user)
    activity_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/activity-logs/{activity_id}")

    # Assert
    assert response.status_code == 403
