"""ダッシュボードサービス。

このモジュールは、ダッシュボード機能のビジネスロジックを提供します。
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis.analysis_session import AnalysisSession
from app.models.driver_tree.driver_tree import DriverTree
from app.models.project.project import Project
from app.models.project.project_file import ProjectFile
from app.models.user_account.role_history import RoleHistory
from app.models.user_account.user_account import UserAccount
from app.schemas.dashboard.dashboard import (
    ActivityLogResponse,
    ChartDataPoint,
    ChartDataResponse,
    DashboardActivitiesResponse,
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

    async def get_activities(self, skip: int = 0, limit: int = 20) -> DashboardActivitiesResponse:
        """アクティビティログを取得。

        複数のデータソースから最近のアクティビティを集約して返します：
        - ロール変更履歴（RoleHistory）
        - プロジェクト作成/更新
        - セッション作成/更新
        - ツリー作成/更新
        - ファイルアップロード

        Args:
            skip: スキップ数
            limit: 取得件数

        Returns:
            DashboardActivitiesResponse: アクティビティログ
        """
        activities: list[ActivityLogResponse] = []

        # ロール変更履歴を取得
        role_history_query = (
            select(RoleHistory)
            .options(selectinload(RoleHistory.user), selectinload(RoleHistory.changed_by))
            .order_by(RoleHistory.changed_at.desc())
            .limit(limit)
        )
        role_history_result = await self.db.execute(role_history_query)
        role_histories = role_history_result.scalars().all()

        for rh in role_histories:
            user_name = rh.user.display_name if rh.user else "Unknown"
            changed_by_name = rh.changed_by.display_name if rh.changed_by else "System"

            activities.append(
                ActivityLogResponse(
                    id=rh.id,
                    user_id=rh.user_id,
                    user_name=user_name,
                    action=rh.action,
                    resource_type="role",
                    resource_id=rh.user_id,
                    resource_name=f"{rh.role_type} role",
                    details={
                        "old_roles": rh.old_roles,
                        "new_roles": rh.new_roles,
                        "changed_by": changed_by_name,
                        "reason": rh.reason,
                    },
                    created_at=rh.changed_at,
                )
            )

        # プロジェクト作成を取得
        project_query = select(Project).options(selectinload(Project.created_by_user)).order_by(Project.created_at.desc()).limit(limit)
        project_result = await self.db.execute(project_query)
        projects = project_result.scalars().all()

        for p in projects:
            user_name = p.created_by_user.display_name if p.created_by_user else "Unknown"
            activities.append(
                ActivityLogResponse(
                    id=p.id,
                    user_id=p.created_by if p.created_by else uuid.uuid4(),
                    user_name=user_name,
                    action="created",
                    resource_type="project",
                    resource_id=p.id,
                    resource_name=p.name,
                    details={"description": p.description},
                    created_at=p.created_at,
                )
            )

        # セッション作成を取得
        session_query = (
            select(AnalysisSession)
            .options(selectinload(AnalysisSession.created_by_user))
            .order_by(AnalysisSession.created_at.desc())
            .limit(limit)
        )
        session_result = await self.db.execute(session_query)
        sessions = session_result.scalars().all()

        for s in sessions:
            user_name = s.created_by_user.display_name if s.created_by_user else "Unknown"
            activities.append(
                ActivityLogResponse(
                    id=s.id,
                    user_id=s.created_by if s.created_by else uuid.uuid4(),
                    user_name=user_name,
                    action="created",
                    resource_type="session",
                    resource_id=s.id,
                    resource_name=s.name,
                    details={"status": s.status},
                    created_at=s.created_at,
                )
            )

        # ツリー作成を取得
        tree_query = (
            select(DriverTree).options(selectinload(DriverTree.created_by_user)).order_by(DriverTree.created_at.desc()).limit(limit)
        )
        tree_result = await self.db.execute(tree_query)
        trees = tree_result.scalars().all()

        for t in trees:
            user_name = t.created_by_user.display_name if t.created_by_user else "Unknown"
            activities.append(
                ActivityLogResponse(
                    id=t.id,
                    user_id=t.created_by if t.created_by else uuid.uuid4(),
                    user_name=user_name,
                    action="created",
                    resource_type="tree",
                    resource_id=t.id,
                    resource_name=t.name,
                    details={"status": t.status},
                    created_at=t.created_at,
                )
            )

        # ファイルアップロードを取得
        file_query = (
            select(ProjectFile).options(selectinload(ProjectFile.uploaded_by_user)).order_by(ProjectFile.created_at.desc()).limit(limit)
        )
        file_result = await self.db.execute(file_query)
        files = file_result.scalars().all()

        for f in files:
            user_name = f.uploaded_by_user.display_name if f.uploaded_by_user else "Unknown"
            activities.append(
                ActivityLogResponse(
                    id=f.id,
                    user_id=f.uploaded_by if f.uploaded_by else uuid.uuid4(),
                    user_name=user_name,
                    action="uploaded",
                    resource_type="file",
                    resource_id=f.id,
                    resource_name=f.original_filename,
                    details={"size": f.file_size, "mime_type": f.mime_type},
                    created_at=f.created_at,
                )
            )

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
