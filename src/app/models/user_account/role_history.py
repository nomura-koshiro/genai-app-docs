"""ロール変更履歴モデル。

このモジュールは、ユーザーのロール変更を追跡するための履歴テーブルを定義します。
監査目的でロール変更を記録します。

主な機能:
    - ロール変更の完全な履歴追跡
    - 変更者（誰が変更したか）の記録
    - 変更前後のロール状態の保存
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RoleHistory(Base):
    """ロール変更履歴モデル。

    ユーザーのシステムロールおよびプロジェクトロールの変更履歴を記録します。
    監査証跡として使用されます。

    Attributes:
        id (UUID): 主キー
        user_id (UUID): 変更対象ユーザーID
        changed_by_id (UUID | None): 変更実行者のユーザーID（システム変更の場合はNone）
        action (str): 変更アクション（grant/revoke/update）
        role_type (str): ロール種別（system/project）
        project_id (UUID | None): プロジェクトロールの場合、対象プロジェクトID
        old_roles (list): 変更前のロール一覧
        new_roles (list): 変更後のロール一覧
        reason (str | None): 変更理由
        changed_at (datetime): 変更日時

    インデックス:
        - idx_role_history_user_id: ユーザーIDでの検索用
        - idx_role_history_changed_at: 時系列での検索用
    """

    __tablename__ = "role_history"

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
        comment="変更対象ユーザーID",
    )

    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="変更実行者のユーザーID",
    )

    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="変更アクション（grant/revoke/update）",
    )

    role_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="ロール種別（system/project）",
    )

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="SET NULL"),
        nullable=True,
        comment="プロジェクトロールの場合、対象プロジェクトID",
    )

    old_roles: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="変更前のロール一覧",
    )

    new_roles: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="変更後のロール一覧",
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="変更理由",
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="変更日時",
    )

    # リレーションシップ
    user = relationship(
        "UserAccount",
        foreign_keys=[user_id],
        backref="role_history",
    )

    changed_by = relationship(
        "UserAccount",
        foreign_keys=[changed_by_id],
    )

    project = relationship(
        "Project",
        foreign_keys=[project_id],
    )

    # インデックス
    __table_args__ = (
        Index("idx_role_history_user_id", "user_id"),
        Index("idx_role_history_changed_at", "changed_at"),
        Index("idx_role_history_project_id", "project_id"),
    )

    def __repr__(self) -> str:
        return f"<RoleHistory(id={self.id}, user_id={self.user_id}, action={self.action})>"
