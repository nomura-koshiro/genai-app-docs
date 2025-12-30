"""システム設定管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/settings - 全設定取得
    - GET /api/v1/admin/settings/{category} - カテゴリ別設定取得
    - PATCH /api/v1/admin/settings/{category}/{key} - 設定更新
    - POST /api/v1/admin/settings/maintenance/enable - メンテナンスモード有効化
    - POST /api/v1/admin/settings/maintenance/disable - メンテナンスモード無効化
"""

import pytest
from httpx import AsyncClient


# ================================================================================
# GET /api/v1/admin/settings - 全設定取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_all_settings_success(client: AsyncClient, override_auth, admin_user):
    """[test_settings-001] 全設定取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/settings")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data


@pytest.mark.asyncio
async def test_get_all_settings_unauthorized(client: AsyncClient):
    """[test_settings-002] 認証なしでの全設定取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/settings")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_all_settings_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_settings-003] 一般ユーザーでの全設定取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/settings")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/settings/{category} - カテゴリ別設定取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_settings_by_category_success(client: AsyncClient, override_auth, admin_user):
    """[test_settings-004] カテゴリ別設定取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/settings/GENERAL")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "settings" in data


@pytest.mark.asyncio
async def test_get_settings_by_category_unauthorized(client: AsyncClient):
    """[test_settings-005] 認証なしでのカテゴリ別設定取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/settings/GENERAL")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_settings_by_category_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_settings-006] 一般ユーザーでのカテゴリ別設定取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/settings/GENERAL")

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /api/v1/admin/settings/{category}/{key} - 設定更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_setting_success(client: AsyncClient, override_auth, admin_user):
    """[test_settings-007] 設定更新の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    update_data = {"value": "new_value"}

    # Act
    response = await client.patch("/api/v1/admin/settings/GENERAL/site_name", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "key" in data
    assert "value" in data


@pytest.mark.asyncio
async def test_update_setting_unauthorized(client: AsyncClient):
    """[test_settings-008] 認証なしでの設定更新拒否。"""
    # Arrange
    update_data = {"value": "new_value"}

    # Act
    response = await client.patch("/api/v1/admin/settings/GENERAL/site_name", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_setting_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_settings-009] 一般ユーザーでの設定更新拒否。"""
    # Arrange
    override_auth(regular_user)
    update_data = {"value": "new_value"}

    # Act
    response = await client.patch("/api/v1/admin/settings/GENERAL/site_name", json=update_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/settings/maintenance/enable - メンテナンスモード有効化
# ================================================================================


@pytest.mark.asyncio
async def test_enable_maintenance_mode_success(client: AsyncClient, override_auth, admin_user):
    """[test_settings-010] メンテナンスモード有効化の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    request_data = {
        "message": "システムメンテナンス中です",
        "allow_admin_access": True,
    }

    # Act
    response = await client.post("/api/v1/admin/settings/maintenance/enable", json=request_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "is_enabled" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_enable_maintenance_mode_unauthorized(client: AsyncClient):
    """[test_settings-011] 認証なしでのメンテナンスモード有効化拒否。"""
    # Arrange
    request_data = {
        "message": "システムメンテナンス中です",
        "allow_admin_access": True,
    }

    # Act
    response = await client.post("/api/v1/admin/settings/maintenance/enable", json=request_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_enable_maintenance_mode_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_settings-012] 一般ユーザーでのメンテナンスモード有効化拒否。"""
    # Arrange
    override_auth(regular_user)
    request_data = {
        "message": "システムメンテナンス中です",
        "allow_admin_access": True,
    }

    # Act
    response = await client.post("/api/v1/admin/settings/maintenance/enable", json=request_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/settings/maintenance/disable - メンテナンスモード無効化
# ================================================================================


@pytest.mark.asyncio
async def test_disable_maintenance_mode_success(client: AsyncClient, override_auth, admin_user):
    """[test_settings-013] メンテナンスモード無効化の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.post("/api/v1/admin/settings/maintenance/disable")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "is_enabled" in data


@pytest.mark.asyncio
async def test_disable_maintenance_mode_unauthorized(client: AsyncClient):
    """[test_settings-014] 認証なしでのメンテナンスモード無効化拒否。"""
    # Act
    response = await client.post("/api/v1/admin/settings/maintenance/disable")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_disable_maintenance_mode_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_settings-015] 一般ユーザーでのメンテナンスモード無効化拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.post("/api/v1/admin/settings/maintenance/disable")

    # Assert
    assert response.status_code == 403
