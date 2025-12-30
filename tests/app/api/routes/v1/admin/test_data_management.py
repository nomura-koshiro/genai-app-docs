"""データ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/data/cleanup/preview - 削除対象データプレビュー
    - POST /api/v1/admin/data/cleanup/execute - データ一括削除
    - GET /api/v1/admin/data/retention-policy - 保持ポリシー取得
    - PATCH /api/v1/admin/data/retention-policy - 保持ポリシー更新
"""

import pytest
from httpx import AsyncClient


# ================================================================================
# GET /api/v1/admin/data/cleanup/preview - 削除対象データプレビュー
# ================================================================================


@pytest.mark.asyncio
async def test_preview_cleanup_success(client: AsyncClient, override_auth, admin_user):
    """[test_data_management-001] 削除対象データプレビューの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get(
        "/api/v1/admin/data/cleanup/preview",
        params={
            "target_types": ["ACTIVITY_LOGS", "AUDIT_LOGS"],
            "retention_days": 90,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "target_types" in data
    assert "retention_days" in data
    assert "preview" in data


@pytest.mark.asyncio
async def test_preview_cleanup_unauthorized(client: AsyncClient):
    """[test_data_management-002] 認証なしでの削除対象プレビュー拒否。"""
    # Act
    response = await client.get(
        "/api/v1/admin/data/cleanup/preview",
        params={
            "target_types": ["ACTIVITY_LOGS"],
            "retention_days": 90,
        },
    )

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_preview_cleanup_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_data_management-003] 一般ユーザーでの削除対象プレビュー拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get(
        "/api/v1/admin/data/cleanup/preview",
        params={
            "target_types": ["ACTIVITY_LOGS"],
            "retention_days": 90,
        },
    )

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/data/cleanup/execute - データ一括削除
# ================================================================================


@pytest.mark.asyncio
async def test_execute_cleanup_success(client: AsyncClient, override_auth, admin_user):
    """[test_data_management-004] データ一括削除の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.post(
        "/api/v1/admin/data/cleanup/execute",
        params={
            "target_types": ["ACTIVITY_LOGS"],
            "retention_days": 90,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "deleted_count" in data
    assert "target_types" in data


@pytest.mark.asyncio
async def test_execute_cleanup_unauthorized(client: AsyncClient):
    """[test_data_management-005] 認証なしでのデータ削除拒否。"""
    # Act
    response = await client.post(
        "/api/v1/admin/data/cleanup/execute",
        params={
            "target_types": ["ACTIVITY_LOGS"],
            "retention_days": 90,
        },
    )

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_execute_cleanup_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_data_management-006] 一般ユーザーでのデータ削除拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.post(
        "/api/v1/admin/data/cleanup/execute",
        params={
            "target_types": ["ACTIVITY_LOGS"],
            "retention_days": 90,
        },
    )

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/data/retention-policy - 保持ポリシー取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_retention_policy_success(client: AsyncClient, override_auth, admin_user):
    """[test_data_management-007] 保持ポリシー取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/data/retention-policy")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "policies" in data


@pytest.mark.asyncio
async def test_get_retention_policy_unauthorized(client: AsyncClient):
    """[test_data_management-008] 認証なしでの保持ポリシー取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/data/retention-policy")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_retention_policy_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_data_management-009] 一般ユーザーでの保持ポリシー取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/data/retention-policy")

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /api/v1/admin/data/retention-policy - 保持ポリシー更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_retention_policy_success(client: AsyncClient, override_auth, admin_user):
    """[test_data_management-010] 保持ポリシー更新の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    policy_data = {
        "activity_logs_retention_days": 90,
        "audit_logs_retention_days": 365,
        "session_logs_retention_days": 30,
    }

    # Act
    response = await client.patch("/api/v1/admin/data/retention-policy", json=policy_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "policies" in data


@pytest.mark.asyncio
async def test_update_retention_policy_unauthorized(client: AsyncClient):
    """[test_data_management-011] 認証なしでの保持ポリシー更新拒否。"""
    # Arrange
    policy_data = {
        "activity_logs_retention_days": 90,
    }

    # Act
    response = await client.patch("/api/v1/admin/data/retention-policy", json=policy_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_retention_policy_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_data_management-012] 一般ユーザーでの保持ポリシー更新拒否。"""
    # Arrange
    override_auth(regular_user)
    policy_data = {
        "activity_logs_retention_days": 90,
    }

    # Act
    response = await client.patch("/api/v1/admin/data/retention-policy", json=policy_data)

    # Assert
    assert response.status_code == 403
