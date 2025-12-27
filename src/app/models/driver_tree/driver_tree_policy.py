"""ドライバーツリー施策モデル。

このモジュールは、ドライバーツリーノードに紐づく施策を管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree.driver_tree_node import DriverTreeNode


class DriverTreePolicy(Base, TimestampMixin):
    """ドライバーツリー施策。

    ドライバーツリーノードに紐づく施策を管理します。

    Attributes:
        id: 主キー（UUID）
        node_id: ノードID（外部キー）
        label: 施策ラベル
        value: 施策値
    """

    __tablename__ = "driver_tree_policy"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_node.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ノードID",
    )

    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="施策ラベル",
    )

    value: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
        comment="施策値",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="施策説明",
    )

    cost: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="コスト",
    )

    duration_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="実施期間（月）",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="planned",
        nullable=False,
        comment="状態（planned/in_progress/completed）",
    )

    # リレーションシップ
    node: Mapped["DriverTreeNode"] = relationship(
        "DriverTreeNode",
        back_populates="policies",
    )

    # インデックス
    __table_args__ = (Index("idx_driver_tree_policy_node_id", "node_id"),)

    def __repr__(self) -> str:
        return f"<DriverTreePolicy(id={self.id}, label={self.label})>"
