"""変換ステップの実装。

このモジュールは、データ変換機能を提供します。
camp-backend-code-analysisのtransform/funcs.pyから移植しています。

主な機能:
    - add_axis: 新しい列（軸）を追加
    - modify_axis: 既存列を変更
    - add_subject: 新しい科目を追加
    - modify_subject: 既存科目を変更

計算タイプ:
    - constant: 定数値
    - copy: 他の列/科目をコピー
    - formula: 数式計算
    - mapping: 値マッピング（辞書）

使用例:
    >>> from app.services.analysis.agent.steps.transform import TransformStep
    >>>
    >>> transform_step = TransformStep()
    >>> result = await transform_step.execute(
    ...     source_data=df,
    ...     config={
    ...         "operations": [
    ...             {
    ...                 "operation_type": "add_axis",
    ...                 "target_name": "年度",
    ...                 "calculation": {"type": "constant", "constant_value": "2024"}
    ...             }
    ...         ]
    ...     }
    ... )
"""

from typing import Any

import pandas as pd

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.services.analysis.agent.steps.base import AnalysisStepResult, BaseAnalysisStep

logger = get_logger(__name__)

# 対応している操作タイプ
SUPPORTED_OPERATION_TYPES = ["add_axis", "modify_axis", "add_subject", "modify_subject"]

# 対応している計算タイプ
SUPPORTED_CALCULATION_TYPES = ["constant", "copy", "formula", "mapping"]

# 対応している数式演算子
SUPPORTED_FORMULA_OPERATORS = ["+", "-", "*", "/"]


