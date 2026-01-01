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
