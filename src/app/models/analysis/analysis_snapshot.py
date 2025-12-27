"""分析スナップショットモデル。

このモジュールは、分析セッションのスナップショットを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_chat import AnalysisChat
    from app.models.analysis.analysis_session import AnalysisSession
    from app.models.analysis.analysis_step import AnalysisStep


class AnalysisSnapshot(Base, TimestampMixin):
    """分析スナップショット。

    分析セッションの状態スナップショットを管理します。

    Attributes:
        id: 主キー（UUID）
        session_id: セッションID（外部キー）
        parent_snapshot_id: 親スナップショットID（外部キー、分岐履歴用）
        snapshot_order: スナップショット順序
    """

    __tablename__ = "analysis_snapshot"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="セッションID",
    )

    parent_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_snapshot.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="親スナップショットID（分岐履歴用）",
    )

    snapshot_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="スナップショット順序",
    )

    # リレーションシップ
    session: Mapped["AnalysisSession"] = relationship(
        "AnalysisSession",
        back_populates="snapshots",
    )

    parent_snapshot: Mapped["AnalysisSnapshot | None"] = relationship(
        "AnalysisSnapshot",
        remote_side=[id],
        foreign_keys=[parent_snapshot_id],
        backref="child_snapshots",
    )

    chats: Mapped[list["AnalysisChat"]] = relationship(
        "AnalysisChat",
        back_populates="snapshot",
        cascade="all, delete-orphan",
        order_by="AnalysisChat.chat_order",
    )

    steps: Mapped[list["AnalysisStep"]] = relationship(
        "AnalysisStep",
        back_populates="snapshot",
        cascade="all, delete-orphan",
        order_by="AnalysisStep.step_order",
    )

    def __repr__(self) -> str:
        return f"<AnalysisSnapshot(id={self.id}, snapshot_order={self.snapshot_order})>"
