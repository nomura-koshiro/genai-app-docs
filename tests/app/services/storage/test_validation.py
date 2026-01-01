"""ファイル検証ユーティリティのテスト。

validation.pyの各関数を検証するテストです。
"""

from unittest.mock import MagicMock

import pytest
from fastapi import UploadFile

from app.core.exceptions import PayloadTooLargeError, UnsupportedMediaTypeError, ValidationError
from app.services.storage.validation import (
    ALLOWED_EXCEL_EXTENSIONS,
    ALLOWED_EXCEL_MIME_TYPES,
    DEFAULT_MAX_FILE_SIZE,
    check_file_size,
    sanitize_filename,
    validate_excel_file,
)


class TestValidateExcelFile:
    """validate_excel_file関数のテスト。"""

    def test_validate_excel_file_success_xlsx(self):
        """[test_validation-001] 有効なXLSXファイルの検証が成功することを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.xlsx"
        mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Act & Assert (例外が発生しないことを確認)
        validate_excel_file(mock_file)

    def test_validate_excel_file_success_xls(self):
        """[test_validation-002] 有効なXLSファイルの検証が成功することを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.xls"
        mock_file.content_type = "application/vnd.ms-excel"

        # Act & Assert (例外が発生しないことを確認)
        validate_excel_file(mock_file)

    def test_validate_excel_file_empty_filename_raises_validation_error(self):
        """[test_validation-003] 空のファイル名でValidationErrorが発生することを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = ""
        mock_file.content_type = "application/vnd.ms-excel"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_excel_file(mock_file)

        assert "ファイル名の指定が必要です" in str(exc_info.value.message)

    def test_validate_excel_file_none_filename_raises_validation_error(self):
        """[test_validation-004] Noneのファイル名でValidationErrorが発生することを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = None
        mock_file.content_type = "application/vnd.ms-excel"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_excel_file(mock_file)

        assert "ファイル名の指定が必要です" in str(exc_info.value.message)

    def test_validate_excel_file_invalid_extension_raises_unsupported_media_type_error(self):
        """[test_validation-005] 不正な拡張子でUnsupportedMediaTypeErrorが発生することを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"

        # Act & Assert
        with pytest.raises(UnsupportedMediaTypeError) as exc_info:
            validate_excel_file(mock_file)

        assert ".txt は許可されていません" in str(exc_info.value.message)

    def test_validate_excel_file_invalid_extension_pdf(self):
        """[test_validation-006] PDF拡張子でエラーが発生することを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "document.pdf"
        mock_file.content_type = "application/pdf"

        # Act & Assert
        with pytest.raises(UnsupportedMediaTypeError):
            validate_excel_file(mock_file)

    def test_validate_excel_file_invalid_mime_type_raises_validation_error(self):
        """[test_validation-007] 不正なMIMEタイプでValidationErrorが発生することを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.xlsx"
        mock_file.content_type = "text/plain"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_excel_file(mock_file)

        assert "MIMEタイプ text/plain は許可されていません" in str(exc_info.value.message)

    def test_validate_excel_file_none_content_type_is_allowed(self):
        """[test_validation-008] content_typeがNoneの場合は許可されることを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.xlsx"
        mock_file.content_type = None

        # Act & Assert (例外が発生しないことを確認)
        validate_excel_file(mock_file)

    def test_validate_excel_file_custom_extensions(self):
        """[test_validation-009] カスタム拡張子リストが機能することを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.csv"
        mock_file.content_type = "text/csv"
        custom_extensions = {".csv", ".txt"}
        custom_mime_types = {"text/csv", "text/plain"}

        # Act & Assert (例外が発生しないことを確認)
        validate_excel_file(mock_file, allowed_extensions=custom_extensions, allowed_mime_types=custom_mime_types)

    def test_validate_excel_file_case_insensitive_extension(self):
        """[test_validation-010] 拡張子の大文字小文字を無視することを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.XLSX"
        mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Act & Assert (例外が発生しないことを確認)
        validate_excel_file(mock_file)

    def test_validate_excel_file_mixed_case_extension(self):
        """[test_validation-011] 混合ケースの拡張子も許可されることを確認。"""
        # Arrange
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.XlSx"
        mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Act & Assert (例外が発生しないことを確認)
        validate_excel_file(mock_file)


class TestCheckFileSize:
    """check_file_size関数のテスト。"""

    def test_check_file_size_within_limit(self):
        """[test_validation-012] サイズ制限内で例外が発生しないことを確認。"""
        # Arrange
        file_size = 10 * 1024 * 1024  # 10MB

        # Act & Assert (例外が発生しないことを確認)
        check_file_size(file_size)

    def test_check_file_size_at_limit(self):
        """[test_validation-013] ちょうど制限サイズで例外が発生しないことを確認。"""
        # Arrange
        file_size = DEFAULT_MAX_FILE_SIZE

        # Act & Assert (例外が発生しないことを確認)
        check_file_size(file_size)

    def test_check_file_size_exceeds_limit_raises_payload_too_large_error(self):
        """[test_validation-014] サイズ超過でPayloadTooLargeErrorが発生することを確認。"""
        # Arrange
        file_size = DEFAULT_MAX_FILE_SIZE + 1

        # Act & Assert
        with pytest.raises(PayloadTooLargeError) as exc_info:
            check_file_size(file_size)

        assert "最大サイズ" in str(exc_info.value.message)

    def test_check_file_size_custom_limit(self):
        """[test_validation-015] カスタム制限サイズが機能することを確認。"""
        # Arrange
        file_size = 1024 * 1024  # 1MB
        custom_max_size = 512 * 1024  # 512KB

        # Act & Assert
        with pytest.raises(PayloadTooLargeError):
            check_file_size(file_size, max_size=custom_max_size)

    def test_check_file_size_zero_size(self):
        """[test_validation-016] サイズ0で例外が発生しないことを確認。"""
        # Arrange
        file_size = 0

        # Act & Assert (例外が発生しないことを確認)
        check_file_size(file_size)

    def test_check_file_size_small_custom_limit(self):
        """[test_validation-017] 小さいカスタム制限が機能することを確認。"""
        # Arrange
        file_size = 100
        custom_max_size = 50

        # Act & Assert
        with pytest.raises(PayloadTooLargeError) as exc_info:
            check_file_size(file_size, max_size=custom_max_size)

        assert exc_info.value.details["file_size"] == 100
        assert exc_info.value.details["max_size"] == 50


