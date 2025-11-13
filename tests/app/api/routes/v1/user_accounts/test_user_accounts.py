"""ユーザーAPIルートのテスト。

このテストファイルは TEST_REDUCTION_POLICY.md に従い、
Happy Path とビジネスルールエラーのみをテストします。

バリデーションエラー（Pydantic）や冗長な404テストは含みません。
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models import UserAccount


@pytest.fixture
async def mock_admin_user(db_session):
    """モック管理者ユーザー（SystemAdminロール）。"""
    user = UserAccount(
        azure_oid=f"azure-admin-{uuid.uuid4()}",
        email="admin@example.com",
        display_name="Admin User",
        roles=["SystemAdmin"],
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_list_users_success(client: AsyncClient, override_auth, mock_admin_user):
    """ユーザー一覧取得の正常系テスト（管理者権限）。"""
    # Arrange
    override_auth(mock_admin_user)

    # Act
    response = await client.get("/api/v1/users")

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
async def test_list_users_with_pagination(client: AsyncClient, override_auth, mock_admin_user):
    """ユーザー一覧取得のページネーションテスト。"""
    # Arrange
    override_auth(mock_admin_user)

    # Act
    response = await client.get("/api/v1/users?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 10
    assert len(data["users"]) <= 10


@pytest.mark.asyncio
async def test_list_users_total_count_accuracy(client: AsyncClient, override_auth, mock_admin_user, db_session):
    """ユーザー一覧のtotal件数が正確であることをテスト。"""
    # Arrange
    # 追加で10人のユーザーを作成
    for i in range(10):
        user = UserAccount(
            azure_oid=f"pagination-test-{i}",
            email=f"pagination{i}@example.com",
            display_name=f"Pagination User {i}",
            is_active=True,
        )
        db_session.add(user)
    await db_session.commit()

    override_auth(mock_admin_user)

    # Act - 最初の5件を取得
    response = await client.get("/api/v1/users?skip=0&limit=5")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 5
    assert len(data["users"]) == 5  # 5件取得
    assert data["total"] >= 11  # 最低でも11件（mock_admin_user + 10人）


@pytest.mark.asyncio
async def test_list_users_pagination_second_page(client: AsyncClient, override_auth, mock_admin_user, db_session):
    """ユーザー一覧のページネーション（2ページ目）テスト。"""
    # Arrange
    # 追加で10人のユーザーを作成
    for i in range(10):
        user = UserAccount(
            azure_oid=f"pagination2-test-{i}",
            email=f"pagination2{i}@example.com",
            display_name=f"Pagination2 User {i}",
            is_active=True,
        )
        db_session.add(user)
    await db_session.commit()

    override_auth(mock_admin_user)

    # Act - 2ページ目を取得（skip=5, limit=5）
    response = await client.get("/api/v1/users?skip=5&limit=5")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 5
    assert data["limit"] == 5
    assert len(data["users"]) <= 5  # 最大5件
    assert data["total"] >= 11  # 総件数は正確（最低11件）


@pytest.mark.asyncio
async def test_get_current_user_success(client: AsyncClient, override_auth, mock_admin_user):
    """現在のユーザー情報取得の正常系テスト。"""
    # Arrange
    override_auth(mock_admin_user)

    # Act
    response = await client.get("/api/v1/users/me")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "azure_oid" in data
    assert "email" in data
    assert "display_name" in data
    assert "roles" in data
    assert "is_active" in data
    assert data["email"] == "admin@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_success(client: AsyncClient, override_auth, mock_admin_user):
    """特定ユーザー取得の正常系テスト（管理者権限）。"""
    # Arrange
    override_auth(mock_admin_user)
    user_id = str(mock_admin_user.id)

    # Act
    response = await client.get(f"/api/v1/users/{user_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, override_auth, mock_admin_user):
    """存在しないユーザーの取得テスト（404エラー）。"""
    # Arrange
    override_auth(mock_admin_user)

    # Act
    response = await client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_current_user_success(client: AsyncClient, override_auth, mock_admin_user):
    """現在のユーザー情報更新の正常系テスト。"""
    # Arrange
    override_auth(mock_admin_user)
    update_data = {
        "display_name": "Updated Admin Name",
    }

    # Act
    response = await client.patch("/api/v1/users/me", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Admin Name"
