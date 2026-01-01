"""プロジェクトファイル管理サービス。

このモジュールは、プロジェクトファイルのアップロード、ダウンロード、削除などのビジネスロジックを提供します。

主な機能:
    - ファイルアップロード（権限チェック、サイズ・MIMEタイプ検証）
    - ファイル取得（権限チェック）
    - ファイル一覧取得（権限チェック）
    - ファイルダウンロード（権限チェック）
    - ファイル削除（権限チェック）

サブモジュール:
    - base.py: 共通ベースクラス
    - crud.py: CRUD操作
    - upload.py: アップロード操作
    - download.py: ダウンロード操作
"""

import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProjectFile
from app.schemas.project.project_file import ProjectFileUsageResponse, ProjectFileVersionHistoryResponse
from app.services.project.project_file.crud import ProjectFileCrudService
from app.services.project.project_file.download import ProjectFileDownloadService
from app.services.project.project_file.upload import ALLOWED_MIME_TYPES, ProjectFileUploadService
from app.services.storage.validation import DEFAULT_MAX_FILE_SIZE as MAX_FILE_SIZE


class ProjectFileService:
    """プロジェクトファイル管理のビジネスロジックを提供するサービスクラス。

    CRUD操作、アップロード、ダウンロードを提供します。
    各機能は専用のサービスクラスに委譲されます。
    """

    def __init__(self, db: AsyncSession):
        """プロジェクトファイルサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self._crud_service = ProjectFileCrudService(db)
        self._upload_service = ProjectFileUploadService(db)
        self._download_service = ProjectFileDownloadService(db)

    # ================================================================================
    # CRUD操作
    # ================================================================================

    async def get_file(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> ProjectFile:
        """ファイルメタデータを取得します。"""
        return await self._crud_service.get_file(file_id, requester_id)

    async def list_project_files(
        self,
        project_id: uuid.UUID,
        requester_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        mime_type: str | None = None,
    ) -> tuple[list[ProjectFile], int]:
        """プロジェクトのファイル一覧を取得します。"""
        return await self._crud_service.list_project_files(project_id, requester_id, skip, limit, mime_type)

    async def delete_file(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> bool:
        """ファイルを削除します。"""
        return await self._crud_service.delete_file(file_id, requester_id)

    async def get_file_usage(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> ProjectFileUsageResponse:
        """ファイルの使用状況を取得します。"""
        return await self._crud_service.get_file_usage(file_id, requester_id)

    async def get_version_history(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> ProjectFileVersionHistoryResponse:
        """ファイルのバージョン履歴を取得します。"""
        return await self._crud_service.get_version_history(file_id, requester_id)

    # ================================================================================
    # アップロード
    # ================================================================================

    async def upload_file(self, project_id: uuid.UUID, file: UploadFile, uploaded_by: uuid.UUID) -> ProjectFile:
        """プロジェクトにファイルをアップロードします。"""
        return await self._upload_service.upload_file(project_id, file, uploaded_by)

    async def upload_new_version(self, parent_file_id: uuid.UUID, file: UploadFile, uploaded_by: uuid.UUID) -> ProjectFile:
        """既存ファイルの新バージョンをアップロードします。"""
        return await self._upload_service.upload_new_version(parent_file_id, file, uploaded_by)

    # ================================================================================
    # ダウンロード
    # ================================================================================

    async def download_file(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> str:
        """ファイルをダウンロードします（ファイルパスを返却）。"""
        return await self._download_service.download_file(file_id, requester_id)


__all__ = ["ProjectFileService", "MAX_FILE_SIZE", "ALLOWED_MIME_TYPES"]
