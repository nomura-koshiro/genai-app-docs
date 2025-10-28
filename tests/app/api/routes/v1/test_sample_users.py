"""ユーザーAPIのテスト。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user_endpoint(client: AsyncClient):
    """ユーザー作成エンドポイントのテスト。"""
    # Arrange
    user_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "SecurePass123!",
    }

    # Act
    response = await client.post("/api/v1/sample-users", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "password" not in data  # パスワードはレスポンスに含まれない


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
    """重複メールアドレスでのユーザー作成失敗のテスト。"""
    # Arrange - 最初のユーザーを作成
    user_data = {
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "SecurePass123!",
    }
    await client.post("/api/v1/sample-users", json=user_data)

    # Act - 同じメールアドレスで2回目の作成を試みる
    duplicate_user = {
        "email": "duplicate@example.com",
        "username": "user2",
        "password": "SecurePass123!",
    }
    response = await client.post("/api/v1/sample-users", json=duplicate_user)

    # Assert - エラーが返る
    assert response.status_code in [400, 409]  # Bad Request or Conflict


@pytest.mark.asyncio
async def test_create_user_invalid_data(client: AsyncClient):
    """不正なデータでのユーザー作成失敗のテスト。"""
    # Arrange - メールアドレスが不正
    invalid_user = {
        "email": "invalid-email",
        "username": "testuser",
        "password": "short",
    }

    # Act
    response = await client.post("/api/v1/sample-users", json=invalid_user)

    # Assert - バリデーションエラー
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_endpoint(client: AsyncClient):
    """ログインエンドポイントのテスト。"""
    # Arrange - 最初にユーザーを作成
    user_data = {
        "email": "logintest@example.com",
        "username": "loginuser",
        "password": "SecurePass123!",
    }
    await client.post("/api/v1/sample-users", json=user_data)

    # Act - ログインを試みる
    login_data = {
        "email": "logintest@example.com",
        "password": "SecurePass123!",
    }
    response = await client.post("/api/v1/sample-users/sample-login", json=login_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
