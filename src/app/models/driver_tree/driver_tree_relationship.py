"""ドライバーツリーリレーションシップモデル。

このモジュールは、ドライバーツリーノード間の関係を管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree.driver_tree import DriverTree
    from app.models.driver_tree.driver_tree_node import DriverTreeNode
    from app.models.driver_tree.driver_tree_relationship_child import (
        DriverTreeRelationshipChild,
    )


class DriverTreeRelationship(Base, TimestampMixin):
    """ドライバーツリーリレーションシップ。

    ドライバーツリーの親ノードと子ノード群の関係を管理します。

    Attributes:
        id: 主キー（UUID）
        driver_tree_id: ドライバーツリーID（外部キー）
        parent_node_id: 親ノードID（外部キー）
        operator: 演算子（+, -, *, /）
    """

    __tablename__ = "driver_tree_relationship"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    driver_tree_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ドライバーツリーID",
    )

    parent_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_node.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="親ノードID",
    )

    operator: Mapped[str | None] = mapped_column(
        String(1),
        nullable=True,
        comment="演算子（+, -, *, /）",
    )

    # リレーションシップ
    driver_tree: Mapped["DriverTree"] = relationship(
        "DriverTree",
        back_populates="relationships",
    )

    parent_node: Mapped["DriverTreeNode"] = relationship(
        "DriverTreeNode",
        foreign_keys=[parent_node_id],
    )

    children: Mapped[list["DriverTreeRelationshipChild"]] = relationship(
        "DriverTreeRelationshipChild",
        back_populates="parent_relationship",
        cascade="all, delete-orphan",
        order_by="DriverTreeRelationshipChild.order_index",
    )

    # インデックス
    __table_args__ = (
        Index("idx_driver_tree_relationship_driver_tree_id", "driver_tree_id"),
        Index("idx_driver_tree_relationship_parent_node_id", "parent_node_id"),
    )

    def __repr__(self) -> str:
        return f"<DriverTreeRelationship(id={self.id}, operator={self.operator})>"
