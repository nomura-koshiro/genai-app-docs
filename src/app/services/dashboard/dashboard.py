"""ダッシュボードサービス。

このモジュールは、ダッシュボード機能のビジネスロジックを提供します。
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis.analysis_session import AnalysisSession
from app.models.driver_tree.driver_tree import DriverTree
from app.models.project.project import Project
from app.models.user_account.user_account import UserAccount
from app.schemas.dashboard.dashboard import (
    ChartDataPoint,
    ChartDataResponse,
    DashboardChartsResponse,
    DashboardStatsResponse,
    ProjectStats,
    SessionStats,
    TreeStats,
    UserStats,
)


class DashboardService:
    """ダッシュボードサービスクラス。

    ダッシュボードに関するビジネスロジックを提供します。
    """

    def __init__(self, db: AsyncSession):
        """初期化。

        Args:
            db: データベースセッション
        """
        self.db = db

    async def get_stats(self) -> DashboardStatsResponse:
        """統計情報を取得。

        Returns:
            DashboardStatsResponse: 統計情報
        """
        # プロジェクト統計
        project_total = await self.db.scalar(select(func.count(Project.id)))
        project_active = await self.db.scalar(
            select(func.count(Project.id)).where(Project.is_active == True)  # noqa: E712
        )
        project_archived = (project_total or 0) - (project_active or 0)

        # セッション統計
        session_total = await self.db.scalar(select(func.count(AnalysisSession.id)))
        session_draft = await self.db.scalar(select(func.count(AnalysisSession.id)).where(AnalysisSession.status == "draft"))
        session_active = await self.db.scalar(select(func.count(AnalysisSession.id)).where(AnalysisSession.status == "active"))
        session_completed = await self.db.scalar(select(func.count(AnalysisSession.id)).where(AnalysisSession.status == "completed"))

        # ツリー統計
        tree_total = await self.db.scalar(select(func.count(DriverTree.id)))
        tree_draft = await self.db.scalar(select(func.count(DriverTree.id)).where(DriverTree.status == "draft"))
        tree_active = await self.db.scalar(select(func.count(DriverTree.id)).where(DriverTree.status == "active"))
        tree_completed = await self.db.scalar(select(func.count(DriverTree.id)).where(DriverTree.status == "completed"))

        # ユーザー統計
        user_total = await self.db.scalar(select(func.count(UserAccount.id)))
        user_active = await self.db.scalar(
            select(func.count(UserAccount.id)).where(UserAccount.is_active == True)  # noqa: E712
        )

        return DashboardStatsResponse(
            projects=ProjectStats(
                total=project_total or 0,
                active=project_active or 0,
                archived=project_archived,
            ),
            sessions=SessionStats(
                total=session_total or 0,
                draft=session_draft or 0,
                active=session_active or 0,
                completed=session_completed or 0,
            ),
            trees=TreeStats(
                total=tree_total or 0,
                draft=tree_draft or 0,
                active=tree_active or 0,
                completed=tree_completed or 0,
            ),
            users=UserStats(
                total=user_total or 0,
                active=user_active or 0,
            ),
            generated_at=datetime.utcnow(),
        )

    async def get_charts(self, days: int = 30) -> DashboardChartsResponse:
        """チャートデータを取得。

        Args:
            days: 集計対象日数（デフォルト30日）

        Returns:
            DashboardChartsResponse: チャートデータ
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # セッション作成トレンド（日別）
        session_trend_data = await self._get_creation_trend(AnalysisSession, start_date, days)

        # ツリー作成トレンド（日別）
        tree_trend_data = await self._get_creation_trend(DriverTree, start_date, days)

        # プロジェクト状態分布
        project_active = await self.db.scalar(
            select(func.count(Project.id)).where(Project.is_active == True)  # noqa: E712
        )
        project_archived = await self.db.scalar(
            select(func.count(Project.id)).where(Project.is_active == False)  # noqa: E712
        )

        project_distribution = ChartDataResponse(
            chart_type="pie",
            title="プロジェクト状態分布",
            data=[
                ChartDataPoint(label="アクティブ", value=float(project_active or 0)),
                ChartDataPoint(label="アーカイブ", value=float(project_archived or 0)),
            ],
        )

        # ユーザーアクティビティ（直近のログイン状況）
        user_active = await self.db.scalar(
            select(func.count(UserAccount.id)).where(UserAccount.is_active == True)  # noqa: E712
        )
        user_inactive = await self.db.scalar(
            select(func.count(UserAccount.id)).where(UserAccount.is_active == False)  # noqa: E712
        )

        user_activity = ChartDataResponse(
            chart_type="pie",
            title="ユーザーアクティビティ",
            data=[
                ChartDataPoint(label="アクティブ", value=float(user_active or 0)),
                ChartDataPoint(label="非アクティブ", value=float(user_inactive or 0)),
            ],
        )

        return DashboardChartsResponse(
            session_trend=ChartDataResponse(
                chart_type="line",
                title="セッション作成トレンド",
                data=session_trend_data,
                x_axis_label="日付",
                y_axis_label="作成数",
            ),
            tree_trend=ChartDataResponse(
                chart_type="line",
                title="ツリー作成トレンド",
                data=tree_trend_data,
                x_axis_label="日付",
                y_axis_label="作成数",
            ),
            project_distribution=project_distribution,
            user_activity=user_activity,
            generated_at=datetime.utcnow(),
        )

    async def _get_creation_trend(self, model: type, start_date: datetime, days: int) -> list[ChartDataPoint]:
        """作成トレンドを取得。

        Args:
            model: 対象モデルクラス
            start_date: 集計開始日
            days: 日数

        Returns:
            list[ChartDataPoint]: データポイントリスト
        """
        data_points = []

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            next_date = current_date + timedelta(days=1)

            count = await self.db.scalar(
                select(func.count(model.id)).where(
                    model.created_at >= current_date,
                    model.created_at < next_date,
                )
            )

            data_points.append(
                ChartDataPoint(
                    label=current_date.strftime("%Y-%m-%d"),
                    value=float(count or 0),
                )
            )

        return data_points
