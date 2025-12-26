"""分析ダミー数式マスタモデル。

このモジュールは、分析のダミー数式マスタデータを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_issue_master import AnalysisIssueMaster


class AnalysisDummyFormulaMaster(Base, TimestampMixin):
    """分析ダミー数式マスタ。

    分析におけるダミー数式のマスタデータを管理します。

    Attributes:
        id: 主キー（UUID）
        issue_id: 課題マスタID（外部キー）
        name: 数式名
        value: 数式値
        formula_order: 表示順序
    """

    __tablename__ = "analysis_dummy_formula_master"

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
        comment="数式名",
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="数式値",
    )

    formula_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="表示順序",
    )

    # リレーションシップ
    issue: Mapped["AnalysisIssueMaster"] = relationship(
        "AnalysisIssueMaster",
        back_populates="dummy_formulas",
    )

    def __repr__(self) -> str:
        return f"<AnalysisDummyFormulaMaster(id={self.id}, name={self.name})>"
