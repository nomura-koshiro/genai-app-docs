"""Admin API共通認証・認可テスト。

このテストファイルは、Admin APIエンドポイント全体に適用される
認証・認可ミドルウェアの動作を検証します。

個別エンドポイントでの認証・認可テストは不要となります。
代表的なエンドポイントでミドルウェアの動作を確認することで、
全エンドポイントの認証・認可が機能することを保証します。

テスト対象エンドポイント（代表例）:
    - GET /api/v1/admin/category - 一覧取得
    - POST /api/v1/admin/category - 作成
    - PATCH /api/v1/admin/category/{category_id} - 更新
    - DELETE /api/v1/admin/category/{category_id} - 削除
"""

import pytest
from httpx import AsyncClient


# ================================================================================
# 認証テスト（Unauthorized）
# ================================================================================


@pytest.mark.asyncio
async def test_admin_api_get_unauthorized(client: AsyncClient):
    """[test_admin_authorization-001] 認証なしでのAdmin API GETリクエスト拒否。"""
    # Act
    response = await client.get("/api/v1/admin/category")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_admin_api_post_unauthorized(client: AsyncClient):
    """[test_admin_authorization-002] 認証なしでのAdmin API POSTリクエスト拒否。"""
    # Arrange
    category_data = {
        "categoryId": 100,
        "categoryName": "テストカテゴリ",
        "industryId": 1,
        "industryName": "テスト業界",
        "driverTypeId": 1,
        "driverType": "テストドライバー型",
    }

    # Act
    response = await client.post("/api/v1/admin/category", json=category_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_admin_api_patch_unauthorized(client: AsyncClient):
    """[test_admin_authorization-003] 認証なしでのAdmin API PATCHリクエスト拒否。"""
    # Arrange
    category_id = 1
    update_data = {"categoryName": "更新カテゴリ"}

    # Act
    response = await client.patch(f"/api/v1/admin/category/{category_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_admin_api_delete_unauthorized(client: AsyncClient):
    """[test_admin_authorization-004] 認証なしでのAdmin API DELETEリクエスト拒否。"""
    # Arrange
    category_id = 1

    # Act
    response = await client.delete(f"/api/v1/admin/category/{category_id}")

    # Assert
    assert response.status_code in [401, 403]


# ================================================================================
# 認可テスト（Forbidden - Regular User）
# ================================================================================


@pytest.mark.asyncio
async def test_admin_api_get_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_admin_authorization-005] 一般ユーザーでのAdmin API GETリクエスト拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/category")

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_api_post_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_admin_authorization-006] 一般ユーザーでのAdmin API POSTリクエスト拒否。"""
    # Arrange
    override_auth(regular_user)
    category_data = {
        "categoryId": 100,
        "categoryName": "テストカテゴリ",
        "industryId": 1,
        "industryName": "テスト業界",
        "driverTypeId": 1,
        "driverType": "テストドライバー型",
    }

    # Act
    response = await client.post("/api/v1/admin/category", json=category_data)

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_api_patch_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_admin_authorization-007] 一般ユーザーでのAdmin API PATCHリクエスト拒否。"""
    # Arrange
    override_auth(regular_user)
    category_id = 1
    update_data = {"categoryName": "更新カテゴリ"}

    # Act
    response = await client.patch(f"/api/v1/admin/category/{category_id}", json=update_data)

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_api_delete_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_admin_authorization-008] 一般ユーザーでのAdmin API DELETEリクエスト拒否。"""
    # Arrange
    override_auth(regular_user)
    category_id = 1

    # Act
    response = await client.delete(f"/api/v1/admin/category/{category_id}")

    # Assert
    assert response.status_code == 403
