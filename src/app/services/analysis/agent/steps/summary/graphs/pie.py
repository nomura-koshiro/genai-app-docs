"""円グラフ生成。

このモジュールは、円グラフの生成機能を提供します。
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.logging import get_logger
from app.services.analysis.agent.steps.summary.graphs.base import BaseGraph

logger = get_logger(__name__)


class PieGraph(BaseGraph):
    """円グラフ生成クラス。

    Example:
        >>> graph = PieGraph()
        >>> fig = graph.create(
        ...     df,
        ...     values="売上",
        ...     names="商品"
        ... )
    """

    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """円グラフを作成します。

        Args:
            df: データフレーム
            **kwargs: グラフパラメータ
                - values (str): 値の列名
                - names (str): ラベルの列名
                - title (str, optional): グラフタイトル
                - hole (float, optional): ドーナツグラフの穴のサイズ (0.0-1.0), デフォルト: 0

        Returns:
            go.Figure: Plotly Figure

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        self._validate_dataframe(df)

        values = kwargs.get("values")
        names = kwargs.get("names")
        title = kwargs.get("title", "円グラフ")
        hole = kwargs.get("hole", 0)

        if not values or not names:
            raise ValueError("valuesとnamesは必須です")

        self._validate_column(df, values)
        self._validate_column(df, names)

        logger.debug(
            "円グラフを作成中",
            values=values,
            names=names,
            hole=hole,
        )

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df[names],
                    values=df[values],
                    hole=hole,
                    hovertemplate="<b>%{label}</b><br>" "%{value}<br>" "%{percent}<br>" "<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title=title,
        )

        return self._apply_theme(fig)
