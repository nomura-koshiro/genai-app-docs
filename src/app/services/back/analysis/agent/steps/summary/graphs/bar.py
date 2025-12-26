"""棒グラフ生成。

このモジュールは、棒グラフの生成機能を提供します。
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.logging import get_logger
from app.services.analysis.agent.steps.summary.graphs.base import BaseGraph

logger = get_logger(__name__)


class BarGraph(BaseGraph):
    """棒グラフ生成クラス。

    Example:
        >>> graph = BarGraph()
        >>> fig = graph.create(
        ...     df,
        ...     x_axis="地域",
        ...     y_axis="売上",
        ...     color="商品",
        ...     orientation="v"
        ... )
    """

    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """棒グラフを作成します。

        Args:
            df: データフレーム
            **kwargs: グラフパラメータ
                - x_axis (str): X軸の列名
                - y_axis (str): Y軸の列名
                - color (str, optional): 色分けする列名
                - orientation (str, optional): 'v' (縦) または 'h' (横), デフォルト: 'v'
                - title (str, optional): グラフタイトル
                - barmode (str, optional): 'group' または 'stack', デフォルト: 'group'

        Returns:
            go.Figure: Plotly Figure

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        self._validate_dataframe(df)

        x_axis = kwargs.get("x_axis")
        y_axis = kwargs.get("y_axis")
        color = kwargs.get("color")
        orientation = kwargs.get("orientation", "v")
        title = kwargs.get("title", "棒グラフ")
        barmode = kwargs.get("barmode", "group")

        if not x_axis or not y_axis:
            raise ValueError("x_axisとy_axisは必須です")

        self._validate_column(df, x_axis)
        self._validate_column(df, y_axis)

        if color:
            self._validate_column(df, color)

        logger.debug(
            "棒グラフを作成中",
            x_axis=x_axis,
            y_axis=y_axis,
            color=color,
            orientation=orientation,
        )

        fig = go.Figure()

        if color:
            # 色分けあり
            for category in df[color].unique():
                subset = df[df[color] == category]
                fig.add_trace(
                    go.Bar(
                        x=subset[x_axis] if orientation == "v" else subset[y_axis],
                        y=subset[y_axis] if orientation == "v" else subset[x_axis],
                        name=str(category),
                        orientation=orientation,
                        hovertemplate=(
                            f"<b>{category}</b><br>{x_axis}: %{{x}}<br>{y_axis}: %{{y}}<br><extra></extra>"
                            if orientation == "v"
                            else f"<b>{category}</b><br>{y_axis}: %{{x}}<br>{x_axis}: %{{y}}<br><extra></extra>"
                        ),
                    )
                )
        else:
            # 色分けなし
            fig.add_trace(
                go.Bar(
                    x=df[x_axis] if orientation == "v" else df[y_axis],
                    y=df[y_axis] if orientation == "v" else df[x_axis],
                    orientation=orientation,
                    hovertemplate=(
                        f"{x_axis}: %{{x}}<br>{y_axis}: %{{y}}<br><extra></extra>"
                        if orientation == "v"
                        else f"{y_axis}: %{{x}}<br>{x_axis}: %{{y}}<br><extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title=x_axis if orientation == "v" else y_axis,
            yaxis_title=y_axis if orientation == "v" else x_axis,
            barmode=barmode,
            showlegend=bool(color),
        )

        return self._apply_theme(fig)
