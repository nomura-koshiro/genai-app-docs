"""グラフ軸マスタ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/graph-axis - グラフ軸マスタ一覧取得
    - GET /api/v1/admin/graph-axis/{axis_id} - グラフ軸マスタ詳細取得
    - POST /api/v1/admin/graph-axis - グラフ軸マスタ作成
    - PATCH /api/v1/admin/graph-axis/{axis_id} - グラフ軸マスタ更新
    - DELETE /api/v1/admin/graph-axis/{axis_id} - グラフ軸マスタ削除
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/graph-axis - グラフ軸マスタ一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_graph_axes_success(client: AsyncClient, override_auth, admin_user):
    """[test_graph_axis-001] グラフ軸マスタ一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/graph-axis")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "axes" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_graph_axes_with_filter(client: AsyncClient, override_auth, admin_user):
    """[test_graph_axis-002] フィルタ付きグラフ軸マスタ一覧取得。"""
    # Arrange
    override_auth(admin_user)
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.get(
        "/api/v1/admin/graph-axis",
        params={
            "skip": 0,
            "limit": 10,
            "issueId": issue_id,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "axes" in data


@pytest.mark.asyncio
async def test_list_graph_axes_unauthorized(client: AsyncClient):
    """[test_graph_axis-003] 認証なしでのグラフ軸マスタ一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/graph-axis")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_graph_axes_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_graph_axis-004] 一般ユーザーでのグラフ軸マスタ一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/graph-axis")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/graph-axis/{axis_id} - グラフ軸マスタ詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_graph_axis_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_graph_axis-005] 存在しないグラフ軸マスタの取得。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/graph-axis/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_graph_axis_unauthorized(client: AsyncClient):
    """[test_graph_axis-006] 認証なしでのグラフ軸マスタ詳細取得拒否。"""
    # Arrange
    axis_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/graph-axis/{axis_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_graph_axis_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_graph_axis-007] 一般ユーザーでのグラフ軸マスタ詳細取得拒否。"""
    # Arrange
    override_auth(regular_user)
    axis_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/graph-axis/{axis_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/graph-axis - グラフ軸マスタ作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_graph_axis_unauthorized(client: AsyncClient):
    """[test_graph_axis-008] 認証なしでのグラフ軸マスタ作成拒否。"""
    # Arrange
    axis_data = {
        "issueId": str(uuid.uuid4()),
        "name": "横軸",
        "option": "科目",
        "multiple": False,
        "axisOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/graph-axis", json=axis_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_graph_axis_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_graph_axis-009] 一般ユーザーでのグラフ軸マスタ作成拒否。"""
    # Arrange
    override_auth(regular_user)
    axis_data = {
        "issueId": str(uuid.uuid4()),
        "name": "横軸",
        "option": "科目",
        "multiple": False,
        "axisOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/graph-axis", json=axis_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /api/v1/admin/graph-axis/{axis_id} - グラフ軸マスタ更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_graph_axis_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_graph_axis-010] 存在しないグラフ軸マスタの更新。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())
    update_data = {"name": "更新軸"}

    # Act
    response = await client.patch(f"/api/v1/admin/graph-axis/{nonexistent_id}", json=update_data)

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_graph_axis_unauthorized(client: AsyncClient):
    """[test_graph_axis-011] 認証なしでのグラフ軸マスタ更新拒否。"""
    # Arrange
    axis_id = str(uuid.uuid4())
    update_data = {"name": "更新軸"}

    # Act
    response = await client.patch(f"/api/v1/admin/graph-axis/{axis_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_graph_axis_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_graph_axis-012] 一般ユーザーでのグラフ軸マスタ更新拒否。"""
    # Arrange
    override_auth(regular_user)
    axis_id = str(uuid.uuid4())
    update_data = {"name": "更新軸"}

    # Act
    response = await client.patch(f"/api/v1/admin/graph-axis/{axis_id}", json=update_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/admin/graph-axis/{axis_id} - グラフ軸マスタ削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_graph_axis_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_graph_axis-013] 存在しないグラフ軸マスタの削除。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/graph-axis/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_graph_axis_unauthorized(client: AsyncClient):
    """[test_graph_axis-014] 認証なしでのグラフ軸マスタ削除拒否。"""
    # Arrange
    axis_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/graph-axis/{axis_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_graph_axis_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_graph_axis-015] 一般ユーザーでのグラフ軸マスタ削除拒否。"""
    # Arrange
    override_auth(regular_user)
    axis_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/graph-axis/{axis_id}")

    # Assert
    assert response.status_code == 403
