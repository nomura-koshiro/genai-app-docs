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
    AnalysisSessionDetailResponse,
    AnalysisSessionResultListResponse,
    AnalysisSessionResultResponse,
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
