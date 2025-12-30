"""サポートツールサービスのテスト。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import UserAccount
from app.models.admin.system_setting import SystemSetting
from app.services.admin.support_tools_service import SupportToolsService


@pytest.mark.asyncio
async def test_start_impersonation_success(db_session: AsyncSession):
    """[test_support_tools_service-001] ユーザー代行開始の成功ケース。"""
    # Arrange
    service = SupportToolsService(db_session)
    target_user_id = uuid.uuid4()
    admin_user_id = uuid.uuid4()

    # ユーザーを作成
    target_user = UserAccount(
        id=target_user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"target-{uuid.uuid4()}@example.com",
        display_name="Target User",
    )
    admin_user = UserAccount(
        id=admin_user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"admin-{uuid.uuid4()}@example.com",
        display_name="Admin User",
    )
    db_session.add(target_user)
    db_session.add(admin_user)
    await db_session.commit()

    # Act
    result = await service.start_impersonation(
        target_user_id=target_user_id,
        reason="Customer support",
        admin_user_id=admin_user_id,
    )

    # Assert
    assert result is not None
    assert result.impersonation_token is not None
    assert result.target_user.id == target_user_id


@pytest.mark.asyncio
async def test_start_impersonation_user_not_found(db_session: AsyncSession):
    """[test_support_tools_service-002] 存在しないユーザーの代行開始エラー。"""
    # Arrange
    service = SupportToolsService(db_session)
    nonexistent_user_id = uuid.uuid4()
    admin_user_id = uuid.uuid4()

    # 管理者を作成
    admin_user = UserAccount(
        id=admin_user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"admin-{uuid.uuid4()}@example.com",
        display_name="Admin User",
    )
    db_session.add(admin_user)
    await db_session.commit()

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.start_impersonation(
            target_user_id=nonexistent_user_id,
            reason="Test",
            admin_user_id=admin_user_id,
        )


@pytest.mark.asyncio
async def test_end_impersonation_success(db_session: AsyncSession):
    """[test_support_tools_service-003] ユーザー代行終了の成功ケース。"""
    # Arrange
    service = SupportToolsService(db_session)
    admin_user_id = uuid.uuid4()

    # 管理者を作成
    admin_user = UserAccount(
        id=admin_user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"admin-{uuid.uuid4()}@example.com",
        display_name="Admin User",
    )
    db_session.add(admin_user)
    await db_session.commit()

    # Act
    result = await service.end_impersonation(
        token="test_token",
        admin_user_id=admin_user_id,
    )

    # Assert
    assert result is not None
    assert result.success is True


@pytest.mark.asyncio
async def test_enable_debug_mode_success(db_session: AsyncSession):
    """[test_support_tools_service-004] デバッグモード有効化の成功ケース。"""
    # Arrange
    service = SupportToolsService(db_session)
    admin_user_id = uuid.uuid4()

    # 管理者を作成
    admin_user = UserAccount(
        id=admin_user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"admin-{uuid.uuid4()}@example.com",
        display_name="Admin User",
    )
    db_session.add(admin_user)

    # デバッグモード設定を作成
    setting = SystemSetting(
        category="DEBUG",
        key="debug_mode",
        value=False,
        value_type="BOOLEAN",
        description="Debug mode",
        is_editable=True,
    )
    db_session.add(setting)
    await db_session.commit()

    # Act
    result = await service.enable_debug_mode(admin_user_id)

    # Assert
    assert result is not None
    assert result.enabled is True


@pytest.mark.asyncio
async def test_disable_debug_mode_success(db_session: AsyncSession):
    """[test_support_tools_service-005] デバッグモード無効化の成功ケース。"""
    # Arrange
    service = SupportToolsService(db_session)
    admin_user_id = uuid.uuid4()

    # 管理者を作成
    admin_user = UserAccount(
        id=admin_user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"admin-{uuid.uuid4()}@example.com",
        display_name="Admin User",
    )
    db_session.add(admin_user)

    # デバッグモード設定を作成
    setting = SystemSetting(
        category="DEBUG",
        key="debug_mode",
        value=True,
        value_type="BOOLEAN",
        description="Debug mode",
        is_editable=True,
    )
    db_session.add(setting)
    await db_session.commit()

    # Act
    result = await service.disable_debug_mode(admin_user_id)

    # Assert
    assert result is not None
    assert result.enabled is False


@pytest.mark.asyncio
async def test_simple_health_check_success(db_session: AsyncSession):
    """[test_support_tools_service-006] 簡易ヘルスチェックの成功ケース。"""
    # Arrange
    service = SupportToolsService(db_session)

    # Act
    result = await service.simple_health_check()

    # Assert
    assert result is not None
    assert result.status in ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_detailed_health_check_success(db_session: AsyncSession):
    """[test_support_tools_service-007] 詳細ヘルスチェックの成功ケース。"""
    # Arrange
    service = SupportToolsService(db_session)

    # Act
    result = await service.detailed_health_check()

    # Assert
    assert result is not None
    assert result.status in ["healthy", "degraded", "unhealthy"]
    assert len(result.components) >= 1


@pytest.mark.asyncio
async def test_check_database_health(db_session: AsyncSession):
    """[test_support_tools_service-008] データベースヘルスチェック。"""
    # Arrange
    service = SupportToolsService(db_session)

    # Act
    result = await service._check_database()

    # Assert
    assert result is not None
    assert result.name == "database"
    assert result.status in ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_check_redis_health(db_session: AsyncSession):
    """[test_support_tools_service-009] Redisヘルスチェック。"""
    # Arrange
    service = SupportToolsService(db_session)

    # Act
    result = await service._check_redis()

    # Assert
    assert result is not None
    assert result.name == "redis"
    assert result.status in ["healthy", "unhealthy"]
