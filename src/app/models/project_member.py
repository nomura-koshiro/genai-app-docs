"""プロジェクトメンバーシップ管理モデル。

このモジュールは、プロジェクトとユーザーの多対多関係とロールを管理します。

主な機能:
    - プロジェクトメンバーシップの管理
    - プロジェクトレベルのロール管理（PROJECT_MANAGER/PROJECT_MODERATOR/MEMBER/VIEWER）
    - メンバー追加者の追跡

テーブル設計:
    - テーブル名: project_members
    - プライマリキー: id (UUID)
    - ユニーク制約: (project_id, user_id)

使用例:
    >>> from app.models.project_member import ProjectMember, ProjectRole
    >>> member = ProjectMember(
    ...     project_id=project_id,
    ...     user_id=user_id,
    ...     role=ProjectRole.MEMBER,
    ...     added_by=admin_user_id
    ... )
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class ProjectRole(str, Enum):
    """プロジェクトレベルのロール定義。

    Attributes:
        PROJECT_MANAGER: プロジェクトマネージャー（最高権限）
            - プロジェクト削除
            - プロジェクト設定変更
            - メンバー追加・削除・ロール変更（全ロール）
            - ファイルのアップロード・ダウンロード・削除
        PROJECT_MODERATOR: 権限管理者（メンバー管理担当）
            - メンバー追加・削除
            - ロール変更（VIEWER/MEMBER/PROJECT_MODERATORのみ）
            - ファイルのアップロード・ダウンロード
            - プロジェクト内の編集
        MEMBER: 一般メンバー（編集可能）
            - ファイルのアップロード・ダウンロード
            - プロジェクト内の編集
        VIEWER: 閲覧者（閲覧のみ）
            - ファイルの閲覧・ダウンロードのみ
    """

    PROJECT_MANAGER = "project_manager"
    PROJECT_MODERATOR = "project_moderator"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectMember(Base):
    """プロジェクトメンバーシップモデル。

    プロジェクトとユーザーの多対多関係を管理し、
    プロジェクトレベルのロールを保持します。

    Attributes:
        id (UUID): プライマリキー（UUID）
        project_id (UUID): プロジェクトID（外部キー）
        user_id (UUID): ユーザーID（外部キー）
        role (ProjectRole): プロジェクトロール
        joined_at (datetime): 参加日時
        added_by (UUID | None): 追加者のユーザーID

    インデックス:
        - idx_project_members_project_id: project_id
        - idx_project_members_user_id: user_id
        - uq_project_user: (project_id, user_id) UNIQUE
    """

    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Project ID",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="User ID",
    )

    role: Mapped[ProjectRole] = mapped_column(
        SQLEnum(ProjectRole),
        nullable=False,
        default=ProjectRole.MEMBER,
        comment="Project role (project_manager/project_moderator/member/viewer)",
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        comment="Join timestamp",
    )

    added_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User ID who added this member",
    )

    # リレーションシップ
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="members",
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="project_memberships",
    )

    # インデックスとユニーク制約
    __table_args__ = (
        Index("idx_project_members_project_id", "project_id"),
        Index("idx_project_members_user_id", "user_id"),
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )

    def __repr__(self) -> str:
        """プロジェクトメンバーオブジェクトの文字列表現。

        Returns:
            str: "<ProjectMember(project_id=..., user_id=..., role=...)>" 形式

        Example:
            >>> member = ProjectMember(
            ...     project_id=uuid.uuid4(),
            ...     user_id=uuid.uuid4(),
            ...     role=ProjectRole.MEMBER
            ... )
            >>> print(repr(member))
            '<ProjectMember(project_id=..., user_id=..., role=member)>'
        """
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role={self.role.value})>"
