"""プロジェクトファイル管理モデル。

このモジュールは、プロジェクトに関連付けられたファイルを管理します。

主な機能:
    - ファイルメタデータの管理
    - プロジェクトとの関連付け
    - アップロード者の追跡

テーブル設計:
    - テーブル名: project_files
    - プライマリキー: id (UUID)
    - 外部キー: project_id, uploaded_by

使用例:
    >>> from app.models.project.file import ProjectFile
    >>> file = ProjectFile(
    ...     project_id=project_id,
    ...     filename="document.pdf",
    ...     original_filename="important-document.pdf",
    ...     file_path="projects/proj-001/document.pdf",
    ...     file_size=1024000,
    ...     mime_type="application/pdf",
    ...     uploaded_by=user_id
    ... )
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.analysis.analysis_file import AnalysisFile
    from app.models.driver_tree.driver_tree_file import DriverTreeFile
    from app.models.project.project import Project
    from app.models.user_account.user_account import UserAccount


class ProjectFile(Base):
    """プロジェクトファイルモデル。

    プロジェクトに関連付けられたファイルのメタデータを管理します。

    Attributes:
        id (UUID): プライマリキー（UUID）
        project_id (UUID): プロジェクトID（外部キー）
        filename (str): 保存ファイル名
        original_filename (str): 元のファイル名
        file_path (str): ファイルパス（Azure Blob Storage等）
        file_size (int): ファイルサイズ（バイト）
        mime_type (str | None): MIMEタイプ
        uploaded_by (UUID): アップロード者のユーザーID
        uploaded_at (datetime): アップロード日時

    インデックス:
        - idx_project_files_project_id: project_id
    """

    __tablename__ = "project_file"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="プロジェクトID",
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="保存ファイル名",
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="元のファイル名",
    )

    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="ファイルパス（Azure Blob Storage等）",
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="ファイルサイズ（バイト）",
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="MIMEタイプ",
    )

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_account.id", ondelete="RESTRICT"),
        nullable=False,
        comment="アップロードユーザーID",
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        comment="アップロードタイムスタンプ",
    )

    # リレーションシップ
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="files",
    )

    uploader: Mapped["UserAccount"] = relationship(
        "UserAccount",
        foreign_keys=[uploaded_by],
    )

    analysis_files: Mapped[list["AnalysisFile"]] = relationship(
        "AnalysisFile",
        back_populates="project_file",
        cascade="all, delete-orphan",
    )

    driver_tree_files: Mapped[list["DriverTreeFile"]] = relationship(
        "DriverTreeFile",
        back_populates="project_file",
        cascade="all, delete-orphan",
    )

    # インデックス
    __table_args__ = (Index("idx_project_files_project_id", "project_id"),)

    def __repr__(self) -> str:
        """ファイルオブジェクトの文字列表現。

        Returns:
            str: "<ProjectFile(id=..., filename=...)>" 形式

        Example:
            >>> file = ProjectFile(id=uuid.uuid4(), filename="document.pdf")
            >>> print(repr(file))
            '<ProjectFile(id=..., filename=document.pdf)>'
        """
        return f"<ProjectFile(id={self.id}, filename={self.filename})>"
