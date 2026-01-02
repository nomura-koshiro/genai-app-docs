"""分析セッションモデル。

このモジュールは、分析セッションを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
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
        name: セッション名
        issue_id: 課題マスタID（外部キー）
        creator_id: 作成者ID（外部キー、任意。ユーザー削除時にNULLになる）
        project_id: プロジェクトID（外部キー）
        input_file_id: 入力ファイルID（外部キー、任意）
        current_snapshot_id: 現在のスナップショットID（外部キー、任意）
        status: セッション状態（draft/active/completed/archived）
        custom_system_prompt: カスタムシステムプロンプト（任意）
        initial_message: 初期メッセージ（任意、セッション開始時に表示）
    """

    __tablename__ = "analysis_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        server_default="",
        comment="セッション名",
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_issue_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="課題マスタID",
    )

    creator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="作成者ID（ユーザー削除時にNULLになる）",
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

    current_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_snapshot.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
        index=True,
        comment="現在のスナップショットID",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
        comment="セッション状態（draft/active/completed/archived）",
    )

    # エージェント設定
    custom_system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="カスタムシステムプロンプト（デフォルトプロンプトに追加）",
    )

    initial_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="初期メッセージ（セッション開始時に表示）",
    )

    # テーブル制約
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'completed', 'archived')",
            name="ck_analysis_session_status",
        ),
    )

    # リレーションシップ
    issue: Mapped["AnalysisIssueMaster"] = relationship(
        "AnalysisIssueMaster",
        back_populates="sessions",
    )

    creator: Mapped["UserAccount | None"] = relationship(
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

    current_snapshot: Mapped["AnalysisSnapshot | None"] = relationship(
        "AnalysisSnapshot",
        foreign_keys=[current_snapshot_id],
        post_update=True,
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
        foreign_keys="[AnalysisSnapshot.session_id]",
        cascade="all, delete-orphan",
        order_by="AnalysisSnapshot.snapshot_order",
    )

    def __repr__(self) -> str:
        return f"<AnalysisSession(id={self.id}, project_id={self.project_id})>"
