"""ドライバーツリーリレーションシップ子ノードモデル。

このモジュールは、ドライバーツリーリレーションシップの子ノードを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree.driver_tree_node import DriverTreeNode
    from app.models.driver_tree.driver_tree_relationship import DriverTreeRelationship


class DriverTreeRelationshipChild(Base, TimestampMixin):
    """ドライバーツリーリレーションシップ子ノード。

    ドライバーツリーリレーションシップの子ノードを管理します。

    Attributes:
        id: 主キー（UUID）
        relationship_id: リレーションシップID（外部キー）
        child_node_id: 子ノードID（外部キー）
        order_index: ノードの順番
    """

    __tablename__ = "driver_tree_relationship_child"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    relationship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_relationship.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="リレーションシップID",
    )

    child_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_node.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="子ノードID",
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="ノードの順番",
    )

    # リレーションシップ
    parent_relationship: Mapped["DriverTreeRelationship"] = relationship(
        "DriverTreeRelationship",
        back_populates="children",
    )

    child_node: Mapped["DriverTreeNode"] = relationship(
        "DriverTreeNode",
        foreign_keys=[child_node_id],
    )

    # インデックス
    __table_args__ = (
        Index("idx_driver_tree_relationship_child_relationship_id", "relationship_id"),
        Index("idx_driver_tree_relationship_child_child_node_id", "child_node_id"),
        Index(
            "idx_driver_tree_relationship_child_order",
            "relationship_id",
            "order_index",
        ),
    )

    def __repr__(self) -> str:
        return f"<DriverTreeRelationshipChild(id={self.id}, order_index={self.order_index})>"
