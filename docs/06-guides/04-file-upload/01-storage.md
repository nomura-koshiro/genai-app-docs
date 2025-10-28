# ステップ1: ストレージバックエンド

このドキュメントでは、ストレージバックエンドの実装方法について説明します。

[← ファイルアップロード実装に戻る](./04-file-upload.md)

## 目次

- [1.1 抽象インターフェースの定義](#11-抽象インターフェースの定義)
- [1.2 ローカルストレージの実装](#12-ローカルストレージの実装)
- [1.3 Azure Blobストレージの実装](#13-azure-blobストレージの実装)
- [1.4 ストレージバックエンドのファクトリ](#14-ストレージバックエンドのファクトリ)

## 1.1 抽象インターフェースの定義

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

## 1.2 ローカルストレージの実装

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
        return f"/api/sample-files/download/{file_path}"
```

## 1.3 Azure Blobストレージの実装

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

## 1.4 ストレージバックエンドのファクトリ

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

## 次のステップ

ストレージバックエンドの実装が完了したら、次はファイルバリデーションとサービスを実装します。

**[→ 次へ: ステップ2-3 バリデーションとサービス](./04-file-upload-validation-service.md)**

## 参考リンク

- [Azure Blob Storage Python SDK](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python)
- [aiofiles Documentation](https://github.com/Tinche/aiofiles)
- [ファイルアップロード実装](./04-file-upload.md)
