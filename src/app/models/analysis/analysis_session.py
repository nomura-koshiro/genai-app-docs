"""分析セッションモデル。

このモジュールは、分析セッションを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_file import AnalysisFile
    from app.models.analysis.analysis_issue_master import AnalysisIssueMaster
    from app.models.analysis.analysis_snapshot import AnalysisSnapshot
    from app.models.project.project import Project
    from app.models.user_account.user_account import UserAccount


class AnalysisSession(Base, TimestampMixin):
    """分析セッション。

    分析セッションの情報を管理します。

    Attributes:
        id: 主キー（UUID）
        issue_id: 課題マスタID（外部キー）
        creator_id: 作成者ID（外部キー）
        project_id: プロジェクトID（外部キー）
        input_file_id: 入力ファイルID（外部キー、任意）
        current_snapshot: 現在のスナップショット番号
    """

    __tablename__ = "analysis_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_issue_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="課題マスタID",
    )

    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        comment="作成者ID",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="プロジェクトID",
    )

    input_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_file.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="入力ファイルID",
    )

    current_snapshot: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="現在のスナップショット番号",
    )

    # リレーションシップ
    issue: Mapped["AnalysisIssueMaster"] = relationship(
        "AnalysisIssueMaster",
        back_populates="sessions",
    )

    creator: Mapped["UserAccount"] = relationship(
        "UserAccount",
        back_populates="analysis_sessions",
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="analysis_sessions",
    )

    input_file: Mapped["AnalysisFile | None"] = relationship(
        "AnalysisFile",
        foreign_keys=[input_file_id],
    )

    files: Mapped[list["AnalysisFile"]] = relationship(
        "AnalysisFile",
        back_populates="session",
        foreign_keys="[AnalysisFile.session_id]",
        cascade="all, delete-orphan",
    )

    snapshots: Mapped[list["AnalysisSnapshot"]] = relationship(
        "AnalysisSnapshot",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AnalysisSnapshot.snapshot_order",
    )

    def __repr__(self) -> str:
        return f"<AnalysisSession(id={self.id}, project_id={self.project_id})>"
