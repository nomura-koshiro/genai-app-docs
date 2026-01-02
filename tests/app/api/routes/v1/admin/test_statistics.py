"""システム統計APIのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/admin/statistics/overview - 統計概要取得
    - GET /api/v1/admin/statistics/users - ユーザー統計取得
"""

import pytest
from httpx import AsyncClient

# ================================================================================
# GET /api/v1/admin/statistics/overview - 統計概要取得
# ================================================================================


@pytest.mark.parametrize(
    "params,expected_keys",
    [
        ({}, ["users", "projects", "storage", "api"]),
        ({"period": "week"}, ["users", "projects"]),
    ],
    ids=["basic", "with_period"],
)
@pytest.mark.asyncio
async def test_get_statistics_overview_success(
    client: AsyncClient, override_auth, admin_user, params, expected_keys
):
    """[test_statistics-001-002] 統計概要取得の成功ケース（基本/期間指定付き）。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/statistics/overview", params=params)

    # Assert
    assert response.status_code == 200
    data = response.json()
    for key in expected_keys:
        assert key in data


# ================================================================================
# GET /api/v1/admin/statistics/users - ユーザー統計取得
# ================================================================================


@pytest.mark.parametrize(
    "params,expected_keys",
    [
        ({}, ["total", "activeUsers", "newUsers"]),
        ({"days": 7}, ["activeUsers"]),
    ],
    ids=["basic", "with_days"],
)
@pytest.mark.asyncio
async def test_get_user_statistics_success(
    client: AsyncClient, override_auth, admin_user, params, expected_keys
):
    """[test_statistics-003-004] ユーザー統計取得の成功ケース（基本/日数指定付き）。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/statistics/users", params=params)

    # Assert
    assert response.status_code == 200
    data = response.json()
    for key in expected_keys:
        assert key in data
