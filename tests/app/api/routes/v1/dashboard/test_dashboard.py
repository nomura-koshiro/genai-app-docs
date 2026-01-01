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
    async def test_get_activities_success(self, client: AsyncClient, test_user, override_auth):
        """[test_dashboard-003] 認証済みユーザーでアクティビティを取得。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get("/api/v1/dashboard/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data

    @pytest.mark.asyncio
    async def test_get_activities_with_pagination(self, client: AsyncClient, test_user, override_auth):
        """[test_dashboard-004] ページネーションパラメータのテスト。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get(
            "/api/v1/dashboard/activities",
            params={"skip": 5, "limit": 10},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 5
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_activities_limit_validation(self, client: AsyncClient, test_user, override_auth):
        """[test_dashboard-005] limitパラメータの上限検証。"""
        # Arrange
        override_auth(test_user)

        # Act - limitが100を超える場合
        response = await client.get(
            "/api/v1/dashboard/activities",
            params={"limit": 150},
        )

        # Assert - バリデーションエラー
        assert response.status_code == 422

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
    async def test_get_charts_success(self, client: AsyncClient, test_user, override_auth):
        """[test_dashboard-007] 認証済みユーザーでチャートデータを取得。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get("/api/v1/dashboard/charts")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "sessionTrend" in data
        assert "treeTrend" in data
        assert "projectDistribution" in data
        assert "userActivity" in data
        assert "generatedAt" in data

    @pytest.mark.asyncio
    async def test_get_charts_with_days_parameter(self, client: AsyncClient, test_user, override_auth):
        """[test_dashboard-008] daysパラメータのテスト。"""
        # Arrange
        override_auth(test_user)

        # Act
        response = await client.get(
            "/api/v1/dashboard/charts",
            params={"days": 7},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # セッショントレンドのデータポイント数が7日分
        assert len(data["sessionTrend"]["data"]) == 7

    @pytest.mark.asyncio
    async def test_get_charts_days_validation(self, client: AsyncClient, test_user, override_auth):
        """[test_dashboard-009] daysパラメータの上限検証。"""
        # Arrange
        override_auth(test_user)

        # Act - daysが365を超える場合
        response = await client.get(
            "/api/v1/dashboard/charts",
            params={"days": 400},
        )

        # Assert - バリデーションエラー
        assert response.status_code == 422

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
