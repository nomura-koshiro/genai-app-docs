"""Excel解析ユーティリティのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。
"""

import pandas as pd
import pytest

from app.services.analysis.analysis_session.excel_parser import (
    _build_axis_info,
    _create_record,
    _create_unique_key,
    _extract_column_header_mappings,
    _extract_item_names,
    _validate_uniqueness,
    parse_hierarchical_excel,
)


class TestParseHierarchicalExcel:
    """parse_hierarchical_excel関数のテスト。"""

    def test_parse_simple_excel_success(self):
        """[test_excel_parser-001] シンプルなExcelデータの解析成功ケース。"""
        # Arrange - シンプルな階層ヘッダー形式のデータ
        data = {
            0: ["年度", "部門", None, "売上", "費用"],
            1: ["2023", "営業", None, 1000, 500],
            2: ["2023", "開発", None, 800, 400],
        }
        raw_df = pd.DataFrame(data).T

        # Act
        axis_info, values_df, header_section, data_section = parse_hierarchical_excel(raw_df)

        # Assert
        assert len(axis_info) >= 1
        assert values_df is not None
        assert header_section is not None
        assert data_section is not None


class TestExtractColumnHeaderMappings:
    """_extract_column_header_mappings関数のテスト。"""

    def test_extract_mappings_success(self):
        """[test_excel_parser-002] ヘッダーマッピング抽出の成功ケース。"""
        # Arrange
        header_section = pd.DataFrame({0: ["年度", "部門"], 1: ["2023", "営業"], 2: ["2023", "開発"]}).T
        data_section = pd.DataFrame({0: [None, "売上", "費用"], 1: [None, 1000, 800], 2: [None, 500, 400]}).T

        # Act
        result = _extract_column_header_mappings(header_section, data_section)

        # Assert
        assert isinstance(result, list)


class TestBuildAxisInfo:
    """_build_axis_info関数のテスト。"""

    def test_build_axis_info_success(self):
        """[test_excel_parser-003] 軸情報構築の成功ケース。"""
        # Arrange
        column_mappings = [
            [("年度", "2023"), ("部門", "営業")],
            [("年度", "2023"), ("部門", "開発")],
        ]

        # Act
        axis_info, axis_order = _build_axis_info(column_mappings)

        # Assert
        assert len(axis_info) == 2
        assert axis_order == ["年度", "部門"]
        assert axis_info[0][0] == "年度"
        assert "2023" in axis_info[0][1]


class TestExtractItemNames:
    """_extract_item_names関数のテスト。"""

    def test_extract_item_names_success(self):
        """[test_excel_parser-004] 科目名抽出の成功ケース。"""
        # Arrange
        data_section = pd.DataFrame({0: ["売上", "費用", "利益"], 1: [1000, 500, 500]})

        # Act
        result = _extract_item_names(data_section)

        # Assert
        assert "売上" in result
        assert "費用" in result
        assert "利益" in result


class TestCreateRecord:
    """_create_record関数のテスト。"""

    def test_create_record_success(self):
        """[test_excel_parser-005] レコード作成の成功ケース。"""
        # Arrange
        column_mapping = [("年度", "2023"), ("部門", "営業")]
        axis_order = ["年度", "部門"]
        item_name = "売上"
        cell_value = 1000.0

        # Act
        result = _create_record(column_mapping, axis_order, item_name, cell_value)

        # Assert
        assert result["年度"] == "2023"
        assert result["部門"] == "営業"
        assert result["科目"] == "売上"
        assert result["値"] == 1000.0


class TestCreateUniqueKey:
    """_create_unique_key関数のテスト。"""

    def test_create_unique_key_success(self):
        """[test_excel_parser-006] 一意キー作成の成功ケース。"""
        # Arrange
        record = {"年度": "2023", "部門": "営業", "科目": "売上", "値": 1000}
        axis_order = ["年度", "部門"]
        item_name = "売上"

        # Act
        result = _create_unique_key(record, axis_order, item_name)

        # Assert
        assert result == ("2023", "営業", "売上")


class TestValidateUniqueness:
    """_validate_uniqueness関数のテスト。"""

    def test_validate_uniqueness_success(self):
        """[test_excel_parser-007] 一意性検証成功ケース（重複なし）。"""
        # Arrange
        unique_key = ("2023", "営業", "売上")
        existing_keys: set = set()
        axis_order = ["年度", "部門"]
        item_name = "売上"

        # Act & Assert - 例外が発生しないこと
        _validate_uniqueness(unique_key, existing_keys, axis_order, item_name)

    def test_validate_uniqueness_duplicate_error(self):
        """[test_excel_parser-008] 一意性検証失敗ケース（重複あり）。"""
        # Arrange
        unique_key = ("2023", "営業", "売上")
        existing_keys = {unique_key}
        axis_order = ["年度", "部門"]
        item_name = "売上"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            _validate_uniqueness(unique_key, existing_keys, axis_order, item_name)

        assert "重複した組み合わせ" in str(exc_info.value)
