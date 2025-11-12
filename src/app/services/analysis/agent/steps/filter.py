"""フィルタリングステップの実装。

このモジュールは、データフィルタリング機能を提供します。
camp-backend-code-analysisのfilter/funcs.pyから移植しています。

主な機能:
    - カテゴリフィルタ: 特定の値を含む/除外
    - 数値フィルタ: 範囲指定、上位K件、パーセンタイル
    - テーブルフィルタ: 他のステップの結果を参照してフィルタ

使用例:
    >>> from app.services.analysis.agent.steps.filter import FilterStep
    >>>
    >>> filter_step = FilterStep()
    >>> result = await filter_step.execute(
    ...     source_data=df,
    ...     config={
    ...         "category_filter": {"地域": ["東京", "大阪"]},
    ...         "numeric_filter": {"column": "売上", "filter_type": "range", ...},
    ...         "table_filter": {"enable": False}
    ...     }
    ... )
"""

from typing import Any

import pandas as pd
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.schemas import (
    FilterConfig,
    NumericFilterConfig,
    TableFilterConfig,
)
from app.services.analysis.agent.steps.base import AnalysisStepResult, BaseAnalysisStep

logger = get_logger(__name__)


class FilterStep(BaseAnalysisStep):
    """フィルタリングステップ。

    データを3種類の方法でフィルタリングします：
    1. カテゴリフィルタ: 特定の値を含む/除外
    2. 数値フィルタ: 範囲指定、上位K件、パーセンタイル
    3. テーブルフィルタ: 他のステップの結果を参照してフィルタ

    Attributes:
        step_type (str): "filter"

    Example:
        >>> filter_step = FilterStep()
        >>> config = {
        ...     "category_filter": {"地域": ["東京", "大阪"]},
        ...     "numeric_filter": {
        ...         "column": "売上",
        ...         "filter_type": "range",
        ...         "enable_min": True,
        ...         "min_value": 1000,
        ...         "include_min": True,
        ...         "enable_max": True,
        ...         "max_value": 5000,
        ...         "include_max": False
        ...     },
        ...     "table_filter": {"enable": False}
        ... }
        >>> result = await filter_step.execute(df, config)
    """

    step_type = "filter"

    async def validate_config(
        self,
        config: dict[str, Any],
        source_data: pd.DataFrame | None = None,
    ) -> None:
        """フィルタ設定を検証します。

        Args:
            config (dict[str, Any]): フィルタ設定
                - category_filter (dict): カテゴリフィルタ設定
                - numeric_filter (dict): 数値フィルタ設定
                - table_filter (dict): テーブルフィルタ設定
            source_data (pd.DataFrame | None): ソースデータ

        Raises:
            ValidationError: 設定が不正な場合
                - 必須フィールドが欠けている
                - カラム名が存在しない
                - filter_typeが不正
                - 数値範囲が不正

        Example:
            >>> await filter_step.validate_config(
            ...     config={"category_filter": {"地域": ["東京"]}},
            ...     source_data=df
            ... )
        """
        logger.debug("フィルタ設定を検証中", config_keys=list(config.keys()))

        # Pydanticスキーマで基本構造を検証
        try:
            filter_config = FilterConfig.model_validate(config)
        except PydanticValidationError as e:
            raise ValidationError(
                "フィルタ設定の形式が不正です",
                details={"validation_errors": e.errors()},
            ) from e

        # カテゴリフィルタの検証
        if filter_config.category_filter is not None:
            category_filter = filter_config.category_filter

            # カラム存在確認（source_dataが提供されている場合）
            if source_data is not None:
                for column in category_filter.keys():
                    if column not in source_data.columns:
                        raise ValidationError(
                            f"カラムが存在しません: {column}",
                            details={
                                "column": column,
                                "available_columns": list(source_data.columns),
                            },
                        )

        # 数値フィルタの検証
        if filter_config.numeric_filter is not None:
            numeric_filter = filter_config.numeric_filter

            # カラム存在確認
            column = numeric_filter.column
            if source_data is not None and column:
                if column not in source_data.columns:
                    raise ValidationError(
                        f"カラムが存在しません: {column}",
                        details={
                            "column": column,
                            "available_columns": list(source_data.columns),
                        },
                    )

                # 数値型カラムの確認
                if not pd.api.types.is_numeric_dtype(source_data[column]):
                    raise ValidationError(
                        f"カラムは数値型である必要があります: {column}",
                        details={
                            "column": column,
                            "dtype": str(source_data[column].dtype),
                        },
                    )

            # filter_type別の検証
            filter_type = numeric_filter.filter_type
            if filter_type == "range":
                # 範囲検証
                if numeric_filter.enable_min and numeric_filter.enable_max:
                    min_val = numeric_filter.min_value
                    max_val = numeric_filter.max_value
                    if min_val is not None and max_val is not None and min_val > max_val:
                        raise ValidationError(
                            "min_valueはmax_value以下である必要があります",
                            details={"min_value": min_val, "max_value": max_val},
                        )

            elif filter_type == "topk":
                # k_valueの検証
                k_value = numeric_filter.k_value
                if k_value is not None and k_value <= 0:
                    raise ValidationError(
                        "k_valueは正の整数である必要があります",
                        details={"k_value": k_value},
                    )

            elif filter_type == "percentage":
                # パーセンタイル範囲の検証
                min_pct = numeric_filter.min_percentile if numeric_filter.min_percentile is not None else 0.0
                max_pct = numeric_filter.max_percentile if numeric_filter.max_percentile is not None else 100.0
                if not (0 <= min_pct <= 100):
                    raise ValidationError(
                        "min_percentileは0～100の範囲である必要があります",
                        details={"min_percentile": min_pct},
                    )
                if not (0 <= max_pct <= 100):
                    raise ValidationError(
                        "max_percentileは0～100の範囲である必要があります",
                        details={"max_percentile": max_pct},
                    )
                if min_pct > max_pct:
                    raise ValidationError(
                        "min_percentileはmax_percentile以下である必要があります",
                        details={"min_percentile": min_pct, "max_percentile": max_pct},
                    )

        # テーブルフィルタの検証
        if filter_config.table_filter is not None:
            table_filter = filter_config.table_filter

            # enable=Trueの場合のみ詳細検証
            if table_filter.enable:
                # table_dfの検証
                if table_filter.table_df is None:
                    raise ValidationError(
                        "table_filterが有効な場合、table_dfが必要です",
                        details={"table_filter": table_filter},
                    )

                # key_columnsの検証
                key_columns = table_filter.key_columns
                if not key_columns:
                    raise ValidationError(
                        "table_filterが有効な場合、key_columnsが必要です",
                        details={"table_filter": table_filter},
                    )

                # カラム存在確認
                if source_data is not None:
                    for column in key_columns:
                        if column not in source_data.columns:
                            raise ValidationError(
                                f"key_columnsのカラムが存在しません: {column}",
                                details={
                                    "column": column,
                                    "available_columns": list(source_data.columns),
                                },
                            )

        logger.debug("フィルタ設定の検証が完了しました")

    async def execute(
        self,
        source_data: pd.DataFrame,
        config: dict[str, Any],
        **kwargs: Any,
    ) -> AnalysisStepResult:
        """フィルタリングを実行します。

        Args:
            source_data (pd.DataFrame): ソースデータ
            config (dict[str, Any]): フィルタ設定
            **kwargs (Any): 追加パラメータ
                - table_filter_df (pd.DataFrame): テーブルフィルタ用の参照DataFrame

        Returns:
            AnalysisStepResult: フィルタリング結果
                - result_data: フィルタリング後のDataFrame

        Raises:
            ValidationError: フィルタリング実行時のエラー

        Example:
            >>> result = await filter_step.execute(
            ...     source_data=df,
            ...     config={"category_filter": {"地域": ["東京", "大阪"]}}
            ... )
            >>> print(len(result.result_data))
            50
        """
        logger.info(
            "フィルタリングを実行中",
            rows_before=len(source_data),
            columns=len(source_data.columns),
        )

        # Pydanticスキーマに変換（型安全性）
        try:
            filter_config = FilterConfig.model_validate(config)
        except PydanticValidationError as e:
            raise ValidationError(
                "フィルタ設定の形式が不正です",
                details={"validation_errors": e.errors()},
            ) from e

        # データのコピーを作成（元データを変更しない）
        filtered_df = source_data.copy()

        # カテゴリフィルタ
        if filter_config.category_filter is not None:
            filtered_df = await self._apply_category_filter(
                filtered_df,
                filter_config.category_filter,
            )

        # 数値フィルタ
        if filter_config.numeric_filter is not None:
            filtered_df = await self._apply_numeric_filter(
                filtered_df,
                filter_config.numeric_filter,
            )

        # テーブルフィルタ
        if filter_config.table_filter is not None and filter_config.table_filter.enable:
            table_filter_df = kwargs.get("table_filter_df")
            if table_filter_df is None:
                raise ValidationError(
                    "table_filter有効時はtable_filter_dfが必要です",
                    details={"config": filter_config.table_filter.model_dump()},
                )

            filtered_df = await self._apply_table_filter(
                filtered_df,
                filter_config.table_filter,
                table_filter_df,
            )

        logger.info(
            "フィルタリングが完了しました",
            rows_before=len(source_data),
            rows_after=len(filtered_df),
            filtered_ratio=f"{len(filtered_df) / len(source_data) * 100:.1f}%",
        )

        return AnalysisStepResult(
            result_data=filtered_df,
            result_chart=None,
            result_formula=None,
        )

    async def _apply_category_filter(
        self,
        df: pd.DataFrame,
        category_filter: dict[str, list[str]],
    ) -> pd.DataFrame:
        """カテゴリフィルタを適用します。

        Args:
            df (pd.DataFrame): データフレーム
            category_filter (dict[str, list[str]]): カテゴリフィルタ設定
                - キー: カラム名
                - 値: 含める値のリスト

        Returns:
            pd.DataFrame: フィルタリング後のDataFrame

        Example:
            >>> filtered = await self._apply_category_filter(
            ...     df,
            ...     {"地域": ["東京", "大阪"], "商品": ["商品A"]}
            ... )
        """
        logger.debug("カテゴリフィルタを適用中", filters=list(category_filter.keys()))

        filtered_df = df.copy()

        for column, values in category_filter.items():
            if column not in filtered_df.columns:
                logger.warning(f"カラムが存在しません: {column}")
                continue

            # 指定された値のみを保持
            filtered_df = filtered_df[filtered_df[column].isin(values)]

            logger.debug(
                f"カテゴリフィルタ適用: {column}",
                values_count=len(values),
                rows_after=len(filtered_df),
            )

        return filtered_df

    async def _apply_numeric_filter(
        self,
        df: pd.DataFrame,
        numeric_filter: NumericFilterConfig,
    ) -> pd.DataFrame:
        """数値フィルタを適用します。

        Args:
            df (pd.DataFrame): データフレーム
            numeric_filter (NumericFilterConfig): 数値フィルタ設定

        Returns:
            pd.DataFrame: フィルタリング後のDataFrame

        Example:
            >>> filtered = await self._apply_numeric_filter(
            ...     df,
            ...     NumericFilterConfig(
            ...         column="売上",
            ...         filter_type="range",
            ...         enable_min=True,
            ...         min_value=1000,
            ...         include_min=True,
            ...         enable_max=True,
            ...         max_value=5000,
            ...         include_max=False
            ...     )
            ... )
        """
        column = numeric_filter.column
        filter_type = numeric_filter.filter_type

        logger.debug(
            "数値フィルタを適用中",
            column=column,
            filter_type=filter_type,
        )

        if column not in df.columns:
            logger.warning(f"カラムが存在しません: {column}")
            return df

        filtered_df = df.copy()

        if filter_type == "range":
            # 範囲フィルタ
            if numeric_filter.enable_min and numeric_filter.min_value is not None:
                min_value = numeric_filter.min_value
                include_min = numeric_filter.include_min
                if include_min:
                    filtered_df = filtered_df[filtered_df[column] >= min_value]
                else:
                    filtered_df = filtered_df[filtered_df[column] > min_value]

                logger.debug(f"最小値フィルタ適用: {min_value} (include={include_min})")

            if numeric_filter.enable_max and numeric_filter.max_value is not None:
                max_value = numeric_filter.max_value
                include_max = numeric_filter.include_max
                if include_max:
                    filtered_df = filtered_df[filtered_df[column] <= max_value]
                else:
                    filtered_df = filtered_df[filtered_df[column] < max_value]

                logger.debug(f"最大値フィルタ適用: {max_value} (include={include_max})")

        elif filter_type == "topk":
            # 上位K件フィルタ
            k_value = numeric_filter.k_value if numeric_filter.k_value is not None else 10
            ascending = numeric_filter.ascending

            sorted_df = filtered_df.sort_values(by=column, ascending=ascending)
            filtered_df = sorted_df.head(k_value)

            logger.debug(
                f"上位K件フィルタ適用: k={k_value}, ascending={ascending}",
                rows_after=len(filtered_df),
            )

        elif filter_type == "percentage":
            # パーセンタイルフィルタ
            min_percentile = numeric_filter.min_percentile
            max_percentile = numeric_filter.max_percentile

            min_value = filtered_df[column].quantile(min_percentile / 100.0)
            max_value = filtered_df[column].quantile(max_percentile / 100.0)

            filtered_df = filtered_df[(filtered_df[column] >= min_value) & (filtered_df[column] <= max_value)]

            logger.debug(
                f"パーセンタイルフィルタ適用: {min_percentile}%-{max_percentile}%",
                min_value=min_value,
                max_value=max_value,
                rows_after=len(filtered_df),
            )

        return filtered_df

    async def _apply_table_filter(
        self,
        df: pd.DataFrame,
        table_filter: TableFilterConfig,
        reference_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """テーブルフィルタを適用します。

        Args:
            df (pd.DataFrame): データフレーム
            table_filter (TableFilterConfig): テーブルフィルタ設定
            reference_df (pd.DataFrame): 参照用DataFrame

        Returns:
            pd.DataFrame: フィルタリング後のDataFrame

        Example:
            >>> filtered = await self._apply_table_filter(
            ...     df,
            ...     TableFilterConfig(
            ...         key_columns=["地域"],
            ...         exclude_mode=False
            ...     ),
            ...     reference_df
            ... )
        """
        key_columns = table_filter.key_columns
        exclude_mode = table_filter.exclude_mode

        logger.debug(
            "テーブルフィルタを適用中",
            key_columns=key_columns,
            exclude_mode=exclude_mode,
            reference_rows=len(reference_df),
        )

        # key_columnsでマージ
        # exclude_mode=False: 参照DataFrameに存在する行を保持
        # exclude_mode=True: 参照DataFrameに存在しない行を保持

        if exclude_mode:
            # 除外モード: 参照DataFrameに存在しない行を保持
            merged = df.merge(
                reference_df[key_columns],
                on=key_columns,
                how="left",
                indicator=True,
            )
            filtered_df = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])
        else:
            # 包含モード: 参照DataFrameに存在する行を保持
            filtered_df = df.merge(
                reference_df[key_columns],
                on=key_columns,
                how="inner",
            )

        logger.debug(
            "テーブルフィルタ適用完了",
            rows_before=len(df),
            rows_after=len(filtered_df),
        )

        return filtered_df
