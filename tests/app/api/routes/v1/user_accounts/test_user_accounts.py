"""ユーザーアカウントAPIのテスト。

このテストファイルは API_ROUTE_TEST_POLICY.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

基本的なバリデーションエラーはPydanticスキーマで検証済み、
ビジネスロジックはサービス層でカバーされます。

対応エンドポイント:
    - GET /api/v1/user_account - ユーザー一覧取得
    - GET /api/v1/user_account/me - 現在のユーザー情報取得
    - GET /api/v1/user_account/{user_id} - ユーザー情報取得
    - PATCH /api/v1/user_account/me - 現在のユーザー情報更新
    - DELETE /api/v1/user_account/{user_id} - ユーザー削除
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/user_account - ユーザー一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_users_success(client: AsyncClient, override_auth, admin_user):
    """[test_user_accounts-001] ユーザー一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/user_account")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert isinstance(data["users"], list)
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_list_users_with_pagination(client: AsyncClient, override_auth, admin_user):
    """[test_user_accounts-002] ページネーション付きユーザー一覧取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/user_account?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 10
    assert len(data["users"]) <= 10


@pytest.mark.asyncio
async def test_list_users_total_count_accuracy(
    client: AsyncClient,
    override_auth,
    admin_user,
    test_data_seeder,
):
    """[test_user_accounts-003] ユーザー一覧のtotal件数の正確性確認。"""
    # Arrange - 追加で10人のユーザーを作成
    for i in range(10):
        await test_data_seeder.create_user(display_name=f"Pagination User {i}")
    await test_data_seeder.db.commit()

    override_auth(admin_user)

    # Act - 最初の5件を取得
    response = await client.get("/api/v1/user_account?skip=0&limit=5")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 5
    assert len(data["users"]) == 5
    assert data["total"] >= 11  # 最低でも11件（admin_user + 10人）


@pytest.mark.asyncio
async def test_list_users_pagination_second_page(
    client: AsyncClient,
    override_auth,
    admin_user,
    test_data_seeder,
):
    """[test_user_accounts-004] ユーザー一覧のページネーション（2ページ目）。"""
    # Arrange - 追加で10人のユーザーを作成
    for i in range(10):
        await test_data_seeder.create_user(display_name=f"Pagination2 User {i}")
    await test_data_seeder.db.commit()

    override_auth(admin_user)

    # Act - 2ページ目を取得
    response = await client.get("/api/v1/user_account?skip=5&limit=5")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 5
    assert data["limit"] == 5
    assert len(data["users"]) <= 5
    assert data["total"] >= 11


@pytest.mark.asyncio
async def test_list_users_unauthorized(client: AsyncClient):
    """[test_user_accounts-005] 認証なしでのユーザー一覧取得失敗。"""
    # Act
    response = await client.get("/api/v1/user_account")

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_non_admin_fails(client: AsyncClient, override_auth, regular_user):
    """[test_user_accounts-006] 非管理者によるユーザー一覧取得失敗。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/user_account")

    # Assert
    assert response.status_code == 422


