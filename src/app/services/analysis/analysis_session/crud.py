"""分析セッションCRUDサービス。

セッションの作成、取得、一覧、削除を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.schemas.analysis import (
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisSessionResponse,
)
from app.services.analysis.analysis_session.base import AnalysisSessionServiceBase

logger = get_logger(__name__)


class AnalysisSessionCrudService(AnalysisSessionServiceBase):
    """分析セッションのCRUD操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """分析セッションCRUDサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    async def list_sessions(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[AnalysisSessionResponse]:
        """プロジェクトに属する分析セッションの一覧を取得します。

        created_at降順でソートされます（最新が先頭）。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            skip: スキップするレコード数
            limit: 取得する最大レコード数
            is_active: アクティブフラグフィルタ

        Returns:
            list[AnalysisSessionResponse]: セッション一覧
        """
        sessions = await self.session_repository.list_by_project(
            project_id=project_id,
            skip=skip,
            limit=limit,
        )
        response = []
        for s in sessions:
            current_snapshot_order = s.current_snapshot.snapshot_order if s.current_snapshot else 0
            response.append(
                AnalysisSessionResponse(
                    current_snapshot=current_snapshot_order,
                    id=s.id,
                    project_id=s.project_id,
                    issue_id=s.issue_id,
                    creator_id=s.creator_id,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )
        return response

    @transactional
    async def create_session(
        self,
        project_id: uuid.UUID,
        creator_id: uuid.UUID,
        session_create: AnalysisSessionCreate,
    ) -> AnalysisSessionDetailResponse:
        """新しい分析セッションを作成します。

        - セッション作成時に初期スナップショット（snapshot_id=0）が作成されます
        - validation_config（施策・課題）が設定されます
        - 空のチャット履歴が初期化されます

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            creator_id: 作成者のユーザーID
            session_create: セッション作成データ

        Returns:
            AnalysisSessionDetailResponse: 作成されたセッション詳細

        Raises:
            NotFoundError: 施策または課題が見つからない場合
        """
        # セッションを作成（current_snapshot_idは初期スナップショット作成後に設定）
        session = await self.session_repository.create(
            project_id=project_id,
            issue_id=session_create.issue_id,
            creator_id=creator_id,
        )

        # 初期スナップショットを作成
        snapshot = await self.snapshot_repository.create(
            session_id=session.id,
            snapshot_order=0,
        )

        # セッションのcurrent_snapshot_idを設定
        session = await self.session_repository.update(session, current_snapshot_id=snapshot.id)

        # issueを取得して課題のpromptを作成
        issue = await self.issue_repository.get(session_create.issue_id)
        if not issue:
            raise NotFoundError(
                "Issue not found",
                details={"issue_id": str(session_create.issue_id)},
            )
        agent_prompt = issue.agent_prompt
        await self.chat_repository.create(
            snapshot_id=snapshot.id,
            chat_order=0,
            role="system",
            message=agent_prompt,
        )

        # リレーションを取得してレスポンスを構築
        await self.db.commit()
        session = await self.session_repository.get_with_relations(session.id)
        if not session:
            raise NotFoundError("セッション作成後の取得に失敗しました")
        snapshots = await self.snapshot_repository.list_by_session(session.id)
        for snap in snapshots:
            snap_with_relations = await self.snapshot_repository.get_with_relations(snap.id)
            if snap_with_relations:
                snap.chats = snap_with_relations.chats
                snap.steps = snap_with_relations.steps

        files = await self.file_repository.list_by_session(session.id)

        return self._build_session_detail_response(session, snapshots, files)

    async def get_session(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> AnalysisSessionDetailResponse:
        """分析セッション詳細を取得します。

        ステップ、ファイル、チャット履歴を含む完全な情報を返します。
        N+1クエリを回避するため、selectinloadを使用します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID

        Returns:
            AnalysisSessionDetailResponse: セッション詳細

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # セッションを取得
        session = await self.session_repository.get_with_relations(session_id)
        if not session:
            raise NotFoundError(
                "セッションが見つかりません",
                details={"session_id": str(session_id)},
            )

        # プロジェクトの一致を確認
        if session.project_id != project_id:
            raise NotFoundError(
                "このプロジェクトにセッションが見つかりません",
                details={"session_id": str(session_id), "project_id": str(project_id)},
            )

        # スナップショットを取得（チャット、ステップ含む）
        snapshots = await self.snapshot_repository.list_by_session(session_id)
        for snap in snapshots:
            snap_with_relations = await self.snapshot_repository.get_with_relations(snap.id)
            if snap_with_relations:
                snap.chats = snap_with_relations.chats
                snap.steps = snap_with_relations.steps

        # ファイルを取得
        files = await self.file_repository.list_by_session(session_id)

        return self._build_session_detail_response(session, snapshots, files)

    @transactional
    async def delete_session(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> None:
        """分析セッションを削除します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # セッションを取得して存在確認
        session = await self.session_repository.get(session_id)
        if not session:
            raise NotFoundError(
                "セッションが見つかりません",
                details={"session_id": str(session_id)},
            )

        # プロジェクトの一致を確認
        if session.project_id != project_id:
            raise NotFoundError(
                "このプロジェクトにセッションが見つかりません",
                details={"session_id": str(session_id), "project_id": str(project_id)},
            )

        # セッションを削除（CASCADEで関連データも削除される）
        await self.session_repository.delete(session_id)

    @transactional
    async def duplicate_session(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        creator_id: uuid.UUID,
        new_name: str | None = None,
    ) -> AnalysisSessionDetailResponse:
        """分析セッションを複製します。

        セッションとその関連データ（スナップショット、ステップ、チャット、ファイル）を
        深いコピーで複製します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: 複製元セッションID
            creator_id: 複製実行者のユーザーID
            new_name: 新しいセッション名（オプション、未指定の場合は自動生成）

        Returns:
            AnalysisSessionDetailResponse: 複製されたセッション詳細

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # 複製元セッションを取得
        original_session = await self.session_repository.get_with_relations(session_id)
        if not original_session:
            raise NotFoundError(
                "セッションが見つかりません",
                details={"session_id": str(session_id)},
            )

        if original_session.project_id != project_id:
            raise NotFoundError(
                "このプロジェクトにセッションが見つかりません",
                details={"session_id": str(session_id), "project_id": str(project_id)},
            )

        # 新しいセッションを作成（current_snapshot_idはスナップショット複製後に設定）
        new_session = await self.session_repository.create(
            project_id=project_id,
            issue_id=original_session.issue_id,
            creator_id=creator_id,
            status=original_session.status if hasattr(original_session, "status") else "draft",
        )

        # 元のcurrent_snapshot_idを保存
        original_current_snapshot_id = original_session.current_snapshot_id

        # スナップショットを複製
        original_snapshots = await self.snapshot_repository.list_by_session(session_id)
        snapshot_id_mapping: dict[uuid.UUID, uuid.UUID] = {}

        for original_snap in original_snapshots:
            # 親スナップショットIDをマッピング
            parent_id = None
            if hasattr(original_snap, "parent_snapshot_id") and original_snap.parent_snapshot_id:
                parent_id = snapshot_id_mapping.get(original_snap.parent_snapshot_id)

            new_snap = await self.snapshot_repository.create(
                session_id=new_session.id,
                snapshot_order=original_snap.snapshot_order,
                parent_snapshot_id=parent_id,
            )
            snapshot_id_mapping[original_snap.id] = new_snap.id

            # ステップを複製
            original_steps = await self.step_repository.list_by_snapshot(original_snap.id)
            for step in original_steps:
                await self.step_repository.create(
                    snapshot_id=new_snap.id,
                    name=step.name,
                    step_order=step.step_order,
                    type=step.type,
                    input=step.input,
                    config=step.config,
                )

            # チャットを複製
            original_chats = await self.chat_repository.list_by_snapshot(original_snap.id)
            for chat in original_chats:
                await self.chat_repository.create(
                    snapshot_id=new_snap.id,
                    chat_order=chat.chat_order,
                    role=chat.role,
                    message=chat.message,
                )

        # ファイルを複製
        original_files = await self.file_repository.list_by_session(session_id)
        for file in original_files:
            await self.file_repository.create(
                session_id=new_session.id,
                project_file_id=file.project_file_id,
                sheet_name=file.sheet_name,
                axis_config=file.axis_config,
                data=file.data,
            )

        # current_snapshot_idを設定（元のスナップショットに対応する新しいスナップショットID）
        if original_current_snapshot_id and original_current_snapshot_id in snapshot_id_mapping:
            new_current_snapshot_id = snapshot_id_mapping[original_current_snapshot_id]
            new_session = await self.session_repository.update(new_session, current_snapshot_id=new_current_snapshot_id)

        # リレーションを取得してレスポンスを構築
        await self.db.commit()
        new_session = await self.session_repository.get_with_relations(new_session.id)
        if not new_session:
            raise NotFoundError("セッション複製後の取得に失敗しました")
        snapshots = await self.snapshot_repository.list_by_session(new_session.id)
        for snap in snapshots:
            snap_with_relations = await self.snapshot_repository.get_with_relations(snap.id)
            if snap_with_relations:
                snap.chats = snap_with_relations.chats
                snap.steps = snap_with_relations.steps

        files = await self.file_repository.list_by_session(new_session.id)

        return self._build_session_detail_response(new_session, snapshots, files)
