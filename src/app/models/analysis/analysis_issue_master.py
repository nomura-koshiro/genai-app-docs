"""分析課題マスタモデル。

このモジュールは、分析課題（issue）のマスタデータを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_dummy_chart_master import AnalysisDummyChartMaster
    from app.models.analysis.analysis_dummy_formula_master import (
        AnalysisDummyFormulaMaster,
    )
    from app.models.analysis.analysis_graph_axis_master import AnalysisGraphAxisMaster
    from app.models.analysis.analysis_session import AnalysisSession
    from app.models.analysis.analysis_validation_master import AnalysisValidationMaster


class AnalysisIssueMaster(Base, TimestampMixin):
    """分析課題マスタ。

    分析における課題項目のマスタデータを管理します。

    Attributes:
        id: 主キー（UUID）
        validation_id: 検証マスタID（外部キー）
        name: 課題名
        description: 説明
        agent_prompt: エージェントプロンプト
        initial_msg: 初期メッセージ
        dummy_hint: ダミーヒント
        dummy_input: ダミー入力データ
        issue_order: 表示順序
    """

    __tablename__ = "analysis_issue_master"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    validation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_validation_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="検証マスタID",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="課題名",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="説明",
    )

    agent_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="エージェントプロンプト",
    )

    initial_msg: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="初期メッセージ",
    )

    dummy_hint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="ダミーヒント",
    )

    dummy_input: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
        comment="ダミー入力データ",
    )

    issue_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="表示順序",
    )

    # リレーションシップ
    validation: Mapped["AnalysisValidationMaster"] = relationship(
        "AnalysisValidationMaster",
        back_populates="issues",
    )

    graph_axes: Mapped[list["AnalysisGraphAxisMaster"]] = relationship(
        "AnalysisGraphAxisMaster",
        back_populates="issue",
        cascade="all, delete-orphan",
    )

    dummy_formulas: Mapped[list["AnalysisDummyFormulaMaster"]] = relationship(
        "AnalysisDummyFormulaMaster",
        back_populates="issue",
        cascade="all, delete-orphan",
    )

    dummy_charts: Mapped[list["AnalysisDummyChartMaster"]] = relationship(
        "AnalysisDummyChartMaster",
        back_populates="issue",
        cascade="all, delete-orphan",
    )

    sessions: Mapped[list["AnalysisSession"]] = relationship(
        "AnalysisSession",
        back_populates="issue",
    )

    def __repr__(self) -> str:
        return f"<AnalysisIssueMaster(id={self.id}, name={self.name})>"
