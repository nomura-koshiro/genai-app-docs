# ファイルアップロード実装

このガイドでは、ローカルストレージとAzure Blobストレージを使用したファイルアップロード機能の実装方法を説明します。

## 目次

- [概要](#概要)
- [前提条件](#前提条件)
- [ステップバイステップ](#ステップバイステップ)
- [チェックリスト](#チェックリスト)
- [よくある落とし穴](#よくある落とし穴)
- [ベストプラクティス](#ベストプラクティス)
- [参考リンク](#参考リンク)

## 概要

ファイルアップロード機能の主要コンポーネント：

```
ファイルアップロード機能
├── ストレージバックエンド（storage/）
│   ├── base.py - 抽象インターフェース
│   ├── local.py - ローカルストレージ実装
│   └── azure_blob.py - Azure Blob実装
├── ファイルモデル（models/file.py）
├── ファイルリポジトリ（repositories/file.py）
├── ファイルサービス（services/file.py）
└── ファイルAPI（api/routes/files.py）
```

## 前提条件

- FastAPIの基礎知識
- ストレージシステムの理解
- 非同期I/Oの理解
- ファイル処理のセキュリティ知識

## ステップバイステップ

### 1. ストレージバックエンドの実装

#### 1.1 抽象インターフェースの定義

`src/app/storage/base.py`：

```python
"""ストレージバックエンドの抽象インターフェース。"""

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """ストレージバックエンドの抽象基底クラス。"""

    @abstractmethod
    async def save(self, filename: str, content: bytes) -> str:
        """
        ファイルを保存します。

        Args:
            filename: ファイル名
            content: ファイル内容（バイト）

        Returns:
            保存されたファイルのパス/ID
        """
        pass

    @abstractmethod
    async def load(self, file_path: str) -> bytes:
        """
        ファイルを読み込みます。

        Args:
            file_path: ファイルパス/ID

        Returns:
            ファイル内容（バイト）
        """
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> None:
        """
        ファイルを削除します。

        Args:
            file_path: ファイルパス/ID
        """
        pass

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """
        ファイルの存在を確認します。

        Args:
            file_path: ファイルパス/ID

        Returns:
            存在する場合はTrue
        """
        pass

    @abstractmethod
    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        ファイルの署名付きURLを取得します。

        Args:
            file_path: ファイルパス/ID
            expires_in: 有効期限（秒）

        Returns:
            署名付きURL
        """
        pass
```

#### 1.2 ローカルストレージの実装

`src/app/storage/local.py`：

```python
"""ローカルファイルシステムストレージバックエンド。"""

from pathlib import Path

import aiofiles
import aiofiles.os

from app.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """ローカルファイルシステムストレージ実装。"""

    def __init__(self, base_path: str | Path):
        """
        ローカルストレージバックエンドを初期化します。

        Args:
            base_path: ファイル保存のベースディレクトリ
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, content: bytes) -> str:
        """ファイルをローカルストレージに保存します。"""
        file_path = self.base_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        return str(filename)

    async def load(self, file_path: str) -> bytes:
        """ローカルストレージからファイルを読み込みます。"""
        full_path = self.base_path / file_path

        if not await self.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, file_path: str) -> None:
        """ローカルストレージからファイルを削除します。"""
        full_path = self.base_path / file_path

        if not await self.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        await aiofiles.os.remove(full_path)

    async def exists(self, file_path: str) -> bool:
        """ファイルの存在を確認します。"""
        full_path = self.base_path / file_path
        return full_path.exists() and full_path.is_file()

    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        ローカルファイルのURLを取得します。

        Note: ローカルストレージでは署名付きURLは提供されません。
        """
        return f"/api/files/download/{file_path}"
```

#### 1.3 Azure Blobストレージの実装

`src/app/storage/azure_blob.py`：

```python
"""Azure Blob Storageバックエンド。"""

from datetime import datetime, timedelta, timezone

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

from app.storage.base import StorageBackend


class AzureBlobStorageBackend(StorageBackend):
    """Azure Blob Storage実装。"""

    def __init__(
        self,
        connection_string: str,
        container_name: str = "uploads",
    ):
        """
        Azure Blobストレージバックエンドを初期化します。

        Args:
            connection_string: Azure Storage接続文字列
            container_name: コンテナ名
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        self.container_name = container_name
        self._ensure_container()

    def _ensure_container(self) -> None:
        """コンテナが存在することを確認します。"""
        try:
            self.blob_service_client.create_container(self.container_name)
        except Exception:
            # コンテナが既に存在する場合は無視
            pass

    async def save(self, filename: str, content: bytes) -> str:
        """ファイルをAzure Blobに保存します。"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=filename,
        )

        blob_client.upload_blob(content, overwrite=True)
        return filename

    async def load(self, file_path: str) -> bytes:
        """Azure Blobからファイルを読み込みます。"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path,
        )

        if not await self.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        download_stream = blob_client.download_blob()
        return download_stream.readall()

    async def delete(self, file_path: str) -> None:
        """Azure Blobからファイルを削除します。"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path,
        )

        if not await self.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        blob_client.delete_blob()

    async def exists(self, file_path: str) -> bool:
        """ファイルの存在を確認します。"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path,
        )

        return blob_client.exists()

    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        署名付きURLを生成します。

        Args:
            file_path: ファイルパス
            expires_in: 有効期限（秒）

        Returns:
            署名付きURL
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path,
        )

        # SAS トークンを生成
        sas_token = generate_blob_sas(
            account_name=blob_client.account_name,
            container_name=self.container_name,
            blob_name=file_path,
            account_key=blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        )

        return f"{blob_client.url}?{sas_token}"
```

#### 1.4 ストレージバックエンドのファクトリ

`src/app/storage/__init__.py`：

```python
"""ストレージバックエンドパッケージ。"""

from app.config import settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend


def get_storage_backend() -> StorageBackend:
    """
    設定に基づいてストレージバックエンドを返します。

    Returns:
        StorageBackendインスタンス
    """
    if settings.STORAGE_TYPE == "azure":
        from app.storage.azure_blob import AzureBlobStorageBackend

        return AzureBlobStorageBackend(
            connection_string=settings.AZURE_STORAGE_CONNECTION_STRING,
            container_name=settings.AZURE_STORAGE_CONTAINER_NAME,
        )
    else:
        # デフォルトはローカルストレージ
        return LocalStorageBackend(base_path=settings.UPLOAD_DIR)


__all__ = [
    "StorageBackend",
    "LocalStorageBackend",
    "get_storage_backend",
]
```

### 2. ファイルバリデーション

#### 2.1 ファイル検証ユーティリティ

`src/app/core/file_validator.py`を作成：

```python
"""ファイルバリデーションユーティリティ。"""

from pathlib import Path

from fastapi import UploadFile

from app.config import settings
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

### 3. ファイルサービスの拡張

`src/app/services/file.py`を拡張：

```python
"""ファイルビジネスロジック用サービス。"""

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.file_validator import sanitize_filename, validate_file
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

### 4. APIエンドポイントの実装

`src/app/api/routes/files.py`：

```python
"""ファイルアップロード/ダウンロードAPIルート。"""

from io import BytesIO

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.dependencies import CurrentUserOptionalDep, FileServiceDep
from app.schemas.file import (
    FileDeleteResponse,
    FileInfo,
    FileListResponse,
    FileUploadResponse,
    FileUrlResponse,
)

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="アップロードするファイル"),
    file_service: FileServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> FileUploadResponse:
    """
    ファイルをアップロードします。

    - **file**: アップロードするファイル
    - 最大サイズ: 10MB（設定可能）
    - 許可される形式: jpg, png, pdf, txt など
    """
    user_id = current_user.id if current_user else None
    db_file = await file_service.upload_file(file, user_id)

    return FileUploadResponse(
        file_id=db_file.file_id,
        filename=db_file.original_filename,
        size=db_file.size,
        content_type=db_file.content_type,
        message="File uploaded successfully",
    )


@router.post("/upload/chunked", response_model=FileUploadResponse)
async def upload_file_chunked(
    file: UploadFile = File(..., description="大きなファイル"),
    file_service: FileServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> FileUploadResponse:
    """
    チャンク形式でファイルをアップロードします（大きなファイル用）。

    - メモリ効率的なアップロード
    - 大きなファイルに推奨
    """
    user_id = current_user.id if current_user else None
    db_file = await file_service.upload_chunked(file, user_id)

    return FileUploadResponse(
        file_id=db_file.file_id,
        filename=db_file.original_filename,
        size=db_file.size,
        content_type=db_file.content_type,
        message="File uploaded successfully (chunked)",
    )


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    file_service: FileServiceDep = None,
) -> StreamingResponse:
    """
    ファイルをダウンロードします。

    - ストリーミングレスポンスで効率的に配信
    """
    contents, filename, content_type = await file_service.download_file(file_id)

    return StreamingResponse(
        BytesIO(contents),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{file_id}/url", response_model=FileUrlResponse)
async def get_file_url(
    file_id: str,
    expires_in: int = Query(3600, ge=60, le=86400, description="有効期限（秒）"),
    file_service: FileServiceDep = None,
) -> FileUrlResponse:
    """
    ファイルの署名付きURLを取得します。

    - 一時的なアクセスURLを生成
    - Azure Blob使用時に署名付きURLを返す
    """
    url = await file_service.get_file_url(file_id, expires_in)

    return FileUrlResponse(
        file_id=file_id,
        url=url,
        expires_in=expires_in,
    )


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    file_service: FileServiceDep = None,
) -> FileDeleteResponse:
    """
    ファイルを削除します。
    """
    await file_service.delete_file(file_id)

    return FileDeleteResponse(
        file_id=file_id,
        message=f"File {file_id} deleted successfully",
    )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    file_service: FileServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> FileListResponse:
    """
    アップロードされたファイルのリストを取得します。
    """
    user_id = current_user.id if current_user else None
    files = await file_service.list_files(user_id=user_id, skip=skip, limit=limit)

    file_infos = [
        FileInfo(
            file_id=f.file_id,
            filename=f.original_filename,
            size=f.size,
            content_type=f.content_type,
            created_at=f.created_at,
        )
        for f in files
    ]

    return FileListResponse(files=file_infos, total=len(file_infos))
```

### 5. スキーマの追加

`src/app/schemas/file.py`に追加：

```python
class FileUrlResponse(BaseModel):
    """ファイルURL取得レスポンス。"""

    file_id: str = Field(..., description="ファイルID")
    url: str = Field(..., description="ファイルURL")
    expires_in: int = Field(..., description="有効期限（秒）")
```

## チェックリスト

ファイルアップロード実装のチェックリスト：

- [ ] ストレージバックエンドインターフェースの定義
- [ ] ローカルストレージの実装
- [ ] Azure Blobストレージの実装（必要な場合）
- [ ] ストレージファクトリの実装
- [ ] ファイルバリデーションの実装
- [ ] 許可されるファイルタイプの定義
- [ ] ファイルサイズ制限の実装
- [ ] ファイル名のサニタイゼーション
- [ ] チャンクアップロードの実装（大きなファイル用）
- [ ] ストリーミングダウンロードの実装
- [ ] 署名付きURL生成（Azure用）
- [ ] ファイル削除機能
- [ ] エラーハンドリング
- [ ] セキュリティ対策
- [ ] テストの作成

## よくある落とし穴

### 1. メモリの過剰使用

```python
# 悪い例（大きなファイルでメモリ不足）
contents = await file.read()  # ファイル全体をメモリに読み込む

# 良い例（チャンク単位で処理）
async def upload_chunked(file: UploadFile, chunk_size: int = 1024 * 1024):
    while chunk := await file.read(chunk_size):
        # チャンクを処理
        pass
```

### 2. ファイル名のセキュリティ

```python
# 悪い例（パストラバーサル攻撃の可能性）
filename = file.filename  # "../../../etc/passwd"

# 良い例
filename = sanitize_filename(file.filename)
```

### 3. Content-Typeの検証不足

```python
# 悪い例
# Content-Typeをチェックしない

# 良い例
if file.content_type not in ALLOWED_MIME_TYPES:
    raise ValidationError("Content type not allowed")
```

### 4. ファイルポインタのリセット忘れ

```python
# 悪い例
contents = await file.read()
# ファイルポインタが末尾のまま
validate_file(file)  # 空のファイルとして検証される

# 良い例
contents = await file.read()
await file.seek(0)  # ポインタをリセット
```

### 5. エラー時のクリーンアップ忘れ

```python
# 悪い例
await storage.save(filename, contents)
# エラーが発生してもファイルが残る
await repository.create(...)

# 良い例
try:
    storage_path = await storage.save(filename, contents)
    await repository.create(...)
except Exception:
    await storage.delete(storage_path)  # クリーンアップ
    raise
```

## ベストプラクティス

### 1. ストレージの抽象化

```python
# 抽象インターフェースを使用
storage: StorageBackend = get_storage_backend()

# 環境に応じて実装を切り替え
# 開発: ローカルストレージ
# 本番: Azure Blob
```

### 2. ファイルバリデーション

```python
# 複数のレイヤーでバリデーション
# 1. 拡張子チェック
# 2. MIMEタイプチェック
# 3. ファイルサイズチェック
# 4. ファイル内容チェック（オプション）
```

### 3. セキュアなファイル名

```python
# ユニークIDを使用
file_id = str(uuid.uuid4())
storage_filename = f"{file_id}{file_extension}"

# 元のファイル名は別途保存
original_filename = sanitize_filename(file.filename)
```

### 4. 効率的なストリーミング

```python
# StreamingResponseを使用
return StreamingResponse(
    BytesIO(contents),
    media_type=content_type,
    headers={"Content-Disposition": f'attachment; filename="{filename}"'},
)
```

### 5. 環境変数の活用

```python
# .env
STORAGE_TYPE=local  # または azure
MAX_UPLOAD_SIZE=10485760  # 10MB
AZURE_STORAGE_CONNECTION_STRING=...
```

## 参考リンク

### 公式ドキュメント

- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Azure Blob Storage Python SDK](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python)
- [aiofiles Documentation](https://github.com/Tinche/aiofiles)

### プロジェクト内リンク

- [ストレージ設定](../03-core-concepts/06-storage.md)
- [セキュリティ](../03-core-concepts/05-security.md)
- [エラーハンドリング](../03-core-concepts/04-error-handling.md)

### 関連ガイド

- [新しいエンドポイント追加](./01-add-endpoint.md)
- [バックグラウンドタスク](./05-background-tasks.md)