class TransformStep(BaseAnalysisStep):
    """変換ステップ。

    データの列（axis）や科目（subject）を追加・変更します。

    Attributes:
        step_type (str): "transform"

    Example:
        >>> transform_step = TransformStep()
        >>> config = {
        ...     "operations": [
        ...         {
        ...             "operation_type": "add_axis",
        ...             "target_name": "年度",
        ...             "calculation": {
        ...                 "type": "constant",
        ...                 "constant_value": "2024"
        ...             }
        ...         },
        ...         {
        ...             "operation_type": "modify_subject",
        ...             "target_name": "売上",
        ...             "calculation": {
        ...                 "type": "formula",
        ...                 "formula_type": "*",
        ...                 "operands": ["売上", "1.1"]
        ...             }
        ...         }
        ...     ]
        ... }
        >>> result = await transform_step.execute(df, config)
    """

    step_type = "transform"

    async def validate_config(
        self,
        config: dict[str, Any],
        source_data: pd.DataFrame | None = None,
    ) -> None:
        """変換設定を検証します。

        Args:
            config: 変換設定
            source_data: ソースデータ

        Raises:
            ValidationError: 設定が不正な場合
        """
        logger.debug("変換設定を検証中")

        if "operations" not in config:
            raise ValidationError("operationsが必要です", details={"config": config})

        operations = config["operations"]

        if not isinstance(operations, list):
            raise ValidationError(
                "operationsはlistである必要があります",
                details={"operations": operations},
            )

        for i, operation in enumerate(operations):
            if not isinstance(operation, dict):
                raise ValidationError(
                    f"operations[{i}]はdictである必要があります",
                    details={"operation": operation},
                )

            # 必須フィールド
            if "operation_type" not in operation:
                raise ValidationError(
                    f"operations[{i}]にoperation_typeが必要です",
                    details={"operation": operation},
                )

            if "target_name" not in operation:
                raise ValidationError(
                    f"operations[{i}]にtarget_nameが必要です",
                    details={"operation": operation},
                )

            if "calculation" not in operation:
                raise ValidationError(
                    f"operations[{i}]にcalculationが必要です",
                    details={"operation": operation},
                )

            operation_type = operation["operation_type"]
            calculation = operation["calculation"]

            # operation_typeの検証
            if operation_type not in SUPPORTED_OPERATION_TYPES:
                raise ValidationError(
                    f"未対応のoperation_typeです: {operation_type}",
                    details={
                        "operation_type": operation_type,
                        "supported": SUPPORTED_OPERATION_TYPES,
                    },
                )

            # calculationの検証
            if not isinstance(calculation, dict):
                raise ValidationError(
                    f"operations[{i}].calculationはdictである必要があります",
                    details={"calculation": calculation},
                )

            if "type" not in calculation:
                raise ValidationError(
                    f"operations[{i}].calculationにtypeが必要です",
                    details={"calculation": calculation},
                )

            calc_type = calculation["type"]

            if calc_type not in SUPPORTED_CALCULATION_TYPES:
                raise ValidationError(
                    f"未対応のcalculation typeです: {calc_type}",
                    details={"type": calc_type, "supported": SUPPORTED_CALCULATION_TYPES},
                )

            # calc_type別の検証
            if calc_type == "constant":
                if "constant_value" not in calculation:
                    raise ValidationError(
                        "type='constant'の場合、constant_valueが必要です",
                        details={"calculation": calculation},
                    )

            elif calc_type == "copy":
                if "copy_from" not in calculation:
                    raise ValidationError(
                        "type='copy'の場合、copy_fromが必要です",
                        details={"calculation": calculation},
                    )

            elif calc_type == "formula":
                if "formula_type" not in calculation:
                    raise ValidationError(
                        "type='formula'の場合、formula_typeが必要です",
                        details={"calculation": calculation},
                    )

                if "operands" not in calculation:
                    raise ValidationError(
                        "type='formula'の場合、operandsが必要です",
                        details={"calculation": calculation},
                    )

                formula_type = calculation["formula_type"]
                if formula_type not in SUPPORTED_FORMULA_OPERATORS:
                    raise ValidationError(
                        f"未対応のformula_typeです: {formula_type}",
                        details={"formula_type": formula_type, "supported": SUPPORTED_FORMULA_OPERATORS},
                    )

            elif calc_type == "mapping":
                if "mapping_dict" not in calculation:
                    raise ValidationError(
                        "type='mapping'の場合、mapping_dictが必要です",
                        details={"calculation": calculation},
                    )

        logger.debug("変換設定の検証が完了しました", operations_count=len(operations))

    async def execute(
        self,
        source_data: pd.DataFrame,
        config: dict[str, Any],
        **kwargs: Any,
    ) -> AnalysisStepResult:
        """変換を実行します。

        Args:
            source_data: ソースデータ
            config: 変換設定
            **kwargs: 追加パラメータ

        Returns:
            AnalysisStepResult: 変換結果
        """
        logger.info(
            "変換を実行中",
            rows=len(source_data),
            operations_count=len(config["operations"]),
        )

        result_df = source_data.copy()

        for _i, operation in enumerate(config["operations"]):
            operation_type = operation["operation_type"]
            target_name = operation["target_name"]
            calculation = operation["calculation"]

            logger.debug(
                f"操作実行中: {operation_type}",
                target_name=target_name,
                calc_type=calculation["type"],
            )

            if operation_type in ["add_axis", "modify_axis"]:
                # 軸（列）の操作
                result_df = await self._apply_axis_operation(
                    result_df,
                    operation_type,
                    target_name,
                    calculation,
                )

            elif operation_type in ["add_subject", "modify_subject"]:
                # 科目（行）の操作
                result_df = await self._apply_subject_operation(
                    result_df,
                    operation_type,
                    target_name,
                    calculation,
                )

        logger.info(
            "変換が完了しました",
            rows_before=len(source_data),
            rows_after=len(result_df),
            columns_before=len(source_data.columns),
            columns_after=len(result_df.columns),
        )

        return AnalysisStepResult(
            result_data=result_df,
            result_chart=None,
            result_formula=None,
        )

    async def _apply_axis_operation(
        self,
        df: pd.DataFrame,
        operation_type: str,
        target_name: str,
        calculation: dict[str, Any],
    ) -> pd.DataFrame:
        """軸（列）操作を適用します。

        Args:
            df: データフレーム
            operation_type: 操作タイプ（add_axis/modify_axis）
            target_name: ターゲット列名
            calculation: 計算設定

        Returns:
            pd.DataFrame: 処理後のDataFrame
        """
        calc_type = calculation["type"]

        # 計算値を取得
        if calc_type == "constant":
            values = calculation["constant_value"]

        elif calc_type == "copy":
            copy_from = calculation["copy_from"]
            if copy_from not in df.columns:
                raise ValidationError(
                    f"コピー元カラムが存在しません: {copy_from}",
                    details={"copy_from": copy_from},
                )
            values = df[copy_from]

        elif calc_type == "formula":
            formula_type = calculation["formula_type"]
            operands = calculation["operands"]

            # operandsの値を取得
            operand_values = []
            for operand in operands:
                if operand in df.columns:
                    operand_values.append(df[operand])
                else:
                    # 定数として扱う
                    try:
                        operand_values.append(float(operand))
                    except ValueError as e:
                        raise ValidationError(
                            f"operandが不正です: {operand}",
                            details={"operand": operand},
                        ) from e

            # 数式計算
            if formula_type == "+":
                values = operand_values[0] + operand_values[1]
            elif formula_type == "-":
                values = operand_values[0] - operand_values[1]
            elif formula_type == "*":
                values = operand_values[0] * operand_values[1]
            elif formula_type == "/":
                values = operand_values[0] / operand_values[1]
            else:
                raise ValidationError(f"未対応のformula_type: {formula_type}")

        elif calc_type == "mapping":
            mapping_dict = calculation["mapping_dict"]
            source_column = calculation.get("source_column")

            if source_column not in df.columns:
                raise ValidationError(
                    f"マッピング元カラムが存在しません: {source_column}",
                    details={"source_column": source_column},
                )

            values = df[source_column].map(mapping_dict)

        else:
            raise ValidationError(f"未対応のcalc_type: {calc_type}")

        # 列を追加/変更
        df[target_name] = values

        return df

    async def _apply_subject_operation(
        self,
        df: pd.DataFrame,
        operation_type: str,
        target_name: str,
        calculation: dict[str, Any],
    ) -> pd.DataFrame:
        """科目（行）操作を適用します。

        科目は列として扱います（Wide Format）。
        - add_subject: 新しい科目列を追加
        - modify_subject: 既存の科目列を変更

        Args:
            df: データフレーム
            operation_type: 操作タイプ（add_subject/modify_subject）
            target_name: ターゲット科目名
            calculation: 計算設定

        Returns:
            pd.DataFrame: 処理後のDataFrame

        Raises:
            ValidationError: 科目列が存在しない場合（modify_subject時）
        """
        calc_type = calculation["type"]

        logger.debug(
            f"科目操作を実行中: {operation_type}",
            target_name=target_name,
            calc_type=calc_type,
        )

        # 計算値を取得
        if calc_type == "constant":
            values = calculation["constant_value"]

        elif calc_type == "copy":
            copy_from = calculation["copy_from"]
            if copy_from not in df.columns:
                raise ValidationError(
                    f"コピー元科目列が存在しません: {copy_from}",
                    details={"copy_from": copy_from},
                )
            values = df[copy_from]

        elif calc_type == "formula":
            formula_type = calculation["formula_type"]
            operands = calculation["operands"]

            # operandsの値を取得
            operand_values = []
            for operand in operands:
                if operand in df.columns:
                    operand_values.append(df[operand])
                else:
                    # 定数として扱う
                    try:
                        operand_values.append(float(operand))
                    except ValueError as e:
                        raise ValidationError(
                            f"operandが不正です: {operand}",
                            details={"operand": operand},
                        ) from e

            # 数式計算
            if formula_type == "+":
                values = operand_values[0] + operand_values[1]
            elif formula_type == "-":
                values = operand_values[0] - operand_values[1]
            elif formula_type == "*":
                values = operand_values[0] * operand_values[1]
            elif formula_type == "/":
                values = operand_values[0] / operand_values[1]
            else:
                raise ValidationError(f"未対応のformula_type: {formula_type}")

        elif calc_type == "mapping":
            mapping_dict = calculation["mapping_dict"]
            source_column = calculation.get("source_column")

            if source_column not in df.columns:
                raise ValidationError(
                    f"マッピング元科目列が存在しません: {source_column}",
                    details={"source_column": source_column},
                )

            values = df[source_column].map(mapping_dict)

        else:
            raise ValidationError(f"未対応のcalc_type: {calc_type}")

        # modify_subjectの場合、既存列の存在確認
        if operation_type == "modify_subject":
            if target_name not in df.columns:
                raise ValidationError(
                    f"変更対象の科目列が存在しません: {target_name}",
                    details={"target_name": target_name, "available_columns": list(df.columns)},
                )
            logger.debug(f"既存の科目列を変更: {target_name}")

        # 列を追加/変更
        df[target_name] = values

        logger.debug(
            f"科目操作が完了しました: {operation_type}",
            target_name=target_name,
            rows=len(df),
        )

        return df
