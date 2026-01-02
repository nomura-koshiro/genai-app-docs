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


@pytest.mark.parametrize(
    "params,expected_keys",
    [
        ({}, ["categories", "total"]),
        ({"skip": 0, "limit": 10}, ["categories"]),
    ],
    ids=["basic", "with_pagination"],
)
@pytest.mark.asyncio
async def test_list_categories_success(
    client: AsyncClient, override_auth, admin_user, params, expected_keys
):
    """[test_category-001-002] カテゴリマスタ一覧取得の成功ケース（基本/ページネーション付き）。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/category", params=params)

    # Assert
    assert response.status_code == 200
    data = response.json()
    for key in expected_keys:
        assert key in data


# ================================================================================
# POST /api/v1/admin/category - カテゴリマスタ作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_category_success(client: AsyncClient, override_auth, admin_user):
    """[test_category-003] カテゴリマスタ作成の成功ケース。"""
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
