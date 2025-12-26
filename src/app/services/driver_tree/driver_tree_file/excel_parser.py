"""ドライバーツリー用Excel解析ユーティリティ。

Excelファイルのシートを読み込み、メタデータとデータに分割して転置します。
"""

from io import BytesIO
from pathlib import Path

import pandas as pd

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.services.storage.excel import find_separator_row, read_excel_sheet, split_by_separator

logger = get_logger(__name__)


def parse_driver_tree_excel(file_path: Path | str | BytesIO, sheet_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Excelファイルのシートを読み込み、2つのDataFrameに分割して転置する。

    Excel構造の想定:
        - 空行前: メタデータ行（FY、地域、対象など）
        - 空行: 区切り
        - 空行後: データ行（施設数、稼働率など）

    処理フロー:
        1. 全データを読み込む
        2. 空行を見つける
        3. 空行前のメタデータを転置（1列目をヘッダーに）
        4. 空行後のデータを転置（1列目をヘッダーに）
        5. 両方を返す

    例:
        Excel 元データ:
                   列0    列1         列2         列3
            行0:   FY,    2021-03-31, 2021-03-31, 2022-03-31
            行1:   地域,   首都圏,     首都圏,     京阪奈
            行2:   対象,   リゾート,   ビジネス,   リゾート
            行3:   NaN,   NaN,       NaN,       NaN
            行4:   施設数,  5,         10,        4
            行5:   稼働率,  0.75,      0.85,      0.7

        返却値:
            df_metadata_transposed:
                   FY          地域    対象
                0  2021-03-31  首都圏  リゾート
                1  2021-03-31  首都圏  ビジネス
                2  2022-03-31  京阪奈  リゾート

            df_data_transposed:
                   施設数  稼働率
                0  5      0.75
                1  10     0.85
                2  4      0.7

    Args:
        file_path: Excelファイルのパス、またはBytesIOオブジェクト
        sheet_name: シート名

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (転置後のメタデータDataFrame, 転置後のデータDataFrame)

    Raises:
        ValidationError: Excel解析に失敗した場合
    """
    try:
        # 1. Excelシートを読み込む（共通関数使用）
        df_raw = read_excel_sheet(file_path, sheet_name)

        # 2. 空行を探す（共通関数使用）
        empty_row_idx = find_separator_row(df_raw)

        # 3. 空行でメタデータとデータに分割（共通関数使用）
        df_metadata, df_data = split_by_separator(df_raw, empty_row_idx)

        # 4. メタデータを転置（1列目をヘッダーに）
        df_metadata_transposed = df_metadata.T
        df_metadata_transposed.columns = df_metadata_transposed.iloc[0]
        df_metadata_transposed = df_metadata_transposed.drop(df_metadata_transposed.index[0])
        df_metadata_transposed = df_metadata_transposed.reset_index(drop=True)

        # 5. データを転置（1列目をヘッダーに）
        df_data_transposed = df_data.T
        df_data_transposed.columns = df_data_transposed.iloc[0]
        df_data_transposed = df_data_transposed.drop(df_data_transposed.index[0])
        df_data_transposed = df_data_transposed.reset_index(drop=True)

        return df_metadata_transposed, df_data_transposed
    except ValidationError:
        # ValidationErrorはそのまま再送出
        raise
    except Exception as e:
        logger.error(
            "Excel解析エラー",
            error=str(e),
            file_path=str(file_path),
            sheet_name=sheet_name,
        )
        raise ValidationError(
            "Excelシートの解析に失敗しました",
            details={"error": str(e), "sheet_name": sheet_name},
        ) from e
