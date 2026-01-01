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


@pytest.fixture
async def seeded_settings(test_data_seeder):
    """システム設定のシードデータを作成。"""
    await test_data_seeder.seed_default_settings()
    return test_data_seeder


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
    assert "preview" in data
    assert "retentionDays" in data
    assert "cutoffDate" in data


# ================================================================================
# POST /api/v1/admin/data/cleanup/execute - データ一括削除
# ================================================================================


@pytest.mark.asyncio
async def test_execute_cleanup_success(client: AsyncClient, override_auth, admin_user):
    """[test_data_management-002] データ一括削除の成功ケース。"""
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
    assert "success" in data
    assert "results" in data
    assert "totalDeletedCount" in data


# ================================================================================
# GET /api/v1/admin/data/retention-policy - 保持ポリシー取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_retention_policy_success(client: AsyncClient, override_auth, admin_user):
    """[test_data_management-003] 保持ポリシー取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/data/retention-policy")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "activityLogsDays" in data
    assert "auditLogsDays" in data


# ================================================================================
# PATCH /api/v1/admin/data/retention-policy - 保持ポリシー更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_retention_policy_success(client: AsyncClient, override_auth, admin_user, seeded_settings):
    """[test_data_management-004] 保持ポリシー更新の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    policy_data = {
        "activityLogsDays": 90,
        "auditLogsDays": 365,
        "sessionLogsDays": 30,
    }

    # Act
    response = await client.patch("/api/v1/admin/data/retention-policy", json=policy_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "activityLogsDays" in data
    assert "auditLogsDays" in data
