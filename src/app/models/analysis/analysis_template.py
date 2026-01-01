"""分析セッションテンプレートモデル。

このモジュールは、分析セッションテンプレートを管理するモデルを定義します。
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.analysis_session import AnalysisSession
    from app.models.project.project import Project
    from app.models.user_account.user_account import UserAccount


class AnalysisTemplate(Base, TimestampMixin):
    """分析セッションテンプレート。

    セッションやステップ構成を再利用可能なテンプレートとして保存します。

    Attributes:
        id: 主キー（UUID）
        project_id: プロジェクトID（外部キー、NULLの場合はグローバルテンプレート）
        name: テンプレート名
        description: 説明
        template_type: テンプレートタイプ（session/step）
        template_config: テンプレート設定（JSONB）
        source_session_id: 元セッションID（外部キー、任意）
        is_public: 公開フラグ
        usage_count: 使用回数
        created_by: 作成者ID（外部キー、任意）
    """

    __tablename__ = "analysis_template"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="プロジェクトID（NULLの場合はグローバルテンプレート）",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="テンプレート名",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="説明",
    )

    template_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="テンプレートタイプ（session/step）",
    )

    template_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="テンプレート設定（JSONB）",
    )

    source_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_session.id", ondelete="SET NULL"),
        nullable=True,
        comment="元セッションID",
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="公開フラグ",
    )

    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="使用回数",
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="作成者ID",
    )

    # リレーションシップ
    project: Mapped["Project | None"] = relationship(
        "Project",
        back_populates="analysis_templates",
    )

    source_session: Mapped["AnalysisSession | None"] = relationship(
        "AnalysisSession",
        foreign_keys=[source_session_id],
    )

    creator: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        foreign_keys=[created_by],
    )

    # インデックス
    __table_args__ = (
        Index("idx_analysis_template_project_id", "project_id"),
        Index("idx_analysis_template_type", "template_type"),
        Index("idx_analysis_template_public", "is_public"),
    )

    def __repr__(self) -> str:
        return f"<AnalysisTemplate(id={self.id}, name='{self.name}')>"
