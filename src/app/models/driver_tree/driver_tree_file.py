"""ドライバーツリーファイルモデル。

このモジュールは、ドライバーツリー用のファイルデータを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.driver_tree.driver_tree_data_frame import DriverTreeDataFrame
    from app.models.project.project_file import ProjectFile
    from app.models.user_account.user_account import UserAccount


class DriverTreeFile(Base, TimestampMixin):
    """ドライバーツリーファイル。

    プロジェクトファイルから取り込んだドライバーツリー用データを管理します。

    Attributes:
        id: 主キー（UUID）
        project_file_id: プロジェクトファイルID（外部キー）
        sheet_name: シート名
        axis_config: 軸設定（推移/軸/値/利用しない）
        added_by: 追加者ユーザーID（外部キー、任意）
    """

    __tablename__ = "driver_tree_file"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_file.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="プロジェクトファイルID",
    )

    sheet_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="シート名",
    )

    axis_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="軸設定（推移/軸/値/利用しない）",
    )

    added_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="追加者ユーザーID",
    )

    # リレーションシップ
    project_file: Mapped["ProjectFile"] = relationship(
        "ProjectFile",
        back_populates="driver_tree_files",
    )

    data_frames: Mapped[list["DriverTreeDataFrame"]] = relationship(
        "DriverTreeDataFrame",
        back_populates="driver_tree_file",
        cascade="all, delete-orphan",
    )

    adder: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        foreign_keys=[added_by],
    )

    def __repr__(self) -> str:
        return f"<DriverTreeFile(id={self.id}, sheet_name={self.sheet_name})>"
