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


@pytest.mark.asyncio
async def test_list_sessions_unauthorized(client: AsyncClient):
    """[test_security-003] 認証なしでのセッション一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/sessions")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_sessions_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_security-004] 一般ユーザーでのセッション一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/sessions")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/sessions/user/{user_id} - ユーザー別セッション取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_user_sessions_success(client: AsyncClient, override_auth, admin_user):
    """[test_security-005] ユーザー別セッション取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)
    user_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/sessions/user/{user_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_get_user_sessions_unauthorized(client: AsyncClient):
    """[test_security-006] 認証なしでのユーザー別セッション取得拒否。"""
    # Arrange
    user_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/sessions/user/{user_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_user_sessions_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_security-007] 一般ユーザーでのユーザー別セッション取得拒否。"""
    # Arrange
    override_auth(regular_user)
    user_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/sessions/user/{user_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/sessions/{session_id}/terminate - セッション終了
# ================================================================================


@pytest.mark.asyncio
async def test_terminate_session_unauthorized(client: AsyncClient):
    """[test_security-008] 認証なしでのセッション終了拒否。"""
    # Arrange
    session_id = str(uuid.uuid4())
    request_data = {"reason": "セキュリティ上の理由"}

    # Act
    response = await client.post(f"/api/v1/admin/sessions/{session_id}/terminate", json=request_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_terminate_session_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_security-009] 一般ユーザーでのセッション終了拒否。"""
    # Arrange
    override_auth(regular_user)
    session_id = str(uuid.uuid4())
    request_data = {"reason": "セキュリティ上の理由"}

    # Act
    response = await client.post(f"/api/v1/admin/sessions/{session_id}/terminate", json=request_data)

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_terminate_session_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_security-010] 存在しないセッションの終了。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())
    request_data = {"reason": "テスト"}

    # Act
    response = await client.post(f"/api/v1/admin/sessions/{nonexistent_id}/terminate", json=request_data)

    # Assert
    assert response.status_code == 404


# ================================================================================
# POST /api/v1/admin/sessions/user/{user_id}/terminate-all - 全セッション終了
# ================================================================================


@pytest.mark.asyncio
async def test_terminate_all_user_sessions_unauthorized(client: AsyncClient):
    """[test_security-011] 認証なしでの全セッション終了拒否。"""
    # Arrange
    user_id = str(uuid.uuid4())
    request_data = {"reason": "セキュリティ上の理由"}

    # Act
    response = await client.post(f"/api/v1/admin/sessions/user/{user_id}/terminate-all", json=request_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_terminate_all_user_sessions_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_security-012] 一般ユーザーでの全セッション終了拒否。"""
    # Arrange
    override_auth(regular_user)
    user_id = str(uuid.uuid4())
    request_data = {"reason": "セキュリティ上の理由"}

    # Act
    response = await client.post(f"/api/v1/admin/sessions/user/{user_id}/terminate-all", json=request_data)

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_terminate_all_user_sessions_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_security-013] 存在しないユーザーの全セッション終了。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_user_id = str(uuid.uuid4())
    request_data = {"reason": "テスト"}

    # Act
    response = await client.post(
        f"/api/v1/admin/sessions/user/{nonexistent_user_id}/terminate-all",
        json=request_data,
    )

    # Assert
    assert response.status_code == 404
