"""分析ステップの基底クラス定義。

このモジュールは、すべての分析ステップが継承すべき基底クラスを定義します。

主な機能:
    - ステップ設定の管理
    - データ検証の抽象メソッド
    - 実行インターフェースの統一

使用例:
    >>> class CustomStep(BaseAnalysisStep):
    ...     async def validate_config(self, config: dict) -> None:
    ...         # 設定の検証ロジック
    ...         pass
    ...
    ...     async def execute(
    ...         self,
    ...         source_data: pd.DataFrame,
    ...         config: dict
    ...     ) -> AnalysisStepResult:
    ...         # 実行ロジック
    ...         pass
"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.schemas.analysis import AnalysisResultFormula

logger = get_logger(__name__)


class AnalysisStepResult(BaseModel):
    """分析ステップの実行結果。

    ステップ実行後の結果データを保持します。

    Attributes:
        result_data (pd.DataFrame | None): 結果データフレーム
            - filter/aggregate/transform: 処理後のDataFrame
            - summary: 元のDataFrameまたはNone（オプション）
        result_chart (dict[str, Any] | None): チャート情報（Plotly JSON）
            - summaryステップのみ使用
            - Plotlyのgo.Figure.to_dict()形式
        result_formula (list[AnalysisResultFormula] | None): 計算式結果
            - summaryステップのみ使用
            - AnalysisResultFormulaスキーマのリスト

    Example:
        >>> from app.schemas.analysis import AnalysisResultFormula
        >>> result = AnalysisStepResult(
        ...     result_data=filtered_df,
        ...     result_chart=None,
        ...     result_formula=[
        ...         AnalysisResultFormula(name="売上合計", formula="sum(売上)", result=1000000.0, unit="円")
        ...     ]
        ... )
    """

    model_config = {"arbitrary_types_allowed": True}

    result_data: pd.DataFrame | None = Field(None, description="結果データフレーム（filter/aggregate/transform）")
    result_chart: dict[str, Any] | None = Field(None, description="チャート情報（Plotly JSON形式、summaryのみ）")
    result_formula: list[AnalysisResultFormula] | None = Field(None, description="計算式結果（summaryのみ）")


class BaseAnalysisStep(ABC):
    """分析ステップの基底クラス。

    すべての分析ステップ（filter, aggregate, transform, summary）が
    継承すべき抽象基底クラスです。

    サブクラスは以下のメソッドを実装する必要があります：
        - validate_config(): 設定の検証
        - execute(): ステップの実行

    Attributes:
        step_type (str): ステップタイプ（filter/aggregate/transform/summary）

    Example:
        >>> class FilterStep(BaseAnalysisStep):
        ...     step_type = "filter"
        ...
        ...     async def validate_config(self, config: dict) -> None:
        ...         if "category_filter" not in config:
        ...             raise ValidationError("category_filterが必要です")
        ...
        ...     async def execute(
        ...         self,
        ...         source_data: pd.DataFrame,
        ...         config: dict
        ...     ) -> AnalysisStepResult:
        ...         # フィルタリングロジック
        ...         filtered_df = source_data[...]
        ...         return AnalysisStepResult(result_data=filtered_df)
    """

    step_type: str = "base"

    @abstractmethod
    async def validate_config(
        self,
        config: dict[str, Any],
        source_data: pd.DataFrame | None = None,
    ) -> None:
        """ステップ設定を検証します（抽象メソッド）。

        サブクラスで実装が必要です。設定に問題がある場合は
        ValidationErrorを発生させます。

        Args:
            config (dict[str, Any]): ステップ設定
                - ステップタイプごとに異なる構造
            source_data (pd.DataFrame | None): ソースデータ
                - 設定検証時にデータの列名やデータ型を参照する場合に使用
                - Noneの場合もある

        Raises:
            ValidationError: 設定が不正な場合
                - 必須フィールドが欠けている
                - データ型が不正
                - 参照する列が存在しない
                - 設定値の範囲が不正

        Example:
            >>> await step.validate_config(
            ...     config={"category_filter": {"地域": ["東京"]}},
            ...     source_data=df
            ... )
        """
        pass

    @abstractmethod
    async def execute(
        self,
        source_data: pd.DataFrame,
        config: dict[str, Any],
        **kwargs: Any,
    ) -> AnalysisStepResult:
        """ステップを実行します（抽象メソッド）。

        サブクラスで実装が必要です。ソースデータと設定を受け取り、
        処理を実行して結果を返します。

        Args:
            source_data (pd.DataFrame): ソースデータ
                - 元データ、または前のステップの結果
            config (dict[str, Any]): ステップ設定
                - validate_config()で検証済みの設定
            **kwargs (Any): 追加パラメータ
                - table_filter用の参照DataFrameなど

        Returns:
            AnalysisStepResult: 実行結果
                - result_data: 処理後のDataFrame
                - result_chart: チャート（summaryのみ）
                - result_formula: 計算式結果（summaryのみ）

        Raises:
            ValidationError: 実行時にデータ検証エラーが発生した場合
            Exception: 予期しないエラーが発生した場合

        Example:
            >>> result = await step.execute(
            ...     source_data=df,
            ...     config={"category_filter": {"地域": ["東京"]}}
            ... )
            >>> print(len(result.result_data))
            100
        """
        pass

    def __repr__(self) -> str:
        """ステップオブジェクトの文字列表現。

        Returns:
            str: "<StepType(type=...)>" 形式

        Example:
            >>> step = FilterStep()
            >>> print(repr(step))
            '<FilterStep(type=filter)>'
        """
        return f"<{self.__class__.__name__}(type={self.step_type})>"
