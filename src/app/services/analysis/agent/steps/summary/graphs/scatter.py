"""散布図生成。

このモジュールは、散布図の生成機能を提供します。
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.logging import get_logger
from app.services.analysis.agent.steps.summary.graphs.base import BaseGraph

logger = get_logger(__name__)


class ScatterGraph(BaseGraph):
    """散布図生成クラス。

    Example:
        >>> graph = ScatterGraph()
        >>> fig = graph.create(
        ...     df,
        ...     x_axis="売上",
        ...     y_axis="利益",
        ...     color="商品",
        ...     size="数量"
        ... )
    """

    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """散布図を作成します。

        Args:
            df: データフレーム
            **kwargs: グラフパラメータ
                - x_axis (str): X軸の列名
                - y_axis (str): Y軸の列名
                - color (str, optional): 色分けする列名
                - size (str, optional): サイズを決定する列名
                - title (str, optional): グラフタイトル
                - mode (str, optional): 'markers' または 'markers+text', デフォルト: 'markers'

        Returns:
            go.Figure: Plotly Figure

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        self._validate_dataframe(df)

        x_axis = kwargs.get("x_axis")
        y_axis = kwargs.get("y_axis")
        color = kwargs.get("color")
        size = kwargs.get("size")
        title = kwargs.get("title", "散布図")
        mode = kwargs.get("mode", "markers")

        if not x_axis or not y_axis:
            raise ValueError("x_axisとy_axisは必須です")

        self._validate_column(df, x_axis)
        self._validate_column(df, y_axis)

        if color:
            self._validate_column(df, color)
        if size:
            self._validate_column(df, size)

        logger.debug(
            "散布図を作成中",
            x_axis=x_axis,
            y_axis=y_axis,
            color=color,
            size=size,
        )

        fig = go.Figure()

        if color:
            # 色分けあり
            for category in df[color].unique():
                subset = df[df[color] == category]
                marker_dict: dict[str, Any] = {"size": 10}
                if size:
                    marker_dict["size"] = subset[size]
                    marker_dict["sizemode"] = "area"
                    marker_dict["sizeref"] = 2.0 * max(subset[size]) / (40.0**2)
                    marker_dict["sizemin"] = 4

                fig.add_trace(
                    go.Scatter(
                        x=subset[x_axis],
                        y=subset[y_axis],
                        name=str(category),
                        mode=mode,
                        marker=marker_dict,
                        hovertemplate=(
                            f"<b>{category}</b><br>"
                            f"{x_axis}: %{{x}}<br>"
                            f"{y_axis}: %{{y}}<br>"
                            + (f"{size}: %{{marker.size}}<br>" if size else "")
                            + "<extra></extra>"
                        ),
                    )
                )
        else:
            # 色分けなし
            marker_dict: dict[str, Any] = {"size": 10}
            if size:
                marker_dict["size"] = df[size]
                marker_dict["sizemode"] = "area"
                marker_dict["sizeref"] = 2.0 * max(df[size]) / (40.0**2)
                marker_dict["sizemin"] = 4

            fig.add_trace(
                go.Scatter(
                    x=df[x_axis],
                    y=df[y_axis],
                    mode=mode,
                    marker=marker_dict,
                    hovertemplate=(
                        f"{x_axis}: %{{x}}<br>"
                        f"{y_axis}: %{{y}}<br>"
                        + (f"{size}: %{{marker.size}}<br>" if size else "")
                        + "<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title=x_axis,
            yaxis_title=y_axis,
            showlegend=bool(color),
        )

        return self._apply_theme(fig)
