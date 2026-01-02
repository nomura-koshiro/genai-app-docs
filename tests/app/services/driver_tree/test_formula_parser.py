"""数式パーサーのテスト。

このテストファイルは docs/specifications/08-testing/01-test-strategy.md に従い、
Happy Pathとビジネスルールエラーのみをテストします。
"""

import pytest

from app.core.exceptions import ValidationError
from app.services.driver_tree.formula_parser import FormulaParser, ParsedFormula


@pytest.mark.skip_db
class TestFormulaParser:
    """FormulaParserクラスのテスト。"""

    @pytest.mark.parametrize(
        "formula,expected_result_name,expected_expression,expected_operator,expected_operands",
        [
            ("売上高 = 総売上", "売上高", "総売上", None, ["総売上"]),
            ("売上高 = 単価 * 数量", "売上高", "単価 * 数量", "*", ["単価", "数量"]),
            ("総額 = 本体 + 税金", "総額", "本体 + 税金", "+", ["本体", "税金"]),
            ("利益 = 売上 - 原価", "利益", "売上 - 原価", "-", ["売上", "原価"]),
            ("平均 = 合計 / 件数", "平均", "合計 / 件数", "/", ["合計", "件数"]),
        ],
        ids=["assignment", "multiplication", "addition", "subtraction", "division"],
    )
    def test_parse_formula_operators(
        self,
        formula,
        expected_result_name,
        expected_expression,
        expected_operator,
        expected_operands,
    ):
        """[test_formula_parser-001-005] 各演算子の解析成功ケース。"""
        # Arrange
        parser = FormulaParser()

        # Act
        result = parser.parse(formula)

        # Assert
        assert result.result_name == expected_result_name
        assert result.expression == expected_expression
        assert result.operator == expected_operator
        assert result.operands == expected_operands

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

    @pytest.mark.parametrize(
        "formula,expected_error_message",
        [
            ("売上高 単価 * 数量", "数式のフォーマットが不正です"),
            ("売上高 = 単価 = 数量", "数式のフォーマットが不正です"),
            (" = 単価 * 数量", "結果変数名が空です"),
            ("売上高 = ", "式が空です"),
        ],
        ids=["no_equals", "multiple_equals", "empty_result", "empty_expression"],
    )
    def test_parse_formula_errors(self, formula, expected_error_message):
        """[test_formula_parser-007-010] 数式解析のエラーケース。"""
        # Arrange
        parser = FormulaParser()

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            parser.parse(formula)

        assert expected_error_message in str(exc_info.value)

    @pytest.mark.parametrize(
        "node_name,expected_type",
        [
            ("100", "定数"),
            ("3.14", "定数"),
            ("-50", "定数"),
        ],
        ids=["integer", "float", "negative"],
    )
    def test_determine_node_type_constant(self, node_name, expected_type):
        """[test_formula_parser-011] 定数ノードタイプ判定。"""
        # Arrange
        parser = FormulaParser()

        # Act & Assert
        assert parser.determine_node_type(node_name) == expected_type

    @pytest.mark.parametrize(
        "node_name,expected_type",
        [
            ("売上", "入力"),
            ("単価", "入力"),
            ("Sales", "入力"),
        ],
        ids=["japanese_kanji", "japanese_kanji_2", "english"],
    )
    def test_determine_node_type_input(self, node_name, expected_type):
        """[test_formula_parser-012] 入力ノードタイプ判定。"""
        # Arrange
        parser = FormulaParser()

        # Act & Assert
        assert parser.determine_node_type(node_name) == expected_type


@pytest.mark.skip_db
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
