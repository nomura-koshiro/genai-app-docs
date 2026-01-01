"""検証マスタ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/validation - 検証マスタ一覧取得
    - GET /api/v1/admin/validation/{validation_id} - 検証マスタ詳細取得
    - POST /api/v1/admin/validation - 検証マスタ作成
    - PATCH /api/v1/admin/validation/{validation_id} - 検証マスタ更新
    - DELETE /api/v1/admin/validation/{validation_id} - 検証マスタ削除
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/validation - 検証マスタ一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_validations_success(client: AsyncClient, override_auth, admin_user):
    """[test_validation-001] 検証マスタ一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/validation")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "validations" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_validations_with_pagination(client: AsyncClient, override_auth, admin_user):
    """[test_validation-002] ページネーション付き検証マスタ一覧取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get(
        "/api/v1/admin/validation",
        params={
            "skip": 0,
            "limit": 10,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "validations" in data


@pytest.mark.asyncio
async def test_list_validations_unauthorized(client: AsyncClient):
    """[test_validation-003] 認証なしでの検証マスタ一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/validation")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_validations_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_validation-004] 一般ユーザーでの検証マスタ一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/validation")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/validation/{validation_id} - 検証マスタ詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_validation_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_validation-005] 存在しない検証マスタの取得。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/validation/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_validation_unauthorized(client: AsyncClient):
    """[test_validation-006] 認証なしでの検証マスタ詳細取得拒否。"""
    # Arrange
    validation_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/validation/{validation_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_validation_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_validation-007] 一般ユーザーでの検証マスタ詳細取得拒否。"""
    # Arrange
    override_auth(regular_user)
    validation_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/validation/{validation_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/validation - 検証マスタ作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_validation_unauthorized(client: AsyncClient):
    """[test_validation-008] 認証なしでの検証マスタ作成拒否。"""
    # Arrange
    validation_data = {
        "name": "テスト検証",
        "validationOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/validation", json=validation_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_validation_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_validation-009] 一般ユーザーでの検証マスタ作成拒否。"""
    # Arrange
    override_auth(regular_user)
    validation_data = {
        "name": "テスト検証",
        "validationOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/validation", json=validation_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /api/v1/admin/validation/{validation_id} - 検証マスタ更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_validation_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_validation-010] 存在しない検証マスタの更新。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())
    update_data = {"name": "更新検証"}

    # Act
    response = await client.patch(f"/api/v1/admin/validation/{nonexistent_id}", json=update_data)

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_validation_unauthorized(client: AsyncClient):
    """[test_validation-011] 認証なしでの検証マスタ更新拒否。"""
    # Arrange
    validation_id = str(uuid.uuid4())
    update_data = {"name": "更新検証"}

    # Act
    response = await client.patch(f"/api/v1/admin/validation/{validation_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_validation_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_validation-012] 一般ユーザーでの検証マスタ更新拒否。"""
    # Arrange
    override_auth(regular_user)
    validation_id = str(uuid.uuid4())
    update_data = {"name": "更新検証"}

    # Act
    response = await client.patch(f"/api/v1/admin/validation/{validation_id}", json=update_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/admin/validation/{validation_id} - 検証マスタ削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_validation_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_validation-013] 存在しない検証マスタの削除。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/validation/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_validation_unauthorized(client: AsyncClient):
    """[test_validation-014] 認証なしでの検証マスタ削除拒否。"""
    # Arrange
    validation_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/validation/{validation_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_validation_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_validation-015] 一般ユーザーでの検証マスタ削除拒否。"""
    # Arrange
    override_auth(regular_user)
    validation_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/validation/{validation_id}")

    # Assert
    assert response.status_code == 403
