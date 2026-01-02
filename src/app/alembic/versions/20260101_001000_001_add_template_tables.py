"""add_template_tables

Revision ID: 20260101_001000_001
Revises: 20251229_001000_001
Create Date: 2026-01-01 00:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260101_001000_001"
down_revision: str | None = "20251229_001000_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """テンプレートテーブル作成。"""
    # analysis_template テーブル作成
    op.create_table(
        "analysis_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False, comment="テンプレート名"),
        sa.Column("description", sa.Text(), nullable=True, comment="説明"),
        sa.Column("template_type", sa.String(length=50), nullable=False, comment="テンプレートタイプ（session/step）"),
        sa.Column("template_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment="テンプレート設定（JSONB）"),
        sa.Column("source_session_id", postgresql.UUID(as_uuid=True), nullable=True, comment="元セッションID"),
        sa.Column("is_public", sa.Boolean(), server_default="false", nullable=False, comment="公開フラグ"),
        sa.Column("usage_count", sa.Integer(), server_default="0", nullable=False, comment="使用回数"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True, comment="作成者ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["user_account.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_session_id"], ["analysis_session.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_analysis_template_project_id", "analysis_template", ["project_id"], unique=False)
    op.create_index("idx_analysis_template_type", "analysis_template", ["template_type"], unique=False)
    op.create_index("idx_analysis_template_public", "analysis_template", ["is_public"], unique=False)

    # driver_tree_template テーブル作成
    op.create_table(
        "driver_tree_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False, comment="テンプレート名"),
        sa.Column("description", sa.Text(), nullable=True, comment="説明"),
        sa.Column("category", sa.String(length=100), nullable=True, comment="カテゴリ（業種）"),
        sa.Column(
            "template_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="テンプレート設定（JSONB、ノード・リレーション情報）",
        ),
        sa.Column("source_tree_id", postgresql.UUID(as_uuid=True), nullable=True, comment="元ツリーID"),
        sa.Column("is_public", sa.Boolean(), server_default="false", nullable=False, comment="公開フラグ"),
        sa.Column("usage_count", sa.Integer(), server_default="0", nullable=False, comment="使用回数"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True, comment="作成者ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["user_account.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_tree_id"], ["driver_tree.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_driver_tree_template_project_id", "driver_tree_template", ["project_id"], unique=False)
    op.create_index("idx_driver_tree_template_category", "driver_tree_template", ["category"], unique=False)
    op.create_index("idx_driver_tree_template_public", "driver_tree_template", ["is_public"], unique=False)


def downgrade() -> None:
    """テンプレートテーブル削除。"""
    # インデックス削除
    op.drop_index("idx_driver_tree_template_public", table_name="driver_tree_template")
    op.drop_index("idx_driver_tree_template_category", table_name="driver_tree_template")
    op.drop_index("idx_driver_tree_template_project_id", table_name="driver_tree_template")
    op.drop_index("idx_analysis_template_public", table_name="analysis_template")
    op.drop_index("idx_analysis_template_type", table_name="analysis_template")
    op.drop_index("idx_analysis_template_project_id", table_name="analysis_template")

    # テーブル削除
    op.drop_table("driver_tree_template")
    op.drop_table("analysis_template")
