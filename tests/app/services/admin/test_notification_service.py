"""通知管理サービスのテスト。"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import UserAccount
from app.models.system.notification_template import NotificationTemplate
from app.models.system.system_alert import SystemAlert
from app.models.system.system_announcement import SystemAnnouncement
from app.schemas.admin.announcement import AnnouncementCreate
from app.schemas.admin.notification_template import NotificationTemplateUpdate
from app.schemas.admin.system_alert import SystemAlertCreate, SystemAlertUpdate
from app.services.admin.notification_service import NotificationService


@pytest.mark.asyncio
async def test_create_alert_success(db_session: AsyncSession):
    """[test_notification_service-001] アラート作成の成功ケース。"""
    # Arrange
    service = NotificationService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    data = SystemAlertCreate(
        name="Test Alert",
        condition_type="THRESHOLD",
        threshold={"value": 100},
        comparison_operator="GT",
        notification_channels=["email"],
        is_enabled=True,
    )
    result = await service.create_alert(data, creator_id)

    # Assert
    assert result is not None
    assert result.name == "Test Alert"
    assert result.is_enabled is True


@pytest.mark.asyncio
async def test_update_alert_success(db_session: AsyncSession):
    """[test_notification_service-002] アラート更新の成功ケース。"""
    # Arrange
    service = NotificationService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # アラートを作成
    alert = SystemAlert(
        name="Original Alert",
        condition_type="THRESHOLD",
        threshold={"value": 100},
        comparison_operator="GT",
        notification_channels=["email"],
        is_enabled=True,
        created_by=creator_id,
    )
    db_session.add(alert)
    await db_session.commit()

    # Act
    update_data = SystemAlertUpdate(
        name="Updated Alert",
        is_enabled=False,
    )
    result = await service.update_alert(alert.id, update_data)

    # Assert
    assert result.name == "Updated Alert"
    assert result.is_enabled is False


@pytest.mark.asyncio
async def test_delete_alert_success(db_session: AsyncSession):
    """[test_notification_service-003] アラート削除の成功ケース。"""
    # Arrange
    service = NotificationService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # アラートを作成
    alert = SystemAlert(
        name="Alert to Delete",
        condition_type="THRESHOLD",
        threshold={"value": 100},
        comparison_operator="GT",
        notification_channels=["email"],
        is_enabled=True,
        created_by=creator_id,
    )
    db_session.add(alert)
    await db_session.commit()
    alert_id = alert.id

    # Act
    result = await service.delete_alert(alert_id)

    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_delete_alert_not_found(db_session: AsyncSession):
    """[test_notification_service-004] 存在しないアラート削除のエラー。"""
    # Arrange
    service = NotificationService(db_session)
    nonexistent_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.delete_alert(nonexistent_id)


@pytest.mark.asyncio
async def test_list_templates_success(db_session: AsyncSession):
    """[test_notification_service-005] テンプレート一覧取得の成功ケース。"""
    # Arrange
    service = NotificationService(db_session)

    # テンプレートを作成
    template = NotificationTemplate(
        event_type="PROJECT_CREATED",
        name="Project Created Template",
        subject="New Project: {{project_name}}",
        body="A new project has been created.",
        is_active=True,
    )
    db_session.add(template)
    await db_session.commit()

    # Act
    result = await service.list_templates()

    # Assert
    assert result is not None
    assert len(result.items) >= 1


@pytest.mark.asyncio
async def test_update_template_success(db_session: AsyncSession):
    """[test_notification_service-006] テンプレート更新の成功ケース。"""
    # Arrange
    service = NotificationService(db_session)

    # テンプレートを作成
    template = NotificationTemplate(
        event_type="PROJECT_CREATED",
        name="Original Template",
        subject="Original Subject",
        body="Original Body",
        is_active=True,
    )
    db_session.add(template)
    await db_session.commit()

    # Act
    update_data = NotificationTemplateUpdate(
        name="Updated Template",
        subject="Updated Subject",
    )
    result = await service.update_template(template.id, update_data)

    # Assert
    assert result.name == "Updated Template"
    assert result.subject == "Updated Subject"


@pytest.mark.asyncio
async def test_create_announcement_success(db_session: AsyncSession):
    """[test_notification_service-007] お知らせ作成の成功ケース。"""
    # Arrange
    service = NotificationService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    data = AnnouncementCreate(
        title="Test Announcement",
        content="This is a test announcement",
        announcement_type="MAINTENANCE",
        target_roles=["User"],
        start_at=datetime.now(UTC),
        end_at=datetime.now(UTC) + timedelta(days=7),
        priority=1,
    )
    result = await service.create_announcement(data, creator_id)

    # Assert
    assert result is not None
    assert result.title == "Test Announcement"


@pytest.mark.asyncio
async def test_list_active_announcements_success(db_session: AsyncSession):
    """[test_notification_service-008] アクティブなお知らせ一覧取得。"""
    # Arrange
    service = NotificationService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # アクティブなお知らせを作成
    now = datetime.now(UTC)
    announcement = SystemAnnouncement(
        title="Active Announcement",
        content="This is active",
        announcement_type="INFO",
        target_roles=["User"],
        start_at=now - timedelta(days=1),
        end_at=now + timedelta(days=1),
        priority=1,
        is_active=True,
        created_by=creator_id,
    )
    db_session.add(announcement)
    await db_session.commit()

    # Act
    result = await service.list_active_announcements()

    # Assert
    assert result is not None
    assert len(result.items) >= 1
