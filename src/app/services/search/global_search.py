"""グローバル検索サービスの実装。

共通UI設計書（UI-004〜UI-005）に基づくグローバル検索機能を提供します。
"""

import re
import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analysis import AnalysisSession
from app.models.driver_tree import DriverTree
from app.models.project import Project, ProjectFile, ProjectMember
from app.schemas.search import SearchQuery, SearchResponse, SearchResultInfo, SearchTypeEnum

logger = get_logger(__name__)


class GlobalSearchService:
    """グローバル検索サービス。

    プロジェクト・セッション・ファイル・ツリーを横断検索する機能を提供します。
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db

    async def search(
        self,
        query: SearchQuery,
        user_id: uuid.UUID,
    ) -> SearchResponse:
        """グローバル検索を実行します。

        Args:
            query: 検索クエリ
            user_id: 実行ユーザーID

        Returns:
            SearchResponse: 検索結果
        """
        search_text = query.q
        types = query.type or list(SearchTypeEnum)
        project_id = query.project_id
        limit = query.limit

        # 各タイプごとに検索を実行
        all_results: list[SearchResultInfo] = []

        if SearchTypeEnum.PROJECT in types:
            project_results = await self._search_projects(search_text, user_id, limit)
            all_results.extend(project_results)

        if SearchTypeEnum.SESSION in types:
            session_results = await self._search_sessions(
                search_text, user_id, project_id, limit
            )
            all_results.extend(session_results)

        if SearchTypeEnum.FILE in types:
            file_results = await self._search_files(
                search_text, user_id, project_id, limit
            )
            all_results.extend(file_results)

        if SearchTypeEnum.TREE in types:
            tree_results = await self._search_trees(
                search_text, user_id, project_id, limit
            )
            all_results.extend(tree_results)

        # 結果をマージして制限を適用
        merged_results = self._merge_results(all_results, limit)

        return SearchResponse(
            results=merged_results,
            total=len(merged_results),
            query=search_text,
            types=types,
        )

    async def _search_projects(
        self,
        query: str,
        user_id: uuid.UUID,
        limit: int,
    ) -> list[SearchResultInfo]:
        """プロジェクトを検索します。

        Args:
            query: 検索クエリ
            user_id: ユーザーID
            limit: 取得件数

        Returns:
            list[SearchResultInfo]: 検索結果リスト
        """
        # ユーザーがメンバーのプロジェクトのみ検索
        stmt = (
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                ProjectMember.user_id == user_id,
                Project.is_active == True,  # noqa: E712
                or_(
                    Project.name.ilike(f"%{query}%"),
                    Project.description.ilike(f"%{query}%"),
                ),
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        projects = result.scalars().all()

        results: list[SearchResultInfo] = []
        for project in projects:
            # マッチしたフィールドを特定
            if query.lower() in (project.name or "").lower():
                matched_field = "name"
                matched_text = project.name
            else:
                matched_field = "description"
                matched_text = project.description or ""

            results.append(
                SearchResultInfo(
                    type=SearchTypeEnum.PROJECT,
                    id=project.id,
                    name=project.name,
                    description=project.description,
                    matched_field=matched_field,
                    highlighted_text=self._highlight_text(matched_text, query),
                    project_id=None,
                    project_name=None,
                    updated_at=project.updated_at,
                    url=f"/projects/{project.id}",
                )
            )

        return results

    async def _search_sessions(
        self,
        query: str,
        user_id: uuid.UUID,
        project_id: uuid.UUID | None,
        limit: int,
    ) -> list[SearchResultInfo]:
        """分析セッションを検索します。

        Args:
            query: 検索クエリ
            user_id: ユーザーID
            project_id: プロジェクトID（絞り込み用）
            limit: 取得件数

        Returns:
            list[SearchResultInfo]: 検索結果リスト
        """
        # ユーザーがメンバーのプロジェクトのセッションのみ検索
        stmt = (
            select(AnalysisSession, Project)
            .join(Project, Project.id == AnalysisSession.project_id)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                ProjectMember.user_id == user_id,
                AnalysisSession.name.ilike(f"%{query}%"),
            )
        )

        if project_id:
            stmt = stmt.where(AnalysisSession.project_id == project_id)

        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        rows = result.all()

        results: list[SearchResultInfo] = []
        for session, project in rows:
            results.append(
                SearchResultInfo(
                    type=SearchTypeEnum.SESSION,
                    id=session.id,
                    name=session.name,
                    description=None,
                    matched_field="name",
                    highlighted_text=self._highlight_text(session.name, query),
                    project_id=project.id,
                    project_name=project.name,
                    updated_at=session.updated_at,
                    url=f"/projects/{project.id}/sessions/{session.id}",
                )
            )

        return results

    async def _search_files(
        self,
        query: str,
        user_id: uuid.UUID,
        project_id: uuid.UUID | None,
        limit: int,
    ) -> list[SearchResultInfo]:
        """ファイルを検索します。

        Args:
            query: 検索クエリ
            user_id: ユーザーID
            project_id: プロジェクトID（絞り込み用）
            limit: 取得件数

        Returns:
            list[SearchResultInfo]: 検索結果リスト
        """
        # ユーザーがメンバーのプロジェクトのファイルのみ検索
        stmt = (
            select(ProjectFile, Project)
            .join(Project, Project.id == ProjectFile.project_id)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                ProjectMember.user_id == user_id,
                ProjectFile.original_filename.ilike(f"%{query}%"),
            )
        )

        if project_id:
            stmt = stmt.where(ProjectFile.project_id == project_id)

        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        rows = result.all()

        results: list[SearchResultInfo] = []
        for file, project in rows:
            # マッチしたフィールドを特定
            if query.lower() in (file.original_filename or "").lower():
                matched_field = "filename"
                matched_text = file.original_filename
            else:
                matched_field = "description"
                matched_text = file.description or ""

            results.append(
                SearchResultInfo(
                    type=SearchTypeEnum.FILE,
                    id=file.id,
                    name=file.original_filename,
                    description=file.description,
                    matched_field=matched_field,
                    highlighted_text=self._highlight_text(matched_text, query),
                    project_id=project.id,
                    project_name=project.name,
                    updated_at=file.updated_at,
                    url=f"/projects/{project.id}/files/{file.id}",
                )
            )

        return results

    async def _search_trees(
        self,
        query: str,
        user_id: uuid.UUID,
        project_id: uuid.UUID | None,
        limit: int,
    ) -> list[SearchResultInfo]:
        """ドライバーツリーを検索します。

        Args:
            query: 検索クエリ
            user_id: ユーザーID
            project_id: プロジェクトID（絞り込み用）
            limit: 取得件数

        Returns:
            list[SearchResultInfo]: 検索結果リスト
        """
        # ユーザーがメンバーのプロジェクトのツリーのみ検索
        stmt = (
            select(DriverTree, Project)
            .join(Project, Project.id == DriverTree.project_id)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                ProjectMember.user_id == user_id,
                or_(
                    DriverTree.name.ilike(f"%{query}%"),
                    DriverTree.description.ilike(f"%{query}%"),
                ),
            )
        )

        if project_id:
            stmt = stmt.where(DriverTree.project_id == project_id)

        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        rows = result.all()

        results: list[SearchResultInfo] = []
        for tree, project in rows:
            # マッチしたフィールドを特定
            if query.lower() in (tree.name or "").lower():
                matched_field = "name"
                matched_text = tree.name
            else:
                matched_field = "description"
                matched_text = tree.description or ""

            results.append(
                SearchResultInfo(
                    type=SearchTypeEnum.TREE,
                    id=tree.id,
                    name=tree.name,
                    description=tree.description,
                    matched_field=matched_field,
                    highlighted_text=self._highlight_text(matched_text, query),
                    project_id=project.id,
                    project_name=project.name,
                    updated_at=tree.updated_at,
                    url=f"/projects/{project.id}/trees/{tree.id}",
                )
            )

        return results

    def _highlight_text(self, text: str, query: str) -> str:
        """テキスト内のクエリ部分をハイライトします。

        Args:
            text: 対象テキスト
            query: 検索クエリ

        Returns:
            str: ハイライト済みテキスト
        """
        if not text:
            return ""

        # 大文字小文字を無視してハイライト
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(lambda m: f"<mark>{m.group()}</mark>", text)

    def _merge_results(
        self,
        results: list[SearchResultInfo],
        limit: int,
    ) -> list[SearchResultInfo]:
        """検索結果をマージして制限を適用します。

        Args:
            results: 検索結果リスト
            limit: 最大件数

        Returns:
            list[SearchResultInfo]: マージ済み結果
        """
        # 更新日時でソート
        sorted_results = sorted(results, key=lambda r: r.updated_at, reverse=True)
        return sorted_results[:limit]
