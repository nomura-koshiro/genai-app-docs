"""一括操作サービスのテスト。"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, UserAccount
from app.models.audit.user_activity import UserActivity
from app.services.admin.bulk_operation_service import BulkOperationService


@pytest.mark.asyncio
async def test_import_users_success(db_session: AsyncSession):
    """[test_bulk_operation_service-001] ユーザー一括インポートの成功ケース。"""
    # Arrange
    service = BulkOperationService(db_session)
    performer_id = uuid.uuid4()

    # ユーザーを作成（実行者）
    performer = UserAccount(
        id=performer_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"performer-{uuid.uuid4()}@example.com",
        display_name="Performer User",
    )
    db_session.add(performer)
    await db_session.commit()

    # CSV データ
    csv_content = """email,display_name
test1@example.com,Test User 1
test2@example.com,Test User 2
"""

    # Act
    result = await service.import_users(csv_content, performer_id)

    # Assert
    assert result.success is True
    assert result.imported_count == 2
    assert result.error_count == 0


@pytest.mark.asyncio
async def test_import_users_with_errors(db_session: AsyncSession):
    """[test_bulk_operation_service-002] ユーザー一括インポートのエラーケース。"""
    # Arrange
    service = BulkOperationService(db_session)
    performer_id = uuid.uuid4()

    # ユーザーを作成（実行者）
    performer = UserAccount(
        id=performer_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"performer-{uuid.uuid4()}@example.com",
        display_name="Performer User",
    )
    db_session.add(performer)
    await db_session.commit()

    # CSV データ（無効なデータを含む）
    csv_content = """email,display_name
,Invalid User
valid@example.com,Valid User
"""

    # Act
    result = await service.import_users(csv_content, performer_id)

    # Assert
    assert result.imported_count == 1
    assert result.error_count == 1
    assert result.errors is not None


@pytest.mark.asyncio
async def test_export_users_success(db_session: AsyncSession):
    """[test_bulk_operation_service-003] ユーザー一括エクスポートの成功ケース。"""
    # Arrange
    service = BulkOperationService(db_session)

    # ユーザーを作成
    for i in range(3):
        user = UserAccount(
            azure_oid=f"azure-oid-{uuid.uuid4()}",
            email=f"test-{i}-{uuid.uuid4()}@example.com",
            display_name=f"Test User {i}",
            is_active=True,
        )
        db_session.add(user)
    await db_session.commit()

    # Act
    csv_data = await service.export_users(is_active=True)

    # Assert
    assert csv_data is not None
    assert "id" in csv_data
    assert "email" in csv_data


@pytest.mark.asyncio
async def test_deactivate_inactive_users_dry_run(db_session: AsyncSession):
    """[test_bulk_operation_service-004] 非アクティブユーザー一括無効化のプレビュー。"""
    # Arrange
    service = BulkOperationService(db_session)
    user_id = uuid.uuid4()

    # 非アクティブなユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Inactive User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    result = await service.deactivate_inactive_users(
        inactive_days=90,
        dry_run=True,
    )

    # Assert
    assert result.success is True
    assert result.deactivated_count == 0  # Dry run なので0
    assert result.preview_items is not None


@pytest.mark.asyncio
async def test_deactivate_inactive_users_execute(db_session: AsyncSession):
    """[test_bulk_operation_service-005] 非アクティブユーザー一括無効化の実行。"""
    # Arrange
    service = BulkOperationService(db_session)
    user_id = uuid.uuid4()
    performer_id = uuid.uuid4()

    # 実行者を作成
    performer = UserAccount(
        id=performer_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"performer-{uuid.uuid4()}@example.com",
        display_name="Performer User",
    )
    db_session.add(performer)

    # 非アクティブなユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Inactive User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # 古いアクティビティを作成
    old_date = datetime.now(UTC) - timedelta(days=100)
    activity = UserActivity(
        user_id=user_id,
        action_type="LOGIN",
        endpoint="/api/v1/auth/login",
        method="POST",
        response_status=200,
        duration_ms=100,
        created_at=old_date,
    )
    db_session.add(activity)
    await db_session.commit()

    # Act
    result = await service.deactivate_inactive_users(
        inactive_days=90,
        dry_run=False,
        performed_by=performer_id,
    )

    # Assert
    assert result.success is True


@pytest.mark.asyncio
async def test_archive_inactive_projects_dry_run(db_session: AsyncSession):
    """[test_bulk_operation_service-006] 非アクティブプロジェクト一括アーカイブのプレビュー。"""
    # Arrange
    service = BulkOperationService(db_session)
    creator_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # 古いプロジェクトを作成
    old_date = datetime.now(UTC) - timedelta(days=100)
    project = Project(
        name="Old Project",
        code=f"OLD-{uuid.uuid4().hex[:6]}",
        created_by=creator_id,
        is_active=True,
        updated_at=old_date,
    )
    db_session.add(project)
    await db_session.commit()

    # Act
    result = await service.archive_inactive_projects(
        inactive_days=90,
        dry_run=True,
    )

    # Assert
    assert result.success is True
    assert result.archived_count == 0  # Dry run なので0
    assert result.preview_items is not None


@pytest.mark.asyncio
async def test_archive_inactive_projects_execute(db_session: AsyncSession):
    """[test_bulk_operation_service-007] 非アクティブプロジェクト一括アーカイブの実行。"""
    # Arrange
    service = BulkOperationService(db_session)
    creator_id = uuid.uuid4()
    performer_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=creator_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    performer = UserAccount(
        id=performer_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"performer-{uuid.uuid4()}@example.com",
        display_name="Performer User",
    )
    db_session.add(user)
    db_session.add(performer)

    # 古いプロジェクトを作成
    old_date = datetime.now(UTC) - timedelta(days=100)
    project = Project(
        name="Old Project",
        code=f"OLD-{uuid.uuid4().hex[:6]}",
        created_by=creator_id,
        is_active=True,
        updated_at=old_date,
    )
    db_session.add(project)
    await db_session.commit()

    # Act
    result = await service.archive_inactive_projects(
        inactive_days=90,
        dry_run=False,
        performed_by=performer_id,
    )

    # Assert
    assert result.success is True
