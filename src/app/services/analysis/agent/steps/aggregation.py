"""集計ステップの実装。

このモジュールは、データ集計機能を提供します。
camp-backend-code-analysisのaggregation/funcs.pyから移植しています。

主な機能:
    - 基本集計: sum, mean, count, max, min
    - 四則演算: 集計結果間の計算（+, -, *, /）
    - グループ化: 指定軸でグループ化して集計

データ構造の設計:
    このモジュールは **Wide Format（横持ち）** を採用しています。

    例:
        地域  | 売上 | 原価
        -----|------|-----
        東京 | 100  | 60
        大阪 | 80   | 50

    camp-backendは **Long Format（縦持ち）** を使用していました:
        地域  | 科目 | 値
        -----|------|----
        東京 | 売上 | 100
        東京 | 原価 | 60

    Wide Formatを採用した理由:
        1. pandas標準のデータ構造
        2. メモリ効率が良い
        3. 集計後の分析が容易
        4. 複数科目の同時処理が簡単

使用例:
    >>> from app.services.analysis.agent.steps.aggregation import AggregationStep
    >>>
    >>> agg_step = AggregationStep()
    >>> result = await agg_step.execute(
    ...     source_data=df,
    ...     config={
    ...         "axis": ["地域", "商品"],
    ...         "column": [
    ...             {"name": "売上合計", "subject": "売上", "method": "sum"},
    ...             {"name": "平均単価", "subject": "単価", "method": "mean"}
    ...         ]
    ...     }
    ... )
"""

from typing import Any

import pandas as pd
from pandas.core.groupby import DataFrameGroupBy
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.schemas import AggregateConfig
from app.services.analysis.agent.steps.base import AnalysisStepResult, BaseAnalysisStep

logger = get_logger(__name__)

# 対応している集計メソッド
SUPPORTED_AGGREGATION_METHODS = ["sum", "mean", "count", "max", "min"]

# 対応している四則演算
SUPPORTED_OPERATIONS = ["+", "-", "*", "/"]


