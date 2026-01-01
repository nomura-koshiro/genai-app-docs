"""サポートツールAPIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - POST /api/v1/admin/impersonate/{user_id} - ユーザー代行操作開始
    - POST /api/v1/admin/impersonate/end - ユーザー代行操作終了
    - POST /api/v1/admin/debug/enable - デバッグモード有効化
    - POST /api/v1/admin/debug/disable - デバッグモード無効化
    - GET /api/v1/admin/health-check - 簡易ヘルスチェック
    - GET /api/v1/admin/health-check/detailed - 詳細ヘルスチェック
"""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def seeded_settings(test_data_seeder):
    """システム設定のシードデータを作成。"""
    await test_data_seeder.seed_default_settings()
    return test_data_seeder


# ================================================================================
# Debug Mode - デバッグモード
# ================================================================================


@pytest.mark.asyncio
async def test_enable_debug_mode_success(client: AsyncClient, override_auth, admin_user, seeded_settings):
    """[test_support_tools-001] デバッグモード有効化の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.post("/api/v1/admin/debug/enable")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data


@pytest.mark.asyncio
async def test_disable_debug_mode_success(client: AsyncClient, override_auth, admin_user, seeded_settings):
    """[test_support_tools-002] デバッグモード無効化の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.post("/api/v1/admin/debug/disable")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data


# ================================================================================
# Health Check - ヘルスチェック
# ================================================================================


@pytest.mark.asyncio
async def test_health_check_success(client: AsyncClient, override_auth, admin_user):
    """[test_support_tools-003] 簡易ヘルスチェックの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/health-check")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_detailed_health_check_success(client: AsyncClient, override_auth, admin_user):
    """[test_support_tools-004] 詳細ヘルスチェックの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/health-check/detailed")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
