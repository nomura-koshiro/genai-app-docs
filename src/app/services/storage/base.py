"""ストレージサービス抽象基底クラス。

このモジュールは、ファイルストレージ操作の共通インターフェースを定義します。
"""

from abc import ABC, abstractmethod


class StorageService(ABC):
    """ストレージサービスの抽象基底クラス。

    このクラスは、ファイルストレージ操作の共通インターフェースを定義します。
    具体的な実装（ローカル、Azure）は、このクラスを継承して実装されます。

    メソッド:
        upload(): ファイルをアップロード
        download(): ファイルをダウンロード
        delete(): ファイルを削除
        exists(): ファイルの存在を確認
        list_blobs(): コンテナ内のファイル一覧を取得
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

    @abstractmethod
    def get_file_path(self, container: str, path: str) -> str:
        """ファイルの完全パスを取得します。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            str: 完全なファイルパス
        """
        pass

    @abstractmethod
    async def download_to_temp_file(self, container: str, path: str) -> str:
        """ファイルを一時ファイルにダウンロードし、そのパスを返します。

        FileResponseで使用するために、ファイルをローカルに保存します。
        ローカルストレージの場合は既存パスを返し、
        Azure Blobの場合は一時ファイルにダウンロードしてパスを返します。

        Args:
            container (str): コンテナ名
            path (str): ファイルパス

        Returns:
            str: ファイルのローカルパス

        Raises:
            NotFoundError: ファイルが存在しない場合
            ValidationError: ダウンロード失敗時
        """
        pass
