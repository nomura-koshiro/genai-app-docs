"""分析ファイルモデル。

このモジュールは、分析用のファイルデータを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_session import AnalysisSession
    from app.models.project.project_file import ProjectFile


class AnalysisFile(Base, TimestampMixin):
    """分析ファイル。

    プロジェクトファイルから取り込んだ分析用データを管理します。

    Attributes:
        id: 主キー（UUID）
        session_id: セッションID（外部キー）
        project_file_id: プロジェクトファイルID（外部キー）
        sheet_name: シート名
        axis_config: 軸設定（JSONB）
        data: データ（JSONB）
    """

    __tablename__ = "analysis_file"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="セッションID",
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
        comment="軸設定",
    )

    data: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        comment="データ",
    )

    # リレーションシップ
    session: Mapped["AnalysisSession"] = relationship(
        "AnalysisSession",
        foreign_keys=[session_id],
        back_populates="files",
    )

    project_file: Mapped["ProjectFile"] = relationship(
        "ProjectFile",
        back_populates="analysis_files",
    )

    def __repr__(self) -> str:
        return f"<AnalysisFile(id={self.id}, sheet_name={self.sheet_name})>"
