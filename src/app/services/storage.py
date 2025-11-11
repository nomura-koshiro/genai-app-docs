"""ストレージサービス。

このモジュールは、ファイルストレージ操作の抽象化を提供します。
ローカルストレージとAzure Blob Storageの両方をサポートし、
環境に応じて自動的に切り替えます。

主な機能:
    - ファイルのアップロード/ダウンロード
    - ファイルの削除と存在確認
    - ローカル/Azure の透過的な切り替え

設計原則:
    - Strategy パターン: ストレージの実装を抽象化
    - 環境別設定: 開発/本番で自動切り替え
    - 非同期I/O: aiofiles と azure.storage.blob.aio を使用

使用例:
    >>> from app.services.storage import get_storage_service
    >>>
    >>> storage = get_storage_service()
    >>> await storage.upload("my-container", "file.txt", b"Hello")
    >>> data = await storage.download("my-container", "file.txt")
"""

from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles
import aiofiles.os
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient, ContainerClient

from app.api.decorators import async_timeout
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService(ABC):
    """ストレージサービスの抽象基底クラス。

    このクラスは、ファイルストレージ操作の共通インターフェースを定義します。
    具体的な実装（ローカル、Azure）は、このクラスを継承して実装されます。

    メソッド:
        upload(): ファイルをアップロード
        download(): ファイルをダウンロード
        delete(): ファイルを削除
        exists(): ファイルの存在を確認
        list_files(): コンテナ内のファイル一覧を取得
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def exists(self, container: str, path: str) -> bool:
        """ファイルの存在を確認します。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            bool: ファイルが存在する場合True
        """
        pass

    @abstractmethod
    async def list_blobs(self, container: str, prefix: str = "") -> list[str]:
        """コンテナ内のファイル一覧を取得します。

        Args:
            container (str): コンテナ名
            prefix (str): ファイルパスのプレフィックス（フィルタ用）

        Returns:
            list[str]: ファイルパスのリスト
        """
        pass


class LocalStorageService(StorageService):
    """ローカルファイルシステムストレージサービス。

    開発環境で使用するローカルストレージの実装です。
    ファイルはbase_pathディレクトリに保存されます。

    Attributes:
        base_path (Path): ストレージのルートディレクトリ

    Example:
        >>> storage = LocalStorageService("./uploads")
        >>> await storage.upload("analysis", "data.csv", b"data")
        True
        >>> # ファイルは ./uploads/analysis/data.csv に保存されます
    """

    def __init__(self, base_path: str = "./uploads"):
        """ローカルストレージサービスを初期化します。

        Args:
            base_path (str): ストレージのルートディレクトリ
                デフォルト: "./uploads"

        Note:
            - base_pathが存在しない場合、自動的に作成されます
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(
            "ローカルストレージサービスを初期化しました",
            base_path=str(self.base_path),
        )

    def _get_file_path(self, container: str, path: str) -> Path:
        """ファイルの完全パスを取得します。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            Path: 完全なファイルパス
        """
        container_path = self.base_path / container
        container_path.mkdir(parents=True, exist_ok=True)
        return container_path / path

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

        Example:
            >>> await storage.upload("analysis", "data.csv", b"data")
            True
        """
        try:
            file_path = self._get_file_path(container, path)
            # 親ディレクトリを作成
            file_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(data)

            logger.info(
                "ファイルをアップロードしました",
                container=container,
                path=path,
                size=len(data),
            )
            return True

        except Exception as e:
            logger.error(
                "ファイルのアップロードに失敗しました",
                container=container,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"ファイルのアップロードに失敗しました: {str(e)}",
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

        Example:
            >>> data = await storage.download("analysis", "data.csv")
            >>> print(data.decode())
            data
        """
        file_path = self._get_file_path(container, path)

        if not await aiofiles.os.path.exists(file_path):
            logger.warning(
                "ファイルが見つかりません",
                container=container,
                path=path,
            )
            raise NotFoundError(
                f"ファイルが見つかりません: {path}",
                details={"container": container, "path": path},
            )

        try:
            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()

            logger.debug(
                "ファイルをダウンロードしました",
                container=container,
                path=path,
                size=len(data),
            )
            return data

        except Exception as e:
            logger.error(
                "ファイルのダウンロードに失敗しました",
                container=container,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"ファイルのダウンロードに失敗しました: {str(e)}",
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

        Example:
            >>> await storage.delete("analysis", "data.csv")
            True
        """
        file_path = self._get_file_path(container, path)

        if not await aiofiles.os.path.exists(file_path):
            logger.warning(
                "削除対象のファイルが見つかりません",
                container=container,
                path=path,
            )
            raise NotFoundError(
                f"ファイルが見つかりません: {path}",
                details={"container": container, "path": path},
            )

        try:
            await aiofiles.os.remove(file_path)

            logger.info(
                "ファイルを削除しました",
                container=container,
                path=path,
            )
            return True

        except Exception as e:
            logger.error(
                "ファイルの削除に失敗しました",
                container=container,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"ファイルの削除に失敗しました: {str(e)}",
                details={"container": container, "path": path},
            ) from e

    async def exists(self, container: str, path: str) -> bool:
        """ファイルの存在を確認します。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            bool: ファイルが存在する場合True

        Example:
            >>> exists = await storage.exists("analysis", "data.csv")
            >>> print(exists)
            True
        """
        file_path = self._get_file_path(container, path)
        return await aiofiles.os.path.exists(file_path)

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
        import glob as sync_glob

        container_path = self.base_path / container
        if not container_path.exists():
            return []

        # プレフィックスを使用してファイルを検索
        if prefix:
            search_pattern = str(container_path / (prefix + "**"))
        else:
            search_pattern = str(container_path / "**")
        all_files = sync_glob.glob(search_pattern, recursive=True)

        # ディレクトリを除外し、相対パスに変換
        result = []
        for file_path in all_files:
            p = Path(file_path)
            if p.is_file():
                relative_path = p.relative_to(container_path)
                result.append(str(relative_path).replace("\\", "/"))

        return result


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
                f"ファイルのアップロードに失敗しました: {str(e)}",
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
                    f"ファイルが見つかりません: {path}",
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
                f"コンテナが見つかりません: {container}",
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
                f"ファイルのダウンロードに失敗しました: {str(e)}",
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
                    f"ファイルが見つかりません: {path}",
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
                f"ファイルの削除に失敗しました: {str(e)}",
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


def get_storage_service() -> StorageService:
    """環境に応じたストレージサービスを取得します。

    設定に基づいてローカルまたはAzure Blob Storageのインスタンスを返します。

    Returns:
        StorageService: ストレージサービスインスタンス
            - 開発環境: LocalStorageService
            - 本番環境: AzureStorageService

    Example:
        >>> storage = get_storage_service()
        >>> await storage.upload("container", "file.txt", b"data")

    Note:
        - STORAGE_TYPE環境変数で切り替え（local/azure）
        - デフォルトはローカルストレージ
    """
    storage_type = getattr(settings, "STORAGE_TYPE", "local")

    if storage_type == "azure":
        connection_string = getattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None)
        if not connection_string:
            logger.warning("Azure Storage接続文字列が設定されていません。ローカルストレージを使用します。")
            return LocalStorageService()
        return AzureStorageService(connection_string)

    # デフォルトはローカルストレージ
    local_path = getattr(settings, "LOCAL_STORAGE_PATH", "./uploads")
    return LocalStorageService(local_path)