# ================================================================================
# GET /api/v1/user_account/me - 現在のユーザー情報取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_current_user_success(client: AsyncClient, override_auth, admin_user):
    """[test_user_accounts-007] 現在のユーザー情報取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/user_account/me")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "azureOid" in data
    assert "email" in data
    assert "displayName" in data
    assert "roles" in data
    assert "isActive" in data
    assert data["id"] == str(admin_user.id)


@pytest.mark.asyncio
async def test_get_current_user_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_user_accounts-008] 一般ユーザーの現在のユーザー情報取得の成功ケース。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/user_account/me")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(regular_user.id)


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """[test_user_accounts-009] 認証なしでの現在ユーザー情報取得失敗。"""
    # Act
    response = await client.get("/api/v1/user_account/me")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/user_account/{user_id} - ユーザー情報取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_user_by_id_success(client: AsyncClient, override_auth, admin_user):
    """[test_user_accounts-010] ユーザーID指定での取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    user_id = str(admin_user.id)

    # Act
    response = await client.get(f"/api/v1/user_account/{user_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_user_accounts-011] 存在しないユーザーの取得（404エラー）。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/user_account/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_by_id_non_admin_fails(client: AsyncClient, override_auth, regular_user, admin_user):
    """[test_user_accounts-012] 非管理者による他ユーザー取得失敗。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get(f"/api/v1/user_account/{admin_user.id}")

    # Assert
    assert response.status_code == 422


# ================================================================================
# PATCH /api/v1/user_account/me - 現在のユーザー情報更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_current_user_success(client: AsyncClient, override_auth, regular_user):
    """[test_user_accounts-013] 現在のユーザー情報更新の成功ケース。"""
    # Arrange
    override_auth(regular_user)
    update_data = {
        "display_name": "Updated Display Name",
    }

    # Act
    response = await client.patch("/api/v1/user_account/me", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["displayName"] == "Updated Display Name"


@pytest.mark.asyncio
async def test_update_current_user_roles_by_admin(client: AsyncClient, override_auth, admin_user):
    """[test_user_accounts-014] 管理者によるロール更新の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # 管理者が自身のロールを更新
    update_data = {
        "roles": ["SystemAdmin", "User"],
    }

    # Act
    response = await client.patch("/api/v1/user_account/me", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "SystemAdmin" in data["roles"]
    assert "User" in data["roles"]


@pytest.mark.asyncio
async def test_update_current_user_roles_by_non_admin_fails(
    client: AsyncClient,
    override_auth,
    regular_user,
):
    """[test_user_accounts-015] 非管理者によるロール更新失敗。"""
    # Arrange
    override_auth(regular_user)
    update_data = {
        "roles": ["SystemAdmin"],
    }

    # Act
    response = await client.patch("/api/v1/user_account/me", json=update_data)

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_current_user_is_active_by_admin(client: AsyncClient, override_auth, admin_user):
    """[test_user_accounts-016] 管理者によるis_active更新の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    update_data = {
        "is_active": False,
    }

    # Act
    response = await client.patch("/api/v1/user_account/me", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["isActive"] is False


@pytest.mark.asyncio
async def test_update_current_user_is_active_by_non_admin_fails(
    client: AsyncClient,
    override_auth,
    regular_user,
):
    """[test_user_accounts-017] 非管理者によるis_active更新失敗。"""
    # Arrange
    override_auth(regular_user)
    update_data = {
        "is_active": False,
    }

    # Act
    response = await client.patch("/api/v1/user_account/me", json=update_data)

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_current_user_unauthorized(client: AsyncClient):
    """[test_user_accounts-018] 認証なしでのユーザー情報更新失敗。"""
    # Act
    update_data = {"display_name": "Unauthorized Update"}
    response = await client.patch("/api/v1/user_account/me", json=update_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/user_account/{user_id} - ユーザー削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_user_success(client: AsyncClient, override_auth, admin_user, test_data_seeder):
    """[test_user_accounts-019] 管理者によるユーザー削除の成功ケース。"""
    # Arrange - 削除対象のユーザーを作成
    target_user = await test_data_seeder.create_user(display_name="Delete Target User")
    await test_data_seeder.db.commit()

    override_auth(admin_user)

    # Act
    response = await client.delete(f"/api/v1/user_account/{target_user.id}")

    # Assert
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_user_accounts-020] 存在しないユーザーの削除（404エラー）。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/user_account/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_by_non_admin_fails(
    client: AsyncClient,
    override_auth,
    regular_user,
    test_data_seeder,
):
    """[test_user_accounts-021] 非管理者によるユーザー削除失敗。"""
    # Arrange - 削除対象のユーザーを作成
    target_user = await test_data_seeder.create_user(display_name="Delete Target User 2")
    await test_data_seeder.db.commit()

    override_auth(regular_user)

    # Act
    response = await client.delete(f"/api/v1/user_account/{target_user.id}")

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_self_fails(client: AsyncClient, override_auth, admin_user):
    """[test_user_accounts-022] 自分自身の削除失敗。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.delete(f"/api/v1/user_account/{admin_user.id}")

    # Assert
    assert response.status_code == 422
