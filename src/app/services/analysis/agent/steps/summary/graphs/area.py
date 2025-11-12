"""面グラフ生成。

このモジュールは、面グラフの生成機能を提供します。
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.logging import get_logger
from app.services.analysis.agent.steps.summary.graphs.base import BaseGraph

logger = get_logger(__name__)


class AreaGraph(BaseGraph):
    """面グラフ生成クラス。

    Example:
        >>> graph = AreaGraph()
        >>> fig = graph.create(
        ...     df,
        ...     x_axis="月",
        ...     y_axis="売上",
        ...     color="商品"
        ... )
    """

    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """面グラフを作成します。

        Args:
            df: データフレーム
            **kwargs: グラフパラメータ
                - x_axis (str): X軸の列名
                - y_axis (str): Y軸の列名
                - color (str, optional): 色分けする列名
                - title (str, optional): グラフタイトル
                - stackgroup (str, optional): 積み上げグループ名, デフォルト: 'one'

        Returns:
            go.Figure: Plotly Figure

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        self._validate_dataframe(df)

        x_axis = kwargs.get("x_axis")
        y_axis = kwargs.get("y_axis")
        color = kwargs.get("color")
        title = kwargs.get("title", "面グラフ")
        stackgroup = kwargs.get("stackgroup", "one")

        if not x_axis or not y_axis:
            raise ValueError("x_axisとy_axisは必須です")

        self._validate_column(df, x_axis)
        self._validate_column(df, y_axis)

        if color:
            self._validate_column(df, color)

        logger.debug(
            "面グラフを作成中",
            x_axis=x_axis,
            y_axis=y_axis,
            color=color,
        )

        fig = go.Figure()

        if color:
            # 色分けあり
            for category in df[color].unique():
                subset = df[df[color] == category]
                fig.add_trace(
                    go.Scatter(
                        x=subset[x_axis],
                        y=subset[y_axis],
                        name=str(category),
                        mode="lines",
                        stackgroup=stackgroup,
                        fill="tonexty",
                        hovertemplate=(f"<b>{category}</b><br>{x_axis}: %{{x}}<br>{y_axis}: %{{y}}<br><extra></extra>"),
                    )
                )
        else:
            # 色分けなし
            fig.add_trace(
                go.Scatter(
                    x=df[x_axis],
                    y=df[y_axis],
                    mode="lines",
                    fill="tozeroy",
                    hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis}: %{{y}}<br><extra></extra>",
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title=x_axis,
            yaxis_title=y_axis,
            showlegend=bool(color),
        )

        return self._apply_theme(fig)
