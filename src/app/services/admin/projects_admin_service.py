"""管理者用プロジェクト管理サービス。

このモジュールは、管理者向けの全プロジェクト管理機能を提供します。
"""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.decorators import measure_performance
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models import Project, ProjectMember
from app.schemas.admin.project_admin import (
    AdminProjectDetailResponse,
    AdminProjectListResponse,
    AdminProjectResponse,
    AdminProjectStatistics,
    ProjectOwnerInfo,
    ProjectStorageListResponse,
    ProjectStorageResponse,
)
from app.utils import DataFormatter

logger = get_logger(__name__)


class ProjectsAdminService:
    """管理者用プロジェクト管理サービス。

    全プロジェクトの閲覧・管理機能を提供します。

    メソッド:
        - get_all_projects: 全プロジェクト一覧を取得
        - get_project_detail: プロジェクト詳細を取得（管理者ビュー）
        - get_storage_usage: プロジェクト別ストレージ使用量を取得
        - get_inactive_projects: 非アクティブプロジェクトを取得
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db

    def _build_project_response(
        self,
        project: Project,
        member_count: int,
        storage_used_bytes: int,
    ) -> AdminProjectResponse:
        """プロジェクトレスポンスを構築します（DRY原則）。

        Args:
            project: プロジェクトモデル
            member_count: メンバー数
            storage_used_bytes: ストレージ使用量（バイト）

        Returns:
            AdminProjectResponse: 管理者用プロジェクトレスポンス
        """
        # オーナー情報を構築（オーナーが存在しない場合はNone）
        owner_info = None
        if project.owner:
            owner_info = ProjectOwnerInfo(
                id=project.owner.id,
                name=project.owner.display_name or project.owner.email,
            )

        return AdminProjectResponse(
            id=project.id,
            name=project.name,
            owner=owner_info,
            status="active" if project.is_active else "archived",
            member_count=member_count,
            storage_used_bytes=storage_used_bytes,
            storage_used_display=DataFormatter.format_bytes(storage_used_bytes),
            last_activity_at=project.updated_at,
            created_at=project.created_at,
        )

    @measure_performance
    async def get_all_projects(
        self,
        status: str | None = None,
        owner_id: uuid.UUID | None = None,
        inactive_days: int | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 50,
    ) -> AdminProjectListResponse:
        """全プロジェクト一覧を取得します。

        Args:
            status: ステータスフィルタ（active/archived/deleted）
            owner_id: オーナーIDフィルタ
            inactive_days: 非アクティブ日数フィルタ
            search: 検索キーワード
            sort_by: ソート項目
            sort_order: ソート順（asc/desc）
            page: ページ番号
            limit: 取得件数

        Returns:
            AdminProjectListResponse: プロジェクト一覧と統計情報
        """
        logger.info(
            "全プロジェクト一覧を取得中",
            status=status,
            page=page,
            limit=limit,
            action="get_all_projects",
        )

        # 基本クエリ
        query = select(Project).options(selectinload(Project.owner))

        # フィルタ適用
        if status == "active":
            query = query.where(Project.is_active == True)  # noqa: E712
        elif status == "archived":
            query = query.where(Project.is_active == False)  # noqa: E712

        if owner_id:
            query = query.where(Project.created_by == owner_id)

        if search:
            query = query.where(Project.name.ilike(f"%{search}%"))

        # ソート
        sort_mapping = {
            "storage": Project.id,  # TODO: ストレージカラム追加時に変更
            "last_activity": Project.updated_at,
            "created_at": Project.created_at,
        }
        sort_column = sort_mapping.get(sort_by or "created_at", Project.created_at)

        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # 総件数取得
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one() or 0

        # ページネーション
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # プロジェクト取得
        result = await self.db.execute(query)
        projects = result.scalars().all()

        # プロジェクトID一覧を取得
        project_ids = [project.id for project in projects]

        # メンバー数を一括取得（N+1回避）
        member_counts: dict[uuid.UUID, int] = {}
        if project_ids:
            member_count_query = (
                select(ProjectMember.project_id, func.count().label("count"))
                .where(ProjectMember.project_id.in_(project_ids))
                .group_by(ProjectMember.project_id)
            )
            member_count_result = await self.db.execute(member_count_query)
            # SQLAlchemy Rowのcount属性はmypy上Callableに見える問題の回避
            member_counts = {
                row.project_id: row.count  # type: ignore[misc]
                for row in member_count_result.all()
            }

        # レスポンス構築（共通メソッドでDRY化）
        items = []
        for project in projects:
            # メンバー数を辞書から取得
            member_count = member_counts.get(project.id, 0)

            # TODO: 実際のストレージ使用量を計算（現在はプレースホルダ）
            storage_used_bytes = 0

            items.append(
                self._build_project_response(project, member_count, storage_used_bytes)
            )

        # 統計情報取得
        statistics = await self._get_project_statistics()

        return AdminProjectListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            statistics=statistics,
        )

    async def _get_project_statistics(self) -> AdminProjectStatistics:
        """プロジェクト統計情報を取得します。"""
        # 1クエリで全カウントを取得
        from sqlalchemy import case

        result = await self.db.execute(
            select(
                func.count(Project.id).label("total"),
                func.count(case((Project.is_active == True, 1))).label(  # noqa: E712
                    "active"
                ),
                func.count(case((Project.is_active == False, 1))).label(  # noqa: E712
                    "archived"
                ),
            )
        )
        row = result.one()

        # TODO: 削除済みプロジェクトのカウント（deleted_atカラム追加時）
        deleted_projects = 0

        # TODO: 実際のストレージ使用量を集計
        total_storage_bytes = 0

        return AdminProjectStatistics(
            total_projects=row.total or 0,
            active_projects=row.active or 0,
            archived_projects=row.archived or 0,
            deleted_projects=deleted_projects,
            total_storage_bytes=total_storage_bytes,
            total_storage_display=DataFormatter.format_bytes(total_storage_bytes),
        )

    @measure_performance
    async def get_project_detail(
        self, project_id: uuid.UUID
    ) -> AdminProjectDetailResponse:
        """プロジェクト詳細を取得します（管理者ビュー）。

        Args:
            project_id: プロジェクトID

        Returns:
            AdminProjectDetailResponse: プロジェクト詳細

        Raises:
            NotFoundError: プロジェクトが見つからない場合
        """
        logger.info(
            "プロジェクト詳細を取得中",
            project_id=str(project_id),
            action="get_project_detail",
        )

        query = (
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.owner))
        )

        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundError(
                f"プロジェクト（ID: {project_id}）が見つかりません",
                details={"project_id": str(project_id)},
            )

        # メンバー数取得
        member_count_query = (
            select(func.count())
            .select_from(ProjectMember)
            .where(ProjectMember.project_id == project_id)
        )
        member_count_result = await self.db.execute(member_count_query)
        member_count = member_count_result.scalar_one() or 0

        # TODO: 実際のストレージ使用量を計算
        storage_used_bytes = 0

        # オーナー情報を構築（オーナーが存在しない場合はNone）
        owner_info = None
        if project.owner:
            owner_info = ProjectOwnerInfo(
                id=project.owner.id,
                name=project.owner.display_name or project.owner.email,
            )

        return AdminProjectDetailResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            owner=owner_info,
            status="active" if project.is_active else "archived",
            member_count=member_count,
            storage_used_bytes=storage_used_bytes,
            storage_used_display=DataFormatter.format_bytes(storage_used_bytes),
            last_activity_at=project.updated_at,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @measure_performance
    async def get_storage_usage(
        self,
        sort_by: str = "storage",
        limit: int = 50,
    ) -> ProjectStorageListResponse:
        """プロジェクト別ストレージ使用量を取得します。

        Args:
            sort_by: ソート項目（storage/file_count）
            limit: 取得件数

        Returns:
            ProjectStorageListResponse: ストレージ使用量一覧
        """
        logger.info(
            "プロジェクト別ストレージ使用量を取得中",
            sort_by=sort_by,
            limit=limit,
            action="get_storage_usage",
        )

        # 全プロジェクト取得
        query = (
            select(Project).where(Project.is_active == True).limit(limit)  # noqa: E712
        )

        result = await self.db.execute(query)
        projects = result.scalars().all()

        items = []
        total_storage_bytes = 0

        for project in projects:
            # TODO: 実際のストレージ使用量とファイル数を計算
            storage_used_bytes = 0
            file_count = 0
            total_storage_bytes += storage_used_bytes

            items.append(
                ProjectStorageResponse(
                    project_id=project.id,
                    project_name=project.name,
                    storage_used_bytes=storage_used_bytes,
                    storage_used_display=DataFormatter.format_bytes(storage_used_bytes),
                    file_count=file_count,
                )
            )

        # ソート
        if sort_by == "storage":
            items.sort(key=lambda x: x.storage_used_bytes, reverse=True)
        elif sort_by == "file_count":
            items.sort(key=lambda x: x.file_count, reverse=True)

        return ProjectStorageListResponse(
            items=items,
            total_storage_bytes=total_storage_bytes,
            total_storage_display=DataFormatter.format_bytes(total_storage_bytes),
        )

    @measure_performance
    async def get_inactive_projects(
        self,
        inactive_days: int = 30,
        page: int = 1,
        limit: int = 50,
    ) -> AdminProjectListResponse:
        """非アクティブプロジェクト一覧を取得します。

        Args:
            inactive_days: 非アクティブ判定日数
            page: ページ番号
            limit: 取得件数

        Returns:
            AdminProjectListResponse: 非アクティブプロジェクト一覧
        """
        logger.info(
            "非アクティブプロジェクト一覧を取得中",
            inactive_days=inactive_days,
            page=page,
            limit=limit,
            action="get_inactive_projects",
        )

        from datetime import UTC, timedelta

        cutoff_date = datetime.now(UTC) - timedelta(days=inactive_days)

        # 非アクティブプロジェクト取得
        query = (
            select(Project)
            .where(
                Project.is_active == True,  # noqa: E712
                Project.updated_at < cutoff_date,
            )
            .options(selectinload(Project.owner))
            .order_by(Project.updated_at.asc())
        )

        # 総件数取得
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one() or 0

        # ページネーション
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        projects = result.scalars().all()

        # プロジェクトID一覧を取得
        project_ids = [project.id for project in projects]

        # メンバー数を一括取得（N+1回避）
        member_counts: dict[uuid.UUID, int] = {}
        if project_ids:
            member_count_query = (
                select(ProjectMember.project_id, func.count().label("count"))
                .where(ProjectMember.project_id.in_(project_ids))
                .group_by(ProjectMember.project_id)
            )
            member_count_result = await self.db.execute(member_count_query)
            # SQLAlchemy Rowのcount属性はmypy上Callableに見える問題の回避
            member_counts = {
                row.project_id: row.count  # type: ignore[misc]
                for row in member_count_result.all()
            }

        # レスポンス構築（共通メソッドでDRY化）
        items = []
        for project in projects:
            # メンバー数を辞書から取得
            member_count = member_counts.get(project.id, 0)

            # TODO: 実際のストレージ使用量を計算
            storage_used_bytes = 0

            items.append(
                self._build_project_response(project, member_count, storage_used_bytes)
            )

        # 統計情報取得
        statistics = await self._get_project_statistics()

        return AdminProjectListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            statistics=statistics,
        )
