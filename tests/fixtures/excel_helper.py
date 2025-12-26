"""テスト用Excelファイルヘルパー。

このモジュールは、テスト用のExcelファイルを生成するヘルパー関数を提供します。
parse_hierarchical_excelが期待する形式に合わせてExcelファイルを生成します。

期待される形式:
    - ヘッダー部分（複数行可能）
    - 空白行（ヘッダーとデータの区切り）
    - データ部分
"""

from io import BytesIO

import pandas as pd

# デフォルトのテストシートデータ
DEFAULT_SINGLE_SHEET_DATA = [
    ["年度", "2023", "2023", "2024", "2024"],  # ヘッダー行1
    ["部門", "営業", "開発", "営業", "開発"],  # ヘッダー行2
    [None, None, None, None, None],  # 空白行（区切り）
    ["売上", 1000, 500, 1200, 600],  # データ行1
    ["コスト", 800, 400, 900, 450],  # データ行2
]

DEFAULT_MULTI_SHEET_DATA = {
    "Sheet1": [
        ["年度", "2023", "2023"],
        ["部門", "営業", "開発"],
        [None, None, None],
        ["売上", 1000, 500],
    ],
    "Sheet2": [
        ["年度", "2024", "2024"],
        ["部門", "営業", "開発"],
        [None, None, None],
        ["売上", 1200, 600],
    ],
}

# 無効なフォーマットのテストデータ（セパレータ行なし）
INVALID_FORMAT_DATA = [
    ["不正なデータ", 1, 2, 3],
    ["もう一行", 4, 5, 6],
]


def create_test_excel_bytes(
    sheet_name: str = "Sheet1",
) -> bytes:
    """テスト用のExcelファイルをバイト形式で生成します。

    parse_hierarchical_excelが期待する形式:
    - ヘッダー行（軸名と値）
    - 空白行（区切り）
    - データ行（科目と値）

    Args:
        sheet_name: シート名

    Returns:
        bytes: Excelファイルのバイトデータ
    """
    excel_data = pd.DataFrame(DEFAULT_SINGLE_SHEET_DATA)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        excel_data.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

    buffer.seek(0)
    return buffer.getvalue()


def create_multi_sheet_excel_bytes(
    sheets: dict[str, list[list]] | None = None,
) -> bytes:
    """複数シートを持つテスト用Excelファイルを生成します。

    Args:
        sheets: シート名とデータの辞書。Noneの場合はデフォルトデータを使用

    Returns:
        bytes: Excelファイルのバイトデータ
    """
    sheet_data = sheets if sheets is not None else DEFAULT_MULTI_SHEET_DATA

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, data in sheet_data.items():
            excel_data = pd.DataFrame(data)
            excel_data.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

    buffer.seek(0)
    return buffer.getvalue()


def create_invalid_format_excel_bytes() -> bytes:
    """有効なフォーマットを持たないExcelファイルを生成します。

    parse_hierarchical_excelが処理できない形式のデータを含むExcelファイルを生成します。
    （空白行の区切りがない、ヘッダーがない等）

    Returns:
        bytes: Excelファイルのバイトデータ
    """
    excel_data = pd.DataFrame(INVALID_FORMAT_DATA)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        excel_data.to_excel(writer, sheet_name="InvalidSheet", index=False, header=False)

    buffer.seek(0)
    return buffer.getvalue()
