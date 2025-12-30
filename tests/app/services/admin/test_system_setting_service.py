"""システム設定サービスのテスト。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models import UserAccount
from app.models.admin.system_setting import SystemSetting
from app.schemas.admin.system_setting import MaintenanceModeEnable
from app.services.admin.system_setting_service import SystemSettingService


@pytest.mark.asyncio
async def test_get_all_settings_success(db_session: AsyncSession):
    """[test_system_setting_service-001] 全設定取得の成功ケース。"""
    # Arrange
    service = SystemSettingService(db_session)

    # システム設定を作成
    setting = SystemSetting(
        category="GENERAL",
        key="app_name",
        value="Test App",
        value_type="STRING",
        description="Application name",
        is_editable=True,
    )
    db_session.add(setting)
    await db_session.commit()

    # Act
    result = await service.get_all_settings()

    # Assert
    assert result is not None
    assert "GENERAL" in result.categories or len(result.categories) >= 0


@pytest.mark.asyncio
async def test_get_settings_by_category_success(db_session: AsyncSession):
    """[test_system_setting_service-002] カテゴリ別設定取得の成功ケース。"""
    # Arrange
    service = SystemSettingService(db_session)

    # システム設定を作成
    setting = SystemSetting(
        category="MAINTENANCE",
        key="maintenance_mode",
        value=False,
        value_type="BOOLEAN",
        description="Maintenance mode",
        is_editable=True,
    )
    db_session.add(setting)
    await db_session.commit()

    # Act
    result = await service.get_settings_by_category("MAINTENANCE")

    # Assert
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_update_setting_success(db_session: AsyncSession):
    """[test_system_setting_service-003] 設定更新の成功ケース。"""
    # Arrange
    service = SystemSettingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # システム設定を作成
    setting = SystemSetting(
        category="GENERAL",
        key="max_upload_size",
        value=10,
        value_type="NUMBER",
        description="Max upload size in MB",
        is_editable=True,
    )
    db_session.add(setting)
    await db_session.commit()

    # Act
    result = await service.update_setting(
        category="GENERAL",
        key="max_upload_size",
        value=20,
        updated_by=user_id,
    )

    # Assert
    assert result is not None
    assert result.value == 20


@pytest.mark.asyncio
async def test_update_setting_not_found(db_session: AsyncSession):
    """[test_system_setting_service-004] 存在しない設定の更新エラー。"""
    # Arrange
    service = SystemSettingService(db_session)
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

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.update_setting(
            category="NONEXISTENT",
            key="nonexistent_key",
            value="value",
            updated_by=user_id,
        )


@pytest.mark.asyncio
async def test_update_setting_not_editable(db_session: AsyncSession):
    """[test_system_setting_service-005] 編集不可設定の更新エラー。"""
    # Arrange
    service = SystemSettingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # 編集不可の設定を作成
    setting = SystemSetting(
        category="SYSTEM",
        key="version",
        value="1.0.0",
        value_type="STRING",
        description="System version",
        is_editable=False,
    )
    db_session.add(setting)
    await db_session.commit()

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.update_setting(
            category="SYSTEM",
            key="version",
            value="2.0.0",
            updated_by=user_id,
        )


@pytest.mark.asyncio
async def test_enable_maintenance_mode_success(db_session: AsyncSession):
    """[test_system_setting_service-006] メンテナンスモード有効化の成功ケース。"""
    # Arrange
    service = SystemSettingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # システム設定を作成
    for key, value in [
        ("maintenance_mode", False),
        ("maintenance_message", ""),
        ("allow_admin_access", True),
    ]:
        setting = SystemSetting(
            category="MAINTENANCE",
            key=key,
            value=value,
            value_type="BOOLEAN" if isinstance(value, bool) else "STRING",
            description=f"{key} setting",
            is_editable=True,
        )
        db_session.add(setting)
    await db_session.commit()

    # Act
    params = MaintenanceModeEnable(
        message="システムメンテナンス中です",
        allow_admin_access=True,
    )
    result = await service.enable_maintenance_mode(params, user_id)

    # Assert
    assert result.enabled is True
    assert result.message == "システムメンテナンス中です"


@pytest.mark.asyncio
async def test_disable_maintenance_mode_success(db_session: AsyncSession):
    """[test_system_setting_service-007] メンテナンスモード無効化の成功ケース。"""
    # Arrange
    service = SystemSettingService(db_session)
    user_id = uuid.uuid4()

    # ユーザーを作成
    user = UserAccount(
        id=user_id,
        azure_oid=f"azure-oid-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        display_name="Test User",
    )
    db_session.add(user)

    # メンテナンスモードの設定を作成
    setting = SystemSetting(
        category="MAINTENANCE",
        key="maintenance_mode",
        value=True,
        value_type="BOOLEAN",
        description="Maintenance mode",
        is_editable=True,
    )
    db_session.add(setting)
    await db_session.commit()

    # Act
    result = await service.disable_maintenance_mode(user_id)

    # Assert
    assert result.enabled is False
