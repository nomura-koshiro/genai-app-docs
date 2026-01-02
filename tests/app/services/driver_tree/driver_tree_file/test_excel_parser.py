"""Excel解析ユーティリティのテスト。

このテストファイルは、parse_driver_tree_excel関数をテストします。

対応関数:
    - parse_driver_tree_excel: Excelファイル解析
"""

from io import BytesIO

import pandas as pd
import pytest

from app.core.exceptions import ValidationError
from app.services.driver_tree.driver_tree_file.excel_parser import parse_driver_tree_excel
from tests.fixtures.excel_helper import (
    create_invalid_format_excel_bytes,
    create_multi_sheet_excel_bytes,
    create_test_excel_bytes,
)

# ================================================================================
# parse_driver_tree_excel テスト
# ================================================================================


class TestParseDriverTreeExcel:
    """parse_driver_tree_excel関数のテスト。"""

    def test_parse_success(self):
        """[test_excel_parser-001] 正常なExcelファイルの解析成功。"""
        # Arrange
        excel_bytes = create_test_excel_bytes()

        # Act
        df_metadata, df_data = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet1")

        # Assert
        assert isinstance(df_metadata, pd.DataFrame)
        assert isinstance(df_data, pd.DataFrame)

    def test_parse_columns(self):
        """[test_excel_parser-002] メタデータとデータカラムの検証。"""
        # Arrange
        excel_bytes = create_test_excel_bytes()

        # Act
        df_metadata, df_data = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet1")

        # Assert: メタデータには年度・部門が含まれる
        assert "年度" in df_metadata.columns
        assert "部門" in df_metadata.columns

        # Assert: データには売上・コストが含まれる
        assert "売上" in df_data.columns
        assert "コスト" in df_data.columns

    def test_parse_transposed_correctly(self):
        """[test_excel_parser-004] 転置が正しく行われる。"""
        # Arrange
        excel_bytes = create_test_excel_bytes()

        # Act
        df_metadata, df_data = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet1")

        # Assert: 元データは5列（ラベル列+4データ列）なので、転置後は4行
        assert len(df_metadata) == 4
        assert len(df_data) == 4

    def test_parse_multi_sheet_excel(self):
        """[test_excel_parser-005] 複数シートExcelの解析。"""
        # Arrange
        excel_bytes = create_multi_sheet_excel_bytes()

        # Act
        df_metadata1, df_data1 = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet1")
        df_metadata2, df_data2 = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet2")

        # Assert
        assert isinstance(df_metadata1, pd.DataFrame)
        assert isinstance(df_metadata2, pd.DataFrame)
        # 各シートのデータ内容が異なる
        assert not df_metadata1.equals(df_metadata2)

    def test_parse_invalid_format_raises_error(self):
        """[test_excel_parser-006] 無効なフォーマットでValidationError。"""
        # Arrange: セパレータ行がないExcel
        excel_bytes = create_invalid_format_excel_bytes()

        # Act & Assert
        with pytest.raises(ValidationError):
            parse_driver_tree_excel(BytesIO(excel_bytes), "InvalidSheet")

    def test_parse_nonexistent_sheet_raises_error(self):
        """[test_excel_parser-007] 存在しないシートでValidationError。"""
        # Arrange
        excel_bytes = create_test_excel_bytes()

        # Act & Assert
        with pytest.raises(ValidationError):
            parse_driver_tree_excel(BytesIO(excel_bytes), "NonExistentSheet")

    @pytest.mark.parametrize(
        "path_type",
        ["string", "path_object"],
        ids=["string", "path_object"],
    )
    def test_parse_with_path_types(self, tmp_path, path_type: str):
        """[test_excel_parser-008] パス文字列/Pathオブジェクトでの解析。"""
        # Arrange
        excel_bytes = create_test_excel_bytes()
        file_path = tmp_path / "test.xlsx"
        file_path.write_bytes(excel_bytes)

        # Act
        if path_type == "string":
            df_metadata, df_data = parse_driver_tree_excel(str(file_path), "Sheet1")
        else:  # path_object
            df_metadata, df_data = parse_driver_tree_excel(file_path, "Sheet1")

        # Assert
        assert isinstance(df_metadata, pd.DataFrame)
        assert isinstance(df_data, pd.DataFrame)

    def test_parse_metadata_values(self):
        """[test_excel_parser-010] メタデータ値の検証。"""
        # Arrange
        excel_bytes = create_test_excel_bytes()

        # Act
        df_metadata, _ = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet1")

        # Assert: 年度カラムには2023, 2024が含まれる
        year_values = df_metadata["年度"].unique().tolist()
        assert "2023" in year_values or 2023 in year_values
        assert "2024" in year_values or 2024 in year_values

    def test_parse_data_values(self):
        """[test_excel_parser-011] データ値の検証。"""
        # Arrange
        excel_bytes = create_test_excel_bytes()

        # Act
        _, df_data = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet1")

        # Assert: 売上カラムには数値が含まれる
        sales_values = df_data["売上"].tolist()
        assert len(sales_values) > 0
        # 数値型であること
        assert all(isinstance(v, int | float) for v in sales_values)

    def test_parse_preserves_column_order(self):
        """[test_excel_parser-012] カラム順序が保持される。"""
        # Arrange
        excel_bytes = create_test_excel_bytes()

        # Act
        df_metadata, _ = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet1")

        # Assert: カラム順序が元のExcelと一致
        columns = list(df_metadata.columns)
        assert columns.index("年度") < columns.index("部門")

    def test_parse_handles_empty_cells(self):
        """[test_excel_parser-013] 空セルの処理。"""
        # Arrange: 空セルを含むExcelデータ
        data = {
            "Sheet1": [
                ["年度", "2023", None, "2024"],
                ["部門", "営業", "開発", None],
                [None, None, None, None],
                ["売上", 1000, 500, None],
            ]
        }
        excel_bytes = create_multi_sheet_excel_bytes(data)

        # Act
        df_metadata, df_data = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet1")

        # Assert: 解析が成功すること
        assert isinstance(df_metadata, pd.DataFrame)
        assert isinstance(df_data, pd.DataFrame)

    def test_parse_resets_index(self):
        """[test_excel_parser-014] インデックスがリセットされる。"""
        # Arrange
        excel_bytes = create_test_excel_bytes()

        # Act
        df_metadata, df_data = parse_driver_tree_excel(BytesIO(excel_bytes), "Sheet1")

        # Assert: インデックスが0から始まる
        assert df_metadata.index[0] == 0
        assert df_data.index[0] == 0
