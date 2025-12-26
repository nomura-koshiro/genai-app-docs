"""分析チャットモデル。

このモジュールは、分析セッションのチャット履歴を管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_snapshot import AnalysisSnapshot


class AnalysisChat(Base, TimestampMixin):
    """分析チャット。

    分析セッションのチャット履歴を管理します。

    Attributes:
        id: 主キー（UUID）
        snapshot_id: スナップショットID（外部キー）
        chat_order: チャット順序
        role: ロール（user/assistant）
        message: メッセージ内容
    """

    __tablename__ = "analysis_chat"

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

    chat_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="チャット順序",
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="ロール（user/assistant）",
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="メッセージ内容",
    )

    # リレーションシップ
    snapshot: Mapped["AnalysisSnapshot"] = relationship(
        "AnalysisSnapshot",
        back_populates="chats",
    )

    def __repr__(self) -> str:
        return f"<AnalysisChat(id={self.id}, role={self.role})>"
