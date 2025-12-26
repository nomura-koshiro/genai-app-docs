"""Excel操作ユーティリティ。

Excelファイルの読み込み・解析機能を提供します。

主な機能:
    - Excelシート名一覧取得
    - Excelシート読み込み
    - 空行セパレータ検出・分割
"""

from io import BytesIO
from pathlib import Path

import pandas as pd

from app.core.exceptions import ValidationError


def get_excel_sheet_names(file_path: Path | str | BytesIO) -> list[str]:
    """Excelファイルからシート名一覧を取得します。

    Args:
        file_path: Excelファイルのパス、またはBytesIOオブジェクト

    Returns:
        list[str]: シート名のリスト

    Raises:
        ValidationError: Excelファイルの読み込みに失敗した場合
    """
    try:
        with pd.ExcelFile(file_path) as excel_file:
            return [str(name) for name in excel_file.sheet_names]
    except Exception as e:
        raise ValidationError(
            "Excelファイルのシート一覧取得に失敗しました",
            details={"error": str(e)},
        ) from e


def read_excel_sheet(
    file_path: Path | str | BytesIO,
    sheet_name: str,
) -> pd.DataFrame:
    """Excelファイルから指定シートを読み込みます（ヘッダーなし）。

    Args:
        file_path: Excelファイルのパス、またはBytesIOオブジェクト
        sheet_name: シート名

    Returns:
        pd.DataFrame: 読み込んだDataFrame（ヘッダーなし）

    Raises:
        ValidationError: シートの読み込みに失敗した場合
    """
    try:
        with pd.ExcelFile(file_path) as excel_file:
            return pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    except Exception as e:
        raise ValidationError(
            "Excelシートの読み込みに失敗しました",
            details={"sheet_name": sheet_name, "error": str(e)},
        ) from e


def find_separator_row(df: pd.DataFrame) -> int:
    """DataFrameから空行（セパレータ）のインデックスを見つけます。

    空行とは、すべての値がNaNである行です。

    Args:
        df: 検索対象のDataFrame

    Returns:
        int: 空行のインデックス

    Raises:
        ValidationError: 空行が見つからない場合
    """
    for row_idx in range(len(df)):
        if df.iloc[row_idx].isna().all():
            return row_idx

    raise ValidationError(
        "シート内に空行の区切りが見つかりません",
        details={"message": "ヘッダーとデータを区切る空行が必要です"},
    )


def split_by_separator(
    df: pd.DataFrame,
    separator_index: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """DataFrameをセパレータ行で2つに分割します。

    Args:
        df: 分割対象のDataFrame
        separator_index: セパレータ行のインデックス

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (上部のDataFrame, 下部のDataFrame)
    """
    upper_section = df.iloc[:separator_index]
    lower_section = df.iloc[separator_index + 1 :].reset_index(drop=True)
    return upper_section, lower_section
