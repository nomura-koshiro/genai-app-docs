"""監査ログモデル。

このモジュールは、データ変更・アクセス・セキュリティイベントの監査ログを定義します。

主な機能:
    - データ変更履歴の追跡（old_value/new_value）
    - アクセスログの記録
    - セキュリティイベントの記録

テーブル設計:
    - テーブル名: audit_log
    - プライマリキー: id (UUID)
    - 外部キー: user_id -> user_account.id
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums.admin_enums import AuditSeverity

if TYPE_CHECKING:
    from app.models.user_account.user_account import UserAccount


class AuditLog(Base, TimestampMixin):
    """監査ログモデル。

    データ変更、アクセス、セキュリティイベントを記録します。

    Attributes:
        id (UUID): プライマリキー
        user_id (UUID | None): 操作ユーザーID
        event_type (str): イベント種別（DATA_CHANGE/ACCESS/SECURITY）
        action (str): アクション（CREATE/UPDATE/DELETE/LOGIN_SUCCESS/LOGIN_FAILED等）
        resource_type (str): リソース種別
        resource_id (UUID | None): リソースID
        old_value (dict | None): 変更前の値
        new_value (dict | None): 変更後の値
        changed_fields (list | None): 変更されたフィールド一覧
        ip_address (str | None): IPアドレス
        user_agent (str | None): ユーザーエージェント
        severity (str): 重要度（INFO/WARNING/CRITICAL）
        metadata (dict | None): 追加メタデータ
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）

    インデックス:
        - idx_audit_log_user_id: user_id
        - idx_audit_log_event_type: event_type
        - idx_audit_log_resource: (resource_type, resource_id)
        - idx_audit_log_severity: severity
        - idx_audit_log_created_at: created_at DESC
    """

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="操作ユーザーID",
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="イベント種別（DATA_CHANGE/ACCESS/SECURITY）",
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="アクション（CREATE/UPDATE/DELETE/LOGIN_SUCCESS/LOGIN_FAILED等）",
    )

    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="リソース種別",
    )

    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="リソースID",
    )

    old_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="変更前の値",
    )

    new_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="変更後の値",
    )

    changed_fields: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="変更されたフィールド一覧",
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

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AuditSeverity.INFO.value,
        comment="重要度（INFO/WARNING/CRITICAL）",
    )

    extra_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="追加メタデータ",
    )

    # リレーションシップ
    user: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    # インデックス定義
    __table_args__ = (
        Index("idx_audit_log_user_id", "user_id"),
        Index("idx_audit_log_event_type", "event_type"),
        Index("idx_audit_log_resource", "resource_type", "resource_id"),
        Index("idx_audit_log_severity", "severity"),
        Index(
            "idx_audit_log_created_at",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, event={self.event_type}, action={self.action})>"
        )
