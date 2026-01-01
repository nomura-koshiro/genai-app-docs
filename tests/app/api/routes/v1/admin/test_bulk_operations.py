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


@pytest.mark.asyncio
async def test_import_users_unauthorized(client: AsyncClient):
    """[test_bulk_operations-002] 認証なしでのユーザー一括インポート拒否。"""
    # Arrange
    csv_content = "email,display_name\ntest@example.com,Test User\n"
    files = {"file": ("users.csv", io.BytesIO(csv_content.encode()), "text/csv")}

    # Act
    response = await client.post("/api/v1/admin/bulk/users/import", files=files)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_import_users_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_bulk_operations-003] 一般ユーザーでのユーザー一括インポート拒否。"""
    # Arrange
    override_auth(regular_user)
    csv_content = "email,display_name\ntest@example.com,Test User\n"
    files = {"file": ("users.csv", io.BytesIO(csv_content.encode()), "text/csv")}

    # Act
    response = await client.post("/api/v1/admin/bulk/users/import", files=files)

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/bulk/users/export - ユーザー一括エクスポート
# ================================================================================


@pytest.mark.asyncio
async def test_export_users_success(client: AsyncClient, override_auth, admin_user):
    """[test_bulk_operations-004] ユーザー一括エクスポートの成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/bulk/users/export")

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_export_users_with_filter(client: AsyncClient, override_auth, admin_user):
    """[test_bulk_operations-005] フィルタ付きユーザーエクスポート。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/bulk/users/export", params={"is_active": True})

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


@pytest.mark.asyncio
async def test_export_users_unauthorized(client: AsyncClient):
    """[test_bulk_operations-006] 認証なしでのユーザーエクスポート拒否。"""
    # Act
    response = await client.get("/api/v1/admin/bulk/users/export")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_export_users_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_bulk_operations-007] 一般ユーザーでのユーザーエクスポート拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/bulk/users/export")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/bulk/users/deactivate - 非アクティブユーザー一括無効化
# ================================================================================


@pytest.mark.asyncio
async def test_deactivate_inactive_users_success(client: AsyncClient, override_auth, admin_user):
    """[test_bulk_operations-008] 非アクティブユーザー一括無効化の成功ケース。"""
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


@pytest.mark.asyncio
async def test_deactivate_inactive_users_unauthorized(client: AsyncClient):
    """[test_bulk_operations-009] 認証なしでのユーザー無効化拒否。"""
    # Act
    response = await client.post(
        "/api/v1/admin/bulk/users/deactivate",
        params={"inactive_days": 90},
    )

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_deactivate_inactive_users_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_bulk_operations-010] 一般ユーザーでのユーザー無効化拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.post(
        "/api/v1/admin/bulk/users/deactivate",
        params={"inactive_days": 90},
    )

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/bulk/projects/archive - プロジェクト一括アーカイブ
# ================================================================================


@pytest.mark.asyncio
async def test_archive_old_projects_success(client: AsyncClient, override_auth, admin_user):
    """[test_bulk_operations-011] プロジェクト一括アーカイブの成功ケース。"""
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


@pytest.mark.asyncio
async def test_archive_old_projects_unauthorized(client: AsyncClient):
    """[test_bulk_operations-012] 認証なしでのプロジェクトアーカイブ拒否。"""
    # Act
    response = await client.post(
        "/api/v1/admin/bulk/projects/archive",
        params={"inactive_days": 180},
    )

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_archive_old_projects_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_bulk_operations-013] 一般ユーザーでのプロジェクトアーカイブ拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.post(
        "/api/v1/admin/bulk/projects/archive",
        params={"inactive_days": 180},
    )

    # Assert
    assert response.status_code == 403
