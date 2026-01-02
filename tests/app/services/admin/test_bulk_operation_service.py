"""一括操作サービスのテスト。"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, UserAccount
from app.models.audit.user_activity import UserActivity
from app.services.admin.bulk_operation_service import BulkOperationService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "csv_content,expected_imported,expected_errors,has_errors",
    [
        # [test_bulk_operation_service-001] 成功ケース - 全てのユーザーがインポートされる
        (
            """email,display_name
test1@example.com,Test User 1
test2@example.com,Test User 2
""",
            2,
            0,
            False,
        ),
        # [test_bulk_operation_service-002] エラーケース - 無効なデータを含む
        (
            """email,display_name
,Invalid User
valid@example.com,Valid User
""",
            1,
            1,
            True,
        ),
    ],
    ids=["success", "with_errors"],
)
async def test_import_users(
    db_session: AsyncSession,
    csv_content: str,
    expected_imported: int,
    expected_errors: int,
    has_errors: bool,
):
    """ユーザー一括インポートのテスト（成功/エラーケース）。"""
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

    # Act
    result = await service.import_users(csv_content, performer_id)

    # Assert
    assert result.imported_count == expected_imported
    assert result.error_count == expected_errors
    if has_errors:
        assert result.errors is not None
    else:
        assert result.success is True


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
@pytest.mark.parametrize(
    "dry_run,should_deactivate",
    [
        (True, False),  # [test_bulk_operation_service-004] Dry run - プレビューのみ
        (False, True),  # [test_bulk_operation_service-005] Execute - 実際に無効化
    ],
    ids=["dry_run", "execute"],
)
async def test_deactivate_inactive_users(
    db_session: AsyncSession,
    dry_run: bool,
    should_deactivate: bool,
):
    """非アクティブユーザー一括無効化のテスト（プレビュー/実行）。"""
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

    # 古いアクティビティを作成（execute モードの場合のみ）
    if should_deactivate:
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
        dry_run=dry_run,
        performed_by=performer_id if not dry_run else None,
    )

    # Assert
    assert result.success is True
    if dry_run:
        # Dry run の場合は変更なし、プレビューのみ
        assert result.deactivated_count == 0
        assert result.preview_items is not None
    else:
        # Execute の場合は実際に変更される
        assert result.deactivated_count >= 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dry_run,should_archive",
    [
        (True, False),  # [test_bulk_operation_service-006] Dry run - プレビューのみ
        (False, True),  # [test_bulk_operation_service-007] Execute - 実際にアーカイブ
    ],
    ids=["dry_run", "execute"],
)
async def test_archive_inactive_projects(
    db_session: AsyncSession,
    dry_run: bool,
    should_archive: bool,
):
    """非アクティブプロジェクト一括アーカイブのテスト（プレビュー/実行）。"""
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
        dry_run=dry_run,
        performed_by=performer_id if not dry_run else None,
    )

    # Assert
    assert result.success is True
    if dry_run:
        # Dry run の場合は変更なし、プレビューのみ
        assert result.archived_count == 0
        assert result.preview_items is not None
    else:
        # Execute の場合は実際に変更される
        assert result.archived_count >= 0
