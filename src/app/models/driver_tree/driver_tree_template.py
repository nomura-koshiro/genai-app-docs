"""ドライバーツリーテンプレートモデル。

このモジュールは、ドライバーツリーテンプレートを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree.driver_tree import DriverTree
    from app.models.project.project import Project
    from app.models.user_account.user_account import UserAccount


class DriverTreeTemplate(Base, TimestampMixin):
    """ドライバーツリーテンプレート。

    ツリー構造を再利用可能なテンプレートとして保存します。

    Attributes:
        id: 主キー（UUID）
        project_id: プロジェクトID（外部キー、NULLの場合はグローバルテンプレート）
        name: テンプレート名
        description: 説明
        category: カテゴリ（業種）
        template_config: テンプレート設定（JSONB、ノード・リレーション情報）
        source_tree_id: 元ツリーID（外部キー、任意）
        is_public: 公開フラグ
        usage_count: 使用回数
        created_by: 作成者ID（外部キー、任意）
    """

    __tablename__ = "driver_tree_template"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="プロジェクトID（NULLの場合はグローバルテンプレート）",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="テンプレート名",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="説明",
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="カテゴリ（業種）",
    )

    template_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="テンプレート設定（JSONB、ノード・リレーション情報）",
    )

    source_tree_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree.id", ondelete="SET NULL"),
        nullable=True,
        comment="元ツリーID",
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="公開フラグ",
    )

    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="使用回数",
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="作成者ID",
    )

    # リレーションシップ
    project: Mapped["Project | None"] = relationship(
        "Project",
        back_populates="driver_tree_templates",
    )

    source_tree: Mapped["DriverTree | None"] = relationship(
        "DriverTree",
        foreign_keys=[source_tree_id],
    )

    creator: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        foreign_keys=[created_by],
    )

    # インデックス
    __table_args__ = (
        Index("idx_driver_tree_template_project_id", "project_id"),
        Index("idx_driver_tree_template_category", "category"),
        Index("idx_driver_tree_template_public", "is_public"),
    )

    def __repr__(self) -> str:
        return f"<DriverTreeTemplate(id={self.id}, name='{self.name}')>"
