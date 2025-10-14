"""ビジネスロジック用のファイルサービス。"""

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.file import File
from app.repositories.file import FileRepository
from app.storage import get_storage_backend


class FileService:
    """ファイル関連のビジネスロジック用サービス。"""

    def __init__(self, db: AsyncSession):
        """ファイルサービスを初期化します。

        Args:
            db: データベースセッション
        """
        self.repository = FileRepository(db)
        self.storage = get_storage_backend()

    async def upload_file(
        self, file: UploadFile, user_id: int | None = None
    ) -> File:
        """ファイルをアップロードします。

        Args:
            file: アップロードされたファイル
            user_id: オプションのユーザーID

        Returns:
            作成されたファイルインスタンス

        Raises:
            ValidationError: ファイルが大きすぎるか無効な場合
        """
        # Check file size
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise ValidationError(
                f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes",
                details={"size": len(contents), "max_size": settings.MAX_UPLOAD_SIZE},
            )

        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename or "file").suffix
        storage_filename = f"{file_id}{file_extension}"

        # Save file to storage
        storage_path = await self.storage.save(storage_filename, contents)

        # Create database record
        db_file = await self.repository.create(
            file_id=file_id,
            filename=storage_filename,
            original_filename=file.filename or "unknown",
            content_type=file.content_type,
            size=len(contents),
            storage_path=storage_path,
            user_id=user_id,
        )

        return db_file

    async def get_file(self, file_id: str) -> File:
        """file_idによってファイルを取得します。

        Args:
            file_id: ファイル識別子

        Returns:
            ファイルインスタンス

        Raises:
            NotFoundError: ファイルが見つからない場合
        """
        file = await self.repository.get_by_file_id(file_id)
        if not file:
            raise NotFoundError("File not found", details={"file_id": file_id})
        return file

    async def download_file(self, file_id: str) -> tuple[bytes, str, str]:
        """ファイルの内容をダウンロードします。

        Args:
            file_id: ファイル識別子

        Returns:
            (ファイル内容、ファイル名、content_type)のタプル

        Raises:
            NotFoundError: ファイルが見つからない場合
        """
        file = await self.get_file(file_id)

        # Load file from storage
        contents = await self.storage.load(file.storage_path)

        return contents, file.original_filename, file.content_type or "application/octet-stream"

    async def delete_file(self, file_id: str) -> bool:
        """ファイルを削除します。

        Args:
            file_id: ファイル識別子

        Returns:
            削除された場合はTrue

        Raises:
            NotFoundError: ファイルが見つからない場合
        """
        file = await self.get_file(file_id)

        # Delete from storage
        await self.storage.delete(file.storage_path)

        # Delete from database
        await self.repository.delete(file.id)
        return True

    async def list_files(
        self, user_id: int | None = None, skip: int = 0, limit: int = 100
    ) -> list[File]:
        """ファイルの一覧を取得します。

        Args:
            user_id: フィルタリングするオプションのユーザーID
            skip: スキップするレコード数
            limit: 返す最大レコード数

        Returns:
            ファイルのリスト
        """
        if user_id:
            return await self.repository.get_user_files(
                user_id=user_id, skip=skip, limit=limit
            )
        return await self.repository.get_all_files(skip=skip, limit=limit)
