"""一括操作APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - POST /api/v1/admin/bulk/users/import - ユーザー一括インポート
    - GET /api/v1/admin/bulk/users/export - ユーザー一括エクスポート
    - POST /api/v1/admin/bulk/users/deactivate - 非アクティブユーザー一括無効化
    - POST /api/v1/admin/bulk/projects/archive - プロジェクト一括アーカイブ
"""

import io

import pytest
from httpx import AsyncClient

# ================================================================================
# POST /api/v1/admin/bulk/users/import - ユーザー一括インポート
# ================================================================================


@pytest.mark.asyncio
async def test_import_users_success(client: AsyncClient, override_auth, admin_user):
    """[test_bulk_operations-001] ユーザー一括インポートの成功ケース。"""
    # Arrange
    override_auth(admin_user)
    csv_content = "email,display_name\ntest@example.com,Test User\n"
    files = {"file": ("users.csv", io.BytesIO(csv_content.encode()), "text/csv")}

    # Act
    response = await client.post("/api/v1/admin/bulk/users/import", files=files)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "importedCount" in data
    assert "errorCount" in data


# ================================================================================
# GET /api/v1/admin/bulk/users/export - ユーザー一括エクスポート
# ================================================================================


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"is_active": True},
    ],
    ids=["basic", "with_filter"],
)
@pytest.mark.asyncio
async def test_export_users_success(client: AsyncClient, override_auth, admin_user, params):
    """[test_bulk_operations-002-003] ユーザー一括エクスポートの成功ケース（基本/フィルタ付き）。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/bulk/users/export", params=params)

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]


# ================================================================================
# POST /api/v1/admin/bulk/users/deactivate - 非アクティブユーザー一括無効化
# ================================================================================


@pytest.mark.asyncio
async def test_deactivate_inactive_users_success(client: AsyncClient, override_auth, admin_user):
    """[test_bulk_operations-004] 非アクティブユーザー一括無効化の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.post(
        "/api/v1/admin/bulk/users/deactivate",
        params={"inactive_days": 90, "dry_run": True},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "deactivatedCount" in data
    assert "previewItems" in data  # dry_run時はプレビューアイテムが返される


# ================================================================================
# POST /api/v1/admin/bulk/projects/archive - プロジェクト一括アーカイブ
# ================================================================================


@pytest.mark.asyncio
async def test_archive_old_projects_success(client: AsyncClient, override_auth, admin_user):
    """[test_bulk_operations-005] プロジェクト一括アーカイブの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.post(
        "/api/v1/admin/bulk/projects/archive",
        params={"inactive_days": 180, "dry_run": True},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "archivedCount" in data
    assert "success" in data
    assert "previewItems" in data  # dry_run時はプレビューアイテムが返される
