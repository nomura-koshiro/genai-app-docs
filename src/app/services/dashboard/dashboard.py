"""ダッシュボードサービス。

このモジュールは、ダッシュボード機能のビジネスロジックを提供します。
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis.analysis_session import AnalysisSession
from app.models.driver_tree.driver_tree import DriverTree
from app.models.project.project import Project
from app.models.project.project_file import ProjectFile
from app.models.user_account.user_account import UserAccount
from app.schemas.dashboard.dashboard import (
    ActivityLogResponse,
    ChartDataPoint,
    ChartDataResponse,
    DashboardActivitiesResponse,
    DashboardChartsResponse,
    DashboardStatsResponse,
    FileStats,
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

        # ファイル統計
        file_total = await self.db.scalar(select(func.count(ProjectFile.id)))
        file_total_size = await self.db.scalar(
            select(func.coalesce(func.sum(ProjectFile.file_size), 0))
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
            files=FileStats(
                total=file_total or 0,
                total_size_bytes=int(file_total_size or 0),
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
        """作成トレンドを効率的に取得。

        GROUP BYを使用して単一クエリで日別集計を行います。
        N+1クエリを回避し、30日分のデータを1回のクエリで取得します。

        Args:
            model: 対象モデルクラス
            start_date: 集計開始日
            days: 日数

        Returns:
            list[ChartDataPoint]: データポイントリスト（0埋め済み）
        """
        end_date = start_date + timedelta(days=days)

        # 日別の件数を一括集計
        result = await self.db.execute(
            select(
                cast(model.created_at, Date).label("date"),
                func.count(model.id).label("count"),
            )
            .where(
                model.created_at >= start_date,
                model.created_at < end_date,
            )
            .group_by(cast(model.created_at, Date))
        )

        # 結果をマップに変換
        count_map = {row[0]: row[1] for row in result.all()}

        # 全日付のデータポイントを作成（0埋め）
        data_points = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            date_key = current_date.date()

            data_points.append(
                ChartDataPoint(
                    label=current_date.strftime("%Y-%m-%d"),
                    value=float(count_map.get(date_key, 0)),
                )
            )

        return data_points

    async def get_activities(self, skip: int = 0, limit: int = 20) -> DashboardActivitiesResponse:
        """アクティビティログを効率的に取得。

        複数のデータソースから最近のアクティビティを集約して返します。
        各リソースタイプから必要最小限のデータを取得し、メモリ上でマージします。

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            DashboardActivitiesResponse: アクティビティログ
        """
        # 各リソースから取得する件数（skip + limit で必要な件数を確保）
        fetch_limit = skip + limit

        # 並列でクエリを実行するためのリストを構築
        activities: list[ActivityLogResponse] = []

        # プロジェクト作成を取得
        projects = await self._get_recent_projects(fetch_limit)
        activities.extend(projects)

        # セッション作成を取得
        sessions = await self._get_recent_sessions(fetch_limit)
        activities.extend(sessions)

        # ツリー作成を取得
        trees = await self._get_recent_trees(fetch_limit)
        activities.extend(trees)

        # ファイルアップロードを取得
        files = await self._get_recent_files(fetch_limit)
        activities.extend(files)

        # 日時でソートして上位を返す
        activities.sort(key=lambda x: x.created_at, reverse=True)
        total = len(activities)
        paginated = activities[skip : skip + limit]

        return DashboardActivitiesResponse(
            activities=paginated,
            total=total,
            skip=skip,
            limit=limit,
        )

    async def _get_recent_projects(self, limit: int) -> list[ActivityLogResponse]:
        """最近のプロジェクト作成アクティビティを取得。"""
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.created_by_user))
            .order_by(Project.created_at.desc())
            .limit(limit)
        )
        return [
            ActivityLogResponse(
                id=p.id,
                user_id=p.created_by if p.created_by else uuid.uuid4(),
                user_name=p.created_by_user.display_name if p.created_by_user else "Unknown",
                action="created",
                resource_type="project",
                resource_id=p.id,
                resource_name=p.name,
                details={"description": p.description},
                created_at=p.created_at,
            )
            for p in result.scalars().all()
        ]

    async def _get_recent_sessions(self, limit: int) -> list[ActivityLogResponse]:
        """最近のセッション作成アクティビティを取得。"""
        result = await self.db.execute(
            select(AnalysisSession)
            .options(selectinload(AnalysisSession.created_by_user))
            .order_by(AnalysisSession.created_at.desc())
            .limit(limit)
        )
        return [
            ActivityLogResponse(
                id=s.id,
                user_id=s.created_by if s.created_by else uuid.uuid4(),
                user_name=s.created_by_user.display_name if s.created_by_user else "Unknown",
                action="created",
                resource_type="session",
                resource_id=s.id,
                resource_name=s.name or "",
                details={"status": s.status},
                created_at=s.created_at,
            )
            for s in result.scalars().all()
        ]

    async def _get_recent_trees(self, limit: int) -> list[ActivityLogResponse]:
        """最近のツリー作成アクティビティを取得。"""
        result = await self.db.execute(
            select(DriverTree)
            .options(selectinload(DriverTree.created_by_user))
            .order_by(DriverTree.created_at.desc())
            .limit(limit)
        )
        return [
            ActivityLogResponse(
                id=t.id,
                user_id=t.created_by if t.created_by else uuid.uuid4(),
                user_name=t.created_by_user.display_name if t.created_by_user else "Unknown",
                action="created",
                resource_type="tree",
                resource_id=t.id,
                resource_name=t.name,
                details={"status": t.status},
                created_at=t.created_at,
            )
            for t in result.scalars().all()
        ]

    async def _get_recent_files(self, limit: int) -> list[ActivityLogResponse]:
        """最近のファイルアップロードアクティビティを取得。"""
        result = await self.db.execute(
            select(ProjectFile)
            .options(selectinload(ProjectFile.uploaded_by_user))
            .order_by(ProjectFile.created_at.desc())
            .limit(limit)
        )
        return [
            ActivityLogResponse(
                id=f.id,
                user_id=f.uploaded_by if f.uploaded_by else uuid.uuid4(),
                user_name=f.uploaded_by_user.display_name if f.uploaded_by_user else "Unknown",
                action="uploaded",
                resource_type="file",
                resource_id=f.id,
                resource_name=f.original_filename,
                details={"size": f.file_size, "mime_type": f.mime_type},
                created_at=f.created_at,
            )
            for f in result.scalars().all()
        ]
