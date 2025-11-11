"""セッションモデル。

AIエージェントとの会話セッションを管理するモデル。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, UUID, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.sample.sample_user import SampleUser


class SampleSession(Base, PrimaryKeyMixin, TimestampMixin):
    """サンプル: セッションモデル。

    AIエージェントとの会話セッションを管理します。
    各セッションは複数のメッセージを持ち、ユーザーに紐付けられます（オプション）。

    Attributes:
        id: セッションID（主キー）
        session_id: 外部から参照するセッション識別子（一意）
        user_id: セッションの所有者（ゲストの場合はNone）
        session_metadata: セッションの追加情報（JSON）
        created_at: セッション作成日時
        updated_at: 最終更新日時
        messages: セッションに関連するメッセージのリスト
    """

    __tablename__ = "sample_sessions"

    # PrimaryKeyMixinからid継承
    # TimestampMixinからcreated_at, updated_at継承

    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sample_users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    session_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    # リレーションシップ
    user: Mapped["SampleUser | None"] = relationship("SampleUser", back_populates="sessions")
    messages: Mapped[list["SampleMessage"]] = relationship("SampleMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """デバッグ用の文字列表現。"""
        return f"<SampleSession(id={self.id}, session_id={self.session_id})>"


class SampleMessage(Base, PrimaryKeyMixin):
    """サンプル: メッセージモデル。

    セッション内の個別メッセージ（ユーザーまたはアシスタント）を管理します。

    Attributes:
        id: メッセージID（主キー）
        session_id: 所属するセッションID
        role: メッセージの役割（user/assistant/system）
        content: メッセージの内容
        tokens_used: 使用されたトークン数（オプション）
        model: 使用されたモデル名（オプション）
        created_at: メッセージ作成日時
    """

    __tablename__ = "sample_messages"

    # PrimaryKeyMixinからid継承
    # created_atのみ（updated_atは不要なのでTimestampMixinは使用しない）

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sample_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # リレーションシップ
    session: Mapped["SampleSession"] = relationship("SampleSession", back_populates="messages")

    def __repr__(self) -> str:
        """デバッグ用の文字列表現。"""
        return f"<SampleMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"
