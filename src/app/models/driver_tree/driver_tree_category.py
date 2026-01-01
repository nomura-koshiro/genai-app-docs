"""ドライバーツリーカテゴリマスタモデル。

このモジュールは、業界分類・業界名とドライバー型の対応関係を管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class DriverTreeCategory(Base, TimestampMixin):
    """ドライバーツリーカテゴリマスタ。

    業界分類・業界名とドライバー型の対応関係を管理します。

    Attributes:
        id: 主キー（UUID）
        category_id: 業界分類ID（UUID）
        category_name: 業界分類名
        industry_id: 業界名ID（UUID）
        industry_name: 業界名
        driver_type_id: ドライバー型ID（UUID）
        driver_type: ドライバー型
        description: カテゴリ説明
        created_by: 作成者ID

    Indexes:
        ix_category_industry: 業界名による検索を最適化
        ix_category_driver: ドライバー型IDによるJOINを最適化
    """

    __tablename__ = "driver_tree_category"

    __table_args__ = (
        Index("ix_category_industry", "industry_name"),
        Index("ix_category_driver", "driver_type_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="業界分類ID",
    )

    category_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="業界分類",
    )

    industry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="業界名ID",
    )

    industry_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="業界名",
    )

    driver_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="ドライバー型ID",
    )

    driver_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="ドライバー型",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="カテゴリ説明",
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="作成者ID",
    )

    # リレーションシップ
    creator: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        foreign_keys=[created_by],
    )

    def __repr__(self) -> str:
        """デバッグ用の文字列表現。"""
        return f"<DriverTreeCategory(id={self.id}, industry={self.industry_name}, driver_type={self.driver_type})>"
