"""ドライバーツリーモデル。

このモジュールは、ドライバーツリー本体を管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree.driver_tree_formula import DriverTreeFormula
    from app.models.driver_tree.driver_tree_node import DriverTreeNode
    from app.models.driver_tree.driver_tree_relationship import DriverTreeRelationship
    from app.models.project.project import Project


class DriverTree(Base, TimestampMixin):
    """ドライバーツリー。

    プロジェクトに紐づくドライバーツリーを管理します。

    Attributes:
        id: 主キー（UUID）
        project_id: プロジェクトID（外部キー）
        name: ツリー名
        description: 説明
        root_node_id: ルートノードID（外部キー、任意）
        formula_id: 数式テンプレートID（外部キー、任意）
        status: ツリー状態（draft/active/completed）
    """

    __tablename__ = "driver_tree"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="プロジェクトID",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="ツリー名",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
        comment="説明",
    )

    root_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_node.id", ondelete="SET NULL"),
        nullable=True,
        comment="ルートノードID",
    )

    formula_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_formula.id", ondelete="SET NULL"),
        nullable=True,
        comment="数式テンプレートID",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
        comment="ツリー状態（draft/active/completed）",
    )

    # リレーションシップ
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="driver_trees",
    )

    root_node: Mapped["DriverTreeNode | None"] = relationship(
        "DriverTreeNode",
        foreign_keys=[root_node_id],
    )

    formula: Mapped["DriverTreeFormula | None"] = relationship(
        "DriverTreeFormula",
    )

    relationships: Mapped[list["DriverTreeRelationship"]] = relationship(
        "DriverTreeRelationship",
        back_populates="driver_tree",
        cascade="all, delete-orphan",
    )

    # インデックス・制約
    __table_args__ = (
        Index("idx_driver_tree_project_id", "project_id"),
        CheckConstraint(
            "status IN ('draft', 'active', 'completed')",
            name="ck_driver_tree_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<DriverTree(id={self.id}, project_id={self.project_id})>"
