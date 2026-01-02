"""プロジェクトファイルCRUDサービス。

このモジュールは、プロジェクトファイルのCRUD操作を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import async_timeout, measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.models import ProjectFile, ProjectRole
from app.schemas.project.project_file import (
    FileUsageItem,
    FileVersionCompareResponse,
    FileVersionRestoreResponse,
    ProjectFileUsageResponse,
    ProjectFileVersionHistoryResponse,
    ProjectFileVersionItem,
    VersionComparisonBasicInfo,
    VersionComparisonInfo,
)
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

    @measure_performance
    async def get_version_history(
        self,
        file_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> ProjectFileVersionHistoryResponse:
        """ファイルのバージョン履歴を取得します。

        指定されたファイルIDから親をたどり、同じ元ファイルに属するすべてのバージョンを取得します。

        Args:
            file_id: ファイルID（任意のバージョン）
            requester_id: リクエスター（ユーザー）ID

        Returns:
            ProjectFileVersionHistoryResponse: バージョン履歴

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        logger.debug("バージョン履歴取得", file_id=str(file_id), requester_id=str(requester_id))

        file = await self.repository.get(file_id)
        if not file:
            raise NotFoundError(f"ファイルが見つかりません: {file_id}", details={"file_id": str(file_id)})

        # 権限チェック（VIEWER以上）
        await self._check_member_role(
            file.project_id,
            requester_id,
            [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER, ProjectRole.VIEWER],
        )

        # バージョン履歴を取得
        versions = await self.repository.get_version_history(file_id)

        # 最新バージョンを特定
        latest_file = next((v for v in versions if v.is_latest), versions[0] if versions else file)

        version_items = [
            ProjectFileVersionItem(
                id=v.id,
                version=v.version,
                filename=v.filename,
                original_filename=v.original_filename,
                file_size=v.file_size,
                uploaded_at=v.uploaded_at,
                uploaded_by=v.uploaded_by,
                is_latest=v.is_latest,
                uploader=None,  # 別途ロードが必要な場合は対応
            )
            for v in versions
        ]

        logger.debug(
            "バージョン履歴取得完了",
            file_id=str(file_id),
            total_versions=len(version_items),
        )

        return ProjectFileVersionHistoryResponse(
            file_id=latest_file.id,
            original_filename=latest_file.original_filename,
            total_versions=len(version_items),
            versions=version_items,
        )

    @measure_performance
    @async_timeout(30.0)
    async def download_version(
        self,
        version_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> str:
        """特定バージョンをダウンロードします（ファイルパスを返却）。

        Args:
            version_id: バージョンファイルID
            requester_id: リクエスター（ユーザー）ID

        Returns:
            str: ファイルの完全パス（FileResponseで使用可能）

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        logger.debug("特定バージョンダウンロード", version_id=str(version_id), requester_id=str(requester_id))

        # バージョンファイルを取得
        version_file = await self.repository.get(version_id)
        if not version_file:
            raise NotFoundError(f"バージョンファイルが見つかりません: {version_id}", details={"version_id": str(version_id)})

        # 権限チェック（VIEWER以上）
        await self._check_member_role(
            version_file.project_id,
            requester_id,
            [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER, ProjectRole.VIEWER],
        )

        # ファイルの存在確認
        storage_path = version_file.file_path
        if not await self.storage.exists("", storage_path):
            logger.error(
                "ストレージにファイルが見つかりません",
                version_id=str(version_id),
                storage_path=storage_path,
            )
            raise NotFoundError(
                f"ストレージにファイルが見つかりません: {version_id}",
                details={"version_id": str(version_id)},
            )

        # ファイルパスを返却（Azure Blobの場合は一時ファイルにダウンロード）
        return await self.storage.download_to_temp_file("", storage_path)

    @measure_performance
    @async_timeout(60.0)
    @transactional
    async def restore_version(
        self,
        version_id: uuid.UUID,
        requester_id: uuid.UUID,
        comment: str | None = None,
    ) -> FileVersionRestoreResponse:
        """特定バージョンに復元します（新バージョンとして登録）。

        Args:
            version_id: 復元元のバージョンファイルID
            requester_id: リクエスター（ユーザー）ID
            comment: 復元コメント（省略時は自動生成）

        Returns:
            FileVersionRestoreResponse: 復元レスポンス

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        logger.info("バージョン復元", version_id=str(version_id), requester_id=str(requester_id))

        # 復元元バージョンを取得
        source_version = await self.repository.get(version_id)
        if not source_version:
            raise NotFoundError(f"復元元バージョンが見つかりません: {version_id}", details={"version_id": str(version_id)})

        # 権限チェック（MEMBER以上）
        await self._check_member_role(
            source_version.project_id,
            requester_id,
            [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER],
        )

        # 同じファミリーのバージョン履歴を取得して最大バージョン番号を確認
        versions = await self.repository.get_version_history(source_version.id)
        max_version = max((v.version for v in versions), default=0)
        new_version_number = max_version + 1

        # ストレージからファイルをコピー
        source_storage_path = source_version.file_path
        new_file_id = uuid.uuid4()
        new_storage_path = self._generate_storage_path(
            source_version.project_id, new_file_id, source_version.original_filename
        )

        # ファイルの存在確認
        if not await self.storage.exists("", source_storage_path):
            raise NotFoundError(
                f"復元元のファイルがストレージに見つかりません: {version_id}",
                details={"version_id": str(version_id), "storage_path": source_storage_path},
            )

        # ファイルをコピー
        await self.storage.copy("", source_storage_path, new_storage_path)
        logger.info(
            "ファイルをコピーしました",
            source_path=source_storage_path,
            new_path=new_storage_path,
        )

        # 復元コメントを生成
        restore_comment = comment or f"v{source_version.version}から復元"

        # 最新バージョンを特定
        latest_version = next((v for v in versions if v.is_latest), versions[0] if versions else source_version)

        # 既存の最新バージョンのis_latestをFalseに更新
        if latest_version and latest_version.is_latest:
            await self.repository.update(latest_version, is_latest=False)

        # 新規バージョンレコードを作成
        new_version = await self.repository.create(
            id=new_file_id,
            project_id=source_version.project_id,
            filename=source_version.filename,
            original_filename=source_version.original_filename,
            file_path=new_storage_path,
            file_size=source_version.file_size,
            mime_type=source_version.mime_type,
            version=new_version_number,
            parent_file_id=source_version.parent_file_id or source_version.id,
            is_latest=True,
            uploaded_by=requester_id,
        )
        await self.db.commit()
        await self.db.refresh(new_version)

        logger.info(
            "バージョン復元完了",
            new_version_id=str(new_version.id),
            new_version_number=new_version_number,
            restored_from_version=source_version.version,
        )

        return FileVersionRestoreResponse(
            file_id=latest_version.id if latest_version else new_version.id,
            new_version_id=new_version.id,
            new_version_number=new_version_number,
            restored_from_version=source_version.version,
        )

    @measure_performance
    async def compare_versions(
        self,
        file_id: uuid.UUID,
        version1: int,
        version2: int,
        requester_id: uuid.UUID,
    ) -> FileVersionCompareResponse:
        """バージョン間を比較します（ファイルサイズ比較のみ）。

        Args:
            file_id: ファイルID
            version1: 比較元バージョン番号
            version2: 比較先バージョン番号
            requester_id: リクエスター（ユーザー）ID

        Returns:
            FileVersionCompareResponse: 比較結果

        Raises:
            NotFoundError: ファイルが見つからない場合
            AuthorizationError: 権限が不足している場合
        """
        logger.debug(
            "バージョン比較",
            file_id=str(file_id),
            version1=version1,
            version2=version2,
            requester_id=str(requester_id),
        )

        # ファイルを取得して権限チェック
        file = await self.repository.get(file_id)
        if not file:
            raise NotFoundError(f"ファイルが見つかりません: {file_id}", details={"file_id": str(file_id)})

        # 権限チェック（VIEWER以上）
        await self._check_member_role(
            file.project_id,
            requester_id,
            [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER, ProjectRole.VIEWER],
        )

        # バージョン履歴を取得
        versions = await self.repository.get_version_history(file_id)

        # 指定されたバージョン番号のファイルを検索
        v1_file = next((v for v in versions if v.version == version1), None)
        v2_file = next((v for v in versions if v.version == version2), None)

        if not v1_file:
            raise NotFoundError(
                f"バージョン{version1}が見つかりません",
                details={"file_id": str(file_id), "version": version1},
            )

        if not v2_file:
            raise NotFoundError(
                f"バージョン{version2}が見つかりません",
                details={"file_id": str(file_id), "version": version2},
            )

        # サイズ比較
        size_change = v2_file.file_size - v1_file.file_size
        size_change_percent = (size_change / v1_file.file_size * 100) if v1_file.file_size > 0 else 0.0

        logger.debug(
            "バージョン比較完了",
            file_id=str(file_id),
            version1=version1,
            version2=version2,
            size_change=size_change,
            size_change_percent=size_change_percent,
        )

        return FileVersionCompareResponse(
            file_id=file_id,
            file_name=file.original_filename,
            version1=VersionComparisonBasicInfo(
                version_number=v1_file.version,
                file_size=v1_file.file_size,
                created_at=v1_file.uploaded_at,
            ),
            version2=VersionComparisonBasicInfo(
                version_number=v2_file.version,
                file_size=v2_file.file_size,
                created_at=v2_file.uploaded_at,
            ),
            comparison=VersionComparisonInfo(
                size_change=size_change,
                size_change_percent=round(size_change_percent, 2),
            ),
        )
