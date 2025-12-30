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

import uuid

import pytest
from httpx import AsyncClient


# ================================================================================
# Impersonation - ユーザー代行操作
# ================================================================================


@pytest.mark.asyncio
async def test_start_impersonation_unauthorized(client: AsyncClient):
    """[test_support_tools-001] 認証なしでの代行操作開始拒否。"""
    # Arrange
    user_id = str(uuid.uuid4())
    request_data = {"reason": "サポート対応"}

    # Act
    response = await client.post(f"/api/v1/admin/impersonate/{user_id}", json=request_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_start_impersonation_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_support_tools-002] 一般ユーザーでの代行操作開始拒否。"""
    # Arrange
    override_auth(regular_user)
    user_id = str(uuid.uuid4())
    request_data = {"reason": "サポート対応"}

    # Act
    response = await client.post(f"/api/v1/admin/impersonate/{user_id}", json=request_data)

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_start_impersonation_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_support_tools-003] 存在しないユーザーの代行操作開始。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_user_id = str(uuid.uuid4())
    request_data = {"reason": "サポート対応"}

    # Act
    response = await client.post(f"/api/v1/admin/impersonate/{nonexistent_user_id}", json=request_data)

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_end_impersonation_unauthorized(client: AsyncClient):
    """[test_support_tools-004] 認証なしでの代行操作終了拒否。"""
    # Act
    response = await client.post("/api/v1/admin/impersonate/end")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_end_impersonation_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_support_tools-005] 一般ユーザーでの代行操作終了拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.post("/api/v1/admin/impersonate/end")

    # Assert
    assert response.status_code == 403


# ================================================================================
# Debug Mode - デバッグモード
# ================================================================================


@pytest.mark.asyncio
async def test_enable_debug_mode_success(client: AsyncClient, override_auth, admin_user):
    """[test_support_tools-006] デバッグモード有効化の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.post("/api/v1/admin/debug/enable")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "is_enabled" in data


@pytest.mark.asyncio
async def test_enable_debug_mode_unauthorized(client: AsyncClient):
    """[test_support_tools-007] 認証なしでのデバッグモード有効化拒否。"""
    # Act
    response = await client.post("/api/v1/admin/debug/enable")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_enable_debug_mode_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_support_tools-008] 一般ユーザーでのデバッグモード有効化拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.post("/api/v1/admin/debug/enable")

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_disable_debug_mode_success(client: AsyncClient, override_auth, admin_user):
    """[test_support_tools-009] デバッグモード無効化の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.post("/api/v1/admin/debug/disable")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "is_enabled" in data


@pytest.mark.asyncio
async def test_disable_debug_mode_unauthorized(client: AsyncClient):
    """[test_support_tools-010] 認証なしでのデバッグモード無効化拒否。"""
    # Act
    response = await client.post("/api/v1/admin/debug/disable")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_disable_debug_mode_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_support_tools-011] 一般ユーザーでのデバッグモード無効化拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.post("/api/v1/admin/debug/disable")

    # Assert
    assert response.status_code == 403


# ================================================================================
# Health Check - ヘルスチェック
# ================================================================================


@pytest.mark.asyncio
async def test_health_check_success(client: AsyncClient, override_auth, admin_user):
    """[test_support_tools-012] 簡易ヘルスチェックの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/health-check")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_health_check_unauthorized(client: AsyncClient):
    """[test_support_tools-013] 認証なしでのヘルスチェック拒否。"""
    # Act
    response = await client.get("/api/v1/admin/health-check")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_health_check_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_support_tools-014] 一般ユーザーでのヘルスチェック拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/health-check")

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_detailed_health_check_success(client: AsyncClient, override_auth, admin_user):
    """[test_support_tools-015] 詳細ヘルスチェックの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/health-check/detailed")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data


@pytest.mark.asyncio
async def test_detailed_health_check_unauthorized(client: AsyncClient):
    """[test_support_tools-016] 認証なしでの詳細ヘルスチェック拒否。"""
    # Act
    response = await client.get("/api/v1/admin/health-check/detailed")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_detailed_health_check_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_support_tools-017] 一般ユーザーでの詳細ヘルスチェック拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/health-check/detailed")

    # Assert
    assert response.status_code == 403