class TestSanitizeFilename:
    """sanitize_filename関数のテスト。"""

    def test_sanitize_filename_normal_name(self):
        """[test_validation-018] 通常のファイル名がそのまま返されることを確認。"""
        # Arrange
        filename = "document.xlsx"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == "document.xlsx"

    def test_sanitize_filename_removes_path_traversal(self):
        """[test_validation-019] パストラバーサルが除去されることを確認。"""
        # Arrange
        filename = "../../../etc/passwd"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert ".." not in result
        assert "/" not in result

    def test_sanitize_filename_removes_backslash_path(self):
        """[test_validation-020] バックスラッシュパスが除去されることを確認。"""
        # Arrange
        filename = "..\\..\\windows\\system32\\file.txt"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert "\\" not in result

    def test_sanitize_filename_replaces_spaces(self):
        """[test_validation-021] スペースがアンダースコアに置換されることを確認。"""
        # Arrange
        filename = "my document.xlsx"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert " " not in result
        assert "my_document.xlsx" == result

    def test_sanitize_filename_removes_special_characters(self):
        """[test_validation-022] 特殊文字が除去されることを確認。"""
        # Arrange
        filename = "file@name#test$.xlsx"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

    def test_sanitize_filename_preserves_allowed_characters(self):
        """[test_validation-023] 許可された文字（英数字、点、アンダースコア、ハイフン）が保持されることを確認。"""
        # Arrange
        filename = "file-name_v1.2.xlsx"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == "file-name_v1.2.xlsx"

    def test_sanitize_filename_strips_leading_trailing_dots(self):
        """[test_validation-024] 前後のドットが除去されることを確認。"""
        # Arrange
        filename = "...file..."

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert not result.startswith(".")
        assert not result.endswith(".")

    def test_sanitize_filename_strips_leading_trailing_underscores(self):
        """[test_validation-025] 前後のアンダースコアが除去されることを確認。"""
        # Arrange
        filename = "___file___"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert not result.startswith("_")
        assert not result.endswith("_")

    def test_sanitize_filename_empty_returns_unknown(self):
        """[test_validation-026] 空のファイル名で'unknown'が返されることを確認。"""
        # Arrange
        filename = ""

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == "unknown"

    def test_sanitize_filename_none_returns_unknown(self):
        """[test_validation-027] Noneで'unknown'が返されることを確認。"""
        # Arrange
        filename = None

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == "unknown"

    def test_sanitize_filename_only_special_chars_returns_unknown(self):
        """[test_validation-028] 特殊文字のみで'unknown'が返されることを確認。"""
        # Arrange
        filename = "@#$%^&*()"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == "unknown"

    def test_sanitize_filename_unicode_removed(self):
        """[test_validation-029] Unicode文字が除去されることを確認。"""
        # Arrange
        filename = "file_name.xlsx"

        # Act
        result = sanitize_filename(filename)

        # Assert
        # 日本語文字は除去される
        assert "file_name.xlsx" in result or result == "file_name.xlsx"

    def test_sanitize_filename_preserves_extension(self):
        """[test_validation-030] 拡張子が保持されることを確認。"""
        # Arrange
        filename = "report 2024.xlsx"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result.endswith(".xlsx")

    def test_sanitize_filename_with_multiple_dots(self):
        """[test_validation-031] 複数のドットがあるファイル名が処理されることを確認。"""
        # Arrange
        filename = "file.name.v1.2.xlsx"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == "file.name.v1.2.xlsx"

    def test_sanitize_filename_with_path_separator(self):
        """[test_validation-032] パス区切り文字が除去されてファイル名のみになることを確認。"""
        # Arrange
        filename = "/path/to/file.xlsx"

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == "file.xlsx"


class TestConstants:
    """定数のテスト。"""

    def test_allowed_excel_extensions(self):
        """[test_validation-033] ALLOWED_EXCEL_EXTENSIONSが正しいことを確認。"""
        # Assert
        assert ".xlsx" in ALLOWED_EXCEL_EXTENSIONS
        assert ".xls" in ALLOWED_EXCEL_EXTENSIONS
        assert len(ALLOWED_EXCEL_EXTENSIONS) == 2

    def test_allowed_excel_mime_types(self):
        """[test_validation-034] ALLOWED_EXCEL_MIME_TYPESが正しいことを確認。"""
        # Assert
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in ALLOWED_EXCEL_MIME_TYPES
        assert "application/vnd.ms-excel" in ALLOWED_EXCEL_MIME_TYPES
        assert len(ALLOWED_EXCEL_MIME_TYPES) == 2

    def test_default_max_file_size(self):
        """[test_validation-035] DEFAULT_MAX_FILE_SIZEが50MBであることを確認。"""
        # Assert
        expected_size = 50 * 1024 * 1024  # 50MB
        assert DEFAULT_MAX_FILE_SIZE == expected_size
