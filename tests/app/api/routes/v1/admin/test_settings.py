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


@pytest.fixture
async def seeded_settings(test_data_seeder):
    """システム設定のシードデータを作成。"""
    await test_data_seeder.seed_default_settings()
    return test_data_seeder


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


# ================================================================================
# GET /api/v1/admin/settings/{category} - カテゴリ別設定取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_settings_by_category_success(client: AsyncClient, override_auth, admin_user):
    """[test_settings-002] カテゴリ別設定取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/settings/GENERAL")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "settings" in data


# ================================================================================
# PATCH /api/v1/admin/settings/{category}/{key} - 設定更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_setting_success(client: AsyncClient, override_auth, admin_user, seeded_settings):
    """[test_settings-003] 設定更新の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    update_data = {"value": "NewAppName"}

    # Act
    response = await client.patch("/api/v1/admin/settings/GENERAL/app_name", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
    assert "value" in data
    assert "valueType" in data


# ================================================================================
# POST /api/v1/admin/settings/maintenance - メンテナンスモード有効化/無効化
# ================================================================================


@pytest.mark.parametrize(
    "endpoint,request_data,expected_keys",
    [
        (
            "/api/v1/admin/settings/maintenance/enable",
            {"enabled": True, "message": "システムメンテナンス中です", "allowAdminAccess": True},
            ["enabled", "message"],
        ),
        (
            "/api/v1/admin/settings/maintenance/disable",
            None,
            ["enabled"],
        ),
    ],
    ids=["enable", "disable"],
)
@pytest.mark.asyncio
async def test_maintenance_mode_toggle_success(
    client: AsyncClient, override_auth, admin_user, seeded_settings, endpoint, request_data, expected_keys
):
    """[test_settings-004-005] メンテナンスモード切り替えの成功ケース（有効化/無効化）。"""
    # Arrange
    override_auth(admin_user)

    # Act
    if request_data:
        response = await client.post(endpoint, json=request_data)
    else:
        response = await client.post(endpoint)

    # Assert
    assert response.status_code == 200
    data = response.json()
    for key in expected_keys:
        assert key in data
