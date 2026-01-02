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

import pytest
from httpx import AsyncClient

# ================================================================================
# Consolidated List Endpoints - 一覧取得エンドポイント統合テスト
# ================================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/admin/alerts",
        "/api/v1/admin/notification-templates",
        "/api/v1/admin/announcements",
    ],
    ids=["alerts", "templates", "announcements"],
)
async def test_list_notifications_success(
    client: AsyncClient, override_auth, admin_user, endpoint: str
):
    """[test_notifications-001/003/004] 通知関連一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get(endpoint)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


# ================================================================================
# System Alerts - システムアラート
# ================================================================================


@pytest.mark.asyncio
async def test_create_alert_success(client: AsyncClient, override_auth, admin_user):
    """[test_notifications-002] システムアラート作成の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    alert_data = {
        "name": "High CPU Alert",
        "conditionType": "ERROR_RATE",
        "threshold": {"value": 90},
        "comparisonOperator": ">",
        "notificationChannels": ["email"],
        "isEnabled": True,
    }

    # Act
    response = await client.post("/api/v1/admin/alerts", json=alert_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == alert_data["name"]


# ================================================================================
# Announcements - システムお知らせ
# ================================================================================


@pytest.mark.asyncio
async def test_list_announcements_with_filter(client: AsyncClient, override_auth, admin_user):
    """[test_notifications-005] フィルタ付きお知らせ一覧取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/announcements", params={"is_active": True})

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_announcement_success(client: AsyncClient, override_auth, admin_user):
    """[test_notifications-006] システムお知らせ作成の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    from datetime import UTC, datetime

    announcement_data = {
        "title": "システムアップデートのお知らせ",
        "content": "明日メンテナンスを実施します",
        "announcementType": "INFO",
        "priority": 1,
        "startAt": datetime.now(UTC).isoformat(),
    }

    # Act
    response = await client.post("/api/v1/admin/announcements", json=announcement_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == announcement_data["title"]
