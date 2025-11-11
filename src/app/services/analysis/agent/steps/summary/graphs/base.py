"""グラフ生成の基底クラス。

このモジュールは、すべてのグラフクラスの基底となる抽象クラスを提供します。
"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseGraph(ABC):
    """グラフ生成の基底クラス。

    すべてのグラフクラスはこのクラスを継承します。

    Example:
        >>> class BarGraph(BaseGraph):
        ...     def create(self, df, **kwargs):
        ...         # 棒グラフの実装
        ...         pass
    """

    @abstractmethod
    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """グラフを作成します。

        Args:
            df: データフレーム
            **kwargs: グラフ固有のパラメータ

        Returns:
            go.Figure: Plotly Figureオブジェクト

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        pass

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """DataFrameを検証します。

        Args:
            df: データフレーム

        Raises:
            ValidationError: DataFrameが空の場合
        """
        if df.empty:
            raise ValidationError("DataFrameが空です", details={"df": df})

    def _validate_column(self, df: pd.DataFrame, column: str) -> None:
        """列の存在を検証します。

        Args:
            df: データフレーム
            column: 列名

        Raises:
            ValidationError: 列が存在しない場合
        """
        if column not in df.columns:
            raise ValidationError(
                f"列が存在しません: {column}",
                details={"column": column, "available_columns": list(df.columns)},
            )

    def _apply_theme(self, fig: go.Figure) -> go.Figure:
        """テーマを適用します。

        Args:
            fig: Plotly Figure

        Returns:
            go.Figure: テーマ適用後のFigure
        """
        fig.update_layout(
            template="plotly_white",
            font={"size": 12, "family": "Arial, sans-serif"},
            hovermode="closest",
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        return fig

    def _format_number(self, value: float) -> str:
        """数値をフォーマットします。

        Args:
            value: 数値

        Returns:
            str: フォーマット済み文字列
        """
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{value / 1_000:.1f}K"
        else:
            return f"{value:.1f}"
