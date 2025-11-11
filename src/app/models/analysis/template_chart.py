"""分析テンプレートチャートモデル。

このモジュールは、分析テンプレートに関連するダミーチャートデータを管理します。
dummy/chart/*.json の内容をデータベースに格納します。

主な機能:
    - Plotly形式のチャートデータ保存
    - テンプレートとの関連付け
    - チャート表示順序の管理
    - チャート種別の分類

テーブル設計:
    - テーブル名: analysis_template_charts
    - プライマリキー: id (UUID)
    - 外部キー: template_id (analysis_templates)

使用例:
    >>> from app.models.analysis import AnalysisTemplateChart
    >>> chart = AnalysisTemplateChart(
    ...     template_id=template_id,
    ...     chart_name="不採算製品の撤退-利益改善効果",
    ...     chart_data={"data": [...], "layout": {...}},
    ...     chart_type="bar"
    ... )
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.template import AnalysisTemplate


class AnalysisTemplateChart(Base, TimestampMixin):
    """分析テンプレートチャートモデル。

    dummy/chart/*.json のPlotlyチャートデータをデータベースに格納します。
    各チャートは特定のテンプレートに紐づきます。

    Attributes:
        id (UUID): プライマリキー（UUID）
        template_id (UUID): テンプレートID（外部キー）
        chart_name (str): チャート名（ファイル名由来）
        chart_data (dict): Plotly形式のチャートデータ（JSONB）
            - data (list): チャートのデータ系列
            - layout (dict): レイアウト設定
            - config (dict): チャート設定
        chart_order (int): チャート表示順序
        chart_type (str | None): チャートタイプ（bar, line, pie等）
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    Relationships:
        template (AnalysisTemplate): 所属するテンプレート

    インデックス:
        - ix_analysis_template_charts_template: template_id
    """

    __tablename__ = "analysis_template_charts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Chart ID (Primary Key)",
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Template ID (Foreign Key)",
    )

    chart_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Chart name (from filename)",
    )

    chart_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Plotly chart data (data, layout, config)",
    )

    chart_order: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Display order for charts under same template",
    )

    chart_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Chart type (bar, line, pie, etc.)",
    )

    # リレーションシップ
    template: Mapped["AnalysisTemplate"] = relationship(
        "AnalysisTemplate",
        back_populates="charts",
    )

    def __repr__(self) -> str:
        """分析テンプレートチャートオブジェクトの文字列表現。

        Returns:
            str: "<AnalysisTemplateChart(id=..., chart_name=...)>" 形式

        Example:
            >>> chart = AnalysisTemplateChart(id=uuid.uuid4(), chart_name="利益改善効果")
            >>> print(repr(chart))
            '<AnalysisTemplateChart(id=..., chart_name=利益改善効果)>'
        """
        return f"<AnalysisTemplateChart(id={self.id}, chart_name={self.chart_name})>"
