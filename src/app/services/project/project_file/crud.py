"""プロジェクトファイルCRUDサービス。

このモジュールは、プロジェクトファイルのCRUD操作を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import async_timeout, measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.models import ProjectFile, ProjectRole
from app.schemas.project.project_file import FileUsageItem, ProjectFileUsageResponse
from app.services.project.project_file.base import ProjectFileServiceBase

logger = get_logger(__name__)


class ProjectFileCrudService(ProjectFileServiceBase):
    """プロジェクトファイルのCRUD操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """プロジェクトファイルCRUDサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    @measure_performance
    async def get_file(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> ProjectFile:
        """ファイルメタデータを取得します。

        Args:
            file_id: ファイルID
            requester_id: リクエスター（ユーザー）ID

        Returns:
            ProjectFile: ファイルメタデータ

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

        return file

    @measure_performance
    async def list_project_files(
        self,
        project_id: uuid.UUID,
        requester_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        mime_type: str | None = None,
    ) -> tuple[list[ProjectFile], int]:
        """プロジェクトのファイル一覧を取得します。

        Args:
            project_id: プロジェクトID
            requester_id: リクエスター（ユーザー）ID
            skip: スキップするレコード数
            limit: 取得する最大レコード数
            mime_type: MIMEタイプでフィルタ（部分一致、例: "image/", "application/pdf"）

        Returns:
            tuple[list[ProjectFile], int]: ファイルリストと総件数のタプル

        Raises:
            AuthorizationError: 権限が不足している場合
        """
        logger.debug(
            "ファイル一覧取得",
            project_id=str(project_id),
            skip=skip,
            limit=limit,
            mime_type=mime_type,
        )

        # 権限チェック（VIEWER以上）
        await self._check_member_role(
            project_id,
            requester_id,
            [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER, ProjectRole.VIEWER],
        )

        files = await self.repository.list_by_project(project_id, skip, limit, mime_type)
        total = await self.repository.count_by_project_with_filter(project_id, mime_type)

        logger.debug("ファイル一覧取得完了", count=len(files), total=total)

        return files, total

    @measure_performance
    @async_timeout(30.0)
    @transactional
    async def delete_file(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> bool:
        """ファイルを削除します。

        このメソッドは以下の処理を実行します：
        1. ファイルの存在確認
        2. 権限チェック（アップロード者本人、またはADMIN/OWNER）
        3. StorageServiceを使用してファイル削除
        4. データベースからメタデータ削除

        Args:
            file_id: ファイルID
            requester_id: リクエスター（ユーザー）ID

        Returns:
            bool: 削除成功の場合True

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        logger.info("ファイル削除", file_id=str(file_id), requester_id=str(requester_id))

        file = await self.repository.get(file_id)
        if not file:
            raise NotFoundError(f"ファイルが見つかりません: {file_id}", details={"file_id": str(file_id)})

        # 権限チェック（アップロード者本人、またはADMIN/OWNER）
        member = await self.member_repository.get_by_project_and_user(file.project_id, requester_id)
        if not member:
            raise AuthorizationError(
                "このプロジェクトのメンバーではありません",
                details={"project_id": str(file.project_id), "user_id": str(requester_id)},
            )

        # アップロード者本人、またはADMIN/OWNERのみ削除可能
        if file.uploaded_by != requester_id and member.role not in [ProjectRole.PROJECT_MANAGER]:
            raise AuthorizationError(
                "ファイルのアップロード者またはプロジェクト管理者のみが削除できます",
                details={
                    "file_id": str(file_id),
                    "uploaded_by": str(file.uploaded_by),
                    "requester_id": str(requester_id),
                    "requester_role": member.role.value,
                },
            )

        # StorageServiceを使用してファイルを削除
        storage_path = file.file_path
        if await self.storage.exists("", storage_path):
            await self.storage.delete("", storage_path)
            logger.info(
                "物理ファイルを削除しました",
                file_path=storage_path,
            )

        # データベースから削除
        await self.repository.delete(file_id)
        await self.db.commit()

        logger.info("ファイル削除完了", file_id=str(file_id))

        return True

    @measure_performance
    async def get_file_usage(self, file_id: uuid.UUID, requester_id: uuid.UUID) -> ProjectFileUsageResponse:
        """ファイルの使用状況を取得します。

        このメソッドは、ファイルがどの分析セッションやドライバーツリーで使用されているかを返します。

        Args:
            file_id: ファイルID
            requester_id: リクエスター（ユーザー）ID

        Returns:
            ProjectFileUsageResponse: ファイル使用状況

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        logger.debug("ファイル使用状況取得", file_id=str(file_id), requester_id=str(requester_id))

        # 使用情報を含むファイルを取得
        file = await self.repository.get_with_usage(file_id)
        if not file:
            raise NotFoundError(f"ファイルが見つかりません: {file_id}", details={"file_id": str(file_id)})

        # 権限チェック（VIEWER以上）
        await self._check_member_role(
            file.project_id,
            requester_id,
            [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER, ProjectRole.VIEWER],
        )

        # 使用情報を収集
        usages: list[FileUsageItem] = []

        # 分析セッションでの使用
        for analysis_file in file.analysis_files:
            session = analysis_file.session
            usages.append(
                FileUsageItem(
                    usage_type="analysis_session",
                    target_id=session.id,
                    target_name=session.issue.name if session.issue else f"セッション {session.id}",
                    sheet_name=analysis_file.sheet_name,
                    used_at=analysis_file.created_at,
                )
            )

        # ドライバーツリーでの使用
        for driver_tree_file in file.driver_tree_files:
            usages.append(
                FileUsageItem(
                    usage_type="driver_tree",
                    target_id=driver_tree_file.id,
                    target_name=f"ドライバーツリーファイル {driver_tree_file.id}",
                    sheet_name=driver_tree_file.sheet_name,
                    used_at=driver_tree_file.created_at,
                )
            )

        analysis_count = len(file.analysis_files)
        driver_tree_count = len(file.driver_tree_files)

        logger.debug(
            "ファイル使用状況取得完了",
            file_id=str(file_id),
            analysis_session_count=analysis_count,
            driver_tree_count=driver_tree_count,
        )

        return ProjectFileUsageResponse(
            file_id=file_id,
            filename=file.original_filename,
            analysis_session_count=analysis_count,
            driver_tree_count=driver_tree_count,
            total_usage_count=analysis_count + driver_tree_count,
            usages=usages,
        )
