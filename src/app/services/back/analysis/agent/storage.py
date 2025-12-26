"""分析ファイル用のストレージヘルパー。

このモジュールは、分析機能で使用するファイルストレージ操作の
ヘルパー関数を提供します。Pandas DataFrameとCSVの変換、
ストレージパスの生成などを行います。

主な機能:
    - DataFrame ↔ CSV変換
    - ストレージパスの生成
    - ファイルのアップロード/ダウンロード

使用例:
    >>> from app.services.analysis.agent.storage import AnalysisStorageService
    >>> import pandas as pd
    >>>
    >>> storage = AnalysisStorageService()
    >>> df = pd.DataFrame({"col1": [1, 2, 3]})
    >>> path = await storage.save_dataframe(session_id, "step_0", df)
    >>> loaded_df = await storage.load_dataframe(path)
"""

import uuid
from io import StringIO

import pandas as pd

from app.api.decorators import async_timeout
from app.core.logging import get_logger
from app.services.storage import StorageService, get_storage_service

logger = get_logger(__name__)


class AnalysisStorageService:
    """分析ファイル用のストレージサービス。

    このクラスは、分析機能で使用するDataFrameやチャートデータの
    ストレージ操作をサポートします。

    Attributes:
        storage (StorageService): ストレージサービスインスタンス
        container (str): コンテナ名（デフォルト: "analysis"）

    Example:
        >>> storage_service = AnalysisStorageService()
        >>> df = pd.DataFrame({"地域": ["東京", "大阪"], "売上": [1000, 2000]})
        >>> path = await storage_service.save_dataframe(session_id, "original", df)
        >>> print(path)
        analysis/abc-123-456/original.csv
    """

    def __init__(self, storage: StorageService | None = None, container: str = "analysis"):
        """分析ストレージサービスを初期化します。

        Args:
            storage (StorageService | None): ストレージサービスインスタンス
                - Noneの場合、get_storage_service()で自動取得
            container (str): コンテナ名
                - デフォルト: "analysis"

        Note:
            - テスト時はモックストレージを注入可能
        """
        self.storage = storage or get_storage_service()
        self.container = container
        logger.info(
            "分析ストレージサービスを初期化しました",
            container=container,
        )

    def generate_path(self, session_id: uuid.UUID, filename: str, prefix: str | None = None) -> str:
        """ストレージパスを生成します。

        Args:
            session_id (uuid.UUID): セッションID
            filename (str): ファイル名
            prefix (str | None): プレフィックス（オプション）

        Returns:
            str: ストレージパス
                - 例: "abc-123-456/data.csv"
                - prefix指定時: "abc-123-456/steps/data.csv"

        Example:
            >>> path = storage.generate_path(session_id, "original.csv")
            >>> print(path)
            abc-123-456/original.csv
            >>>
            >>> path = storage.generate_path(session_id, "step_0.csv", prefix="steps")
            >>> print(path)
            abc-123-456/steps/step_0.csv
        """
        session_str = str(session_id)
        if prefix:
            return f"{session_str}/{prefix}/{filename}"
        return f"{session_str}/{filename}"

    @async_timeout(30.0)
    async def save_dataframe(
        self,
        session_id: uuid.UUID,
        filename: str,
        df: pd.DataFrame,
        prefix: str | None = None,
    ) -> str:
        """DataFrameをCSVとして保存します。

        Args:
            session_id (uuid.UUID): セッションID
            filename (str): ファイル名（拡張子なし）
                - 自動的に .csv が追加されます
            df (pd.DataFrame): 保存するDataFrame
            prefix (str | None): プレフィックス（オプション）

        Returns:
            str: 保存されたファイルのストレージパス

        Raises:
            ValidationError: 保存に失敗した場合

        Example:
            >>> df = pd.DataFrame({"地域": ["東京"], "売上": [1000]})
            >>> path = await storage.save_dataframe(session_id, "original", df)
            >>> print(path)
            abc-123-456/original.csv

        Note:
            - CSVはUTF-8エンコーディングで保存されます
            - インデックスは保存されません（index=False）
        """
        # ファイル名に.csvを追加
        if not filename.endswith(".csv"):
            filename = f"{filename}.csv"

        # DataFrameをCSV文字列に変換
        csv_string = df.to_csv(index=False, encoding="utf-8")
        csv_bytes = csv_string.encode("utf-8")

        # ストレージパスを生成
        path = self.generate_path(session_id, filename, prefix)

        # アップロード
        await self.storage.upload(self.container, path, csv_bytes)

        logger.info(
            "DataFrameを保存しました",
            session_id=str(session_id),
            path=path,
            rows=len(df),
            columns=len(df.columns),
            size=len(csv_bytes),
        )

        return path

    @async_timeout(30.0)
    async def load_dataframe(self, path: str) -> pd.DataFrame:
        """CSVファイルをDataFrameとして読み込みます。

        Args:
            path (str): ストレージパス
                - 例: "abc-123-456/original.csv"

        Returns:
            pd.DataFrame: 読み込まれたDataFrame

        Raises:
            NotFoundError: ファイルが存在しない場合
            ValidationError: 読み込みに失敗した場合

        Example:
            >>> df = await storage.load_dataframe("abc-123-456/original.csv")
            >>> print(df.head())
               地域  売上
            0  東京  1000

        Note:
            - CSVはUTF-8エンコーディングで読み込まれます
        """
        # ダウンロード
        csv_bytes = await self.storage.download(self.container, path)
        csv_string = csv_bytes.decode("utf-8")

        # CSVをDataFrameに変換
        df = pd.read_csv(StringIO(csv_string), encoding="utf-8")

        logger.debug(
            "DataFrameを読み込みました",
            path=path,
            rows=len(df),
            columns=len(df.columns),
        )

        return df

    @async_timeout(30.0)
    async def save_text(
        self,
        session_id: uuid.UUID,
        filename: str,
        text: str,
        prefix: str | None = None,
    ) -> str:
        """テキストファイルを保存します。

        Args:
            session_id (uuid.UUID): セッションID
            filename (str): ファイル名
            text (str): テキストデータ
            prefix (str | None): プレフィックス（オプション）

        Returns:
            str: 保存されたファイルのストレージパス

        Raises:
            ValidationError: 保存に失敗した場合

        Example:
            >>> path = await storage.save_text(
            ...     session_id,
            ...     "chart.json",
            ...     '{"data": [...]}'
            ... )
            >>> print(path)
            abc-123-456/chart.json

        Note:
            - テキストはUTF-8エンコーディングで保存されます
        """
        # ストレージパスを生成
        path = self.generate_path(session_id, filename, prefix)

        # テキストをバイトに変換
        text_bytes = text.encode("utf-8")

        # アップロード
        await self.storage.upload(self.container, path, text_bytes)

        logger.info(
            "テキストファイルを保存しました",
            session_id=str(session_id),
            path=path,
            size=len(text_bytes),
        )

        return path

    async def load_text(self, path: str) -> str:
        """テキストファイルを読み込みます。

        Args:
            path (str): ストレージパス

        Returns:
            str: テキストデータ

        Raises:
            NotFoundError: ファイルが存在しない場合
            ValidationError: 読み込みに失敗した場合

        Example:
            >>> text = await storage.load_text("abc-123-456/chart.json")
            >>> print(text)
            {"data": [...]}

        Note:
            - テキストはUTF-8エンコーディングで読み込まれます
        """
        # ダウンロード
        text_bytes = await self.storage.download(self.container, path)
        text = text_bytes.decode("utf-8")

        logger.debug(
            "テキストファイルを読み込みました",
            path=path,
            size=len(text_bytes),
        )

        return text

    async def delete_file(self, path: str) -> bool:
        """ファイルを削除します。

        Args:
            path (str): ストレージパス

        Returns:
            bool: 成功時True

        Raises:
            NotFoundError: ファイルが存在しない場合
            ValidationError: 削除に失敗した場合

        Example:
            >>> success = await storage.delete_file("abc-123-456/original.csv")
            >>> print(success)
            True
        """
        success = await self.storage.delete(self.container, path)

        logger.info(
            "ファイルを削除しました",
            path=path,
        )

        return success

    async def file_exists(self, path: str) -> bool:
        """ファイルの存在を確認します。

        Args:
            path (str): ストレージパス

        Returns:
            bool: ファイルが存在する場合True

        Example:
            >>> exists = await storage.file_exists("abc-123-456/original.csv")
            >>> print(exists)
            True
        """
        return await self.storage.exists(self.container, path)


# ヘルパー関数


def dataframe_to_csv_string(df: pd.DataFrame) -> str:
    """DataFrameをCSV文字列に変換します。

    Args:
        df (pd.DataFrame): DataFrame

    Returns:
        str: CSV文字列

    Example:
        >>> df = pd.DataFrame({"col1": [1, 2, 3]})
        >>> csv = dataframe_to_csv_string(df)
        >>> print(csv)
        col1
        1
        2
        3
    """
    return df.to_csv(index=False, encoding="utf-8")


def csv_string_to_dataframe(csv_string: str) -> pd.DataFrame:
    """CSV文字列をDataFrameに変換します。

    Args:
        csv_string (str): CSV文字列

    Returns:
        pd.DataFrame: DataFrame

    Example:
        >>> csv = "col1\\n1\\n2\\n3"
        >>> df = csv_string_to_dataframe(csv)
        >>> print(df)
           col1
        0     1
        1     2
        2     3
    """
    return pd.read_csv(StringIO(csv_string), encoding="utf-8")
