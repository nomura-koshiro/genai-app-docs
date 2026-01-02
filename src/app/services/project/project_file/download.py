"""プロジェクトファイルダウンロードサービス。

このモジュールは、プロジェクトファイルのダウンロード操作を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import async_timeout, measure_performance
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models import ProjectRole
from app.services.project.project_file.base import ProjectFileServiceBase

logger = get_logger(__name__)


class ProjectFileDownloadService(ProjectFileServiceBase):
    """プロジェクトファイルのダウンロード操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """プロジェクトファイルダウンロードサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    @measure_performance
    @async_timeout(30.0)
    async def download_file(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> str:
        """ファイルをダウンロードします（ファイルパスを返却）。

        ローカルストレージの場合はファイルパスをそのまま返します。
        Azure Blobストレージの場合は一時ファイルにダウンロードしてパスを返します。

        Args:
            file_id: ファイルID
            requester_id: リクエスター（ユーザー）ID

        Returns:
            str: ファイルの完全パス（FileResponseで使用可能）

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        file = await self.repository.get(file_id)
        if not file:
            raise NotFoundError(f"ファイルが見つかりません: {file_id}", details={"file_id": str(file_id)})

        # 権限チェック（VIEWER以上）
        await self._check_member_role(
            file.project_id,
            requester_id,
            [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER, ProjectRole.VIEWER],
        )

        # ファイルの存在確認
        storage_path = file.file_path
        if not await self.storage.exists("", storage_path):
            logger.error(
                "ストレージにファイルが見つかりません",
                file_id=str(file_id),
                storage_path=storage_path,
            )
            raise NotFoundError(
                f"ストレージにファイルが見つかりません: {file_id}",
                details={"file_id": str(file_id)},
            )

        # ファイルパスを返却（Azure Blobの場合は一時ファイルにダウンロード）
        return await self.storage.download_to_temp_file("", storage_path)
