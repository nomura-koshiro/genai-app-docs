"""セキュリティ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/sessions - アクティブセッション一覧取得
    - GET /api/v1/admin/sessions/user/{user_id} - ユーザー別セッション取得
    - POST /api/v1/admin/sessions/{session_id}/terminate - セッション終了
    - POST /api/v1/admin/sessions/user/{user_id}/terminate-all - ユーザー全セッション終了
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/sessions - アクティブセッション一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_sessions_success(client: AsyncClient, override_auth, admin_user):
    """[test_security-001] アクティブセッション一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/sessions")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_sessions_with_filters(client: AsyncClient, override_auth, admin_user):
    """[test_security-002] フィルタ付きセッション一覧取得。"""
    # Arrange
    override_auth(admin_user)
    user_id = str(uuid.uuid4())

    # Act
    response = await client.get(
        "/api/v1/admin/sessions",
        params={
            "user_id": user_id,
            "skip": 0,
            "limit": 10,
        },
    )

    # Assert
    assert response.status_code == 200


# ================================================================================
# GET /api/v1/admin/sessions/user/{user_id} - ユーザー別セッション取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_user_sessions_success(client: AsyncClient, override_auth, admin_user):
    """[test_security-003] ユーザー別セッション取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    user_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/sessions/user/{user_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
