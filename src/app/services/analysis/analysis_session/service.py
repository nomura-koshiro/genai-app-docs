"""分析セッションサービス。

このモジュールは、分析セッションのビジネスロジックを提供します。

主な機能:
    - セッションCRUD（作成、取得、削除）
    - ファイル管理（登録、設定、選択）
    - 分析結果・チャット
    - スナップショット管理
    - 分析ステップ管理
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.analysis import (
    AnalysisChatResponse,
    AnalysisFileConfigResponse,
    AnalysisFileCreate,
    AnalysisFileResponse,
    AnalysisFileUpdate,
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisSessionResponse,
    AnalysisSessionResultListResponse,
    AnalysisSnapshotCreate,
    AnalysisSnapshotResponse,
    AnalysisStepResponse,
)
from app.services.analysis.analysis_session.analysis_operations import AnalysisSessionAnalysisService
from app.services.analysis.analysis_session.crud import AnalysisSessionCrudService
from app.services.analysis.analysis_session.file_operations import AnalysisSessionFileService
from app.services.analysis.analysis_session.step_operations import AnalysisSessionStepService


class AnalysisSessionService:
    """分析セッション管理のビジネスロジックを提供するサービスクラス。

    セッションのCRUD、ファイル管理、分析結果取得、チャット実行、
    スナップショット管理、ステップ管理を提供します。
    各機能は専用のサービスクラスに委譲されます。
    """

    def __init__(self, db: AsyncSession):
        """分析セッションサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self._crud_service = AnalysisSessionCrudService(db)
        self._file_service = AnalysisSessionFileService(db)
        self._analysis_service = AnalysisSessionAnalysisService(db)
        self._step_service = AnalysisSessionStepService(db)

    # ================================================================================
    # セッションCRUD
    # ================================================================================

    async def list_sessions(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[AnalysisSessionResponse]:
        """プロジェクトに属する分析セッションの一覧を取得します。"""
        return await self._crud_service.list_sessions(project_id, skip, limit, is_active)

    async def create_session(
        self,
        project_id: uuid.UUID,
        creator_id: uuid.UUID,
        session_create: AnalysisSessionCreate,
    ) -> AnalysisSessionDetailResponse:
        """新しい分析セッションを作成します。"""
        return await self._crud_service.create_session(project_id, creator_id, session_create)

    async def get_session(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> AnalysisSessionDetailResponse:
        """分析セッション詳細を取得します。"""
        return await self._crud_service.get_session(project_id, session_id)

    async def delete_session(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> None:
        """分析セッションを削除します。"""
        return await self._crud_service.delete_session(project_id, session_id)

    async def duplicate_session(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        creator_id: uuid.UUID,
    ) -> AnalysisSessionDetailResponse:
        """分析セッションを複製します。"""
        return await self._crud_service.duplicate_session(project_id, session_id, creator_id)

    # ================================================================================
    # ファイル操作
    # ================================================================================

    async def list_session_files(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> list[AnalysisFileResponse]:
        """セッションに登録されたファイル一覧を取得します。"""
        return await self._file_service.list_session_files(project_id, session_id)

    async def upload_session_file(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        file_create: AnalysisFileCreate,
    ) -> AnalysisFileConfigResponse:
        """セッションにファイルを登録します。"""
        return await self._file_service.upload_session_file(project_id, session_id, file_create)

    async def update_file_config(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        file_id: uuid.UUID,
        config_data: AnalysisFileUpdate,
    ) -> AnalysisFileResponse:
        """ファイルの設定(シート、軸)を更新します。"""
        return await self._file_service.update_file_config(project_id, session_id, file_id, config_data)

    async def select_input_file(
        self,
        session_id: uuid.UUID,
        file_id: uuid.UUID | None,
    ) -> AnalysisSessionDetailResponse:
        """分析に使用する入力ファイルを選択します。"""
        return await self._file_service.select_input_file(session_id, file_id)

    # ================================================================================
    # 分析操作
    # ================================================================================

    async def get_session_result(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> AnalysisSessionResultListResponse:
        """分析セッションの結果を取得します。"""
        return await self._analysis_service.get_session_result(project_id, session_id)

    async def execute_chat(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        chat_create: Any,
    ) -> AnalysisSessionDetailResponse:
        """AIエージェントとチャットを実行します。"""
        return await self._analysis_service.execute_chat(project_id, session_id, chat_create)

    async def restore_snapshot(
        self,
        session_id: uuid.UUID,
        snapshot_order: int,
    ) -> AnalysisSessionDetailResponse:
        """分析状態を選択されたスナップショットに戻します。"""
        return await self._analysis_service.restore_snapshot(session_id, snapshot_order)

    async def get_chat_messages(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AnalysisChatResponse]:
        """セッションのチャットメッセージ履歴を取得します。"""
        return await self._analysis_service.get_chat_messages(project_id, session_id, skip, limit)

    async def delete_chat_message(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        chat_id: uuid.UUID,
    ) -> None:
        """チャットメッセージを削除します。"""
        return await self._analysis_service.delete_chat_message(project_id, session_id, chat_id)

    # ================================================================================
    # スナップショット操作
    # ================================================================================

    async def list_snapshots(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> list[AnalysisSnapshotResponse]:
        """セッションのスナップショット一覧を取得します。"""
        return await self._analysis_service.list_snapshots(project_id, session_id)

    async def create_snapshot(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        snapshot_create: AnalysisSnapshotCreate,
    ) -> AnalysisSnapshotResponse:
        """手動でスナップショットを保存します。"""
        return await self._analysis_service.create_snapshot(project_id, session_id, snapshot_create)

    # ================================================================================
    # ステップ操作
    # ================================================================================

    async def create_step(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        step_name: str,
        step_type: str,
        data_source: str,
        config: dict[str, Any] | None = None,
    ) -> AnalysisStepResponse:
        """最新snapshotに新しい分析ステップを作成します。"""
        return await self._step_service.create_step(project_id, session_id, step_name, step_type, data_source, config)

    async def update_step(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        step_id: uuid.UUID,
        step_name: str | None = None,
        step_type: str | None = None,
        data_source: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> AnalysisStepResponse:
        """最新snapshotの既存分析ステップを更新します。"""
        return await self._step_service.update_step(project_id, session_id, step_id, step_name, step_type, data_source, config)

    async def delete_step(
        self,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        step_id: uuid.UUID,
    ) -> None:
        """最新snapshotの指定されたステップを削除します。"""
        return await self._step_service.delete_step(project_id, session_id, step_id)
