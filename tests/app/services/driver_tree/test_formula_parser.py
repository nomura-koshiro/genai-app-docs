"""数式パーサーのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。
"""

import pytest

from app.core.exceptions import ValidationError
from app.services.driver_tree.formula_parser import FormulaParser, ParsedFormula


class TestFormulaParser:
    """FormulaParserクラスのテスト。"""

    def test_parse_simple_assignment(self):
        """[test_formula_parser-001] 単純代入の解析成功ケース。"""
        # Arrange
        parser = FormulaParser()
        formula = "売上高 = 総売上"

        # Act
        result = parser.parse(formula)

        # Assert
        assert result.result_name == "売上高"
        assert result.expression == "総売上"
        assert result.operator is None
        assert result.operands == ["総売上"]

    def test_parse_multiplication(self):
        """[test_formula_parser-002] 乗算の解析成功ケース。"""
        # Arrange
        parser = FormulaParser()
        formula = "売上高 = 単価 * 数量"

        # Act
        result = parser.parse(formula)

        # Assert
        assert result.result_name == "売上高"
        assert result.expression == "単価 * 数量"
        assert result.operator == "*"
        assert result.operands == ["単価", "数量"]

    def test_parse_addition(self):
        """[test_formula_parser-003] 加算の解析成功ケース。"""
        # Arrange
        parser = FormulaParser()
        formula = "総額 = 本体 + 税金"

        # Act
        result = parser.parse(formula)

        # Assert
        assert result.result_name == "総額"
        assert result.expression == "本体 + 税金"
        assert result.operator == "+"
        assert result.operands == ["本体", "税金"]

    def test_parse_subtraction(self):
        """[test_formula_parser-004] 減算の解析成功ケース。"""
        # Arrange
        parser = FormulaParser()
        formula = "利益 = 売上 - 原価"

        # Act
        result = parser.parse(formula)

        # Assert
        assert result.result_name == "利益"
        assert result.expression == "売上 - 原価"
        assert result.operator == "-"
        assert result.operands == ["売上", "原価"]

    def test_parse_division(self):
        """[test_formula_parser-005] 除算の解析成功ケース。"""
        # Arrange
        parser = FormulaParser()
        formula = "平均 = 合計 / 件数"

        # Act
        result = parser.parse(formula)

        # Assert
        assert result.result_name == "平均"
        assert result.expression == "合計 / 件数"
        assert result.operator == "/"
        assert result.operands == ["合計", "件数"]

    def test_parse_multiple_operands(self):
        """[test_formula_parser-006] 複数オペランドの解析成功ケース。"""
        # Arrange
        parser = FormulaParser()
        formula = "利益 = 売上 - 原価 - 経費"

        # Act
        result = parser.parse(formula)

        # Assert
        assert result.result_name == "利益"
        assert result.operator == "-"
        assert result.operands == ["売上", "原価", "経費"]

    def test_parse_no_equals_error(self):
        """[test_formula_parser-007] 等号がない場合のエラー。"""
        # Arrange
        parser = FormulaParser()
        formula = "売上高 単価 * 数量"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            parser.parse(formula)

        assert "数式のフォーマットが不正です" in str(exc_info.value)

    def test_parse_multiple_equals_error(self):
        """[test_formula_parser-008] 複数の等号がある場合のエラー。"""
        # Arrange
        parser = FormulaParser()
        formula = "売上高 = 単価 = 数量"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            parser.parse(formula)

        assert "数式のフォーマットが不正です" in str(exc_info.value)

    def test_parse_empty_result_name_error(self):
        """[test_formula_parser-009] 結果変数名が空の場合のエラー。"""
        # Arrange
        parser = FormulaParser()
        formula = " = 単価 * 数量"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            parser.parse(formula)

        assert "結果変数名が空です" in str(exc_info.value)

    def test_parse_empty_expression_error(self):
        """[test_formula_parser-010] 式が空の場合のエラー。"""
        # Arrange
        parser = FormulaParser()
        formula = "売上高 = "

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            parser.parse(formula)

        assert "式が空です" in str(exc_info.value)

    def test_determine_node_type_constant(self):
        """[test_formula_parser-011] 定数ノードタイプ判定。"""
        # Arrange
        parser = FormulaParser()

        # Act & Assert
        assert parser.determine_node_type("100") == "定数"
        assert parser.determine_node_type("3.14") == "定数"
        assert parser.determine_node_type("-50") == "定数"

    def test_determine_node_type_input(self):
        """[test_formula_parser-012] 入力ノードタイプ判定。"""
        # Arrange
        parser = FormulaParser()

        # Act & Assert
        assert parser.determine_node_type("売上") == "入力"
        assert parser.determine_node_type("単価") == "入力"
        assert parser.determine_node_type("Sales") == "入力"


class TestParsedFormula:
    """ParsedFormulaデータクラスのテスト。"""

    def test_parsed_formula_equality(self):
        """[test_formula_parser-014] ParsedFormulaの等価性。"""
        # Arrange
        formula1 = ParsedFormula(
            result_name="売上",
            expression="単価 * 数量",
            operator="*",
            operands=["単価", "数量"],
        )
        formula2 = ParsedFormula(
            result_name="売上",
            expression="単価 * 数量",
            operator="*",
            operands=["単価", "数量"],
        )

        # Assert
        assert formula1 == formula2
