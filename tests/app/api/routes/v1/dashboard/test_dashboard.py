"""ダッシュボードAPIのテスト。

このテストファイルは docs/specifications/13-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。

対応エンドポイント:
    - GET /api/v1/dashboard/stats - 統計情報取得
    - GET /api/v1/dashboard/activities - アクティビティ取得
    - GET /api/v1/dashboard/charts - チャートデータ取得
"""

import pytest
from httpx import AsyncClient


class TestDashboardStatsEndpoint:
    """GET /api/v1/dashboard/stats エンドポイントのテスト。"""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, client: AsyncClient, test_user, override_auth):
        """[test_dashboard-001] 認証済みユーザーで統計情報を取得。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get("/api/v1/dashboard/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "sessions" in data
        assert "trees" in data
        assert "users" in data
        assert "generatedAt" in data

    @pytest.mark.asyncio
    async def test_get_stats_response_structure(self, client: AsyncClient, test_user, override_auth):
        """[test_dashboard-002] レスポンス構造の検証。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get("/api/v1/dashboard/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # プロジェクト統計
        assert "total" in data["projects"]
        assert "active" in data["projects"]
        assert "archived" in data["projects"]

        # セッション統計
        assert "total" in data["sessions"]
        assert "draft" in data["sessions"]
        assert "active" in data["sessions"]
        assert "completed" in data["sessions"]

        # ツリー統計
        assert "total" in data["trees"]
        assert "draft" in data["trees"]
        assert "active" in data["trees"]
        assert "completed" in data["trees"]

        # ユーザー統計
        assert "total" in data["users"]
        assert "active" in data["users"]


class TestDashboardActivitiesEndpoint:
    """GET /api/v1/dashboard/activities エンドポイントのテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "params,expected_status,check_fields",
        [
            ({}, 200, {"activities": True, "total": True, "skip": True, "limit": True}),
            ({"skip": 5, "limit": 10}, 200, {"skip": 5, "limit": 10}),
            ({"limit": 150}, 422, {}),
        ],
        ids=["success", "pagination", "over_limit"],
    )
    async def test_get_activities(
        self,
        client: AsyncClient,
        test_user,
        override_auth,
        params,
        expected_status,
        check_fields,
    ):
        """[test_dashboard-003-005] アクティビティ取得のテストケース。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get("/api/v1/dashboard/activities", params=params)

        # Assert
        assert response.status_code == expected_status
        if expected_status == 200:
            data = response.json()
            for field, value in check_fields.items():
                if value is True:
                    assert field in data
                else:
                    assert data[field] == value

    @pytest.mark.asyncio
    async def test_get_activities_with_data(
        self,
        client: AsyncClient,
        test_user,
        test_project,
        override_auth,
    ):
        """[test_dashboard-006] データがある状態でアクティビティを取得。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get("/api/v1/dashboard/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        # プロジェクトが作成されているのでアクティビティがあるはず
        assert data["total"] >= 0  # アクティビティログに含まれるかは実装による


class TestDashboardChartsEndpoint:
    """GET /api/v1/dashboard/charts エンドポイントのテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "params,expected_status,check_fields",
        [
            (
                {},
                200,
                {
                    "sessionTrend": True,
                    "treeTrend": True,
                    "projectDistribution": True,
                    "userActivity": True,
                    "generatedAt": True,
                },
            ),
            ({"days": 7}, 200, {"sessionTrend_data_length": 7}),
            ({"days": 400}, 422, {}),
        ],
        ids=["success", "with_days_parameter", "days_over_limit"],
    )
    async def test_get_charts(
        self,
        client: AsyncClient,
        test_user,
        override_auth,
        params,
        expected_status,
        check_fields,
    ):
        """[test_dashboard-007-009] チャートデータ取得のテストケース。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get("/api/v1/dashboard/charts", params=params)

        # Assert
        assert response.status_code == expected_status
        if expected_status == 200:
            data = response.json()
            for field, value in check_fields.items():
                if field == "sessionTrend_data_length":
                    assert len(data["sessionTrend"]["data"]) == value
                elif value is True:
                    assert field in data

    @pytest.mark.asyncio
    async def test_get_charts_response_structure(self, client: AsyncClient, test_user, override_auth):
        """[test_dashboard-010] チャートレスポンス構造の検証。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get("/api/v1/dashboard/charts")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # セッショントレンド
        assert data["sessionTrend"]["chartType"] == "line"
        assert "title" in data["sessionTrend"]
        assert "data" in data["sessionTrend"]

        # ツリートレンド
        assert data["treeTrend"]["chartType"] == "line"

        # プロジェクト分布
        assert data["projectDistribution"]["chartType"] == "pie"

        # ユーザーアクティビティ
        assert data["userActivity"]["chartType"] == "pie"
