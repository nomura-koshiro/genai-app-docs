"""create analysis tables

Revision ID: 002
Revises: 001
Create Date: 2025-11-05 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """分析機能用のテーブルを作成します。

    作成するテーブル:
    - analysis_sessions: 分析セッション管理テーブル
    - analysis_steps: 分析ステップ管理テーブル
    - analysis_files: 分析ファイルメタデータテーブル

    これらのテーブルは、AIエージェントによるデータ分析機能を提供します。
    """
    # analysis_sessions テーブル作成
    op.create_table(
        "analysis_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, comment="Session ID (Primary Key)"),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            nullable=False,
            comment="Project ID (Foreign Key)",
        ),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            nullable=True,
            comment="Creator user ID (Foreign Key)",
        ),
        sa.Column("session_name", sa.String(255), nullable=True, comment="Session name"),
        sa.Column(
            "validation_config",
            JSONB,
            nullable=False,
            comment="Validation configuration from validation.yml",
        ),
        sa.Column(
            "chat_history",
            JSONB,
            nullable=False,
            comment="Chat history with AI agent",
        ),
        sa.Column(
            "snapshot_history",
            JSONB,
            nullable=True,
            comment="Snapshot history (list of step states)",
        ),
        sa.Column(
            "original_file_id",
            UUID(as_uuid=True),
            nullable=True,
            comment="Currently selected file ID",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True, comment="Active flag"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, comment="Created timestamp"
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, comment="Updated timestamp"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )

    # analysis_sessions テーブルのインデックス作成
    op.create_index("idx_analysis_sessions_project", "analysis_sessions", ["project_id"])
    op.create_index("idx_analysis_sessions_created_by", "analysis_sessions", ["created_by"])

    # analysis_steps テーブル作成
    op.create_table(
        "analysis_steps",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, comment="Step ID (Primary Key)"),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            nullable=False,
            comment="Session ID (Foreign Key)",
        ),
        sa.Column("step_name", sa.String(255), nullable=False, comment="Step name (user-friendly)"),
        sa.Column(
            "step_type",
            sa.String(50),
            nullable=False,
            comment="Step type: filter/aggregate/transform/summary",
        ),
        sa.Column(
            "step_order",
            sa.Integer,
            nullable=False,
            comment="Step order (0-indexed)",
        ),
        sa.Column(
            "data_source",
            sa.String(100),
            nullable=False,
            comment="Data source: original/step_0/step_1/...",
        ),
        sa.Column(
            "config",
            JSONB,
            nullable=False,
            comment="Step configuration (type-specific structure)",
        ),
        sa.Column(
            "result_data_path",
            sa.Text,
            nullable=True,
            comment="Result data storage path (CSV file path)",
        ),
        sa.Column(
            "result_chart",
            JSONB,
            nullable=True,
            comment="Result chart (Plotly JSON format)",
        ),
        sa.Column(
            "result_formula",
            JSONB,
            nullable=True,
            comment="Result formulas (list of calculation results)",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True, comment="Active flag"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, comment="Created timestamp"
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, comment="Updated timestamp"
        ),
        sa.ForeignKeyConstraint(["session_id"], ["analysis_sessions.id"], ondelete="CASCADE"),
    )

    # analysis_steps テーブルのインデックス作成
    op.create_index("idx_analysis_steps_session", "analysis_steps", ["session_id"])
    op.create_index("idx_analysis_steps_order", "analysis_steps", ["session_id", "step_order"])

    # analysis_files テーブル作成
    op.create_table(
        "analysis_files",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, comment="File ID (Primary Key)"),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            nullable=False,
            comment="Session ID (Foreign Key)",
        ),
        sa.Column(
            "uploaded_by",
            UUID(as_uuid=True),
            nullable=True,
            comment="Uploader user ID (Foreign Key)",
        ),
        sa.Column("file_name", sa.String(255), nullable=False, comment="Original file name"),
        sa.Column("table_name", sa.String(255), nullable=False, comment="Table name (user-defined)"),
        sa.Column(
            "storage_path",
            sa.Text,
            nullable=False,
            comment="Storage path in Blob Storage",
        ),
        sa.Column("file_size", sa.BigInteger, nullable=False, comment="File size in bytes"),
        sa.Column(
            "content_type",
            sa.String(100),
            nullable=True,
            comment="MIME type (e.g., application/vnd.ms-excel)",
        ),
        sa.Column(
            "table_axis",
            ARRAY(sa.String),
            nullable=True,
            comment="Table axis candidates (e.g., ['地域', '商品'])",
        ),
        sa.Column(
            "metadata",
            JSONB,
            nullable=True,
            comment="Additional metadata (sheet_name, row_count, etc.)",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True, comment="Active flag"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, comment="Created timestamp"
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, comment="Updated timestamp"
        ),
        sa.ForeignKeyConstraint(["session_id"], ["analysis_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
    )

    # analysis_files テーブルのインデックス作成
    op.create_index("idx_analysis_files_session", "analysis_files", ["session_id"])
    op.create_index("idx_analysis_files_uploaded_by", "analysis_files", ["uploaded_by"])


def downgrade() -> None:
    """分析機能用のテーブルを削除します。

    ロールバック時にすべてのテーブルとインデックスを削除します。
    外部キー制約により、analysis_files → analysis_steps → analysis_sessions の順で削除します。
    """
    # analysis_files テーブル削除
    op.drop_index("idx_analysis_files_uploaded_by", table_name="analysis_files")
    op.drop_index("idx_analysis_files_session", table_name="analysis_files")
    op.drop_table("analysis_files")

    # analysis_steps テーブル削除
    op.drop_index("idx_analysis_steps_order", table_name="analysis_steps")
    op.drop_index("idx_analysis_steps_session", table_name="analysis_steps")
    op.drop_table("analysis_steps")

    # analysis_sessions テーブル削除
    op.drop_index("idx_analysis_sessions_created_by", table_name="analysis_sessions")
    op.drop_index("idx_analysis_sessions_project", table_name="analysis_sessions")
    op.drop_table("analysis_sessions")
