"""通知テンプレートモデル。

このモジュールは、通知メッセージのテンプレートを管理するモデルを定義します。

主な機能:
    - イベント種別ごとのテンプレート管理
    - 変数置換のサポート
    - テンプレートの有効/無効管理

テーブル設計:
    - テーブル名: notification_template
    - プライマリキー: id (UUID)
"""

import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class NotificationTemplate(Base, TimestampMixin):
    """通知テンプレートモデル。

    通知メッセージのテンプレートを管理します。

    Attributes:
        id (UUID): プライマリキー
        name (str): テンプレート名
        event_type (str): イベント種別（PROJECT_CREATED/MEMBER_ADDED等）
        subject (str): 件名テンプレート
        body (str): 本文テンプレート
        variables (list): 利用可能変数リスト
        is_active (bool): 有効フラグ
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）
    """

    __tablename__ = "notification_template"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="テンプレート名",
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="イベント種別（PROJECT_CREATED/MEMBER_ADDED等）",
    )

    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="件名テンプレート",
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="本文テンプレート",
    )

    variables: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="利用可能変数リスト",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="有効フラグ",
    )

    def __repr__(self) -> str:
        return f"<NotificationTemplate(id={self.id}, event_type={self.event_type})>"
