"""分析グラフ軸マスタモデル。

このモジュールは、分析グラフの軸設定マスタデータを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_issue_master import AnalysisIssueMaster


class AnalysisGraphAxisMaster(Base, TimestampMixin):
    """分析グラフ軸マスタ。

    分析グラフにおける軸設定のマスタデータを管理します。

    Attributes:
        id: 主キー（UUID）
        issue_id: 課題マスタID（外部キー）
        name: 軸名
        option: オプション
        multiple: 複数選択可否
        axis_order: 表示順序
    """

    __tablename__ = "analysis_graph_axis_master"

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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="軸名",
    )

    option: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="オプション",
    )

    multiple: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="複数選択可否",
    )

    axis_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="表示順序",
    )

    # リレーションシップ
    issue: Mapped["AnalysisIssueMaster"] = relationship(
        "AnalysisIssueMaster",
        back_populates="graph_axes",
    )

    def __repr__(self) -> str:
        return f"<AnalysisGraphAxisMaster(id={self.id}, name={self.name})>"
