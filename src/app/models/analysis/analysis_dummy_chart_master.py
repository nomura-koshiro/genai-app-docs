"""分析ダミーチャートマスタモデル。

このモジュールは、分析のダミーチャートマスタデータを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_issue_master import AnalysisIssueMaster


class AnalysisDummyChartMaster(Base, TimestampMixin):
    """分析ダミーチャートマスタ。

    分析におけるダミーチャートのマスタデータを管理します。

    Attributes:
        id: 主キー（UUID）
        issue_id: 課題マスタID（外部キー）
        chart: チャートデータ（バイナリ）
        chart_order: 表示順序
    """

    __tablename__ = "analysis_dummy_chart_master"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_issue_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="課題マスタID",
    )

    chart: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="チャートデータ",
    )

    chart_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="表示順序",
    )

    # リレーションシップ
    issue: Mapped["AnalysisIssueMaster"] = relationship(
        "AnalysisIssueMaster",
        back_populates="dummy_charts",
    )

    def __repr__(self) -> str:
        return f"<AnalysisDummyChartMaster(id={self.id}, chart_order={self.chart_order})>"
