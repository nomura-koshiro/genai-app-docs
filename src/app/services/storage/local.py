"""ローカルファイルシステムストレージサービス。

開発環境で使用するローカルストレージの実装です。
"""

from pathlib import Path

import aiofiles
import aiofiles.os

from app.api.decorators import async_timeout
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger

from .base import StorageService

logger = get_logger(__name__)


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
        """ファイルの完全パスを取得します（内部用）。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            Path: 完全なファイルパス
        """
        container_path = self.base_path / container
        container_path.mkdir(parents=True, exist_ok=True)
        return container_path / path

    def get_file_path(self, container: str, path: str) -> str:
        """ファイルの完全パスを取得します。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            str: 完全なファイルパス
        """
        return str(self._get_file_path(container, path))

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
                f"File not found: {path}",
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
                f"File not found: {path}",
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
        import asyncio
        import glob as sync_glob

        container_path = self.base_path / container
        if not container_path.exists():
            return []

        # プレフィックスを使用してファイルを検索（非同期でブロッキングを回避）
        if prefix:
            search_pattern = str(container_path / (prefix + "**"))
        else:
            search_pattern = str(container_path / "**")

        # 同期globを別スレッドで実行してブロッキングを回避
        all_files = await asyncio.to_thread(sync_glob.glob, search_pattern, recursive=True)

        # ディレクトリを除外し、相対パスに変換
        result = []
        for file_path in all_files:
            p = Path(file_path)
            if p.is_file():
                relative_path = p.relative_to(container_path)
                result.append(str(relative_path).replace("\\", "/"))

        return result

    async def download_to_temp_file(self, container: str, path: str) -> str:
        """ファイルのパスを返します（ローカルストレージはそのまま）。

        ローカルストレージの場合、ファイルは既にローカルに存在するため、
        そのパスをそのまま返します。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            str: ファイルのローカルパス

        Raises:
            NotFoundError: ファイルが存在しない場合
        """
        file_path = self._get_file_path(container, path)

        if not await aiofiles.os.path.exists(file_path):
            logger.warning(
                "File not found",
                container=container,
                path=path,
            )
            raise NotFoundError(
                f"File not found: {path}",
                details={"container": container, "path": path},
            )

        return str(file_path)
