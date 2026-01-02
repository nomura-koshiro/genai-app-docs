"""データ管理サービスのテスト。"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserAccount
from app.models.audit.audit_log import AuditLog
from app.models.audit.user_activity import UserActivity
from app.models.system.system_setting import SystemSetting
from app.schemas.admin.data_management import RetentionPolicyUpdate
from app.services.admin.data_management_service import DataManagementService


@pytest.mark.parametrize(
    "target_types,expected_preview_count",
    [
        (["ACTIVITY_LOGS"], 1),
        (["ACTIVITY_LOGS", "AUDIT_LOGS"], 2),
    ],
    ids=["single_type", "multiple_types"],
)
@pytest.mark.asyncio
async def test_preview_cleanup_success(
    db_session: AsyncSession,
    target_types: list[str],
    expected_preview_count: int,
):
    """[test_data_management_service-001-005] クリーンアッププレビューの成功ケース。"""
    # Arrange
    service = DataManagementService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # 古い操作履歴を作成
    old_date = datetime.now(UTC) - timedelta(days=100)
    activity = UserActivity(
        user_id=user_id,
        action_type="READ",
        endpoint="/api/v1/test",
        method="GET",
        response_status=200,
        duration_ms=100,
        created_at=old_date,
    )
    db_session.add(activity)

    # 複数種別テストの場合は監査ログも作成
    if "AUDIT_LOGS" in target_types:
        audit_log = AuditLog(
            user_id=user_id,
            event_type="ACCESS",
            action="LOGIN",
            resource_type="Auth",
            severity="INFO",
            created_at=old_date,
        )
        db_session.add(audit_log)

    await db_session.commit()

    # Act
    result = await service.preview_cleanup(
        target_types=target_types,
        retention_days=90,
    )

    # Assert
    assert result is not None
    assert len(result.preview) >= expected_preview_count
    assert result.total_record_count >= 1


@pytest.mark.asyncio
async def test_execute_cleanup_success(db_session: AsyncSession):
    """[test_data_management_service-002] クリーンアップ実行の成功ケース。"""
    # Arrange
    service = DataManagementService(db_session)
    user_id = uuid.uuid4()
    performer_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
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

    # 古い操作履歴を作成
    old_date = datetime.now(UTC) - timedelta(days=100)
    activity = UserActivity(
        user_id=user_id,
        action_type="READ",
        endpoint="/api/v1/test",
        method="GET",
        response_status=200,
        duration_ms=100,
        created_at=old_date,
    )
    db_session.add(activity)
    await db_session.commit()

    # Act
    result = await service.execute_cleanup(
        target_types=["ACTIVITY_LOGS"],
        retention_days=90,
        performed_by=performer_id,
    )

    # Assert
    assert result is not None
    assert result.success is True


@pytest.mark.asyncio
async def test_get_retention_policy_success(db_session: AsyncSession):
    """[test_data_management_service-003] 保持ポリシー取得の成功ケース。"""
    # Arrange
    service = DataManagementService(db_session)

    # 保持ポリシー設定を作成
    settings = [
        ("RETENTION", "activity_logs_days", 90),
        ("RETENTION", "audit_logs_days", 365),
        ("RETENTION", "deleted_projects_days", 30),
        ("RETENTION", "session_logs_days", 30),
    ]
    for category, key, value in settings:
        setting = SystemSetting(
            category=category,
            key=key,
            value=value,
            value_type="NUMBER",
            description=f"{key} setting",
            is_editable=True,
        )
        db_session.add(setting)
    await db_session.commit()

    # Act
    result = await service.get_retention_policy()

    # Assert
    assert result is not None
    assert result.activity_logs_days == 90
    assert result.audit_logs_days == 365


@pytest.mark.asyncio
async def test_update_retention_policy_success(db_session: AsyncSession):
    """[test_data_management_service-004] 保持ポリシー更新の成功ケース。"""
    # Arrange
    service = DataManagementService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # 保持ポリシー設定を作成
    setting = SystemSetting(
        category="RETENTION",
        key="activity_logs_days",
        value=90,
        value_type="NUMBER",
        description="Activity logs retention days",
        is_editable=True,
    )
    db_session.add(setting)
    await db_session.commit()

    # Act
    policy = RetentionPolicyUpdate(activity_logs_days=120)
    result = await service.update_retention_policy(policy, user_id)

    # Assert
    assert result is not None
    assert result.activity_logs_days == 120


@pytest.mark.asyncio
async def test_format_bytes(db_session: AsyncSession):
    """[test_data_management_service-006] バイト数フォーマット。"""
    # Arrange
    service = DataManagementService(db_session)

    # Act & Assert
    assert service._format_bytes(500) == "500.0 B"
    assert service._format_bytes(1024) == "1.0 KB"
    assert service._format_bytes(1024 * 1024) == "1.0 MB"
    assert service._format_bytes(1024 * 1024 * 1024) == "1.0 GB"
