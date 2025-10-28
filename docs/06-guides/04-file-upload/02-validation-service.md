# ステップ2-3: バリデーションとサービス

このドキュメントでは、ファイルバリデーションとファイルサービスの実装方法について説明します。

[← 前へ: ストレージバックエンド](./04-file-upload-storage.md) | [↑ ファイルアップロード実装](./04-file-upload.md)

## 目次

- [ステップ2: ファイルバリデーション](#ステップ2-ファイルバリデーション)
- [ステップ3: ファイルサービスの拡張](#ステップ3-ファイルサービスの拡張)

## ステップ2: ファイルバリデーション

### 2.1 ファイル検証ユーティリティ

`src/app/core/file_validator.py`を作成：

```python
"""ファイルバリデーションユーティリティ。"""

from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError


# 許可されるMIMEタイプ
ALLOWED_MIME_TYPES = {
    # 画像
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    # ドキュメント
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # テキスト
    "text/plain",
    "text/csv",
}

# 許可される拡張子
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".csv",
}


async def validate_file(file: UploadFile) -> None:
    """
    アップロードされたファイルを検証します。

    Args:
        file: アップロードされたファイル

    Raises:
        ValidationError: ファイルが無効な場合
    """
    # ファイル名のチェック
    if not file.filename:
        raise ValidationError("Filename is required")

    # 拡張子のチェック
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}",
            details={"extension": file_extension},
        )

    # MIMEタイプのチェック
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"Content type not allowed: {file.content_type}",
            details={"content_type": file.content_type},
        )

    # ファイルサイズのチェック
    contents = await file.read()
    file_size = len(contents)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(
            f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes",
            details={"size": file_size, "max_size": settings.MAX_UPLOAD_SIZE},
        )

    # ファイルポインタをリセット
    await file.seek(0)


def sanitize_filename(filename: str) -> str:
    """
    ファイル名をサニタイズします。

    Args:
        filename: 元のファイル名

    Returns:
        サニタイズされたファイル名
    """
    # 危険な文字を削除
    import re

    # パス区切り文字を削除
    filename = filename.replace("/", "_").replace("\\", "_")

    # 特殊文字を削除
    filename = re.sub(r"[^\w\s.-]", "", filename)

    # 複数のドットを単一のドットに
    filename = re.sub(r"\.+", ".", filename)

    # 先頭と末尾の空白を削除
    filename = filename.strip()

    return filename
```

## ステップ3: ファイルサービスの拡張

`src/app/services/file.py`を拡張：

```python
"""ファイルビジネスロジック用サービス。"""

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.file_validator import sanitize_filename, validate_file
from app.models.sample_file import SampleFile
from app.repositories.file import FileRepository
from app.storage import get_storage_backend


class SampleFileService:
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
        """
        ファイルをアップロードします。

        Args:
            file: アップロードされたファイル
            user_id: オプションのユーザーID

        Returns:
            作成されたファイルインスタンス

        Raises:
            ValidationError: ファイルが無効な場合
        """
        # ファイルを検証
        await validate_file(file)

        # ファイル内容を読み込み
        contents = await file.read()

        # ユニークなファイルIDを生成
        file_id = str(uuid.uuid4())
        original_filename = sanitize_filename(file.filename or "file")
        file_extension = Path(original_filename).suffix

        # ストレージ用のファイル名
        storage_filename = f"{file_id}{file_extension}"

        # ストレージに保存
        storage_path = await self.storage.save(storage_filename, contents)

        # データベースレコードを作成
        db_file = await self.repository.create(
            file_id=file_id,
            filename=storage_filename,
            original_filename=original_filename,
            content_type=file.content_type,
            size=len(contents),
            storage_path=storage_path,
            user_id=user_id,
        )

        return db_file

    async def upload_chunked(
        self,
        file: UploadFile,
        user_id: int | None = None,
        chunk_size: int = 1024 * 1024,  # 1MB
    ) -> File:
        """
        チャンク形式でファイルをアップロードします（大きなファイル用）。

        Args:
            file: アップロードされたファイル
            user_id: オプションのユーザーID
            chunk_size: チャンクサイズ（バイト）

        Returns:
            作成されたファイルインスタンス
        """
        # ファイル名とメタデータの検証
        if not file.filename:
            raise ValidationError("Filename is required")

        original_filename = sanitize_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_extension = Path(original_filename).suffix
        storage_filename = f"{file_id}{file_extension}"

        # チャンク単位でファイルを読み込み
        chunks = []
        total_size = 0

        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break

            chunks.append(chunk)
            total_size += len(chunk)

            # サイズチェック
            if total_size > settings.MAX_UPLOAD_SIZE:
                raise ValidationError(
                    f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes"
                )

        # 全チャンクを結合
        contents = b"".join(chunks)

        # ストレージに保存
        storage_path = await self.storage.save(storage_filename, contents)

        # データベースレコードを作成
        db_file = await self.repository.create(
            file_id=file_id,
            filename=storage_filename,
            original_filename=original_filename,
            content_type=file.content_type,
            size=total_size,
            storage_path=storage_path,
            user_id=user_id,
        )

        return db_file

    async def get_file_url(
        self, file_id: str, expires_in: int = 3600
    ) -> str:
        """
        ファイルの署名付きURLを取得します。

        Args:
            file_id: ファイルID
            expires_in: 有効期限（秒）

        Returns:
            署名付きURL

        Raises:
            NotFoundError: ファイルが見つからない場合
        """
        file = await self.get_file(file_id)
        return await self.storage.get_url(file.storage_path, expires_in)
```

## 次のステップ

ファイルバリデーションとサービスの実装が完了したら、次はAPIエンドポイントとベストプラクティスを確認します。

**[→ 次へ: ステップ4-5 APIとベストプラクティス](./04-file-upload-api-best-practices.md)**

## 参考リンク

- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [ファイルアップロード実装](./04-file-upload.md)
