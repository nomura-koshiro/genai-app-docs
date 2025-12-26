"""ウォーターフォール図生成。

このモジュールは、ウォーターフォール図の生成機能を提供します。
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.logging import get_logger
from app.services.analysis.agent.steps.summary.graphs.base import BaseGraph

logger = get_logger(__name__)


class WaterfallGraph(BaseGraph):
    """ウォーターフォール図生成クラス。

    Example:
        >>> graph = WaterfallGraph()
        >>> fig = graph.create(
        ...     df,
        ...     x_axis="項目",
        ...     y_axis="金額"
        ... )
    """

    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """ウォーターフォール図を作成します。

        Args:
            df: データフレーム
            **kwargs: グラフパラメータ
                - x_axis (str): X軸（カテゴリ）の列名
                - y_axis (str): Y軸（値）の列名
                - measure (list, optional): 各要素のタイプ ('relative', 'total', 'absolute')
                - title (str, optional): グラフタイトル

        Returns:
            go.Figure: Plotly Figure

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        self._validate_dataframe(df)

        x_axis = kwargs.get("x_axis")
        y_axis = kwargs.get("y_axis")
        measure = kwargs.get("measure")
        title = kwargs.get("title", "ウォーターフォール図")

        if not x_axis or not y_axis:
            raise ValueError("x_axisとy_axisは必須です")

        self._validate_column(df, x_axis)
        self._validate_column(df, y_axis)

        logger.debug(
            "ウォーターフォール図を作成中",
            x_axis=x_axis,
            y_axis=y_axis,
        )

        # measureが指定されていない場合は自動設定
        if not measure:
            # 最初と最後をtotal、それ以外をrelativeとする
            measure = ["relative"] * len(df)
            if len(df) > 0:
                measure[0] = "absolute"  # 最初は絶対値
            if len(df) > 1:
                measure[-1] = "total"  # 最後は合計

        fig = go.Figure(
            data=[
                go.Waterfall(
                    x=df[x_axis],
                    y=df[y_axis],
                    measure=measure,
                    text=df[y_axis],
                    textposition="outside",
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis}: %{{y}}<br><extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title=title,
            xaxis_title=x_axis,
            yaxis_title=y_axis,
            showlegend=False,
        )

        return self._apply_theme(fig)
