"""Azure Blob Storageサービス。

本番環境で使用するAzure Blob Storageの実装です。
"""

import tempfile
from pathlib import Path

import aiofiles
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient, ContainerClient

from app.api.decorators import async_timeout
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger

from .base import StorageService

logger = get_logger(__name__)


class AzureStorageService(StorageService):
    """Azure Blob Storageサービス。

    本番環境で使用するAzure Blob Storageの実装です。

    Attributes:
        client (BlobServiceClient): Azure Blob Storageクライアント

    Example:
        >>> storage = AzureStorageService(connection_string)
        >>> await storage.upload("analysis", "data.csv", b"data")
        True
    """

    def __init__(self, connection_string: str):
        """Azure Blob Storageサービスを初期化します。

        Args:
            connection_string (str): Azure Storage接続文字列

        Note:
            - 接続文字列は環境変数から取得されることを想定
        """
        self.client = BlobServiceClient.from_connection_string(connection_string)
        logger.info("Azure Blob Storageサービスを初期化しました")

    def _get_container_client(self, container: str) -> ContainerClient:
        """コンテナクライアントを取得します。

        Args:
            container (str): コンテナ名

        Returns:
            ContainerClient: コンテナクライアント
        """
        return self.client.get_container_client(container)

    @async_timeout(30.0)
    async def upload(self, container: str, path: str, data: bytes) -> bool:
        """ファイルをアップロードします。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス
            data (bytes): ファイルデータ

        Returns:
            bool: 成功時True

        Raises:
            ValidationError: アップロード失敗時
        """
        try:
            container_client = self._get_container_client(container)
            await container_client.create_container(exist_ok=True)

            blob_client = container_client.get_blob_client(path)
            await blob_client.upload_blob(data, overwrite=True)

            logger.info(
                "Azure Blob Storageにアップロードしました",
                container=container,
                path=path,
                size=len(data),
            )
            return True

        except Exception as e:
            logger.error(
                "Azure Blob Storageへのアップロードに失敗しました",
                container=container,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"Failed to upload file: {str(e)}",
                details={"container": container, "path": path},
            ) from e

    @async_timeout(30.0)
    async def download(self, container: str, path: str) -> bytes:
        """ファイルをダウンロードします。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            bytes: ファイルデータ

        Raises:
            NotFoundError: ファイルが存在しない場合
            ValidationError: ダウンロード失敗時
        """
        try:
            container_client = self._get_container_client(container)
            blob_client = container_client.get_blob_client(path)

            if not await blob_client.exists():
                logger.warning(
                    "Azure Blob Storageにファイルが見つかりません",
                    container=container,
                    path=path,
                )
                raise NotFoundError(
                    f"File not found: {path}",
                    details={"container": container, "path": path},
                )

            downloader = await blob_client.download_blob()
            data = await downloader.readall()

            logger.debug(
                "Azure Blob Storageからダウンロードしました",
                container=container,
                path=path,
                size=len(data),
            )
            return data

        except NotFoundError:
            raise
        except ResourceNotFoundError as e:
            logger.warning(
                "Azure Blob Storageのコンテナが見つかりません",
                container=container,
            )
            raise NotFoundError(
                f"Container not found: {container}",
                details={"container": container},
            ) from e
        except Exception as e:
            logger.error(
                "Azure Blob Storageからのダウンロードに失敗しました",
                container=container,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"Failed to download file: {str(e)}",
                details={"container": container, "path": path},
            ) from e

    @async_timeout(30.0)
    async def delete(self, container: str, path: str) -> bool:
        """ファイルを削除します。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            bool: 成功時True

        Raises:
            NotFoundError: ファイルが存在しない場合
            ValidationError: 削除失敗時
        """
        try:
            container_client = self._get_container_client(container)
            blob_client = container_client.get_blob_client(path)

            if not await blob_client.exists():
                logger.warning(
                    "削除対象のファイルが見つかりません",
                    container=container,
                    path=path,
                )
                raise NotFoundError(
                    f"File not found: {path}",
                    details={"container": container, "path": path},
                )

            await blob_client.delete_blob()

            logger.info(
                "Azure Blob Storageからファイルを削除しました",
                container=container,
                path=path,
            )
            return True

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Azure Blob Storageからの削除に失敗しました",
                container=container,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"Failed to delete file: {str(e)}",
                details={"container": container, "path": path},
            ) from e

    async def exists(self, container: str, path: str) -> bool:
        """ファイルの存在を確認します。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            bool: ファイルが存在する場合True
        """
        try:
            container_client = self._get_container_client(container)
            blob_client = container_client.get_blob_client(path)
            return await blob_client.exists()
        except Exception:
            return False

    @async_timeout(30.0)
    async def list_blobs(self, container: str, prefix: str = "") -> list[str]:
        """コンテナ内のファイル一覧を取得します。

        Args:
            container (str): コンテナ名
            prefix (str): ファイルパスのプレフィックス（フィルタ用）

        Returns:
            list[str]: ファイルパスのリスト

        Example:
            >>> files = await storage.list_blobs("analysis", prefix="data/")
            >>> print(files)
            ['data/file1.csv', 'data/file2.csv']
        """
        try:
            container_client = self._get_container_client(container)

            # コンテナが存在するか確認
            try:
                await container_client.get_container_properties()
            except ResourceNotFoundError:
                logger.warning(
                    "コンテナが見つかりません",
                    container=container,
                )
                return []

            # Blobリストを取得
            result = []
            async for blob in container_client.list_blobs(name_starts_with=prefix or None):
                result.append(blob.name)

            logger.debug(
                "ファイル一覧を取得しました",
                container=container,
                prefix=prefix,
                count=len(result),
            )
            return result

        except Exception as e:
            logger.error(
                "ファイル一覧の取得に失敗しました",
                container=container,
                prefix=prefix,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            return []

    def get_file_path(self, container: str, path: str) -> str:
        """ファイルの完全パス（URL）を取得します。

        Note:
            Azure Blob Storageの場合、このメソッドはBlobのURLを返します。
            FileResponseで使用する場合は、download_to_temp_file()を使用してください。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            str: Blob URL
        """
        container_client = self._get_container_client(container)
        blob_client = container_client.get_blob_client(path)
        return blob_client.url

    @async_timeout(30.0)
    async def download_to_temp_file(self, container: str, path: str) -> str:
        """ファイルを一時ファイルにダウンロードし、そのパスを返します。

        FileResponseで使用するために、Azure Blobの内容を一時ファイルに保存します。
        呼び出し元は、ファイル使用後に一時ファイルを削除する責任があります。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            str: 一時ファイルのパス

        Raises:
            NotFoundError: ファイルが存在しない場合
            ValidationError: ダウンロード失敗時
        """
        # ファイルをダウンロード
        data = await self.download(container, path)

        # 元のファイル名から拡張子を取得
        original_filename = Path(path).name
        suffix = Path(original_filename).suffix or ""

        # 一時ファイルを作成して書き込み
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix="azure_blob_")

        try:
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(data)

            logger.debug(
                "一時ファイルにダウンロードしました",
                container=container,
                path=path,
                temp_path=temp_path,
                size=len(data),
            )
            return temp_path

        except Exception as e:
            # エラー時は一時ファイルを削除
            import os

            try:
                os.close(temp_fd)
                os.unlink(temp_path)
            except Exception:
                pass
            logger.error(
                "一時ファイルへの書き込みに失敗しました",
                container=container,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"Failed to write to temporary file: {str(e)}",
                details={"container": container, "path": path},
            ) from e

    @async_timeout(30.0)
    async def copy(self, container: str, source_path: str, dest_path: str) -> bool:
        """ファイルをコピーします。

        Args:
            container (str): コンテナ名
            source_path (str): コピー元ファイルパス
            dest_path (str): コピー先ファイルパス

        Returns:
            bool: 成功時True

        Raises:
            NotFoundError: コピー元ファイルが存在しない場合
            ValidationError: コピー失敗時
        """
        try:
            container_client = self._get_container_client(container)

            # コピー元Blobの存在確認
            source_blob_client = container_client.get_blob_client(source_path)
            if not await source_blob_client.exists():
                logger.warning(
                    "コピー元ファイルが見つかりません",
                    container=container,
                    source_path=source_path,
                )
                raise NotFoundError(
                    f"Source file not found: {source_path}",
                    details={"container": container, "source_path": source_path},
                )

            # コピー先Blobクライアントを取得
            dest_blob_client = container_client.get_blob_client(dest_path)

            # Azure Blob Storageのcopy操作を実行
            # コピー元のURLを取得してコピーを開始
            source_url = source_blob_client.url
            await dest_blob_client.start_copy_from_url(source_url)

            logger.info(
                "Azure Blob Storageでファイルをコピーしました",
                container=container,
                source_path=source_path,
                dest_path=dest_path,
            )
            return True

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Azure Blob Storageでのコピーに失敗しました",
                container=container,
                source_path=source_path,
                dest_path=dest_path,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"Failed to copy file: {str(e)}",
                details={"container": container, "source_path": source_path, "dest_path": dest_path},
            ) from e
