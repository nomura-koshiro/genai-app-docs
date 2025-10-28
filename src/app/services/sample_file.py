"""ファイル管理サービス。

このモジュールは、ファイルのアップロード、ダウンロード、削除機能を提供します。
"""

import os
import re
import secrets
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.sample_file import SampleFile
from app.repositories.sample_file import SampleFileRepository

logger = get_logger(__name__)

# アップロードを許可するMIMEタイプ
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/csv",
    "application/pdf",
    "application/json",
    "image/png",
    "image/jpeg",
    "image/gif",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# 最大ファイルサイズ（バイト）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class SampleFileService:
    """ファイル管理サービス。

    ファイルのアップロード、ダウンロード、削除、一覧取得を提供します。
    """

    def __init__(self, db: AsyncSession):
        """ファイルサービスを初期化します。

        Args:
            db: SQLAlchemyの非同期データベースセッション
        """
        self.db = db
        self.repository = SampleFileRepository(db)
        self.upload_dir = Path(settings.LOCAL_STORAGE_PATH)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, file: UploadFile, user_id: int | None = None) -> SampleFile:
        """ファイルをアップロードします。

        Args:
            file: アップロードするファイル
            user_id: ユーザーID（オプション）

        Returns:
            SampleFile: 作成されたファイルメタデータ

        Raises:
            ValidationError: ファイルが無効な場合
        """
        logger.info(
            "ファイルアップロード開始",
            extra={
                "filename": file.filename,
                "content_type": file.content_type,
                "user_id": user_id,
            },
        )

        # バリデーション
        if not file.filename:
            raise ValidationError("ファイル名が必要です")

        if file.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"許可されていないファイルタイプです: {file.content_type}",
                details={"allowed_types": list(ALLOWED_MIME_TYPES)},
            )

        # ファイルサイズチェック
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # ファイルポインタをリセット

        if file_size > MAX_FILE_SIZE:
            raise ValidationError(
                f"ファイルサイズが大きすぎます（最大: {MAX_FILE_SIZE / 1024 / 1024}MB）",
                details={"size": file_size, "max_size": MAX_FILE_SIZE},
            )

        # ファイルIDと安全なファイル名を生成
        file_id = self._generate_file_id()
        safe_filename = self._sanitize_filename(file.filename)
        filename_with_id = f"{file_id}_{safe_filename}"
        filepath = self.upload_dir / filename_with_id

        # ファイルを保存
        try:
            with open(filepath, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.error(
                "ファイル保存エラー",
                extra={"filename": safe_filename, "error": str(e)},
                exc_info=True,
            )
            raise ValidationError(f"ファイルの保存に失敗しました: {str(e)}") from e

        # データベースに保存
        file_metadata = await self.repository.create_file(
            file_id=file_id,
            filename=safe_filename,
            filepath=str(filepath),
            size=file_size,
            content_type=file.content_type or "application/octet-stream",
            user_id=user_id,
        )

        await self.db.commit()

        logger.info(
            "ファイルアップロード完了",
            extra={
                "file_id": file_id,
                "filename": safe_filename,
                "size": file_size,
            },
        )

        return file_metadata

    async def get_file(self, file_id: str) -> SampleFile:
        """ファイルメタデータを取得します。

        Args:
            file_id: ファイル識別子

        Returns:
            SampleFile: ファイルメタデータ

        Raises:
            NotFoundError: ファイルが存在しない場合
        """
        file = await self.repository.get_by_file_id(file_id)
        if not file:
            raise NotFoundError(f"ファイルが見つかりません: {file_id}", details={"file_id": file_id})

        # ファイルの存在確認
        if not os.path.exists(file.filepath):
            logger.error(
                "ファイルがディスク上に存在しません",
                extra={"file_id": file_id, "filepath": file.filepath},
            )
            raise NotFoundError(
                f"ファイルがディスク上に存在しません: {file_id}",
                details={"file_id": file_id},
            )

        return file

    async def delete_file(self, file_id: str) -> bool:
        """ファイルを削除します。

        Args:
            file_id: ファイル識別子

        Returns:
            bool: 削除成功の場合True

        Raises:
            NotFoundError: ファイルが存在しない場合
        """
        logger.info("ファイル削除", file_id=file_id)

        file = await self.repository.get_by_file_id(file_id)
        if not file:
            raise NotFoundError(f"ファイルが見つかりません: {file_id}", details={"file_id": file_id})

        # ディスクからファイルを削除
        try:
            if os.path.exists(file.filepath):
                os.remove(file.filepath)
        except Exception as e:
            logger.error(
                "ファイル削除エラー",
                extra={"file_id": file_id, "filepath": file.filepath, "error": str(e)},
                exc_info=True,
            )

        # データベースから削除
        await self.repository.delete_file(file_id)
        await self.db.commit()

        logger.info("ファイル削除完了", file_id=file_id)

        return True

    async def list_files(self, user_id: int | None = None, skip: int = 0, limit: int = 100) -> list[SampleFile]:
        """ファイル一覧を取得します。

        Args:
            user_id: ユーザーID（指定した場合、そのユーザーのファイルのみ）
            skip: スキップするレコード数
            limit: 取得する最大レコード数

        Returns:
            list[SampleFile]: ファイルのリスト
        """
        logger.debug("ファイル一覧取得", extra={"user_id": user_id, "skip": skip, "limit": limit})

        files = await self.repository.list_files(user_id=user_id, skip=skip, limit=limit)

        logger.debug("ファイル一覧取得完了", extra={"count": len(files)})

        return files

    def _generate_file_id(self) -> str:
        """ファイルIDを生成します。

        Returns:
            str: ランダムなファイル識別子
        """
        return f"file_{secrets.token_urlsafe(16)}"

    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名をサニタイズします。

        Args:
            filename: 元のファイル名

        Returns:
            str: サニタイズされたファイル名
        """
        # ファイル名から危険な文字を削除
        filename = re.sub(r'[<>:"/\\|?*]', "", filename)
        # 先頭・末尾の空白とドットを削除
        filename = filename.strip(". ")
        # 空の場合はデフォルト名を使用
        if not filename:
            filename = "unnamed_file"
        return filename
