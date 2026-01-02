"""プロジェクトファイルアップロードサービス。

このモジュールは、プロジェクトファイルのアップロード操作を提供します。
"""

import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import async_timeout, measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import ProjectFile, ProjectRole
from app.services.project.project_file.base import ProjectFileServiceBase
from app.services.storage.validation import check_file_size, sanitize_filename

logger = get_logger(__name__)

# アップロードを許可するMIMEタイプ
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
}


class ProjectFileUploadService(ProjectFileServiceBase):
    """プロジェクトファイルのアップロード操作を提供するサービスクラス。"""

    def __init__(self, db: AsyncSession):
        """プロジェクトファイルアップロードサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        super().__init__(db)

    @measure_performance
    @async_timeout(60.0)
    @transactional
    async def upload_file(self, project_id: uuid.UUID, file: UploadFile, uploaded_by: uuid.UUID) -> ProjectFile:
        """プロジェクトにファイルをアップロードします。

        このメソッドは以下の処理を実行します：
        1. プロジェクトメンバーシップ確認（MEMBER以上）
        2. ファイル名の検証
        3. MIMEタイプの検証
        4. ファイルサイズの検証
        5. ファイル名のサニタイズ
        6. StorageServiceを使用してファイルを保存
        7. メタデータのデータベース保存

        Args:
            project_id: プロジェクトID
            file: アップロードするファイル
            uploaded_by: アップロード者のユーザーID

        Returns:
            ProjectFile: 作成されたファイルメタデータ

        Raises:
            AuthorizationError: ユーザーがメンバーでない、または権限が不足している場合
            ValidationError: ファイルが無効な場合
        """
        logger.info(
            "ファイルアップロード開始",
            project_id=str(project_id),
            filename=file.filename,
            content_type=file.content_type,
            uploaded_by=str(uploaded_by),
        )

        # 権限チェック（MEMBER以上）
        await self._check_member_role(project_id, uploaded_by, [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER])

        # ファイル名の検証
        if not file.filename:
            raise ValidationError("ファイル名が必要です")

        # MIMEタイプの検証
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"許可されていないファイル形式です: {file.content_type}",
                details={
                    "content_type": file.content_type,
                    "allowed_types": list(ALLOWED_MIME_TYPES),
                },
            )

        # ファイル読み込み
        content = await file.read()
        file_size = len(content)
        await file.seek(0)

        # ファイルサイズの検証
        check_file_size(file_size)

        # ファイル名のサニタイズ
        safe_filename = sanitize_filename(file.filename)
        file_id = uuid.uuid4()

        # ストレージパスを生成
        storage_path = self._generate_storage_path(project_id, file_id, safe_filename)

        # StorageServiceを使用してファイルを保存
        await self.storage.upload("", storage_path, content)

        try:
            # データベースに保存
            file_metadata = await self.repository.create(
                id=file_id,
                project_id=project_id,
                filename=safe_filename,
                original_filename=file.filename,
                file_path=storage_path,
                file_size=file_size,
                mime_type=file.content_type,
                uploaded_by=uploaded_by,
            )

            await self.db.commit()

            logger.info(
                "ファイルアップロード完了",
                file_id=str(file_id),
                filename=safe_filename,
                size=file_size,
            )

            return file_metadata

        except Exception:
            # 異常時は保存されたファイルを削除
            if await self.storage.exists("", storage_path):
                await self.storage.delete("", storage_path)
            raise

    @measure_performance
    @async_timeout(60.0)
    @transactional
    async def upload_new_version(
        self,
        parent_file_id: uuid.UUID,
        file: UploadFile,
        uploaded_by: uuid.UUID,
    ) -> ProjectFile:
        """既存ファイルの新しいバージョンをアップロードします。

        このメソッドは以下の処理を実行します：
        1. 親ファイルの存在確認
        2. プロジェクトメンバーシップ確認（MEMBER以上）
        3. ファイルの検証とサニタイズ
        4. 親ファイルのis_latestをFalseに更新
        5. 新バージョンとしてファイルを保存

        Args:
            parent_file_id: 親ファイルID（前のバージョン）
            file: アップロードするファイル
            uploaded_by: アップロード者のユーザーID

        Returns:
            ProjectFile: 作成されたファイルメタデータ（新バージョン）

        Raises:
            NotFoundError: 親ファイルが見つからない場合
            AuthorizationError: ユーザーがメンバーでない、または権限が不足している場合
            ValidationError: ファイルが無効な場合
        """
        logger.info(
            "ファイル新バージョンアップロード開始",
            parent_file_id=str(parent_file_id),
            filename=file.filename,
            content_type=file.content_type,
            uploaded_by=str(uploaded_by),
        )

        # 親ファイルの存在確認
        parent_file = await self.repository.get(parent_file_id)
        if not parent_file:
            raise NotFoundError(
                f"親ファイルが見つかりません: {parent_file_id}",
                details={"parent_file_id": str(parent_file_id)},
            )

        project_id = parent_file.project_id

        # 権限チェック（MEMBER以上）
        await self._check_member_role(project_id, uploaded_by, [ProjectRole.PROJECT_MANAGER, ProjectRole.MEMBER])

        # ファイル名の検証
        if not file.filename:
            raise ValidationError("ファイル名が必要です")

        # MIMEタイプの検証
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"許可されていないファイル形式です: {file.content_type}",
                details={
                    "content_type": file.content_type,
                    "allowed_types": list(ALLOWED_MIME_TYPES),
                },
            )

        # ファイル読み込み
        content = await file.read()
        file_size = len(content)
        await file.seek(0)

        # ファイルサイズの検証
        check_file_size(file_size)

        # ファイル名のサニタイズ
        safe_filename = sanitize_filename(file.filename)
        file_id = uuid.uuid4()

        # ストレージパスを生成
        storage_path = self._generate_storage_path(project_id, file_id, safe_filename)

        # StorageServiceを使用してファイルを保存
        await self.storage.upload("", storage_path, content)

        try:
            # 親ファイルのis_latestをFalseに更新
            await self.repository.update_is_latest(parent_file_id, False)

            # 新しいバージョン番号を計算
            new_version = parent_file.version + 1

            # データベースに保存
            file_metadata = await self.repository.create(
                id=file_id,
                project_id=project_id,
                filename=safe_filename,
                original_filename=parent_file.original_filename,  # 元のファイル名は引き継ぐ
                file_path=storage_path,
                file_size=file_size,
                mime_type=file.content_type,
                uploaded_by=uploaded_by,
                version=new_version,
                parent_file_id=parent_file_id,
                is_latest=True,
            )

            await self.db.commit()

            logger.info(
                "ファイル新バージョンアップロード完了",
                file_id=str(file_id),
                parent_file_id=str(parent_file_id),
                version=new_version,
                filename=safe_filename,
                size=file_size,
            )

            return file_metadata

        except Exception:
            # 異常時は保存されたファイルを削除
            if await self.storage.exists("", storage_path):
                await self.storage.delete("", storage_path)
            raise
