"""データフォーマットユーティリティ。

このモジュールは、データの表示用フォーマット変換を提供します。
"""


class DataFormatter:
    """データフォーマッター。

    メソッド:
        - format_bytes: バイト数を人間が読める形式に変換
    """

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """バイト数を人間が読める形式に変換します。

        Args:
            bytes_value: バイト数

        Returns:
            フォーマット済み文字列（例: "1.5 MB", "2.3 GB"）

        Examples:
            >>> DataFormatter.format_bytes(1024)
            "1.0 KB"
            >>> DataFormatter.format_bytes(1536)
            "1.5 KB"
            >>> DataFormatter.format_bytes(1073741824)
            "1.0 GB"
        """
        value: float = float(bytes_value)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"
