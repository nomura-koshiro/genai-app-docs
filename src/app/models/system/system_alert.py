"""システムアラート設定モデル。

このモジュールは、システム監視アラートの設定を管理するモデルを定義します。

主な機能:
    - 条件ベースのアラート設定
    - 通知チャネルの指定
    - 発火履歴の追跡

テーブル設計:
    - テーブル名: system_alert
    - プライマリキー: id (UUID)
    - 外部キー: created_by -> user_account.id
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class SystemAlert(Base, TimestampMixin):
    """システムアラート設定モデル。

    システム監視アラートの設定を管理します。

    Attributes:
        id (UUID): プライマリキー
        name (str): アラート名
        condition_type (str): 条件種別
        threshold (dict): 閾値設定
        comparison_operator (str): 比較演算子
        notification_channels (list): 通知先
        is_enabled (bool): 有効フラグ
        last_triggered_at (datetime | None): 最終発火日時
        trigger_count (int): 発火回数
        created_by (UUID): 作成者ID
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）
    """

    __tablename__ = "system_alert"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="アラート名",
    )

    condition_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="条件種別（ERROR_RATE/STORAGE_USAGE等）",
    )

    threshold: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="閾値設定",
    )

    comparison_operator: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="比較演算子（GT/GTE/LT/LTE/EQ）",
    )

    notification_channels: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="通知先（EMAIL/SLACK等）",
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="有効フラグ",
    )

    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最終発火日時",
    )

    trigger_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="発火回数",
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="作成者ID",
    )

    # リレーションシップ
    creator: Mapped["UserAccount"] = relationship(
        "UserAccount",
        foreign_keys=[created_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<SystemAlert(id={self.id}, name={self.name})>"
