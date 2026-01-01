"""ダッシュボードサービスのテスト。

このテストファイルは docs/specifications/13-testing/01-test-strategy.md に従い、
DashboardServiceクラスのビジネスロジックをテストします。

対応メソッド:
    - get_stats() - 統計情報取得
    - get_activities() - アクティビティ取得
    - get_charts() - チャートデータ取得
"""

from datetime import datetime

import pytest

from app.models.user_account.role_history import RoleHistory
from app.services.dashboard.dashboard import DashboardService


class TestDashboardServiceGetStats:
    """get_statsメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_get_stats_empty_database(self, db_session):
        """[test_dashboard-001] 空のデータベースで統計情報を取得。"""
        # Arrange
        service = DashboardService(db_session)

        # Act
        stats = await service.get_stats()

        # Assert
        assert stats.projects.total == 0
        assert stats.projects.active == 0
        assert stats.projects.archived == 0
        assert stats.sessions.total == 0
        assert stats.trees.total == 0
        assert stats.users.total == 0
        assert stats.generated_at is not None

    @pytest.mark.asyncio
    async def test_get_stats_with_data(self, db_session, test_data_seeder):
        """[test_dashboard-002] データがある状態で統計情報を取得。"""
        # Arrange
        # ユーザーを作成
        await test_data_seeder.create_user(display_name="User1", is_active=True)
        await test_data_seeder.create_user(display_name="User2", is_active=True)
        await test_data_seeder.create_user(display_name="User3", is_active=False)

        # プロジェクトを作成
        await test_data_seeder.create_project(name="Project1", is_active=True)
        await test_data_seeder.create_project(name="Project2", is_active=True)
        await test_data_seeder.create_project(name="Project3", is_active=False)

        await db_session.commit()

        service = DashboardService(db_session)

        # Act
        stats = await service.get_stats()

        # Assert
        assert stats.users.total == 3
        assert stats.users.active == 2
        assert stats.projects.total == 3
        assert stats.projects.active == 2
        assert stats.projects.archived == 1


class TestDashboardServiceGetCharts:
    """get_chartsメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_get_charts_empty_database(self, db_session):
        """[test_dashboard-003] 空のデータベースでチャートデータを取得。"""
        # Arrange
        service = DashboardService(db_session)

        # Act
        charts = await service.get_charts(days=7)

        # Assert
        assert charts.session_trend is not None
        assert charts.session_trend.chart_type == "line"
        assert charts.session_trend.title == "セッション作成トレンド"
        assert len(charts.session_trend.data) == 7

        assert charts.tree_trend is not None
        assert charts.tree_trend.chart_type == "line"

        assert charts.project_distribution is not None
        assert charts.project_distribution.chart_type == "pie"

        assert charts.user_activity is not None
        assert charts.user_activity.chart_type == "pie"

        assert charts.generated_at is not None

    @pytest.mark.asyncio
    async def test_get_charts_with_data(self, db_session, test_data_seeder):
        """[test_dashboard-004] データがある状態でチャートデータを取得。"""
        # Arrange
        await test_data_seeder.create_user(display_name="TestUser")
        await test_data_seeder.create_project(name="ActiveProject", is_active=True)
        await test_data_seeder.create_project(name="ArchivedProject", is_active=False)
        await db_session.commit()

        service = DashboardService(db_session)

        # Act
        charts = await service.get_charts(days=30)

        # Assert
        # プロジェクト分布を確認
        active_count = next(
            (d.value for d in charts.project_distribution.data if d.label == "アクティブ"),
            0,
        )
        archived_count = next(
            (d.value for d in charts.project_distribution.data if d.label == "アーカイブ"),
            0,
        )
        assert active_count == 1.0
        assert archived_count == 1.0


class TestDashboardServiceGetActivities:
    """get_activitiesメソッドのテスト。"""

    @pytest.mark.asyncio
    async def test_get_activities_empty_database(self, db_session):
        """[test_dashboard-005] 空のデータベースでアクティビティを取得。"""
        # Arrange
        service = DashboardService(db_session)

        # Act
        activities = await service.get_activities(skip=0, limit=20)

        # Assert
        assert activities.activities == []
        assert activities.total == 0
        assert activities.skip == 0
        assert activities.limit == 20

    @pytest.mark.asyncio
    async def test_get_activities_with_project(self, db_session, test_data_seeder):
        """[test_dashboard-006] プロジェクト作成のアクティビティを取得。"""
        # Arrange
        user = await test_data_seeder.create_user(display_name="TestUser")
        await test_data_seeder.create_project(
            name="TestProject",
            created_by=user.id,
        )
        await db_session.commit()

        service = DashboardService(db_session)

        # Act
        activities = await service.get_activities(skip=0, limit=20)

        # Assert
        assert activities.total > 0
        # プロジェクト作成アクティビティが含まれていることを確認
        project_activities = [a for a in activities.activities if a.resource_type == "project"]
        assert len(project_activities) > 0
        assert project_activities[0].action == "created"
        assert project_activities[0].resource_name == "TestProject"

    @pytest.mark.asyncio
    async def test_get_activities_with_role_history(self, db_session, test_data_seeder):
        """[test_dashboard-007] ロール変更履歴のアクティビティを取得。"""
        # Arrange
        user = await test_data_seeder.create_user(display_name="TestUser")
        admin = await test_data_seeder.create_admin_user()

        # ロール変更履歴を作成
        role_history = RoleHistory(
            user_id=user.id,
            changed_by_id=admin.id,
            action="grant",
            role_type="system",
            old_roles=[],
            new_roles=["Admin"],
            reason="Promotion",
            changed_at=datetime.utcnow(),
        )
        db_session.add(role_history)
        await db_session.commit()

        service = DashboardService(db_session)

        # Act
        activities = await service.get_activities(skip=0, limit=20)

        # Assert
        role_activities = [a for a in activities.activities if a.resource_type == "role"]
        assert len(role_activities) > 0
        assert role_activities[0].action == "grant"

    @pytest.mark.asyncio
    async def test_get_activities_pagination(self, db_session, test_data_seeder):
        """[test_dashboard-008] ページネーションのテスト。"""
        # Arrange
        user = await test_data_seeder.create_user(display_name="TestUser")
        for i in range(5):
            await test_data_seeder.create_project(
                name=f"Project{i}",
                created_by=user.id,
            )
        await db_session.commit()

        service = DashboardService(db_session)

        # Act
        page1 = await service.get_activities(skip=0, limit=2)
        page2 = await service.get_activities(skip=2, limit=2)

        # Assert
        assert len(page1.activities) <= 2
        assert len(page2.activities) <= 2
        # 異なるアクティビティが返されていることを確認
        if page1.activities and page2.activities:
            page1_ids = {a.id for a in page1.activities}
            page2_ids = {a.id for a in page2.activities}
            assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_get_activities_sorted_by_date(self, db_session, test_data_seeder):
        """[test_dashboard-009] 日時順でソートされていることを確認。"""
        # Arrange
        user = await test_data_seeder.create_user(display_name="TestUser")
        for i in range(3):
            await test_data_seeder.create_project(
                name=f"Project{i}",
                created_by=user.id,
            )
        await db_session.commit()

        service = DashboardService(db_session)

        # Act
        activities = await service.get_activities(skip=0, limit=10)

        # Assert
        if len(activities.activities) > 1:
            for i in range(len(activities.activities) - 1):
                assert activities.activities[i].created_at >= activities.activities[i + 1].created_at
