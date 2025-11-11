"""箱ひげ図生成。

このモジュールは、箱ひげ図の生成機能を提供します。
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.logging import get_logger
from app.services.analysis.agent.steps.summary.graphs.base import BaseGraph

logger = get_logger(__name__)


class BoxGraph(BaseGraph):
    """箱ひげ図生成クラス。

    Example:
        >>> graph = BoxGraph()
        >>> fig = graph.create(
        ...     df,
        ...     x_axis="商品",
        ...     y_axis="売上"
        ... )
    """

    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """箱ひげ図を作成します。

        Args:
            df: データフレーム
            **kwargs: グラフパラメータ
                - x_axis (str, optional): カテゴリ列名（グループ化）
                - y_axis (str): 値の列名
                - color (str, optional): 色分けする列名
                - title (str, optional): グラフタイトル

        Returns:
            go.Figure: Plotly Figure

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        self._validate_dataframe(df)

        x_axis = kwargs.get("x_axis")
        y_axis = kwargs.get("y_axis")
        color = kwargs.get("color")
        title = kwargs.get("title", "箱ひげ図")

        if not y_axis:
            raise ValueError("y_axisは必須です")

        self._validate_column(df, y_axis)

        if x_axis:
            self._validate_column(df, x_axis)
        if color:
            self._validate_column(df, color)

        logger.debug(
            "箱ひげ図を作成中",
            x_axis=x_axis,
            y_axis=y_axis,
            color=color,
        )

        fig = go.Figure()

        if x_axis and color:
            # x_axisとcolorの両方がある場合
            for category in df[color].unique():
                subset = df[df[color] == category]
                fig.add_trace(
                    go.Box(
                        x=subset[x_axis],
                        y=subset[y_axis],
                        name=str(category),
                        hovertemplate=(
                            f"<b>{category}</b><br>"
                            f"{x_axis}: %{{x}}<br>"
                            f"{y_axis}: %{{y}}<br>"
                            "<extra></extra>"
                        ),
                    )
                )
        elif x_axis:
            # x_axisのみ
            for category in df[x_axis].unique():
                subset = df[df[x_axis] == category]
                fig.add_trace(
                    go.Box(
                        y=subset[y_axis],
                        name=str(category),
                        hovertemplate=f"<b>{category}</b><br>" f"{y_axis}: %{{y}}<br>" "<extra></extra>",
                    )
                )
        else:
            # x_axisなし（全体の分布）
            fig.add_trace(
                go.Box(
                    y=df[y_axis],
                    name=y_axis,
                    hovertemplate=f"{y_axis}: %{{y}}<br>" "<extra></extra>",
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title=x_axis if x_axis else "",
            yaxis_title=y_axis,
            showlegend=bool(color or x_axis),
        )

        return self._apply_theme(fig)
