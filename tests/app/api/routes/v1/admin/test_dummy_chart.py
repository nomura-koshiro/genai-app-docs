"""ダミーチャートマスタ管理APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/dummy-chart - ダミーチャートマスタ一覧取得
    - GET /api/v1/admin/dummy-chart/{chart_id} - ダミーチャートマスタ詳細取得
    - POST /api/v1/admin/dummy-chart - ダミーチャートマスタ作成
    - PATCH /api/v1/admin/dummy-chart/{chart_id} - ダミーチャートマスタ更新
    - DELETE /api/v1/admin/dummy-chart/{chart_id} - ダミーチャートマスタ削除
"""

import uuid

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/dummy-chart - ダミーチャートマスタ一覧取得
# ================================================================================


@pytest.mark.asyncio
async def test_list_dummy_charts_success(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_chart-001] ダミーチャートマスタ一覧取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/dummy-chart")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "charts" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_dummy_charts_with_filter(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_chart-002] フィルタ付きダミーチャートマスタ一覧取得。"""
    # Arrange
    override_auth(admin_user)
    issue_id = str(uuid.uuid4())

    # Act
    response = await client.get(
        "/api/v1/admin/dummy-chart",
        params={
            "skip": 0,
            "limit": 10,
            "issueId": issue_id,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "charts" in data


@pytest.mark.asyncio
async def test_list_dummy_charts_unauthorized(client: AsyncClient):
    """[test_dummy_chart-003] 認証なしでのダミーチャートマスタ一覧取得拒否。"""
    # Act
    response = await client.get("/api/v1/admin/dummy-chart")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_dummy_charts_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_chart-004] 一般ユーザーでのダミーチャートマスタ一覧取得拒否。"""
    # Arrange
    override_auth(regular_user)

    # Act
    response = await client.get("/api/v1/admin/dummy-chart")

    # Assert
    assert response.status_code == 403


# ================================================================================
# GET /api/v1/admin/dummy-chart/{chart_id} - ダミーチャートマスタ詳細取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_dummy_chart_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_chart-005] 存在しないダミーチャートマスタの取得。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/dummy-chart/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_dummy_chart_unauthorized(client: AsyncClient):
    """[test_dummy_chart-006] 認証なしでのダミーチャートマスタ詳細取得拒否。"""
    # Arrange
    chart_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/dummy-chart/{chart_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_dummy_chart_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_chart-007] 一般ユーザーでのダミーチャートマスタ詳細取得拒否。"""
    # Arrange
    override_auth(regular_user)
    chart_id = str(uuid.uuid4())

    # Act
    response = await client.get(f"/api/v1/admin/dummy-chart/{chart_id}")

    # Assert
    assert response.status_code == 403


# ================================================================================
# POST /api/v1/admin/dummy-chart - ダミーチャートマスタ作成
# ================================================================================


@pytest.mark.asyncio
async def test_create_dummy_chart_unauthorized(client: AsyncClient):
    """[test_dummy_chart-008] 認証なしでのダミーチャートマスタ作成拒否。"""
    # Arrange
    chart_data = {
        "issueId": str(uuid.uuid4()),
        "chart": {"data": [], "layout": {}},
        "chartOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/dummy-chart", json=chart_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_dummy_chart_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_chart-009] 一般ユーザーでのダミーチャートマスタ作成拒否。"""
    # Arrange
    override_auth(regular_user)
    chart_data = {
        "issueId": str(uuid.uuid4()),
        "chart": {"data": [], "layout": {}},
        "chartOrder": 1,
    }

    # Act
    response = await client.post("/api/v1/admin/dummy-chart", json=chart_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# PATCH /api/v1/admin/dummy-chart/{chart_id} - ダミーチャートマスタ更新
# ================================================================================


@pytest.mark.asyncio
async def test_update_dummy_chart_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_chart-010] 存在しないダミーチャートマスタの更新。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())
    update_data = {"chartOrder": 2}

    # Act
    response = await client.patch(f"/api/v1/admin/dummy-chart/{nonexistent_id}", json=update_data)

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_dummy_chart_unauthorized(client: AsyncClient):
    """[test_dummy_chart-011] 認証なしでのダミーチャートマスタ更新拒否。"""
    # Arrange
    chart_id = str(uuid.uuid4())
    update_data = {"chartOrder": 2}

    # Act
    response = await client.patch(f"/api/v1/admin/dummy-chart/{chart_id}", json=update_data)

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_dummy_chart_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_chart-012] 一般ユーザーでのダミーチャートマスタ更新拒否。"""
    # Arrange
    override_auth(regular_user)
    chart_id = str(uuid.uuid4())
    update_data = {"chartOrder": 2}

    # Act
    response = await client.patch(f"/api/v1/admin/dummy-chart/{chart_id}", json=update_data)

    # Assert
    assert response.status_code == 403


# ================================================================================
# DELETE /api/v1/admin/dummy-chart/{chart_id} - ダミーチャートマスタ削除
# ================================================================================


@pytest.mark.asyncio
async def test_delete_dummy_chart_not_found(client: AsyncClient, override_auth, admin_user):
    """[test_dummy_chart-013] 存在しないダミーチャートマスタの削除。"""
    # Arrange
    override_auth(admin_user)
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/dummy-chart/{nonexistent_id}")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_dummy_chart_unauthorized(client: AsyncClient):
    """[test_dummy_chart-014] 認証なしでのダミーチャートマスタ削除拒否。"""
    # Arrange
    chart_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/dummy-chart/{chart_id}")

    # Assert
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_dummy_chart_forbidden_regular_user(client: AsyncClient, override_auth, regular_user):
    """[test_dummy_chart-015] 一般ユーザーでのダミーチャートマスタ削除拒否。"""
    # Arrange
    override_auth(regular_user)
    chart_id = str(uuid.uuid4())

    # Act
    response = await client.delete(f"/api/v1/admin/dummy-chart/{chart_id}")

    # Assert
    assert response.status_code == 403
