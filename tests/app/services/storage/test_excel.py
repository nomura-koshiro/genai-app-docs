"""Excel操作ユーティリティのテスト。

excel.pyの各関数を検証するテストです。
"""

import tempfile
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from app.core.exceptions import ValidationError
from app.services.storage.excel import (
    find_separator_row,
    get_excel_sheet_names,
    read_excel_sheet,
    split_by_separator,
)


class TestGetExcelSheetNames:
    """get_excel_sheet_names関数のテスト。"""

    def test_get_sheet_names_from_file_path(self):
        """[test_excel-001] ファイルパスからシート名一覧を取得できることを確認。"""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # DataFrameを作成して複数シートで保存
            df = pd.DataFrame({"A": [1, 2, 3]})
            with pd.ExcelWriter(tmp_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Sheet1", index=False)
                df.to_excel(writer, sheet_name="Sheet2", index=False)
                df.to_excel(writer, sheet_name="Sheet3", index=False)

            # Act
            result = get_excel_sheet_names(tmp_path)

            # Assert
            assert result == ["Sheet1", "Sheet2", "Sheet3"]

            # Cleanup
            tmp_path.unlink()

    def test_get_sheet_names_from_string_path(self):
        """[test_excel-002] 文字列パスからシート名一覧を取得できることを確認。"""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name
            df = pd.DataFrame({"A": [1, 2, 3]})
            with pd.ExcelWriter(tmp_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="TestSheet", index=False)

            # Act
            result = get_excel_sheet_names(tmp_path)

            # Assert
            assert "TestSheet" in result

            # Cleanup
            Path(tmp_path).unlink()

    def test_get_sheet_names_from_bytes_io(self):
        """[test_excel-003] BytesIOからシート名一覧を取得できることを確認。"""
        # Arrange
        buffer = BytesIO()
        df = pd.DataFrame({"A": [1, 2, 3]})
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="BytesSheet", index=False)
        buffer.seek(0)

        # Act
        result = get_excel_sheet_names(buffer)

        # Assert
        assert "BytesSheet" in result

    def test_get_sheet_names_raises_validation_error_for_invalid_file(self):
        """[test_excel-004] 不正なファイルでValidationErrorが発生することを確認。"""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"This is not an Excel file")

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                get_excel_sheet_names(tmp_path)

            assert "シート一覧取得に失敗" in str(exc_info.value.message)

            # Cleanup
            tmp_path.unlink()

    def test_get_sheet_names_raises_validation_error_for_nonexistent_file(self):
        """[test_excel-005] 存在しないファイルでValidationErrorが発生することを確認。"""
        # Arrange
        nonexistent_path = Path("/nonexistent/path/file.xlsx")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            get_excel_sheet_names(nonexistent_path)

        assert "シート一覧取得に失敗" in str(exc_info.value.message)


class TestReadExcelSheet:
    """read_excel_sheet関数のテスト。"""

    def test_read_excel_sheet_success(self):
        """[test_excel-006] Excelシートの読み込みが成功することを確認。"""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            df.to_excel(tmp_path, sheet_name="DataSheet", index=False)

            # Act
            result = read_excel_sheet(tmp_path, "DataSheet")

            # Assert
            assert isinstance(result, pd.DataFrame)
            # ヘッダーなしで読むので、最初の行がデータとして含まれる
            assert len(result) == 4  # ヘッダー行 + 3データ行

            # Cleanup
            tmp_path.unlink()

    def test_read_excel_sheet_without_header(self):
        """[test_excel-007] ヘッダーなしで読み込まれることを確認。"""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            df = pd.DataFrame({"Col1": ["a", "b"], "Col2": ["c", "d"]})
            df.to_excel(tmp_path, sheet_name="TestSheet", index=False)

            # Act
            result = read_excel_sheet(tmp_path, "TestSheet")

            # Assert
            # ヘッダー（Col1, Col2）がデータ行として含まれる
            assert result.iloc[0, 0] == "Col1"
            assert result.iloc[0, 1] == "Col2"

            # Cleanup
            tmp_path.unlink()

    def test_read_excel_sheet_from_bytes_io(self):
        """[test_excel-008] BytesIOからシートを読み込めることを確認。"""
        # Arrange
        buffer = BytesIO()
        df = pd.DataFrame({"A": [1, 2, 3]})
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="BytesSheet", index=False)
        buffer.seek(0)

        # Act
        result = read_excel_sheet(buffer, "BytesSheet")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4  # ヘッダー行 + 3データ行

    def test_read_excel_sheet_raises_validation_error_for_invalid_sheet(self):
        """[test_excel-009] 存在しないシートでValidationErrorが発生することを確認。"""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            df = pd.DataFrame({"A": [1, 2, 3]})
            df.to_excel(tmp_path, sheet_name="ExistingSheet", index=False)

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                read_excel_sheet(tmp_path, "NonexistentSheet")

            assert "シートの読み込みに失敗" in str(exc_info.value.message)

            # Cleanup
            tmp_path.unlink()

    def test_read_excel_sheet_raises_validation_error_for_invalid_file(self):
        """[test_excel-010] 不正なファイルでValidationErrorが発生することを確認。"""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"Not an Excel file")

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                read_excel_sheet(tmp_path, "AnySheet")

            assert "シートの読み込みに失敗" in str(exc_info.value.message)

            # Cleanup
            tmp_path.unlink()


