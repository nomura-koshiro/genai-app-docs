"""分析サービスのファサード。

このモジュールは後方互換性のためのファサードパターンを提供します。
各機能は専用のサービスクラスに委譲されています。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnalysisFile, AnalysisSession, AnalysisStep
from app.schemas.analysis import AnalysisChatMessage
from app.schemas.analysis.analysis_session import (
    AnalysisChatRequest,
    AnalysisChatResponse,
    AnalysisDummyDataResponse,
    AnalysisFileUploadRequest,
    AnalysisFileUploadResponse,
    AnalysisSessionCreate,
    AnalysisSessionDetailResponse,
    AnalysisStepCreate,
    AnalysisValidationConfigResponse,
)

from .chat import AnalysisChatService
from .config import AnalysisConfigService
from .file import AnalysisFileService
from .session import AnalysisSessionService
from .snapshot import AnalysisSnapshotService
from .step import AnalysisStepService


class AnalysisService:
    """分析サービスのファサード（後方互換性のため）。

    このクラスは既存のAPIを維持しながら、各機能を専門のサービスクラスに委譲します。
    """

    def __init__(self, db: AsyncSession):
        """分析サービスを初期化します。

        Args:
            db: 非同期データベースセッション
        """
        self.db = db

        # 専門サービスの初期化
        self._session_service = AnalysisSessionService(db)
        self._file_service = AnalysisFileService(db)
        self._step_service = AnalysisStepService(db)
        self._chat_service = AnalysisChatService(db)
        self._snapshot_service = AnalysisSnapshotService(db)
        self._config_service = AnalysisConfigService(db)

        # 後方互換性のためリポジトリを公開
        self.session_repository = self._session_service.session_repository
        self.step_repository = self._step_service.step_repository
        self.file_repository = self._file_service.file_repository
        self.storage_service = self._file_service.storage_service

    async def create_session(self, session_data: AnalysisSessionCreate, creator_id: uuid.UUID) -> AnalysisSession:
        """新しい分析セッションを作成します。"""
        return await self._session_service.create_session(session_data, creator_id)

    async def get_session(self, session_id: uuid.UUID) -> AnalysisSession | None:
        """セッションIDで分析セッションを取得します。"""
        return await self._session_service.get_session(session_id)

    async def get_session_with_details(self, session_id: uuid.UUID) -> AnalysisSession | None:
        """セッションをステップとファイルと共に取得します（N+1クエリ対策）。"""
        return await self._session_service.get_session_with_details(session_id)

    async def list_project_sessions(
        self, project_id: uuid.UUID, skip: int = 0, limit: int = 100, is_active: bool | None = None
    ) -> list[AnalysisSession]:
        """プロジェクトの分析セッション一覧を取得します。"""
        return await self._session_service.list_project_sessions(project_id, skip, limit, is_active)

    async def get_session_result(self, session_id: uuid.UUID) -> AnalysisSessionDetailResponse:
        """分析セッションの結果を取得します。"""
        return await self._session_service.get_session_result(session_id)

    async def upload_data_file(
        self,
        session_id: uuid.UUID,
        file_request: AnalysisFileUploadRequest,
        user_id: uuid.UUID,
    ) -> AnalysisFileUploadResponse:
        """データファイルをアップロードし、メタデータを保存します。"""
        return await self._file_service.upload_data_file(session_id, file_request, user_id)

    async def list_session_files(self, session_id: uuid.UUID, is_active: bool | None = None) -> list[AnalysisFile]:
        """セッションのファイル一覧を取得します。"""
        return await self._file_service.list_session_files(session_id, is_active)

    async def create_step(self, session_id: uuid.UUID, step_data: AnalysisStepCreate) -> AnalysisStep:
        """新しい分析ステップを作成します。"""
        return await self._step_service.create_step(session_id, step_data)

    async def list_session_steps(self, session_id: uuid.UUID, is_active: bool | None = None) -> list[AnalysisStep]:
        """セッションの分析ステップ一覧を取得します。"""
        return await self._step_service.list_session_steps(session_id, is_active)

    async def delete_step(self, step_id: uuid.UUID) -> None:
        """分析ステップを削除します。"""
        await self._step_service.delete_step(step_id)

    async def chat(self, session_id: uuid.UUID, user_id: uuid.UUID, message: str) -> str:
        """分析エージェントとチャットします。"""
        return await self._chat_service.chat(session_id, user_id, message)

    async def get_chat_history(self, session_id: uuid.UUID, user_id: uuid.UUID) -> list[AnalysisChatMessage]:
        """チャット履歴を取得します。"""
        return await self._chat_service.get_chat_history(session_id, user_id)

    async def clear_chat_history(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """チャット履歴をクリアします。"""
        await self._chat_service.clear_chat_history(session_id, user_id)

    async def execute_chat(self, session_id: uuid.UUID, chat_request: AnalysisChatRequest) -> AnalysisChatResponse:
        """AIエージェントとチャットを実行します（準備中）。"""
        return await self._chat_service.execute_chat(session_id, chat_request)

    async def get_snapshot_id(self, session_id: uuid.UUID, user_id: uuid.UUID) -> int:
        """現在のスナップショットIDを取得します。"""
        return await self._snapshot_service.get_snapshot_id(session_id, user_id)

    async def save_snapshot(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        current_snapshot: bool = False,
    ) -> int:
        """現在の状態をスナップショットとして保存します。"""
        return await self._snapshot_service.save_snapshot(session_id, user_id, current_snapshot)

    async def revert_snapshot(self, session_id: uuid.UUID, user_id: uuid.UUID, snapshot_id: int) -> None:
        """指定したスナップショットに戻します。"""
        await self._snapshot_service.revert_snapshot(session_id, user_id, snapshot_id)

    async def get_validation_config(self) -> AnalysisValidationConfigResponse:
        """検証設定を取得します。"""
        return await self._config_service.get_validation_config()

    async def get_dummy_data(self, chart_type: str) -> AnalysisDummyDataResponse:
        """ダミーチャートデータを取得します。"""
        return await self._config_service.get_dummy_data(chart_type)


__all__ = [
    "AnalysisService",
    "AnalysisSessionService",
    "AnalysisFileService",
    "AnalysisStepService",
    "AnalysisChatService",
    "AnalysisSnapshotService",
    "AnalysisConfigService",
]
