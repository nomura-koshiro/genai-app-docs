"""ファイル操作モジュール。

ファイルアップロード、削除、一覧取得を提供します。
"""

import uuid
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.driver_tree import DriverTreeFileRepository
from app.repositories.project import ProjectFileRepository
from app.services.storage import StorageService
from app.services.storage.excel import get_excel_sheet_names
from app.services.storage.validation import check_file_size, sanitize_filename, validate_excel_file

logger = get_logger(__name__)


class FileOperationsMixin:
    """ファイル操作機能を提供するMixinクラス。

    Attributes:
        db: データベースセッション
        file_repository: DriverTreeFileリポジトリ
        project_file_repository: ProjectFileリポジトリ
        storage: ストレージサービス
        container: コンテナ名（service.pyで定義）
    """

    db: AsyncSession
    file_repository: DriverTreeFileRepository
    project_file_repository: ProjectFileRepository
    storage: StorageService
    container: str

    @transactional
    @measure_performance
    async def upload_file(
        self,
        project_id: uuid.UUID,
        file: UploadFile,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Excelファイルをアップロードします。

        最大ファイルサイズ: 50MB
        対応形式: .xlsx/.xls

        ファイルをアップロードし、プロジェクト内の全アップロード済みファイルとシート一覧を返します。
        カラム情報の解析はSelect Sheet APIで行われます。

        Args:
            project_id: プロジェクトID
            file: アップロードファイル
            user_id: アップロードユーザーID

        Returns:
            dict[str, Any]: アップロード結果
                - files: list[dict] - アップロード済みファイル一覧

        Raises:
            ValidationError: 不正なファイル形式の場合
            PayloadTooLargeError: ペイロードサイズ超過の場合
        """
        logger.info(
            "ファイルアップロードリクエスト",
            user_id=str(user_id),
            project_id=str(project_id),
            filename=file.filename,
            content_type=file.content_type,
            action="upload_file",
        )

        # 1. ファイル検証
        validate_excel_file(file)

        # 2. ファイル読み込み
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # ポインタをリセット

        # 3. ペイロードサイズチェック（50MB制限）
        check_file_size(file_size)

        # 4. ファイル名をサニタイズ
        safe_filename = sanitize_filename(file.filename)
        file_id = uuid.uuid4()

        # 5. ストレージパスを生成
        storage_path = self._generate_storage_path(project_id, file_id, safe_filename)

        # 6. StorageServiceを使用してファイルを保存
        await self.storage.upload(self.container, storage_path, content)

        try:
            # 7. ProjectFile作成
            project_file = await self.project_file_repository.create(
                id=file_id,
                project_id=project_id,
                filename=safe_filename,
                original_filename=file.filename or "unknown",
                file_path=storage_path,
                file_size=file_size,
                mime_type=file.content_type,
                uploaded_by=user_id,
                uploaded_at=datetime.now(UTC),
            )

            # 8. Excelファイルからシート名を取得（BytesIOを使用）
            sheet_names = get_excel_sheet_names(BytesIO(content))

            # 9. 各シートに対してDriverTreeFileを作成（基本情報のみ）
            for sheet_name in sheet_names:
                # DriverTreeFile作成（列情報はSelect時に解析）
                await self.file_repository.create(
                    project_file_id=project_file.id,
                    sheet_name=sheet_name,
                    axis_config={},  # 初期は空
                )

            logger.info(
                "ファイルをアップロードしました",
                user_id=str(user_id),
                project_id=str(project_id),
                file_id=str(project_file.id),
                sheet_count=len(sheet_names),
            )

            # 10. プロジェクトの全アップロード済みファイル一覧を取得して返す
            return await self.list_uploaded_files(project_id, user_id)

        except Exception:
            # 異常時は保存されたファイルを削除
            if await self.storage.exists(self.container, storage_path):
                await self.storage.delete(self.container, storage_path)
            raise

    def _generate_storage_path(self, project_id: uuid.UUID, file_id: uuid.UUID, filename: str) -> str:
        """ストレージパスを生成します。

        Args:
            project_id: プロジェクトID
            file_id: ファイルID
            filename: ファイル名

        Returns:
            str: ストレージパス
        """
        return f"projects/{project_id}/{file_id}_{filename}"

    @measure_performance
    @transactional
    async def delete_file(
        self,
        project_id: uuid.UUID,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """アップロード済みファイルを削除します。

        Args:
            project_id: プロジェクトID
            file_id: ファイルID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: 削除結果

        Raises:
            NotFoundError: ファイルが見つからない場合
        """
        logger.info(
            "ファイル削除リクエスト",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
            action="delete_file",
        )

        # 1. ファイルを取得
        project_file = await self.project_file_repository.get(file_id)
        if not project_file:
            raise NotFoundError(
                "ファイルが見つかりません",
                details={"file_id": str(file_id)},
            )

        # 2. プロジェクトIDの確認
        if project_file.project_id != project_id:
            raise NotFoundError(
                "このプロジェクト内で該当ファイルが見つかりません",
                details={"file_id": str(file_id), "project_id": str(project_id)},
            )

        # 3. StorageServiceを使用してファイルを削除
        storage_path = project_file.file_path
        if await self.storage.exists(self.container, storage_path):
            await self.storage.delete(self.container, storage_path)
            logger.info(
                "物理ファイルを削除しました",
                file_path=storage_path,
            )

        # 4. DBレコードを削除（cascade deleteでDriverTreeFile、DriverTreeDataFrameも削除される）
        await self.project_file_repository.delete(file_id)

        logger.info(
            "ファイルを削除しました",
            user_id=str(user_id),
            project_id=str(project_id),
            file_id=str(file_id),
        )

        # 5. プロジェクトの全アップロード済みファイル一覧を取得して返す
        return await self.list_uploaded_files(project_id, user_id)

    @measure_performance
    async def list_uploaded_files(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """アップロード済みファイル一覧を取得します。

        Args:
            project_id: プロジェクトID
            user_id: ユーザーID

        Returns:
            dict[str, Any]: アップロード済みファイル一覧
        """
        logger.info(
            "アップロード済みファイル一覧取得リクエスト",
            user_id=str(user_id),
            project_id=str(project_id),
            action="list_uploaded_files",
        )

        # プロジェクトの全ProjectFileを取得
        project_files = await self.project_file_repository.list_by_project(project_id)

        # 各ファイルに対してシート情報を取得
        result_files = []
        for project_file in project_files:
            # 各ファイルに紐づく全シート一覧を取得
            driver_tree_files = await self.file_repository.list_by_project_file(project_file.id)

            # シート情報を構築（カラム情報なし）
            sheets = []
            for driver_tree_file in driver_tree_files:
                sheets.append(
                    {
                        "sheet_id": str(driver_tree_file.id),
                        "sheet_name": driver_tree_file.sheet_name,
                    }
                )

            result_files.append(
                {
                    "file_id": project_file.id,
                    "filename": project_file.original_filename,
                    "file_size": project_file.file_size,
                    "uploaded_at": project_file.uploaded_at,
                    "sheets": sheets,
                }
            )

        logger.info(
            "アップロード済みファイル一覧を取得しました",
            project_id=str(project_id),
            file_count=len(result_files),
        )

        return {"files": result_files}
