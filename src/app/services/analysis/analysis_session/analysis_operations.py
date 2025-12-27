"""分析操作サービス。

分析結果取得、チャット実行、スナップショット復元を提供します。
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.schemas.analysis import (
    AnalysisChatResponse,
    AnalysisSessionDetailResponse,
    AnalysisSessionResultListResponse,
    AnalysisSessionResultResponse,
    AnalysisSnapshotCreate,
    AnalysisSnapshotResponse,
    AnalysisStepResponse,
)
from app.services.analysis.analysis_session.base import AnalysisSessionServiceBase

logger = get_logger(__name__)


class AnalysisSessionAnalysisService(AnalysisSessionServiceBase):
    """分析操作機能を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """分析操作サービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    async def get_session_result(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> AnalysisSessionResultListResponse:
        """分析セッションの結果を取得します。

        最新snapshotに存在するsummaryステップにある結果を一覧表記。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID

        Returns:
            AnalysisSessionResultListResponse: 分析結果

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # セッションを取得
        session = await self.session_repository.get(session_id)
        if not session or session.project_id != project_id:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # 最新スナップショットを取得
        snapshot = await self.snapshot_repository.get_by_order(session_id, session.current_snapshot)
        if not snapshot:
            return AnalysisSessionResultListResponse(results=[], total=0)

        # summaryステップを取得
        summary_steps = await self.step_repository.get_summary_steps(snapshot.id)

        results = [
            AnalysisSessionResultResponse(
                step_id=step.id,
                step_name=step.name,
                result_formula=step.config.get("result_formula") if step.config else None,
                result_chart=step.config.get("result_chart") if step.config else None,
                result_table=step.config.get("result_table") if step.config else None,
            )
            for step in summary_steps
        ]

        return AnalysisSessionResultListResponse(results=results, total=len(results))

    async def execute_chat(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        chat_create: Any,
    ) -> AnalysisSessionDetailResponse:
        """AIエージェントとチャットを実行します。

        Phase 3.1で完全実装予定。タイムアウト: 10分。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID
            chat_create: チャット作成リクエスト

        Returns:
            AnalysisSessionDetailResponse: チャット応答

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # user messageを取得
        user_message = chat_create.message
        if not user_message:
            raise ValidationError("チャットメッセージは必須です")

        # セッションを取得し、stateとagentを構築
        session = await self._get_session_with_full_relations(session_id)
        state = self._build_state(session)
        agent = self._build_agent(state)

        # チャットを実行
        agent.chat(user_message)

        # 新しいsnapshotを作成し、今のstateを保存
        new_snapshot_order = session.current_snapshot + 1
        new_snapshot = await self.snapshot_repository.create(
            session_id=session_id,
            snapshot_order=new_snapshot_order,
        )
        new_snapshot_id = new_snapshot.id
        # ステップを保存
        # TODO: stepのbulk_createを実装してパフォーマンス改善
        for step_idx, step in enumerate(state.all_steps):
            await self.step_repository.create(
                snapshot_id=new_snapshot_id,
                name=step["name"],
                step_order=step_idx,
                type=step["type"],
                input=step["data_source"],
                config=step["config"],
            )
        # チャット履歴保存
        await self.chat_repository.bulk_create(
            snapshot_id=new_snapshot_id,
            chat_list=state.chat_history,
        )
        # セッションのcurrent_snapshotを更新
        session = await self.session_repository.update(session, current_snapshot=new_snapshot_order)

        # リレーションを取得してレスポンスを構築
        await self.db.commit()
        session = await self.session_repository.get_with_relations(session.id)
        if not session:
            raise NotFoundError("Session not found after creation")
        snapshots = await self.snapshot_repository.list_by_session(session.id)
        for snap in snapshots:
            snap_with_relations = await self.snapshot_repository.get_with_relations(snap.id)
            if snap_with_relations:
                snap.chats = snap_with_relations.chats
                snap.steps = snap_with_relations.steps
        files = await self.file_repository.list_by_session(session.id)

        return self._build_session_detail_response(session, snapshots, files)

    @transactional
    async def restore_snapshot(
        self,
        session_id: uuid.UUID,
        snapshot_order: int,
    ) -> AnalysisSessionDetailResponse:
        """分析状態を選択されたスナップショットに戻します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            session_id: セッションID
            snapshot_order: スナップショットID（順序番号）

        Returns:
            AnalysisSessionDetailResponse: 復元結果

        Raises:
            NotFoundError: セッションまたはスナップショットが見つからない場合
        """
        # セッションを取得
        session = await self.session_repository.get_with_relations(session_id)
        if not session:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # スナップショットの存在確認
        snapshot = await self.snapshot_repository.get_by_order(session_id, snapshot_order)
        if not snapshot:
            raise NotFoundError(
                "Snapshot not found",
                details={"session_id": str(session_id), "snapshot_order": snapshot_order},
            )

        # セッションのcurrent_snapshotを更新
        session = await self.session_repository.update(session, current_snapshot=snapshot_order)

        # current_snapshot以降のsnapshot（後続分）を削除する（chat, stepも一緒に）
        snapshots = await self.snapshot_repository.list_by_session(session_id)
        for snap in snapshots:
            if snap.snapshot_order > snapshot_order:
                await self._delete_snapshot(snap.id)

        # スナップショットを取得
        snapshots = await self.snapshot_repository.list_by_session_with_relations(session_id)

        # ファイルを取得
        files = await self.file_repository.list_by_session(session_id)

        return self._build_session_detail_response(session, snapshots, files)

    async def get_chat_messages(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AnalysisChatResponse]:
        """セッションのチャットメッセージ履歴を取得します。

        現在のスナップショットに関連付けられたチャットメッセージを返します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID
            skip: スキップ数
            limit: 取得件数

        Returns:
            list[AnalysisChatResponse]: チャットメッセージ一覧

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # セッションを取得
        session = await self.session_repository.get(session_id)
        if not session or session.project_id != project_id:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # 現在のスナップショットを取得
        snapshot = await self.snapshot_repository.get_by_order(session_id, session.current_snapshot)
        if not snapshot:
            return []

        # チャットメッセージを取得
        chats = await self.chat_repository.list_by_snapshot(snapshot.id, skip=skip, limit=limit)

        return [
            AnalysisChatResponse(
                id=chat.id,
                chat_order=chat.chat_order,
                snapshot=snapshot.snapshot_order,
                role=chat.role,
                message=chat.message,
                created_at=chat.created_at,
                updated_at=chat.updated_at,
            )
            for chat in chats
        ]

    async def list_snapshots(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> list[AnalysisSnapshotResponse]:
        """セッションのスナップショット一覧を取得します。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID

        Returns:
            list[AnalysisSnapshotResponse]: スナップショット一覧

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # セッションを取得
        session = await self.session_repository.get(session_id)
        if not session or session.project_id != project_id:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # スナップショット一覧を取得（リレーション含む）
        snapshots = await self.snapshot_repository.list_by_session_with_relations(session_id)

        return [
            AnalysisSnapshotResponse(
                id=snap.id,
                snapshot_order=snap.snapshot_order,
                parent_snapshot_id=snap.parent_snapshot_id if hasattr(snap, "parent_snapshot_id") else None,
                chat_list=[
                    AnalysisChatResponse(
                        id=chat.id,
                        chat_order=chat.chat_order,
                        snapshot=snap.snapshot_order,
                        role=chat.role,
                        message=chat.message,
                        created_at=chat.created_at,
                        updated_at=chat.updated_at,
                    )
                    for chat in (snap.chats or [])
                ],
                step_list=[
                    AnalysisStepResponse(
                        id=step.id,
                        name=step.name,
                        type=step.type,
                        input=step.input,
                        step_order=step.step_order,
                        config=step.config,
                        snapshot_id=step.snapshot_id,
                        result_formula=step.config.get("result_formula") if step.config else None,
                        result_chart=step.config.get("result_chart") if step.config else None,
                        result_table=step.config.get("result_table") if step.config else None,
                        created_at=step.created_at,
                        updated_at=step.updated_at,
                    )
                    for step in (snap.steps or [])
                ],
                created_at=snap.created_at,
                updated_at=snap.updated_at,
            )
            for snap in snapshots
        ]

    @transactional
    async def create_snapshot(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        snapshot_create: AnalysisSnapshotCreate,
    ) -> AnalysisSnapshotResponse:
        """手動でスナップショットを保存します。

        現在のセッション状態をスナップショットとして保存します。
        親スナップショットは現在のスナップショットになります。

        Note:
            権限チェックはルーター層の ProjectMemberDep で行われます。

        Args:
            project_id: プロジェクトID
            session_id: セッションID
            snapshot_create: スナップショット作成リクエスト

        Returns:
            AnalysisSnapshotResponse: 作成されたスナップショット

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # セッションを取得
        session = await self.session_repository.get(session_id)
        if not session or session.project_id != project_id:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # 現在のスナップショットを取得
        current_snapshot = await self.snapshot_repository.get_by_order(session_id, session.current_snapshot)
        parent_snapshot_id = current_snapshot.id if current_snapshot else None

        # 新しいスナップショットを作成
        new_snapshot_order = session.current_snapshot + 1
        new_snapshot = await self.snapshot_repository.create(
            session_id=session_id,
            snapshot_order=new_snapshot_order,
            parent_snapshot_id=parent_snapshot_id,
        )

        # 現在のスナップショットのステップをコピー
        if current_snapshot:
            steps = await self.step_repository.list_by_snapshot(current_snapshot.id)
            for step in steps:
                await self.step_repository.create(
                    snapshot_id=new_snapshot.id,
                    name=step.name,
                    step_order=step.step_order,
                    type=step.type,
                    input=step.input,
                    config=step.config,
                )

            # チャット履歴もコピー
            chats = await self.chat_repository.list_by_snapshot(current_snapshot.id)
            for chat in chats:
                await self.chat_repository.create(
                    snapshot_id=new_snapshot.id,
                    chat_order=chat.chat_order,
                    role=chat.role,
                    message=chat.message,
                )

        # セッションのcurrent_snapshotを更新
        await self.session_repository.update(session, current_snapshot=new_snapshot_order)

        # リレーションを取得
        new_snapshot_with_relations = await self.snapshot_repository.get_with_relations(new_snapshot.id)
        if not new_snapshot_with_relations:
            raise NotFoundError("Snapshot not found after creation")

        return AnalysisSnapshotResponse(
            id=new_snapshot_with_relations.id,
            snapshot_order=new_snapshot_with_relations.snapshot_order,
            parent_snapshot_id=parent_snapshot_id,
            chat_list=[
                AnalysisChatResponse(
                    id=chat.id,
                    chat_order=chat.chat_order,
                    snapshot=new_snapshot_with_relations.snapshot_order,
                    role=chat.role,
                    message=chat.message,
                    created_at=chat.created_at,
                    updated_at=chat.updated_at,
                )
                for chat in (new_snapshot_with_relations.chats or [])
            ],
            step_list=[
                AnalysisStepResponse(
                    id=step.id,
                    name=step.name,
                    type=step.type,
                    input=step.input,
                    step_order=step.step_order,
                    config=step.config,
                    snapshot_id=step.snapshot_id,
                    result_formula=step.config.get("result_formula") if step.config else None,
                    result_chart=step.config.get("result_chart") if step.config else None,
                    result_table=step.config.get("result_table") if step.config else None,
                    created_at=step.created_at,
                    updated_at=step.updated_at,
                )
                for step in (new_snapshot_with_relations.steps or [])
            ],
            created_at=new_snapshot_with_relations.created_at,
            updated_at=new_snapshot_with_relations.updated_at,
        )
