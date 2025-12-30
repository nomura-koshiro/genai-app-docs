"""通知管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/alerts - システムアラート一覧取得
    - POST /api/v1/admin/alerts - システムアラート作成
    - PATCH /api/v1/admin/alerts/{alert_id} - システムアラート更新
    - DELETE /api/v1/admin/alerts/{alert_id} - システムアラート削除
    - GET /api/v1/admin/notification-templates - 通知テンプレート一覧取得
    - PATCH /api/v1/admin/notification-templates/{template_id} - 通知テンプレート更新
    - GET /api/v1/admin/announcements - システムお知らせ一覧取得
    - POST /api/v1/admin/announcements - システムお知らせ作成
    - PATCH /api/v1/admin/announcements/{announcement_id} - システムお知らせ更新
    - DELETE /api/v1/admin/announcements/{announcement_id} - システムお知らせ削除
"""

import uuid

import pytest
from httpx import AsyncClient


# ================================================================================
# System Alerts - システムアラート
# ================================================================================


@pytest.mark.asyncio
async def test_list_alerts_success(client: AsyncClient, override_auth, admin_user):
    """[test_notifications-001] システムアラート一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/alerts")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_alerts_unauthorized(client: AsyncClient):
    """[test_notifications-002] 認証なしでのシステムアラート一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/alerts")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_alerts_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_notifications-003] 一般ユーザーでのシステムアラート一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/alerts")

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_alert_success(client: AsyncClient, override_auth, admin_user):
    """[test_notifications-004] システムアラート作成の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    alert_data = {
        "name": "High CPU Alert",
        "description": "CPU使用率が高い場合のアラート",
        "severity": "WARNING",
        "is_enabled": True,
    }

    # Act
    response = await client.post("/api/v1/admin/alerts", json=alert_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == alert_data["name"]


@pytest.mark.asyncio
async def test_create_alert_unauthorized(client: AsyncClient):
    """[test_notifications-005] 認証なしでのシステムアラート作成拒否。"""
    # Arrange
    alert_data = {
        "name": "Test Alert",
        "description": "Test",
        "severity": "INFO",
        "is_enabled": True,
    }

    # Act
    response = await client.post("/api/v1/admin/alerts", json=alert_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_alert_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_notifications-006] 一般ユーザーでのシステムアラート作成拒否。"""
    # Arrange
    override_auth(regular_user)
    alert_data = {
        "name": "Test Alert",
        "description": "Test",
        "severity": "INFO",
        "is_enabled": True,
    }

    # Act
    response = await client.post("/api/v1/admin/alerts", json=alert_data)

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_alert_unauthorized(client: AsyncClient):
    """[test_notifications-007] 認証なしでのシステムアラート更新拒否。"""
    # Arrange
    alert_id = str(uuid.uuid4())
    update_data = {"name": "Updated Alert"}

    # Act
    response = await client.patch(f"/api/v1/admin/alerts/{alert_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_alert_unauthorized(client: AsyncClient):
    """[test_notifications-008] 認証なしでのシステムアラート削除拒否。"""
    # Arrange
    alert_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/alerts/{alert_id}")

    # Assert
    assert response.status_code in [401, 403]


# ================================================================================
# Notification Templates - 通知テンプレート
# ================================================================================


@pytest.mark.asyncio
async def test_list_templates_success(client: AsyncClient, override_auth, admin_user):
    """[test_notifications-009] 通知テンプレート一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/notification-templates")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_templates_unauthorized(client: AsyncClient):
    """[test_notifications-010] 認証なしでの通知テンプレート一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/notification-templates")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_templates_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_notifications-011] 一般ユーザーでの通知テンプレート一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/notification-templates")

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_template_unauthorized(client: AsyncClient):
    """[test_notifications-012] 認証なしでの通知テンプレート更新拒否。"""
    # Arrange
    template_id = str(uuid.uuid4())
    update_data = {"subject": "Updated Template"}

    # Act
    response = await client.patch(f"/api/v1/admin/notification-templates/{template_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


# ================================================================================
# Announcements - システムお知らせ
# ================================================================================


@pytest.mark.asyncio
async def test_list_announcements_success(client: AsyncClient, override_auth, admin_user):
    """[test_notifications-013] システムお知らせ一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/announcements")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_announcements_with_filter(client: AsyncClient, override_auth, admin_user):
    """[test_notifications-014] フィルタ付きお知らせ一覧取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/announcements", params={"is_active": True})

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_announcements_unauthorized(client: AsyncClient):
    """[test_notifications-015] 認証なしでのシステムお知らせ一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/announcements")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_announcements_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_notifications-016] 一般ユーザーでのシステムお知らせ一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/announcements")

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_announcement_success(client: AsyncClient, override_auth, admin_user):
    """[test_notifications-017] システムお知らせ作成の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    announcement_data = {
        "title": "システムアップデートのお知らせ",
        "content": "明日メンテナンスを実施します",
        "priority": "HIGH",
        "is_active": True,
    }

    # Act
    response = await client.post("/api/v1/admin/announcements", json=announcement_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == announcement_data["title"]


@pytest.mark.asyncio
async def test_create_announcement_unauthorized(client: AsyncClient):
    """[test_notifications-018] 認証なしでのシステムお知らせ作成拒否。"""
    # Arrange
    announcement_data = {
        "title": "Test",
        "content": "Test",
        "priority": "LOW",
        "is_active": True,
    }

    # Act
    response = await client.post("/api/v1/admin/announcements", json=announcement_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_announcement_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_notifications-019] 一般ユーザーでのシステムお知らせ作成拒否。"""
    # Arrange
    override_auth(regular_user)
    announcement_data = {
        "title": "Test",
        "content": "Test",
        "priority": "LOW",
        "is_active": True,
    }

    # Act
    response = await client.post("/api/v1/admin/announcements", json=announcement_data)

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_announcement_unauthorized(client: AsyncClient):
    """[test_notifications-020] 認証なしでのシステムお知らせ更新拒否。"""
    # Arrange
    announcement_id = str(uuid.uuid4())
    update_data = {"title": "Updated"}

    # Act
    response = await client.patch(f"/api/v1/admin/announcements/{announcement_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_announcement_unauthorized(client: AsyncClient):
    """[test_notifications-021] 認証なしでのシステムお知らせ削除拒否。"""
    # Arrange
    announcement_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/announcements/{announcement_id}")

    # Assert
    assert response.status_code in [401, 403]
