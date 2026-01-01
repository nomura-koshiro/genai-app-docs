"""ユーザーセッションモデル。

このモジュールは、ユーザーのログインセッションを管理するモデルを定義します。

主な機能:
    - セッション情報の管理
    - デバイス情報の記録
    - 強制ログアウト対応

テーブル設計:
    - テーブル名: user_session
    - プライマリキー: id (UUID)
    - 外部キー: user_id -> user_account.id
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class UserSession(Base):
    """ユーザーセッションモデル。

    ユーザーのログインセッションを管理します。

    Attributes:
        id (UUID): プライマリキー
        user_id (UUID): ユーザーID
        session_token_hash (str): セッショントークンハッシュ（SHA-256）
        ip_address (str | None): IPアドレス
        user_agent (str | None): ユーザーエージェント
        device_info (dict | None): デバイス情報
        login_at (datetime): ログイン日時
        last_activity_at (datetime): 最終アクティビティ日時
        expires_at (datetime): 有効期限
        is_active (bool): アクティブフラグ
        logout_at (datetime | None): ログアウト日時
        logout_reason (str | None): ログアウト理由

    インデックス:
        - idx_user_session_user_id: user_id
        - idx_user_session_active: (is_active, expires_at)
        - idx_user_session_token: session_token_hash
    """

    __tablename__ = "user_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        comment="ユーザーID（FK: user_account）",
    )

    session_token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="セッショントークンハッシュ（SHA-256）",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IPアドレス",
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="ユーザーエージェント",
    )

    device_info: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="デバイス情報（OS、ブラウザ等）",
    )

    login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="ログイン日時",
    )

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="最終アクティビティ日時",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="有効期限",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="アクティブフラグ",
    )

    logout_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="ログアウト日時",
    )

    logout_reason: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="ログアウト理由（MANUAL/FORCED/EXPIRED/SESSION_LIMIT）",
    )

    # リレーションシップ
    user: Mapped["UserAccount"] = relationship(
        "UserAccount",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    # インデックス定義
    __table_args__ = (
        Index("idx_user_session_user_id", "user_id"),
        Index("idx_user_session_active", "is_active", "expires_at"),
        Index("idx_user_session_token", "session_token_hash"),
    )

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
