"""ユーザー通知APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/notifications - 通知一覧取得
    - GET /api/v1/notifications/{notification_id} - 通知詳細取得
    - PATCH /api/v1/notifications/{notification_id}/read - 通知既読化
    - PATCH /api/v1/notifications/read-all - 全通知既読化
    - DELETE /api/v1/notifications/{notification_id} - 通知削除
"""

import uuid

import pytest
from httpx import AsyncClient


# ================================================================================
# GET /api/v1/notifications - 通知一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_notifications_success(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_user_notifications-001] 通知一覧取得の成功ケース。"""
    # Arrange
    await test_data_seeder.create_unread_notifications(regular_user.id, count=3)
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/notifications")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert "total" in data
    assert "unreadCount" in data
    assert "skip" in data
    assert "limit" in data
    assert len(data["notifications"]) == 3
    assert data["unreadCount"] == 3


@pytest.mark.asyncio
async def test_list_notifications_with_is_read_filter(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_user_notifications-002] 既読/未読フィルター付き通知一覧取得。"""
    # Arrange
    await test_data_seeder.create_unread_notifications(regular_user.id, count=2)
    await test_data_seeder.create_read_notification(regular_user.id)
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act - 未読のみ
    response = await client.get("/api/v1/notifications?is_read=false")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    for notification in data["notifications"]:
        assert notification["isRead"] is False


@pytest.mark.asyncio
async def test_list_notifications_with_pagination(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_user_notifications-003] ページネーション付き通知一覧取得。"""
    # Arrange
    await test_data_seeder.create_unread_notifications(regular_user.id, count=5)
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/notifications?skip=0&limit=2")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 2
    assert len(data["notifications"]) == 2
    assert data["total"] == 5


# ================================================================================
# GET /api/v1/notifications/{notification_id} - 通知詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_notification_success(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_user_notifications-004] 通知詳細取得の成功ケース。"""
    # Arrange
    notification = await test_data_seeder.create_notification(
        user_id=regular_user.id,
        title="詳細取得テスト",
        message="詳細取得テストメッセージ",
    )
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.get(f"/api/v1/notifications/{notification.id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(notification.id)
    assert data["title"] == "詳細取得テスト"
    assert data["message"] == "詳細取得テストメッセージ"


@pytest.mark.asyncio
async def test_get_notification_not_found(
    client: AsyncClient, override_auth, regular_user
):
    """[test_user_notifications-005] 通知詳細取得の404ケース。"""
    # Arrange
    override_auth(regular_user)
    non_existent_id = uuid.uuid4()

    # Act
    response = await client.get(f"/api/v1/notifications/{non_existent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_notification_other_user(
    client: AsyncClient, override_auth, regular_user, admin_user, test_data_seeder
):
    """[test_user_notifications-006] 他ユーザーの通知は取得不可。"""
    # Arrange - admin_userの通知を作成
    notification = await test_data_seeder.create_notification(
        user_id=admin_user.id,
        title="他人の通知",
    )
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act - regular_userで取得を試みる
    response = await client.get(f"/api/v1/notifications/{notification.id}")

    # Assert - 他人の通知は見つからない扱い
    assert response.status_code == 404


# ================================================================================
# PATCH /api/v1/notifications/{notification_id}/read - 通知既読化
# ================================================================================


@pytest.mark.asyncio
async def test_mark_notification_as_read_success(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_user_notifications-007] 通知既読化の成功ケース。"""
    # Arrange
    notification = await test_data_seeder.create_notification(
        user_id=regular_user.id,
        is_read=False,
    )
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.patch(f"/api/v1/notifications/{notification.id}/read")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(notification.id)
    assert data["isRead"] is True
    assert data["readAt"] is not None


@pytest.mark.asyncio
async def test_mark_notification_as_read_not_found(
    client: AsyncClient, override_auth, regular_user
):
    """[test_user_notifications-008] 通知既読化の404ケース。"""
    # Arrange
    override_auth(regular_user)
    non_existent_id = uuid.uuid4()

    # Act
    response = await client.patch(f"/api/v1/notifications/{non_existent_id}/read")

    # Assert
    assert response.status_code == 404


# ================================================================================
# PATCH /api/v1/notifications/read-all - 全通知既読化
# ================================================================================


@pytest.mark.asyncio
async def test_mark_all_notifications_as_read_success(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_user_notifications-009] 全通知既読化の成功ケース。"""
    # Arrange
    await test_data_seeder.create_unread_notifications(regular_user.id, count=5)
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.patch("/api/v1/notifications/read-all")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "updatedCount" in data
    assert data["updatedCount"] == 5


@pytest.mark.asyncio
async def test_mark_all_notifications_as_read_no_unread(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_user_notifications-010] 未読通知がない場合の全既読化。"""
    # Arrange - 既読通知のみ作成
    await test_data_seeder.create_read_notification(regular_user.id)
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.patch("/api/v1/notifications/read-all")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["updatedCount"] == 0


# ================================================================================
# DELETE /api/v1/notifications/{notification_id} - 通知削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_notification_success(
    client: AsyncClient, override_auth, regular_user, test_data_seeder
):
    """[test_user_notifications-011] 通知削除の成功ケース。"""
    # Arrange
    notification = await test_data_seeder.create_notification(user_id=regular_user.id)
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act
    response = await client.delete(f"/api/v1/notifications/{notification.id}")

    # Assert
    assert response.status_code == 204

    # 削除確認
    get_response = await client.get(f"/api/v1/notifications/{notification.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_notification_not_found(
    client: AsyncClient, override_auth, regular_user
):
    """[test_user_notifications-012] 通知削除の404ケース。"""
    # Arrange
    override_auth(regular_user)
    non_existent_id = uuid.uuid4()

    # Act
    response = await client.delete(f"/api/v1/notifications/{non_existent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_notification_other_user(
    client: AsyncClient, override_auth, regular_user, admin_user, test_data_seeder
):
    """[test_user_notifications-013] 他ユーザーの通知は削除不可。"""
    # Arrange - admin_userの通知を作成
    notification = await test_data_seeder.create_notification(user_id=admin_user.id)
    await test_data_seeder.db.commit()
    override_auth(regular_user)

    # Act - regular_userで削除を試みる
    response = await client.delete(f"/api/v1/notifications/{notification.id}")

    # Assert
    assert response.status_code == 404
