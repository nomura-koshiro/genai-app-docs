"""Azure AD認証用のユーザーモデル。

このモジュールは、Azure AD認証に対応したユーザー管理モデルを定義します。

主な機能:
    - Azure AD Object IDによるユーザー識別
    - システムレベルのロール管理
    - プロジェクトメンバーシップとの関連

テーブル設計:
    - テーブル名: users
    - プライマリキー: id (UUID)
    - ユニーク制約: azure_oid, email

使用例:
    >>> from app.models.user import User
    >>> user = User(
    ...     azure_oid="azure-oid-12345",
    ...     email="user@company.com",
    ...     display_name="John Doe",
    ...     roles=["User"]
    ... )
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis_session import AnalysisSession
    from app.models.project_member import ProjectMember


class SystemRole(str, Enum):
    """システムレベルのロール定義。

    Attributes:
        SYSTEM_ADMIN: システム管理者（全プロジェクトアクセス可能、システム設定変更可能）
        USER: 一般ユーザー（デフォルト、プロジェクト単位でアクセス制御）
    """

    SYSTEM_ADMIN = "system_admin"
    USER = "user"


class User(Base, TimestampMixin):
    """Azure AD認証用ユーザーモデル。

    Azure AD Object IDをキーとしてユーザーを管理します。
    システムレベルのロールとプロジェクトメンバーシップを持ちます。

    Attributes:
        id (UUID): プライマリキー（UUID）
        azure_oid (str): Azure AD Object ID（一意識別子）
        email (str): メールアドレス（一意制約）
        display_name (str | None): 表示名
        roles (list): システムロール（例: ["SystemAdmin", "User"]）
        is_active (bool): アクティブフラグ
        created_at (datetime): 作成日時（UTC）
        updated_at (datetime): 更新日時（UTC）
        last_login (datetime | None): 最終ログイン日時

    インデックス:
        - idx_users_azure_oid: azure_oid（UNIQUE）
        - idx_users_email: email（UNIQUE）
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    azure_oid: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Azure AD Object ID",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Email address",
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Display name",
    )

    roles: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="System-level roles (e.g., ['SystemAdmin', 'User'])",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Active flag",
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last login timestamp",
    )

    # リレーションシップ
    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        foreign_keys="[ProjectMember.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    analysis_sessions: Mapped[list["AnalysisSession"]] = relationship(
        "AnalysisSession",
        foreign_keys="[AnalysisSession.created_by]",
        back_populates="creator",
    )

    # インデックス
    __table_args__ = (
        Index("idx_users_azure_oid", "azure_oid", unique=True),
        Index("idx_users_email", "email", unique=True),
    )

    def has_system_role(self, role: "SystemRole") -> bool:
        """指定されたシステムロールを持っているかチェックします。

        Args:
            role (SystemRole): チェックするシステムロール

        Returns:
            bool: ロールを持っている場合True

        Example:
            >>> user = User(roles=["system_admin"])
            >>> user.has_system_role(SystemRole.SYSTEM_ADMIN)
            True
        """
        return role.value in self.roles

    def is_system_admin(self) -> bool:
        """システム管理者かどうかをチェックします。

        Returns:
            bool: システム管理者の場合True

        Example:
            >>> user = User(roles=["system_admin"])
            >>> user.is_system_admin()
            True
        """
        return self.has_system_role(SystemRole.SYSTEM_ADMIN)

    def __repr__(self) -> str:
        """ユーザーオブジェクトの文字列表現。

        Returns:
            str: "<User(id=..., email=...)>" 形式

        Example:
            >>> user = User(id=uuid.uuid4(), email="user@example.com")
            >>> print(repr(user))
            '<User(id=..., email=user@example.com)>'
        """
        return f"<User(id={self.id}, email={self.email})>"
