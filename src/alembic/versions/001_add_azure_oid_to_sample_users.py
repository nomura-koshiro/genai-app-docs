"""create azure ad authentication tables

Revision ID: 001
Revises:
Create Date: 2025-01-29 14:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Azure AD認証用のテーブルを作成します。

    作成するテーブル:
    - users: Azure AD認証用ユーザーテーブル
    - projects: プロジェクト管理テーブル
    - project_members: プロジェクトメンバーシップ（ユーザーとプロジェクトの多対多関係）
    - project_files: プロジェクトファイルメタデータテーブル

    これらのテーブルは既存のsample_usersとは独立したAzure AD専用のスキーマです。
    """
    # users テーブル作成
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("azure_oid", sa.String(255), nullable=False, comment="Azure AD Object ID"),
        sa.Column("email", sa.String(255), nullable=False, comment="Email address"),
        sa.Column("display_name", sa.String(255), nullable=True, comment="Display name"),
        sa.Column("roles", sa.JSON, nullable=False, comment="System-level roles (e.g., ['SystemAdmin', 'User'])"),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True, comment="Active flag"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="Created timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="Updated timestamp"),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True, comment="Last login timestamp"),
    )

    # users テーブルのインデックス作成
    op.create_index("idx_users_azure_oid", "users", ["azure_oid"], unique=True)
    op.create_index("idx_users_email", "users", ["email"], unique=True)

    # projects テーブル作成
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, comment="Project name"),
        sa.Column("code", sa.String(50), nullable=False, comment="Project code (unique identifier)"),
        sa.Column("description", sa.Text, nullable=True, comment="Project description"),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True, comment="Active flag"),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True, comment="Creator user ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="Created timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="Updated timestamp"),
    )

    # projects テーブルのインデックス作成
    op.create_index("idx_projects_code", "projects", ["code"], unique=True)

    # project_members テーブル作成
    op.create_table(
        "project_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False, comment="Project ID"),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, comment="User ID"),
        sa.Column(
            "role",
            sa.Enum("owner", "admin", "member", "viewer", name="projectrole"),
            nullable=False,
            comment="Project role (owner/admin/member/viewer)",
        ),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, comment="Join timestamp"),
        sa.Column("added_by", UUID(as_uuid=True), nullable=True, comment="User ID who added this member"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["added_by"], ["users.id"], ondelete="SET NULL"),
    )

    # project_members テーブルのインデックス作成
    op.create_index("idx_project_members_project_id", "project_members", ["project_id"])
    op.create_index("idx_project_members_user_id", "project_members", ["user_id"])
    op.create_unique_constraint("uq_project_user", "project_members", ["project_id", "user_id"])

    # project_files テーブル作成
    op.create_table(
        "project_files",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False, comment="Project ID"),
        sa.Column("filename", sa.String(255), nullable=False, comment="Stored filename"),
        sa.Column("original_filename", sa.String(255), nullable=False, comment="Original filename"),
        sa.Column("file_path", sa.String(512), nullable=False, comment="File path (Azure Blob Storage, etc.)"),
        sa.Column("file_size", sa.Integer, nullable=False, comment="File size in bytes"),
        sa.Column("mime_type", sa.String(100), nullable=True, comment="MIME type"),
        sa.Column("uploaded_by", UUID(as_uuid=True), nullable=False, comment="Uploader user ID"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, comment="Upload timestamp"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
    )

    # project_files テーブルのインデックス作成
    op.create_index("idx_project_files_project_id", "project_files", ["project_id"])


def downgrade() -> None:
    """Azure AD認証用のテーブルを削除します。

    ロールバック時にすべてのテーブルとインデックスを削除します。
    外部キー制約により、project_files → project_members → projects → users の順で削除します。
    """
    # project_files テーブル削除
    op.drop_index("idx_project_files_project_id", table_name="project_files")
    op.drop_table("project_files")

    # project_members テーブル削除
    op.drop_constraint("uq_project_user", "project_members", type_="unique")
    op.drop_index("idx_project_members_user_id", table_name="project_members")
    op.drop_index("idx_project_members_project_id", table_name="project_members")
    op.drop_table("project_members")

    # Enum型を削除
    op.execute("DROP TYPE IF EXISTS projectrole")

    # projects テーブル削除
    op.drop_index("idx_projects_code", table_name="projects")
    op.drop_table("projects")

    # users テーブル削除
    op.drop_index("idx_users_email", table_name="users")
    op.drop_index("idx_users_azure_oid", table_name="users")
    op.drop_table("users")
