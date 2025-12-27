"""分析セッションサービス共通ベース。

このモジュールは、分析セッションサービスの共通機能を提供します。
"""

import json
from typing import Any

import pandas as pd
import plotly
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.analysis import (
    AnalysisChatRepository,
    AnalysisFileRepository,
    AnalysisIssueRepository,
    AnalysisSessionRepository,
    AnalysisSnapshotRepository,
    AnalysisStepRepository,
)
from app.repositories.project import ProjectFileRepository
from app.schemas.analysis import (
    AnalysisChatResponse,
    AnalysisFileResponse,
    AnalysisSessionDetailResponse,
    AnalysisSnapshotResponse,
    AnalysisStepResponse,
)
from app.services import storage as storage_module
from app.services.analysis.agent.agent import AnalysisAgent
from app.services.analysis.agent.state import AnalysisState
from app.services.storage import StorageService

logger = get_logger(__name__)


class AnalysisSessionServiceBase:
    """分析セッションサービスの共通ベースクラス。"""

    def __init__(self, db: AsyncSession, storage: StorageService | None = None):
        """分析セッションサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
            storage: ストレージサービス（指定しない場合はデフォルトのストレージサービスを使用）
        """
        self.db = db
        self.issue_repository = AnalysisIssueRepository(db)
        self.session_repository = AnalysisSessionRepository(db)
        self.file_repository = AnalysisFileRepository(db)
        self.project_file_repository = ProjectFileRepository(db)
        self.snapshot_repository = AnalysisSnapshotRepository(db)
        self.step_repository = AnalysisStepRepository(db)
        self.chat_repository = AnalysisChatRepository(db)
        # Storageサービスを初期化(ファイルアップロード用)
        # モジュール経由でアクセスすることでテスト時のモックが効くようにする
        self.storage: StorageService = storage if storage is not None else storage_module.get_storage_service()

    def _build_session_detail_response(
        self,
        session: Any,
        snapshots: list[Any],
        files: list[Any],
    ) -> AnalysisSessionDetailResponse:
        """セッション詳細レスポンスを構築します。

        Args:
            session: セッションモデル
            snapshots: スナップショットのリスト
            files: ファイルのリスト

        Returns:
            AnalysisSessionDetailResponse: セッション詳細レスポンス
        """
        snapshot_responses = []
        current_snapshot_order = session.current_snapshot.snapshot_order if session.current_snapshot else 0
        for snap in snapshots:
            chat_responses = [
                AnalysisChatResponse(
                    id=chat.id,
                    chat_order=chat.chat_order,
                    role=chat.role,
                    message=chat.message,
                    created_at=chat.created_at,
                    updated_at=chat.updated_at,
                )
                for chat in snap.chats
            ]
            step_responses = []
            if snap.snapshot_order == current_snapshot_order and session.input_file_id is not None:
                state = self._build_state(session, snapshots, files)
            else:
                state = None
            for step in snap.steps:
                # result_dataをDataFrameから辞書リストに変換
                if state is not None and state.all_steps[step.step_order]["result_data"] is not None:
                    result_data = state.all_steps[step.step_order]["result_data"].to_dict(orient="records")
                else:
                    result_data = None
                # result_formulaをそのまま取得
                result_formula = state.all_steps[step.step_order].get("result_formula") if state else None
                # result_chartがPlotly Figureの場合はJSONシリアライズ可能な形式に変換
                result_chart_raw = state.all_steps[step.step_order].get("result_chart") if state else None
                if isinstance(result_chart_raw, plotly.graph_objs._figure.Figure):
                    # plotly.io.to_jsonで完全にシリアライズしてからパース
                    result_chart = json.loads(plotly.io.to_json(result_chart_raw))  # type: ignore
                else:
                    result_chart = result_chart_raw
                # result_tableをDataFrameから辞書リストに変換
                if state is not None and state.all_steps[step.step_order].get("result_table") is not None:
                    result_table = state.all_steps[step.step_order]["result_table"].to_dict(orient="records")
                else:
                    result_table = None

                step_responses.append(
                    AnalysisStepResponse(
                        id=step.id,
                        snapshot_id=step.snapshot_id,
                        name=step.name,
                        step_order=step.step_order,
                        type=step.type,
                        input=step.input,
                        config=step.config,
                        result_data=result_data,
                        result_formula=result_formula,
                        result_chart=result_chart,
                        result_table=result_table,
                        created_at=step.created_at,
                        updated_at=step.updated_at,
                    )
                )
            snapshot_responses.append(
                AnalysisSnapshotResponse(
                    id=snap.id,
                    snapshot_order=snap.snapshot_order,
                    chat=chat_responses,
                    step=step_responses,
                    created_at=snap.created_at,
                    updated_at=snap.updated_at,
                )
            )

        file_responses = [
            AnalysisFileResponse(
                id=f.id,
                session_id=f.session_id,
                project_file_id=f.project_file_id,
                project_file_name=f.project_file.original_filename if f.project_file else "",
                sheet_name=f.sheet_name,
                axis_config=f.axis_config,
                data=f.data,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            for f in files
        ]

        current_snapshot_order = session.current_snapshot.snapshot_order if session.current_snapshot else 0
        return AnalysisSessionDetailResponse(
            id=session.id,
            project_id=session.project_id,
            issue_id=session.issue_id,
            creator_id=session.creator_id,
            status=session.status,
            custom_system_prompt=session.custom_system_prompt,
            initial_message=session.initial_message,
            current_snapshot=current_snapshot_order,
            input_file_id=session.input_file_id,
            snapshot_list=snapshot_responses,
            file_list=file_responses,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def _build_state(self, session: Any, snapshots: list[Any] | None = None, files: list[Any] | None = None) -> AnalysisState:
        """分析セッションの現在のsnapshotと選択ファイルからAnalysisStateを構築します。

        Args:
            session: 分析セッションモデル
            snapshots: スナップショットのリスト（指定しない場合はsession.snapshotsを使用）
            files: ファイルのリスト（指定しない場合はsession.filesを使用）

        Returns:
            AnalysisState: 分析状態オブジェクト
        """
        # snapshots, filesが指定されていない場合はセッションから取得
        # NOTE: deepcopy前にリストを取得しないとDetachedInstanceErrorが発生する
        if snapshots is None:
            snapshots = list(session.snapshots)
        if files is None:
            files = list(session.files)

        # セッションを取得
        session_id = session.id
        if not session:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )
        # 入力ファイルの存在確認
        if not session.input_file_id:
            raise NotFoundError(
                "Input file not selected",
                details={"session_id": str(session_id)},
            )
        input_file = None
        for file in files:
            if file.id == session.input_file_id:
                input_file = file.data
                break
        if not input_file:
            raise NotFoundError(
                "Input file data not found",
                details={"file_id": str(session.input_file_id)},
            )
        # snapshotの存在確認
        current_snapshot_order = session.current_snapshot.snapshot_order if session.current_snapshot else 0
        if current_snapshot_order >= len(snapshots):
            raise NotFoundError(
                "Current snapshot not found",
                details={
                    "session_id": str(session_id),
                    "current_snapshot": current_snapshot_order,
                },
            )

        # stateを初期化
        input_data_rows = input_file
        input_file_data = pd.DataFrame.from_records(input_data_rows)
        snapshot = snapshots[current_snapshot_order]
        step_list = []
        for step in snapshot.steps:
            step_list.append(
                {
                    "name": step.name,
                    "type": step.type,
                    "data_source": step.input,
                    "config": step.config,
                    "result_data": None,
                    "result_formula": None,
                    "result_chart": None,
                    "result_table": None,
                }
            )
        chat_list = []
        for chat in snapshot.chats:
            chat_list.append((chat.role, chat.message))
        state = AnalysisState(input_file_data, step_list, chat_list)
        return state

    def _build_agent(self, state: AnalysisState) -> AnalysisAgent:
        """AnalysisStateからAnalysisAgentを構築します。

        Args:
            state: AnalysisStateオブジェクト

        Returns:
            AnalysisAgent: 分析エージェントオブジェクト
        """
        agent = AnalysisAgent(state)
        return agent

    # TODO: 将来的にsnapshotを実現するため、各チャットメッセージにsnapshot番号を割り当てる機能
    # TODO: ChatResponseにsnapshotフィールドを追加する
    # def assign_snapshot_number_for_chat(self, snapshots: list[AnalysisSnapshotResponse]) -> None:
    #     """チャットレスポンスにスナップショット番号を割り当てます。

    #     Args:
    #         snapshots: スナップショットレスポンスのリスト
    #     """

    #     exist_chat = {}
    #     for snap_i, snap in enumerate(snapshots):
    #         for chat in snap.chat:
    #             if f"{chat.role}:{chat.message}" not in exist_chat:
    #                 chat.snapshot = snap_i
    #                 exist_chat[f"{chat.role}:{chat.message}"] = snap_i
    #             else:
    #                 chat.snapshot = exist_chat[f"{chat.role}:{chat.message}"]

    async def _delete_snapshot(self, snapshot_id: Any) -> None:
        """スナップショットとその関連データを削除します。

        Args:
            snapshot_id: スナップショットID
        """
        await self.chat_repository.delete_by_snapshot(snapshot_id)
        await self.step_repository.delete_by_snapshot(snapshot_id)
        await self.snapshot_repository.delete(snapshot_id)

    async def _get_session_with_full_relations(self, session_id: Any) -> Any:
        """セッションをスナップショット、ファイル含めて完全に取得します。

        Args:
            session_id: セッションID

        Returns:
            AnalysisSession: リレーションを含むセッションモデル

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        # セッションを取得
        session = await self.session_repository.get_with_relations(session_id)
        if not session:
            raise NotFoundError(
                "Session not found",
                details={"session_id": str(session_id)},
            )

        # スナップショットを取得（chats, steps含む）
        snapshots = await self.snapshot_repository.list_by_session_with_relations(session_id)

        # セッションにスナップショットを設定
        session.snapshots = snapshots

        # ファイルを取得
        files = await self.file_repository.list_by_session(session_id)
        session.files = files

        return session