class AggregationStep(BaseAnalysisStep):
    """集計ステップ。

    指定された軸でグループ化し、各科目に対して集計を実行します。
    また、集計結果間で四則演算を行うこともできます。

    Attributes:
        step_type (str): "aggregate"

    Example:
        >>> agg_step = AggregationStep()
        >>> config = {
        ...     "axis": ["地域"],
        ...     "column": [
        ...         {"name": "売上合計", "subject": "売上", "method": "sum"},
        ...         {"name": "原価合計", "subject": "原価", "method": "sum"},
        ...         {"name": "利益", "subject": ["売上合計", "原価合計"], "method": "-"}
        ...     ]
        ... }
        >>> result = await agg_step.execute(df, config)
    """

    step_type = "aggregate"

    async def validate_config(
        self,
        config: dict[str, Any],
        source_data: pd.DataFrame | None = None,
    ) -> None:
        """集計設定を検証します。

        Args:
            config: 集計設定
            source_data: ソースデータ

        Raises:
            ValidationError: 設定が不正な場合
        """
        logger.debug("集計設定を検証中")

        # Pydanticスキーマで基本構造を検証
        try:
            agg_config = AggregateConfig.model_validate(config)
        except PydanticValidationError as e:
            raise ValidationError(
                "集計設定の形式が不正です",
                details={"validation_errors": e.errors()},
            ) from e

        axis = agg_config.axis
        columns = agg_config.column

        # axisの検証
        if not isinstance(axis, list):
            raise ValidationError("axisはlistである必要があります", details={"axis": axis})

        if source_data is not None:
            for ax in axis:
                if ax not in source_data.columns:
                    raise ValidationError(
                        f"軸カラムが存在しません: {ax}",
                        details={"axis": ax, "available_columns": list(source_data.columns)},
                    )

        # columnの検証
        if not isinstance(columns, list):
            raise ValidationError("columnはlistである必要があります", details={"column": columns})

        defined_names = []  # 定義済みの集計名
        for i, col in enumerate(columns):
            if not isinstance(col, dict):
                raise ValidationError(
                    f"column[{i}]はdictである必要があります",
                    details={"column": col},
                )

            # 必須フィールド
            if "name" not in col:
                raise ValidationError(f"column[{i}]にnameが必要です", details={"column": col})

            if "subject" not in col:
                raise ValidationError(f"column[{i}]にsubjectが必要です", details={"column": col})

            if "method" not in col:
                raise ValidationError(f"column[{i}]にmethodが必要です", details={"column": col})

            name = col["name"]
            subject = col["subject"]
            method = col["method"]

            # methodの検証
            if method in SUPPORTED_AGGREGATION_METHODS:
                # 基本集計: subjectは文字列
                if not isinstance(subject, str):
                    raise ValidationError(
                        f"基本集計のsubjectは文字列である必要があります: {name}",
                        details={"subject": subject},
                    )

                # カラム存在確認
                if source_data is not None and subject not in source_data.columns:
                    raise ValidationError(
                        f"集計対象カラムが存在しません: {subject}",
                        details={"name": name, "subject": subject},
                    )

            elif method in SUPPORTED_OPERATIONS:
                # 四則演算: subjectはリスト（2要素）
                if not isinstance(subject, list) or len(subject) != 2:
                    raise ValidationError(
                        f"四則演算のsubjectは2要素のlistである必要があります: {name}",
                        details={"subject": subject},
                    )

                # 参照する集計名が定義済みか確認
                for ref_name in subject:
                    if ref_name not in defined_names:
                        raise ValidationError(
                            f"未定義の集計名を参照しています: {ref_name} (column: {name})",
                            details={
                                "name": name,
                                "reference": ref_name,
                                "defined_names": defined_names,
                            },
                        )

            else:
                raise ValidationError(
                    f"未対応のmethodです: {method}",
                    details={
                        "method": method,
                        "supported_aggregation": SUPPORTED_AGGREGATION_METHODS,
                        "supported_operations": SUPPORTED_OPERATIONS,
                    },
                )

            # 定義済み名に追加
            defined_names.append(name)

        logger.debug("集計設定の検証が完了しました", columns_count=len(columns))

    async def execute(
        self,
        source_data: pd.DataFrame,
        config: dict[str, Any],
        **kwargs: Any,
    ) -> AnalysisStepResult:
        """集計を実行します。

        Args:
            source_data: ソースデータ
            config: 集計設定
            **kwargs: 追加パラメータ

        Returns:
            AnalysisStepResult: 集計結果

        Example:
            >>> result = await agg_step.execute(df, config)
        """
        # Pydanticスキーマに変換（型安全性）
        try:
            agg_config = AggregateConfig.model_validate(config)
        except PydanticValidationError as e:
            raise ValidationError(
                "集計設定の形式が不正です",
                details={"validation_errors": e.errors()},
            ) from e

        logger.info(
            "集計を実行中",
            rows=len(source_data),
            axis=agg_config.axis,
            columns_count=len(agg_config.column),
        )

        axis = agg_config.axis
        columns = agg_config.column

        # 元の順序を保持するため、_original_order列を追加
        df_with_order = source_data.copy()
        df_with_order["_original_order"] = range(len(df_with_order))

        # 軸でグループ化

        # 軸でグループ化（as_index=Trueでグループキーをindexに）
        grouped = df_with_order.groupby(axis, as_index=True)

        # 結果を格納するDataFrame（グループキーをリセット）
        result_df = pd.DataFrame(index=list(grouped.groups.keys()))
        result_df.index.names = axis if isinstance(axis, list) else [axis]
        result_df = result_df.reset_index()
        # 中間結果を保持（四則演算用）
        intermediate_results = {}

        # 各columnを順次処理
        for col_config in columns:
            name = col_config.name
            subject = col_config.subject
            method = col_config.method

            if method in SUPPORTED_AGGREGATION_METHODS:
                # 基本集計
                if not isinstance(subject, str):
                    raise ValidationError(
                        f"基本集計のsubjectは文字列である必要があります: {subject}",
                        details={"subject": subject, "method": method},
                    )
                agg_result = self._apply_aggregation(grouped, subject, method)
                result_df[name] = agg_result
                intermediate_results[name] = agg_result

                logger.debug(f"基本集計完了: {name} = {method}({subject})")

            elif method in SUPPORTED_OPERATIONS:
                # 四則演算
                if not isinstance(subject, list) or len(subject) < 2:
                    raise ValidationError(f"四則演算にはsubjectが2つ必要です: {subject}")
                left_name, right_name = subject[0], subject[1]
                left_values = intermediate_results[left_name]
                right_values = intermediate_results[right_name]

                if method == "+":
                    calc_result = left_values + right_values
                elif method == "-":
                    calc_result = left_values - right_values
                elif method == "*":
                    calc_result = left_values * right_values
                elif method == "/":
                    # ゼロ除算対策
                    calc_result = left_values / right_values.replace(0, pd.NA)
                else:
                    raise ValidationError(f"未対応の演算: {method}")

                result_df[name] = calc_result
                intermediate_results[name] = calc_result

                logger.debug(f"四則演算完了: {name} = {left_name} {method} {right_name}")

        # _original_order列を削除
        # _original_order列を削除（存在する場合のみ）
        if "_original_order" in result_df.columns:
            result_df = result_df.drop(columns=["_original_order"])
            result_df = result_df.drop(columns=["_original_order"])

        logger.info(
            "集計が完了しました",
            rows_before=len(source_data),
            rows_after=len(result_df),
            columns_added=len(columns),
        )

        return AnalysisStepResult(
            result_data=result_df,
            result_chart=None,
            result_formula=None,
        )

    def _apply_aggregation(
        self,
        grouped: DataFrameGroupBy,
        subject: str,
        method: str,
    ) -> pd.Series:
        """基本集計を適用します。

        Args:
            grouped: グループ化されたDataFrame
            subject: 集計対象カラム
            method: 集計メソッド（sum/mean/count/max/min）

        Returns:
            pd.Series: 集計結果
        """
        if method == "sum":
            return grouped[subject].sum()
        elif method == "mean":
            return grouped[subject].mean()
        elif method == "count":
            return grouped[subject].count()
        elif method == "max":
            return grouped[subject].max()
        elif method == "min":
            return grouped[subject].min()
        else:
            raise ValidationError(f"未対応の集計メソッド: {method}")