class TestFindSeparatorRow:
    """find_separator_row関数のテスト。"""

    def test_find_separator_row_returns_correct_index(self):
        """[test_excel-011] 空行のインデックスが正しく返されることを確認。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: ["Header1", "Header2", None, "Data1", "Data2"],
                1: ["Value1", "Value2", None, "Data3", "Data4"],
            }
        )

        # Act
        result = find_separator_row(df)

        # Assert
        assert result == 2

    def test_find_separator_row_first_row_is_empty(self):
        """[test_excel-012] 最初の行が空行の場合0が返されることを確認。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: [None, "Data1", "Data2"],
                1: [None, "Data3", "Data4"],
            }
        )

        # Act
        result = find_separator_row(df)

        # Assert
        assert result == 0

    def test_find_separator_row_last_row_is_empty(self):
        """[test_excel-013] 最後の行が空行の場合でも検出されることを確認。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: ["Data1", "Data2", None],
                1: ["Data3", "Data4", None],
            }
        )

        # Act
        result = find_separator_row(df)

        # Assert
        assert result == 2

    def test_find_separator_row_raises_validation_error_when_no_empty_row(self):
        """[test_excel-014] 空行がない場合ValidationErrorが発生することを確認。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: ["Data1", "Data2", "Data3"],
                1: ["Data4", "Data5", "Data6"],
            }
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            find_separator_row(df)

        assert "空行の区切りが見つかりません" in str(exc_info.value.message)

    def test_find_separator_row_finds_first_empty_row(self):
        """[test_excel-015] 複数の空行がある場合、最初の空行が返されることを確認。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: ["Header", None, "Data1", None, "Data2"],
                1: ["Value", None, "Data3", None, "Data4"],
            }
        )

        # Act
        result = find_separator_row(df)

        # Assert
        assert result == 1


class TestSplitBySeparator:
    """split_by_separator関数のテスト。"""

    def test_split_by_separator_returns_two_dataframes(self):
        """[test_excel-016] 2つのDataFrameが返されることを確認。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: ["Header1", "Header2", None, "Data1", "Data2"],
                1: ["Value1", "Value2", None, "Data3", "Data4"],
            }
        )
        separator_index = 2

        # Act
        upper, lower = split_by_separator(df, separator_index)

        # Assert
        assert isinstance(upper, pd.DataFrame)
        assert isinstance(lower, pd.DataFrame)

    def test_split_by_separator_upper_section_correct(self):
        """[test_excel-017] 上部セクションが正しいことを確認。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: ["Header1", "Header2", None, "Data1", "Data2"],
                1: ["Value1", "Value2", None, "Data3", "Data4"],
            }
        )
        separator_index = 2

        # Act
        upper, _ = split_by_separator(df, separator_index)

        # Assert
        assert len(upper) == 2
        assert upper.iloc[0, 0] == "Header1"
        assert upper.iloc[1, 0] == "Header2"

    def test_split_by_separator_lower_section_correct(self):
        """[test_excel-018] 下部セクションが正しいことを確認。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: ["Header1", "Header2", None, "Data1", "Data2"],
                1: ["Value1", "Value2", None, "Data3", "Data4"],
            }
        )
        separator_index = 2

        # Act
        _, lower = split_by_separator(df, separator_index)

        # Assert
        assert len(lower) == 2
        assert lower.iloc[0, 0] == "Data1"
        assert lower.iloc[1, 0] == "Data2"

    def test_split_by_separator_lower_section_has_reset_index(self):
        """[test_excel-019] 下部セクションのインデックスがリセットされていることを確認。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: ["Header", None, "Data1", "Data2", "Data3"],
            }
        )
        separator_index = 1

        # Act
        _, lower = split_by_separator(df, separator_index)

        # Assert
        assert list(lower.index) == [0, 1, 2]

    def test_split_by_separator_at_beginning(self):
        """[test_excel-020] 最初の行がセパレータの場合のテスト。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: [None, "Data1", "Data2"],
                1: [None, "Data3", "Data4"],
            }
        )
        separator_index = 0

        # Act
        upper, lower = split_by_separator(df, separator_index)

        # Assert
        assert len(upper) == 0
        assert len(lower) == 2

    def test_split_by_separator_at_end(self):
        """[test_excel-021] 最後の行がセパレータの場合のテスト。"""
        # Arrange
        df = pd.DataFrame(
            {
                0: ["Data1", "Data2", None],
                1: ["Data3", "Data4", None],
            }
        )
        separator_index = 2

        # Act
        upper, lower = split_by_separator(df, separator_index)

        # Assert
        assert len(upper) == 2
        assert len(lower) == 0
