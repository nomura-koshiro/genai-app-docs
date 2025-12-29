"""数式パーサー。

このモジュールは、ドライバーツリー用の数式解析機能を提供します。
"""

from dataclasses import dataclass

from app.core.exceptions import ValidationError


@dataclass(frozen=True)
class ParsedFormula:
    """解析済み数式を表すデータクラス。

    Attributes:
        result_name: 結果変数名（等号の左辺）
        expression: 式（等号の右辺）
        operator: 演算子（+, -, *, / のいずれか、または None）
        operands: オペランドのリスト
    """

    result_name: str
    expression: str
    operator: str | None
    operands: list[str]


class FormulaParser:
    """数式パーサークラス。

    ドライバーツリー用の数式を解析し、構成要素に分解します。

    サポートする形式:
        - 単純代入: "売上高 = 総売上"
        - 二項演算: "売上高 = 単価 * 数量"
        - 多項演算: "利益 = 売上 - 原価 - 経費"
    """

    SUPPORTED_OPERATORS = ["+", "-", "*", "/"]

    def parse(self, formula: str) -> ParsedFormula:
        """数式を解析します。

        Args:
            formula: 数式文字列（例: "売上高 = 単価 * 数量"）

        Returns:
            ParsedFormula: 解析結果

        Raises:
            ValidationError: 数式のフォーマットが不正な場合
        """
        if "=" not in formula:
            raise ValidationError(
                "数式のフォーマットが不正です",
                details={"formula": formula},
            )

        parts = formula.split("=")
        if len(parts) != 2:
            raise ValidationError(
                "数式のフォーマットが不正です",
                details={"formula": formula},
            )

        result_name = parts[0].strip()
        expression = parts[1].strip()

        if not result_name:
            raise ValidationError(
                "結果変数名が空です",
                details={"formula": formula},
            )

        if not expression:
            raise ValidationError(
                "式が空です",
                details={"formula": formula},
            )

        # 演算子を検出
        operator, operands = self._extract_operator_and_operands(expression)

        return ParsedFormula(
            result_name=result_name,
            expression=expression,
            operator=operator,
            operands=operands,
        )

    def _extract_operator_and_operands(self, expression: str) -> tuple[str | None, list[str]]:
        """式から演算子とオペランドを抽出します。

        Args:
            expression: 式（等号の右辺）

        Returns:
            tuple[str | None, list[str]]: (演算子, オペランドリスト)
        """
        for op in self.SUPPORTED_OPERATORS:
            if op in expression:
                operands = [o.strip() for o in expression.split(op)]
                # 空のオペランドを除外
                operands = [o for o in operands if o]
                if len(operands) >= 2:
                    return op, operands

        # 演算子がない場合は単純代入
        return None, [expression]

    def determine_node_type(self, operand: str) -> str:
        """オペランドのノードタイプを判定します。

        Args:
            operand: オペランド文字列

        Returns:
            str: ノードタイプ（"定数" または "入力"）
        """
        try:
            float(operand)
            return "定数"
        except ValueError:
            return "入力"
