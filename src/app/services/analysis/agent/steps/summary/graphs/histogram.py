"""ヒストグラム生成。

このモジュールは、ヒストグラムの生成機能を提供します。
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.logging import get_logger
from app.services.analysis.agent.steps.summary.graphs.base import BaseGraph

logger = get_logger(__name__)


class HistogramGraph(BaseGraph):
    """ヒストグラム生成クラス。

    Example:
        >>> graph = HistogramGraph()
        >>> fig = graph.create(
        ...     df,
        ...     x_axis="売上",
        ...     nbins=20
        ... )
    """

    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """ヒストグラムを作成します。

        Args:
            df: データフレーム
            **kwargs: グラフパラメータ
                - x_axis (str): 値の列名
                - color (str, optional): 色分けする列名
                - nbins (int, optional): ビンの数, デフォルト: 30
                - title (str, optional): グラフタイトル
                - histnorm (str, optional): 正規化方法 ('', 'percent', 'probability'), デフォルト: ''

        Returns:
            go.Figure: Plotly Figure

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        self._validate_dataframe(df)

        x_axis = kwargs.get("x_axis")
        color = kwargs.get("color")
        nbins = kwargs.get("nbins", 30)
        title = kwargs.get("title", "ヒストグラム")
        histnorm = kwargs.get("histnorm", "")

        if not x_axis:
            raise ValueError("x_axisは必須です")

        self._validate_column(df, x_axis)

        if color:
            self._validate_column(df, color)

        logger.debug(
            "ヒストグラムを作成中",
            x_axis=x_axis,
            color=color,
            nbins=nbins,
        )

        fig = go.Figure()

        if color:
            # 色分けあり
            for category in df[color].unique():
                subset = df[df[color] == category]
                fig.add_trace(
                    go.Histogram(
                        x=subset[x_axis],
                        name=str(category),
                        nbinsx=nbins,
                        histnorm=histnorm,
                        hovertemplate=(f"<b>{category}</b><br>{x_axis}: %{{x}}<br>件数: %{{{{y}}}}<br><extra></extra>"),
                    )
                )
        else:
            # 色分けなし
            fig.add_trace(
                go.Histogram(
                    x=df[x_axis],
                    nbinsx=nbins,
                    histnorm=histnorm,
                    hovertemplate=f"{x_axis}: %{{x}}<br>件数: %{{{{y}}}}<br><extra></extra>",
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title=x_axis,
            yaxis_title="件数" if not histnorm else "比率",
            showlegend=bool(color),
            barmode="overlay" if color else "stack",
        )

        if color:
            fig.update_traces(opacity=0.75)

        return self._apply_theme(fig)
