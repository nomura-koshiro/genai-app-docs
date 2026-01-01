"""監査ログサービスのテスト。"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserAccount
from app.models.audit.audit_log import AuditLog
from app.models.enums.admin_enums import AuditEventType, AuditSeverity
from app.schemas.admin.audit_log import AuditLogExportFilter, AuditLogFilter
from app.services.admin.audit_log_service import AuditLogService


@pytest.mark.asyncio
async def test_record_data_change_success(db_session: AsyncSession):
    """[test_audit_log_service-001] データ変更記録の成功ケース。"""
    # Arrange
    service = AuditLogService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    await service.record_data_change(
        user_id=user_id,
        action="UPDATE",
        resource_type="Project",
        resource_id=uuid.uuid4(),
        old_value={"name": "Old Name"},
        new_value={"name": "New Name"},
        changed_fields=["name"],
        ip_address="127.0.0.1",
        severity=AuditSeverity.INFO.value,
    )

    # Assert
    result = await db_session.execute(select(AuditLog).where(AuditLog.user_id == user_id))
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.event_type == AuditEventType.DATA_CHANGE.value
    assert log.action == "UPDATE"
    assert log.changed_fields == ["name"]


@pytest.mark.asyncio
async def test_record_access_success(db_session: AsyncSession):
    """[test_audit_log_service-002] アクセス記録の成功ケース。"""
    # Arrange
    service = AuditLogService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    await service.record_access(
        user_id=user_id,
        action="LOGIN_SUCCESS",
        resource_type="Auth",
        ip_address="127.0.0.1",
        metadata={"method": "password"},
    )

    # Assert
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.event_type == AuditEventType.ACCESS.value,
        )
    )
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.action == "LOGIN_SUCCESS"


@pytest.mark.asyncio
async def test_record_security_event_success(db_session: AsyncSession):
    """[test_audit_log_service-003] セキュリティイベント記録の成功ケース。"""
    # Arrange
    service = AuditLogService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    await service.record_security_event(
        user_id=user_id,
        action="SUSPICIOUS_ACTIVITY",
        resource_type="Auth",
        severity=AuditSeverity.WARNING.value,
        metadata={"reason": "Multiple failed login attempts"},
    )

    # Assert
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.event_type == AuditEventType.SECURITY.value,
        )
    )
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.severity == AuditSeverity.WARNING.value


@pytest.mark.asyncio
async def test_list_audit_logs_success(db_session: AsyncSession):
    """[test_audit_log_service-004] 監査ログ一覧取得の成功ケース。"""
    # Arrange
    service = AuditLogService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # 監査ログを作成
    for _ in range(3):
        await service.record_data_change(
            user_id=user_id,
            action="UPDATE",
            resource_type="Project",
            resource_id=uuid.uuid4(),
            old_value={},
            new_value={},
            changed_fields=[],
        )

    # Act
    filter_params = AuditLogFilter(page=1, limit=10)
    result = await service.list_audit_logs(filter_params)

    # Assert
    assert result.total >= 3
    assert len(result.items) >= 3


@pytest.mark.asyncio
async def test_list_by_event_type_success(db_session: AsyncSession):
    """[test_audit_log_service-005] イベント種別でのログ取得。"""
    # Arrange
    service = AuditLogService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # データ変更とアクセスログを作成
    await service.record_data_change(
        user_id=user_id,
        action="CREATE",
        resource_type="Project",
        resource_id=uuid.uuid4(),
        old_value=None,
        new_value={"name": "Test"},
        changed_fields=["name"],
    )
    await service.record_access(
        user_id=user_id,
        action="LOGIN_SUCCESS",
        resource_type="Auth",
    )

    # Act
    filter_params = AuditLogFilter(page=1, limit=10)
    result = await service.list_by_event_type(
        AuditEventType.DATA_CHANGE.value,
        filter_params,
    )

    # Assert
    assert all(item.event_type == AuditEventType.DATA_CHANGE.value for item in result.items)


@pytest.mark.asyncio
async def test_export_csv_success(db_session: AsyncSession):
    """[test_audit_log_service-006] CSV エクスポートの成功ケース。"""
    # Arrange
    service = AuditLogService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # 監査ログを作成
    await service.record_data_change(
        user_id=user_id,
        action="CREATE",
        resource_type="Project",
        resource_id=uuid.uuid4(),
        old_value=None,
        new_value={"name": "Test"},
        changed_fields=["name"],
    )

    # Act
    filter_params = AuditLogExportFilter(format="csv")
    csv_data = await service.export(filter_params)

    # Assert
    assert csv_data is not None
    assert "ID" in csv_data
    assert "イベント種別" in csv_data


@pytest.mark.asyncio
async def test_export_json_success(db_session: AsyncSession):
    """[test_audit_log_service-007] JSON エクスポートの成功ケース。"""
    # Arrange
    service = AuditLogService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    # 監査ログを作成
    await service.record_data_change(
        user_id=user_id,
        action="CREATE",
        resource_type="Project",
        resource_id=uuid.uuid4(),
        old_value=None,
        new_value={"name": "Test"},
        changed_fields=["name"],
    )

    # Act
    filter_params = AuditLogExportFilter(format="json")
    json_data = await service.export(filter_params)

    # Assert
    assert json_data is not None
    assert "[" in json_data  # JSON 配列形式
