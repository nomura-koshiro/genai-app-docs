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
@pytest.mark.parametrize(
    "service_method,event_type,action,extra_kwargs,assertions",
    [
        (
            "record_data_change",
            AuditEventType.DATA_CHANGE,
            "UPDATE",
            {
                "resource_type": "Project",
                "old_value": {"name": "Old Name"},
                "new_value": {"name": "New Name"},
                "changed_fields": ["name"],
                "ip_address": "127.0.0.1",
                "severity": AuditSeverity.INFO.value,
            },
            {"changed_fields": ["name"]},
        ),
        (
            "record_access",
            AuditEventType.ACCESS,
            "LOGIN_SUCCESS",
            {
                "resource_type": "Auth",
                "ip_address": "127.0.0.1",
                "metadata": {"method": "password"},
            },
            {},
        ),
        (
            "record_security_event",
            AuditEventType.SECURITY,
            "SUSPICIOUS_ACTIVITY",
            {
                "resource_type": "Auth",
                "severity": AuditSeverity.WARNING.value,
                "metadata": {"reason": "Multiple failed login attempts"},
            },
            {"severity": AuditSeverity.WARNING.value},
        ),
    ],
    ids=["data_change", "access", "security"],
)
async def test_record_event_success(
    db_session: AsyncSession,
    service_method: str,
    event_type: AuditEventType,
    action: str,
    extra_kwargs: dict,
    assertions: dict,
):
    """[test_audit_log_service-001~003] 監査イベント記録の成功ケース (parametrized)。"""
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

    # resource_idが必要な場合は追加
    kwargs = extra_kwargs.copy()
    if service_method == "record_data_change":
        kwargs["resource_id"] = uuid.uuid4()

    # Act
    method = getattr(service, service_method)
    await method(user_id=user_id, action=action, **kwargs)

    # Assert
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.event_type == event_type.value,
        )
    )
    log = result.scalar_one_or_none()
    assert log is not None
    assert log.event_type == event_type.value
    assert log.action == action

    # 追加のアサーション
    for key, value in assertions.items():
        assert getattr(log, key) == value


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
@pytest.mark.parametrize(
    "format,expected_content",
    [
        ("csv", ["ID", "イベント種別"]),
        ("json", ["["]),  # JSON配列形式
    ],
    ids=["csv", "json"],
)
async def test_export_audit_logs(
    db_session: AsyncSession,
    format: str,
    expected_content: list[str],
):
    """[test_audit_log_service-006~007] 監査ログエクスポートの成功ケース (parametrized)。"""
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
    filter_params = AuditLogExportFilter(format=format)
    export_data = await service.export(filter_params)

    # Assert
    assert export_data is not None
    for content in expected_content:
        assert content in export_data
