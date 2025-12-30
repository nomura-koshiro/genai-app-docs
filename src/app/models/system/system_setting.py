"""システム設定モデル。

このモジュールは、アプリケーション全体の設定を管理するモデルを定義します。

主な機能:
    - カテゴリ別設定管理
    - 型情報の保持
    - 機密設定のフラグ管理

テーブル設計:
    - テーブル名: system_setting
    - プライマリキー: id (UUID)
    - ユニーク制約: (category, key)
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class SystemSetting(Base, TimestampMixin):
    """システム設定モデル。

    アプリケーション全体の設定値を管理します。

    Attributes:
        id (UUID): プライマリキー
        category (str): カテゴリ（GENERAL/SECURITY/MAINTENANCE）
        key (str): 設定キー
        value (dict): 設定値（JSONB）
        value_type (str): 値の型（STRING/NUMBER/BOOLEAN/JSON）
        description (str | None): 説明
        is_secret (bool): 機密設定フラグ
        is_editable (bool): 編集可能フラグ
        updated_by (UUID | None): 更新者ID
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    ユニーク制約:
        - uq_system_setting_category_key: (category, key)
    """

    __tablename__ = "system_setting"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="カテゴリ（GENERAL/SECURITY/MAINTENANCE）",
    )

    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="設定キー",
    )

    value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="設定値",
    )

    value_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="値の型（STRING/NUMBER/BOOLEAN/JSON）",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="説明",
    )

    is_secret: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="機密設定フラグ",
    )

    is_editable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="編集可能フラグ",
    )

    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="更新者ID",
    )

    # リレーションシップ
    updater: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        foreign_keys=[updated_by],
        lazy="selectin",
    )

    # ユニーク制約
    __table_args__ = (
        UniqueConstraint("category", "key", name="uq_system_setting_category_key"),
    )

    def __repr__(self) -> str:
        return (
            f"<SystemSetting(id={self.id}, category={self.category}, key={self.key})>"
        )
