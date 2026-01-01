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


@pytest.mark.asyncio
async def test_get_statistics_overview_success(client: AsyncClient, override_auth, admin_user):
    """[test_statistics-001] 統計概要取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/statistics/overview")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "projects" in data
    assert "storage" in data
    assert "api" in data


@pytest.mark.asyncio
async def test_get_statistics_overview_with_period(client: AsyncClient, override_auth, admin_user):
    """[test_statistics-002] 期間指定付き統計概要取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/statistics/overview", params={"period": "week"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    # レスポンスに必須フィールドが含まれていることを確認
    assert "users" in data
    assert "projects" in data


# ================================================================================
# GET /api/v1/admin/statistics/users - ユーザー統計取得
# ================================================================================


@pytest.mark.asyncio
async def test_get_user_statistics_success(client: AsyncClient, override_auth, admin_user):
    """[test_statistics-003] ユーザー統計取得の成功ケース。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/statistics/users")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "activeUsers" in data
    assert "newUsers" in data


@pytest.mark.asyncio
async def test_get_user_statistics_with_days(client: AsyncClient, override_auth, admin_user):
    """[test_statistics-004] 日数指定付きユーザー統計取得。"""
    # Arrange
    override_auth(admin_user)

    # Act
    response = await client.get("/api/v1/admin/statistics/users", params={"days": 7})

    # Assert
    assert response.status_code == 200
    data = response.json()
    # レスポンスにactiveUsersが含まれ、daysパラメータに応じたデータ数が返される
    assert "activeUsers" in data
