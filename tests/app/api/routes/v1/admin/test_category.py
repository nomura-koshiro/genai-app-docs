"""カテゴリマスタ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/category - カテゴリマスタ一覧取得
    - GET /api/v1/admin/category/{category_id} - カテゴリマスタ詳細取得
    - POST /api/v1/admin/category - カテゴリマスタ作成
    - PATCH /api/v1/admin/category/{category_id} - カテゴリマスタ更新
    - DELETE /api/v1/admin/category/{category_id} - カテゴリマスタ削除
"""

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/category - カテゴリマスタ一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_categories_success(client: AsyncClient, override_auth, admin_user):
    """[test_category-001] カテゴリマスタ一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/category")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_categories_with_pagination(client: AsyncClient, override_auth, admin_user):
    """[test_category-002] ページネーション付きカテゴリマスタ一覧取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get(
        "/api/v1/admin/category",
        params={
            "skip": 0,
            "limit": 10,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data


@pytest.mark.asyncio
async def test_list_categories_unauthorized(client: AsyncClient):
    """[test_category-003] 認証なしでのカテゴリマスタ一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/category")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_categories_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_category-004] 一般ユーザーでのカテゴリマスタ一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/category")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/category/{category_id} - カテゴリマスタ詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_category_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_category-005] 存在しないカテゴリマスタの取得。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = 99999

    # Act
    response = await client.get(f"/api/v1/admin/category/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_category_unauthorized(client: AsyncClient):
    """[test_category-006] 認証なしでのカテゴリマスタ詳細取得拒否。"""
    # Arrange
    category_id = 1

    # Act
    response = await client.get(f"/api/v1/admin/category/{category_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_category_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_category-007] 一般ユーザーでのカテゴリマスタ詳細取得拒否。"""
    # Arrange
    override_auth(regular_user)
    category_id = 1

    # Act
    response = await client.get(f"/api/v1/admin/category/{category_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/category - カテゴリマスタ作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_category_success(client: AsyncClient, override_auth, admin_user):
    """[test_category-008] カテゴリマスタ作成の成功ケース。"""
    # Arrange
    override_auth(admin_user)
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
    assert response.status_code == 201
    data = response.json()
    assert data["categoryName"] == category_data["categoryName"]


@pytest.mark.asyncio
async def test_create_category_unauthorized(client: AsyncClient):
    """[test_category-009] 認証なしでのカテゴリマスタ作成拒否。"""
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
async def test_create_category_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_category-010] 一般ユーザーでのカテゴリマスタ作成拒否。"""
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


# ================================================================================
# PATCH /api/v1/admin/category/{category_id} - カテゴリマスタ更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_category_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_category-011] 存在しないカテゴリマスタの更新。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = 99999
    update_data = {"categoryName": "更新カテゴリ"}

    # Act
    response = await client.patch(f"/api/v1/admin/category/{nonexistent_id}", json=update_data)

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category_unauthorized(client: AsyncClient):
    """[test_category-012] 認証なしでのカテゴリマスタ更新拒否。"""
    # Arrange
    category_id = 1
    update_data = {"categoryName": "更新カテゴリ"}

    # Act
    response = await client.patch(f"/api/v1/admin/category/{category_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_category_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_category-013] 一般ユーザーでのカテゴリマスタ更新拒否。"""
    # Arrange
    override_auth(regular_user)
    category_id = 1
    update_data = {"categoryName": "更新カテゴリ"}

    # Act
    response = await client.patch(f"/api/v1/admin/category/{category_id}", json=update_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/admin/category/{category_id} - カテゴリマスタ削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_category_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_category-014] 存在しないカテゴリマスタの削除。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = 99999

    # Act
    response = await client.delete(f"/api/v1/admin/category/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_unauthorized(client: AsyncClient):
    """[test_category-015] 認証なしでのカテゴリマスタ削除拒否。"""
    # Arrange
    category_id = 1

    # Act
    response = await client.delete(f"/api/v1/admin/category/{category_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_category_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_category-016] 一般ユーザーでのカテゴリマスタ削除拒否。"""
    # Arrange
    override_auth(regular_user)
    category_id = 1

    # Act
    response = await client.delete(f"/api/v1/admin/category/{category_id}")

    # Assert
    assert response.status_code == 403
