"""セッション管理サービスのテスト。"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import UserAccount
from app.models.admin.user_session import UserSession
from app.schemas.admin.session_management import SessionFilter
from app.services.admin.session_management_service import SessionManagementService


@pytest.mark.asyncio
async def test_list_sessions_success(db_session: AsyncSession):
    """[test_session_management_service-001] セッション一覧取得の成功ケース。"""
    # Arrange
    service = SessionManagementService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # セッションを作成
    session = UserSession(
        user_id=user_id,
        session_token_hash="test_hash",
        login_at=datetime.now(UTC),
        last_activity_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        is_active=True,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
    )
    db_session.add(session)
    await db_session.commit()

    # Act
    filter_params = SessionFilter(page=1, limit=10)
    result = await service.list_sessions(filter_params)

    # Assert
    assert result is not None
    assert len(result.items) >= 1


@pytest.mark.asyncio
async def test_list_user_sessions_success(db_session: AsyncSession):
    """[test_session_management_service-002] ユーザーのセッション一覧取得。"""
    # Arrange
    service = SessionManagementService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # 複数のセッションを作成
    for i in range(2):
        session = UserSession(
            user_id=user_id,
            session_token_hash=f"test_hash_{i}",
            login_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            is_active=True,
            ip_address=f"127.0.0.{i}",
            user_agent="TestAgent/1.0",
        )
        db_session.add(session)
    await db_session.commit()

    # Act
    result = await service.list_user_sessions(user_id)

    # Assert
    assert len(result) >= 2


@pytest.mark.asyncio
async def test_terminate_session_success(db_session: AsyncSession):
    """[test_session_management_service-003] セッション終了の成功ケース。"""
    # Arrange
    service = SessionManagementService(db_session)
    user_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    admin = UserAccount(
        id=admin_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"admin-{uuid.uuid4()}@example.com",
        display_name="Admin User",
    )
    db_session.add(user)
    db_session.add(admin)

    # セッションを作成
    session = UserSession(
        user_id=user_id,
        session_token_hash="test_hash",
        login_at=datetime.now(UTC),
        last_activity_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        is_active=True,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
    )
    db_session.add(session)
    await db_session.commit()
    session_id = session.id

    # Act
    result = await service.terminate_session(
        session_id=session_id,
        reason="Test termination",
        terminated_by=admin_id,
    )

    # Assert
    assert result is not None
    assert result.is_active is False


@pytest.mark.asyncio
async def test_terminate_session_not_found(db_session: AsyncSession):
    """[test_session_management_service-004] 存在しないセッション終了のエラー。"""
    # Arrange
    service = SessionManagementService(db_session)
    admin_id = uuid.uuid4()
    nonexistent_id = uuid.uuid4()

    # 管理者を作成
    admin = UserAccount(
        id=admin_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"admin-{uuid.uuid4()}@example.com",
        display_name="Admin User",
    )
    db_session.add(admin)
    await db_session.commit()

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.terminate_session(
            session_id=nonexistent_id,
            reason="Test termination",
            terminated_by=admin_id,
        )


@pytest.mark.asyncio
async def test_terminate_all_user_sessions_success(db_session: AsyncSession):
    """[test_session_management_service-005] ユーザーの全セッション終了。"""
    # Arrange
    service = SessionManagementService(db_session)
    user_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    admin = UserAccount(
        id=admin_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"admin-{uuid.uuid4()}@example.com",
        display_name="Admin User",
    )
    db_session.add(user)
    db_session.add(admin)

    # 複数のセッションを作成
    for i in range(3):
        session = UserSession(
            user_id=user_id,
            session_token_hash=f"test_hash_{i}",
            login_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            is_active=True,
            ip_address=f"127.0.0.{i}",
            user_agent="TestAgent/1.0",
        )
        db_session.add(session)
    await db_session.commit()

    # Act
    count = await service.terminate_all_user_sessions(
        user_id=user_id,
        reason="Test termination",
        terminated_by=admin_id,
    )

    # Assert
    assert count >= 3


@pytest.mark.asyncio
async def test_list_sessions_with_filter(db_session: AsyncSession):
    """[test_session_management_service-006] フィルタ付きセッション一覧取得。"""
    # Arrange
    service = SessionManagementService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # セッションを作成
    session = UserSession(
        user_id=user_id,
        session_token_hash="test_hash",
        login_at=datetime.now(UTC),
        last_activity_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        is_active=True,
        ip_address="192.168.1.1",
        user_agent="TestAgent/1.0",
    )
    db_session.add(session)
    await db_session.commit()

    # Act
    filter_params = SessionFilter(
        user_id=user_id,
        ip_address="192.168.1.1",
        page=1,
        limit=10,
    )
    result = await service.list_sessions(filter_params)

    # Assert
    assert result is not None
    assert all(item.ip_address == "192.168.1.1" for item in result.items)
