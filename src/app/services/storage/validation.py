"""ファイル検証ユーティリティ。

ファイルアップロード時の検証・サニタイズ機能を提供します。

主な機能:
    - Excelファイル検証（拡張子・MIMEタイプ）
    - ファイルサイズチェック
    - ファイル名サニタイズ
"""

import os
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import PayloadTooLargeError, UnsupportedMediaTypeError, ValidationError

# Excelファイルの許可される拡張子
ALLOWED_EXCEL_EXTENSIONS: set[str] = {".xlsx", ".xls"}

# Excelファイルの許可されるMIMEタイプ
ALLOWED_EXCEL_MIME_TYPES: set[str] = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}

# デフォルトの最大ファイルサイズ（50MB）
DEFAULT_MAX_FILE_SIZE: int = 50 * 1024 * 1024


def validate_excel_file(
    file: UploadFile,
    allowed_extensions: set[str] | None = None,
    allowed_mime_types: set[str] | None = None,
) -> None:
    """Excelファイルを検証します。

    ファイル名の存在、拡張子、MIMEタイプをチェックします。

    Args:
        file: アップロードファイル
        allowed_extensions: 許可する拡張子のセット（デフォルト: .xlsx, .xls）
        allowed_mime_types: 許可するMIMEタイプのセット（デフォルト: Excel用MIMEタイプ）

    Raises:
        ValidationError: ファイル名が空の場合
        UnsupportedMediaTypeError: 拡張子が許可されていない場合
        ValidationError: MIMEタイプが許可されていない場合
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXCEL_EXTENSIONS
    if allowed_mime_types is None:
        allowed_mime_types = ALLOWED_EXCEL_MIME_TYPES

    # ファイル名チェック
    if not file.filename:
        raise ValidationError("ファイル名の指定が必要です")

    # 拡張子チェック
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise UnsupportedMediaTypeError(
            f"拡張子 {file_ext} は許可されていません",
            details={"allowed": list(allowed_extensions)},
        )

    # MIMEタイプチェック
    if file.content_type and file.content_type not in allowed_mime_types:
        raise ValidationError(
            f"MIMEタイプ {file.content_type} は許可されていません",
            details={"allowed": list(allowed_mime_types)},
        )


def check_file_size(
    file_size: int,
    max_size: int = DEFAULT_MAX_FILE_SIZE,
) -> None:
    """ファイルサイズをチェックします。

    Args:
        file_size: ファイルサイズ（バイト）
        max_size: 最大許可サイズ（バイト）。デフォルト: 50MB

    Raises:
        PayloadTooLargeError: ファイルサイズが上限を超えている場合
    """
    if file_size > max_size:
        raise PayloadTooLargeError(
            f"ファイルサイズが許可されている最大サイズ（{max_size} バイト）を超えています",
            details={"file_size": file_size, "max_size": max_size},
        )


def sanitize_filename(filename: str | None) -> str:
    """ファイル名をサニタイズします（セキュリティ対策）。

    以下の処理を行います:
    1. パス区切り文字を削除（パス走査防止）
    2. スペースをアンダースコアに置換
    3. 許可された文字（英数字、点、アンダースコア、ハイフン）のみを保持
    4. 前後のドットやアンダースコアを除去

    Args:
        filename: 元のファイル名

    Returns:
        str: サニタイズされたファイル名。空になった場合は "unknown"
    """
    if not filename:
        return "unknown"

    # 1. パス区切り文字を削除（セキュリティ：パス走査防止）
    safe_name = os.path.basename(filename)

    # 2. スペースをアンダースコアに置換（互換性向上）
    safe_name = safe_name.replace(" ", "_")

    # 3. 許可された文字（英数字、点、アンダースコア、ハイフン）のみを保持
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")

    # 4. 前後のドットやアンダースコアを除去（見た目の改善）
    safe_name = safe_name.strip("._-")

    # 5. 空になった場合
    if not safe_name:
        return "unknown"

    return safe_name
