"""プロジェクト管理モデル。

このモジュールは、プロジェクト情報を管理するモデルを定義します。

主な機能:
    - プロジェクト基本情報の管理
    - メンバーシップとファイルとの関連
    - アクティブ状態の管理

テーブル設計:
    - テーブル名: projects
    - プライマリキー: id (UUID)
    - ユニーク制約: code

使用例:
    >>> from app.models.project import Project
    >>> project = Project(
    ...     name="My Project",
    ...     code="PROJ-001",
    ...     description="Project description",
    ...     created_by=user_id
    ... )
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis.session import AnalysisSession
    from app.models.project_file import ProjectFile
    from app.models.project_member import ProjectMember


class Project(Base, TimestampMixin):
    """プロジェクトモデル。

    プロジェクトの基本情報、メンバー、ファイルを管理します。

    Attributes:
        id (UUID): プライマリキー（UUID）
        name (str): プロジェクト名
        code (str): プロジェクトコード（一意識別子）
        description (str | None): プロジェクト説明
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）
        created_by (UUID | None): 作成者のユーザーID

    インデックス:
        - idx_projects_code: code（UNIQUE）
    """

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Project name",
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Project code (unique identifier)",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Project description",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Active flag",
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Creator user ID",
    )

    # リレーションシップ
    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    files: Mapped[list["ProjectFile"]] = relationship(
        "ProjectFile",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    analysis_sessions: Mapped[list["AnalysisSession"]] = relationship(
        "AnalysisSession",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    # インデックス
    __table_args__ = (Index("idx_projects_code", "code", unique=True),)

    def __repr__(self) -> str:
        """プロジェクトオブジェクトの文字列表現。

        Returns:
            str: "<Project(id=..., code=...)>" 形式

        Example:
            >>> project = Project(id=uuid.uuid4(), code="PROJ-001")
            >>> print(repr(project))
            '<Project(id=..., code=PROJ-001)>'
        """
        return f"<Project(id={self.id}, code={self.code})>"
