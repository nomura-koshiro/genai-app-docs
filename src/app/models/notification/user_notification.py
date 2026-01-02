"""ユーザー通知モデル。

このモジュールは、ユーザー向け通知を管理するモデルを定義します。

主な機能:
    - 通知の作成・管理
    - 既読/未読管理
    - 通知タイプ別の管理
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserNotification(Base, TimestampMixin):
    """ユーザー通知モデル。

    ユーザー向けの通知を管理します。

    Attributes:
        id (UUID): プライマリキー
        user_id (UUID): 通知対象ユーザーID
        type (str): 通知タイプ
        title (str): 通知タイトル
        message (str | None): 通知メッセージ
        icon (str | None): アイコン
        link_url (str | None): リンクURL
        reference_type (str | None): 参照タイプ
        reference_id (UUID | None): 参照ID
        is_read (bool): 既読フラグ
        read_at (datetime | None): 既読日時
    """

    __tablename__ = "user_notification"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="通知対象ユーザーID",
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="通知タイプ",
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="通知タイトル",
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="通知メッセージ",
    )

    icon: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="アイコン",
    )

    link_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="リンクURL",
    )

    reference_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="参照タイプ",
    )

    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="参照ID",
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="既読フラグ",
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="既読日時",
    )

    # リレーションシップ
    user = relationship("UserAccount", backref="notifications")

    def __repr__(self) -> str:
        """通知オブジェクトの文字列表現。"""
        return f"<UserNotification(id={self.id}, user_id={self.user_id}, type={self.type})>"
