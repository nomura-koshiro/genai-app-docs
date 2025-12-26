"""ストレージサービスパッケージ。

このパッケージは、ファイルストレージ操作の抽象化を提供します。
ローカルストレージとAzure Blob Storageの両方をサポートし、
環境に応じて自動的に切り替えます。

主な機能:
    - ファイルのアップロード/ダウンロード
    - ファイルの削除と存在確認
    - ローカル/Azure の透過的な切り替え
    - ファイル検証・サニタイズ
    - Excel操作ユーティリティ

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

from app.core.config import settings
from app.core.logging import get_logger

from .azure import AzureStorageService
from .base import StorageService
from .local import LocalStorageService

logger = get_logger(__name__)


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


__all__ = [
    "StorageService",
    "LocalStorageService",
    "AzureStorageService",
    "get_storage_service",
]
