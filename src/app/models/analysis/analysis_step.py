"""分析ステップモデル。

このモジュールは、分析セッションのステップを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_chat import AnalysisChat
    from app.models.analysis.analysis_snapshot import AnalysisSnapshot


class AnalysisStep(Base, TimestampMixin):
    """分析ステップ。

    分析セッションの各ステップを管理します。

    Attributes:
        id: 主キー（UUID）
        snapshot_id: スナップショットID（外部キー）
        triggered_by_chat_id: トリガーチャットID（外部キー、任意）
        config: ステップ設定（JSONB）
        name: ステップ名
        step_order: ステップ順序
        type: ステップタイプ
        input: 入力
    """

    __tablename__ = "analysis_step"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_snapshot.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="スナップショットID",
    )

    triggered_by_chat_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_chat.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="トリガーチャットID（このステップを生成したチャット）",
    )

    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="ステップ設定",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="ステップ名",
    )

    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="ステップ順序",
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="ステップタイプ",
    )

    input: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="入力",
    )

    # リレーションシップ
    snapshot: Mapped["AnalysisSnapshot"] = relationship(
        "AnalysisSnapshot",
        back_populates="steps",
    )

    triggered_by_chat: Mapped["AnalysisChat | None"] = relationship(
        "AnalysisChat",
        foreign_keys=[triggered_by_chat_id],
    )

    def __repr__(self) -> str:
        return f"<AnalysisStep(id={self.id}, name={self.name})>"
