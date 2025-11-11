"""ツリーマップ生成。

このモジュールは、ツリーマップの生成機能を提供します。
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from app.core.logging import get_logger
from app.services.analysis.agent.steps.summary.graphs.base import BaseGraph

logger = get_logger(__name__)


class TreemapGraph(BaseGraph):
    """ツリーマップ生成クラス。

    Example:
        >>> graph = TreemapGraph()
        >>> fig = graph.create(
        ...     df,
        ...     path=["地域", "商品"],
        ...     values="売上"
        ... )
    """

    def create(self, df: pd.DataFrame, **kwargs: Any) -> go.Figure:
        """ツリーマップを作成します。

        Args:
            df: データフレーム
            **kwargs: グラフパラメータ
                - path (list[str]): 階層を表す列名のリスト
                - values (str): 値の列名
                - title (str, optional): グラフタイトル

        Returns:
            go.Figure: Plotly Figure

        Raises:
            ValidationError: データまたはパラメータが不正な場合
        """
        self._validate_dataframe(df)

        path = kwargs.get("path")
        values = kwargs.get("values")
        title = kwargs.get("title", "ツリーマップ")

        if not path or not values:
            raise ValueError("pathとvaluesは必須です")

        if not isinstance(path, list) or len(path) == 0:
            raise ValueError("pathはリストで1つ以上の要素が必要です")

        for col in path:
            self._validate_column(df, col)
        self._validate_column(df, values)

        logger.debug(
            "ツリーマップを作成中",
            path=path,
            values=values,
        )

        # 階層構造の構築
        labels = []
        parents = []
        values_list = []

        # 各レベルのユニークな組み合わせを取得
        for i in range(len(path)):
            if i == 0:
                # 最上位レベル
                level_data = df.groupby(path[0])[values].sum().reset_index()
                labels.extend(level_data[path[0]].tolist())
                parents.extend([""] * len(level_data))
                values_list.extend(level_data[values].tolist())
            else:
                # 下位レベル
                group_cols = path[: i + 1]
                level_data = df.groupby(group_cols)[values].sum().reset_index()
                for _, row in level_data.iterrows():
                    labels.append(row[path[i]])
                    parents.append(row[path[i - 1]])
                    values_list.append(row[values])

        fig = go.Figure(
            data=[
                go.Treemap(
                    labels=labels,
                    parents=parents,
                    values=values_list,
                    textinfo="label+value+percent parent",
                    hovertemplate="<b>%{label}</b><br>" "値: %{value}<br>" "割合: %{percentParent}<br>" "<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title=title,
        )

        return self._apply_theme(fig)
