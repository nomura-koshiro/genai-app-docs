"""システムお知らせモデル。

このモジュールは、システム全体のお知らせを管理するモデルを定義します。

主な機能:
    - お知らせの作成・管理
    - 表示期間の制御
    - 対象ロールの指定

テーブル設計:
    - テーブル名: system_announcement
    - プライマリキー: id (UUID)
    - 外部キー: created_by -> user_account.id
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class SystemAnnouncement(Base, TimestampMixin):
    """システムお知らせモデル。

    システム全体のお知らせを管理します。

    Attributes:
        id (UUID): プライマリキー
        title (str): タイトル
        content (str): 本文
        announcement_type (str): 種別（INFO/WARNING/MAINTENANCE）
        priority (int): 優先度（1が最高、デフォルト: 5）
        start_at (datetime): 表示開始日時
        end_at (datetime | None): 表示終了日時（NULLは無期限）
        is_active (bool): 有効フラグ
        target_roles (list | None): 対象ロール（NULLまたは空配列は全員）
        created_by (UUID): 作成者ID
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    インデックス:
        - idx_announcement_active: (is_active, start_at, end_at)
    """

    __tablename__ = "system_announcement"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="タイトル",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="本文",
    )

    announcement_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="種別（INFO/WARNING/MAINTENANCE）",
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="優先度（1が最高）",
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="表示開始日時",
    )

    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="表示終了日時（NULLは無期限）",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="有効フラグ",
    )

    target_roles: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="対象ロール（NULLまたは空配列は全員）",
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        comment="作成者ID",
    )

    # リレーションシップ
    creator: Mapped["UserAccount"] = relationship(
        "UserAccount",
        foreign_keys=[created_by],
        lazy="selectin",
    )

    # インデックス定義
    __table_args__ = (Index("idx_announcement_active", "is_active", "start_at", "end_at"),)

    def __repr__(self) -> str:
        return f"<SystemAnnouncement(id={self.id}, title={self.title})>"
