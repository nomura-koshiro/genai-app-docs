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
