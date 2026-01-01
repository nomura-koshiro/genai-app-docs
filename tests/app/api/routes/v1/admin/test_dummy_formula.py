"""ダミー数式マスタ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/dummy-formula - ダミー数式マスタ一覧取得
    - GET /api/v1/admin/dummy-formula/{formula_id} - ダミー数式マスタ詳細取得
    - POST /api/v1/admin/dummy-formula - ダミー数式マスタ作成
    - PATCH /api/v1/admin/dummy-formula/{formula_id} - ダミー数式マスタ更新
    - DELETE /api/v1/admin/dummy-formula/{formula_id} - ダミー数式マスタ削除
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/dummy-formula - ダミー数式マスタ一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_dummy_formulas_success(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_formula-001] ダミー数式マスタ一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/dummy-formula")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "formulas" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_dummy_formulas_with_filter(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_formula-002] フィルタ付きダミー数式マスタ一覧取得。"""
    # Arrange
    override_auth(admin_user)
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.get(
        "/api/v1/admin/dummy-formula",
        params={
            "skip": 0,
            "limit": 10,
            "issueId": issue_id,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "formulas" in data


@pytest.mark.asyncio
async def test_list_dummy_formulas_unauthorized(client: AsyncClient):
    """[test_dummy_formula-003] 認証なしでのダミー数式マスタ一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/dummy-formula")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_dummy_formulas_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_formula-004] 一般ユーザーでのダミー数式マスタ一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/dummy-formula")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/dummy-formula/{formula_id} - ダミー数式マスタ詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_dummy_formula_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_formula-005] 存在しないダミー数式マスタの取得。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/dummy-formula/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_dummy_formula_unauthorized(client: AsyncClient):
    """[test_dummy_formula-006] 認証なしでのダミー数式マスタ詳細取得拒否。"""
    # Arrange
    formula_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/dummy-formula/{formula_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_dummy_formula_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_formula-007] 一般ユーザーでのダミー数式マスタ詳細取得拒否。"""
    # Arrange
    override_auth(regular_user)
    formula_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/dummy-formula/{formula_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/dummy-formula - ダミー数式マスタ作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_dummy_formula_unauthorized(client: AsyncClient):
    """[test_dummy_formula-008] 認証なしでのダミー数式マスタ作成拒否。"""
    # Arrange
    formula_data = {
        "issueId": str(uuid.uuid4()),
        "name": "テスト数式",
        "value": "5000円",
        "formulaOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/dummy-formula", json=formula_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_dummy_formula_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_formula-009] 一般ユーザーでのダミー数式マスタ作成拒否。"""
    # Arrange
    override_auth(regular_user)
    formula_data = {
        "issueId": str(uuid.uuid4()),
        "name": "テスト数式",
        "value": "5000円",
        "formulaOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/dummy-formula", json=formula_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /api/v1/admin/dummy-formula/{formula_id} - ダミー数式マスタ更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_dummy_formula_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_formula-010] 存在しないダミー数式マスタの更新。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())
    update_data = {"name": "更新数式"}

    # Act
    response = await client.patch(f"/api/v1/admin/dummy-formula/{nonexistent_id}", json=update_data)

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_dummy_formula_unauthorized(client: AsyncClient):
    """[test_dummy_formula-011] 認証なしでのダミー数式マスタ更新拒否。"""
    # Arrange
    formula_id = str(uuid.uuid4())
    update_data = {"name": "更新数式"}

    # Act
    response = await client.patch(f"/api/v1/admin/dummy-formula/{formula_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_dummy_formula_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_formula-012] 一般ユーザーでのダミー数式マスタ更新拒否。"""
    # Arrange
    override_auth(regular_user)
    formula_id = str(uuid.uuid4())
    update_data = {"name": "更新数式"}

    # Act
    response = await client.patch(f"/api/v1/admin/dummy-formula/{formula_id}", json=update_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/admin/dummy-formula/{formula_id} - ダミー数式マスタ削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_dummy_formula_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_formula-013] 存在しないダミー数式マスタの削除。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/dummy-formula/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_dummy_formula_unauthorized(client: AsyncClient):
    """[test_dummy_formula-014] 認証なしでのダミー数式マスタ削除拒否。"""
    # Arrange
    formula_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/dummy-formula/{formula_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_dummy_formula_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_formula-015] 一般ユーザーでのダミー数式マスタ削除拒否。"""
    # Arrange
    override_auth(regular_user)
    formula_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/dummy-formula/{formula_id}")

    # Assert
    assert response.status_code == 403
