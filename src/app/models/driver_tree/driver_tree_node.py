"""ドライバーツリーノードモデル。

このモジュールは、ドライバーツリーのノードを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree.driver_tree_data_frame import DriverTreeDataFrame
    from app.models.driver_tree.driver_tree_policy import DriverTreePolicy


class DriverTreeNode(Base, TimestampMixin):
    """ドライバーツリーノード。

    ドライバーツリーの各ノードを管理します。

    Attributes:
        id: 主キー（UUID）
        label: ノードラベル
        position_x: X座標
        position_y: Y座標
        node_type: ノードタイプ（計算/入力/定数）
        data_frame_id: データフレームID（外部キー、任意）
    """

    __tablename__ = "driver_tree_node"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="ノードラベル",
    )

    position_x: Mapped[int | None] = mapped_column(
        Integer,
        default=0,
        nullable=True,
        comment="X座標",
    )

    position_y: Mapped[int | None] = mapped_column(
        Integer,
        default=0,
        nullable=True,
        comment="Y座標",
    )

    node_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="ノードタイプ（計算/入力/定数）",
    )

    data_frame_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_data_frame.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="データフレームID",
    )

    # リレーションシップ
    data_frame: Mapped["DriverTreeDataFrame | None"] = relationship(
        "DriverTreeDataFrame",
        back_populates="node",
    )

    policies: Mapped[list["DriverTreePolicy"]] = relationship(
        "DriverTreePolicy",
        back_populates="node",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DriverTreeNode(id={self.id}, label={self.label})>"
