"""ヒートマップ生成。

このモジュールは、ヒートマップの生成機能を提供します。
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.logging import get_logger
from app.services.analysis.agent.steps.summary.graphs.base import BaseGraph

logger = get_logger(__name__)


class HeatmapGraph(BaseGraph):
    """ヒートマップ生成クラス。

    Example:
        >>> graph = HeatmapGraph()
        >>> fig = graph.create(
        ...     df,
        ...     x_axis="月",
        ...     y_axis="商品",
        ...     z_axis="売上"
        ... )
    """

    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """ヒートマップを作成します。

        Args:
            df: データフレーム
            **kwargs: グラフパラメータ
                - x_axis (str): X軸の列名
                - y_axis (str): Y軸の列名
                - z_axis (str): 値の列名
                - title (str, optional): グラフタイトル
                - colorscale (str, optional): カラースケール, デフォルト: 'Viridis'

        Returns:
            go.Figure: Plotly Figure

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        self._validate_dataframe(df)

        x_axis = kwargs.get("x_axis")
        y_axis = kwargs.get("y_axis")
        z_axis = kwargs.get("z_axis")
        title = kwargs.get("title", "ヒートマップ")
        colorscale = kwargs.get("colorscale", "Viridis")

        if not x_axis or not y_axis or not z_axis:
            raise ValueError("x_axis, y_axis, z_axisは必須です")

        self._validate_column(df, x_axis)
        self._validate_column(df, y_axis)
        self._validate_column(df, z_axis)

        logger.debug(
            "ヒートマップを作成中",
            x_axis=x_axis,
            y_axis=y_axis,
            z_axis=z_axis,
        )

        # データをピボットテーブル形式に変換
        pivot_df = df.pivot_table(
            index=y_axis,
            columns=x_axis,
            values=z_axis,
            aggfunc="mean",  # 重複がある場合は平均を取る
        )

        fig = go.Figure(
            data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns.tolist(),
                y=pivot_df.index.tolist(),
                colorscale=colorscale,
                hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis}: %{{y}}<br>{z_axis}: %{{z}}<br><extra></extra>",
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title=x_axis,
            yaxis_title=y_axis,
        )

        return self._apply_theme(fig)
