"""ドライバーツリーデータフレームモデル。

このモジュールは、ドライバーツリーのデータフレームを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree.driver_tree_file import DriverTreeFile
    from app.models.driver_tree.driver_tree_node import DriverTreeNode


class DriverTreeDataFrame(Base, TimestampMixin):
    """ドライバーツリーデータフレーム。

    ドライバーツリーファイルの列データをキャッシュとして管理します。

    Attributes:
        id: 主キー（UUID）
        driver_tree_file_id: ドライバーツリーファイルID（外部キー）
        column_name: 列名
        data: データ（キャッシュ）
    """

    __tablename__ = "driver_tree_data_frame"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    driver_tree_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("driver_tree_file.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ドライバーツリーファイルID",
    )

    column_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="列名",
    )

    data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="データ（キャッシュ）",
    )

    # リレーションシップ
    driver_tree_file: Mapped["DriverTreeFile"] = relationship(
        "DriverTreeFile",
        back_populates="data_frames",
    )

    node: Mapped["DriverTreeNode | None"] = relationship(
        "DriverTreeNode",
        back_populates="data_frame",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<DriverTreeDataFrame(id={self.id}, column_name={self.column_name})>"
