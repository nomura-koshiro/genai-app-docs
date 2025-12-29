"""API-フロントエンドギャップ対応: 新規カラム追加

このマイグレーションは、フロントエンドUIに必要だがバックエンドAPIに
存在しなかったフィールドを追加します。

追加されるカラム:
- analysis_session.name: セッション名
- driver_tree_category.description: カテゴリ説明
- driver_tree_category.created_by: 作成者ID（FK: user_account.id）
- project.start_date: プロジェクト開始日
- project.end_date: プロジェクト終了日
- project.budget: プロジェクト予算
- project_member.last_activity_at: プロジェクト内最終活動日時

Revision ID: 001
Revises: None (初回マイグレーション)
Create Date: 2025-12-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """アップグレードマイグレーション。

    API-フロントエンドギャップを解消するための新規カラムを追加します。
    """
    # ===== analysis_session テーブル =====
    # セッション名カラムを追加
    op.add_column(
        "analysis_session",
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
            server_default="",
            comment="セッション名",
        ),
    )

    # ===== driver_tree_category テーブル =====
    # カテゴリ説明カラムを追加
    op.add_column(
        "driver_tree_category",
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="カテゴリ説明",
        ),
    )

    # 作成者IDカラムを追加（外部キー付き）
    op.add_column(
        "driver_tree_category",
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="作成者ID",
        ),
    )

    # 作成者への外部キー制約を追加
    op.create_foreign_key(
        "fk_driver_tree_category_created_by",
        "driver_tree_category",
        "user_account",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # ===== project テーブル =====
    # プロジェクト開始日カラムを追加
    op.add_column(
        "project",
        sa.Column(
            "start_date",
            sa.Date(),
            nullable=True,
            comment="プロジェクト開始日",
        ),
    )

    # プロジェクト終了日カラムを追加
    op.add_column(
        "project",
        sa.Column(
            "end_date",
            sa.Date(),
            nullable=True,
            comment="プロジェクト終了日",
        ),
    )

    # プロジェクト予算カラムを追加
    op.add_column(
        "project",
        sa.Column(
            "budget",
            sa.Numeric(precision=15, scale=2),
            nullable=True,
            comment="プロジェクト予算",
        ),
    )

    # ===== project_member テーブル =====
    # 最終活動日時カラムを追加
    op.add_column(
        "project_member",
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="プロジェクト内最終活動日時",
        ),
    )


def downgrade() -> None:
    """ダウングレードマイグレーション。

    追加したカラムを削除してマイグレーション前の状態に戻します。
    """
    # ===== project_member テーブル =====
    op.drop_column("project_member", "last_activity_at")

    # ===== project テーブル =====
    op.drop_column("project", "budget")
    op.drop_column("project", "end_date")
    op.drop_column("project", "start_date")

    # ===== driver_tree_category テーブル =====
    # 外部キー制約を先に削除
    op.drop_constraint(
        "fk_driver_tree_category_created_by",
        "driver_tree_category",
        type_="foreignkey",
    )
    op.drop_column("driver_tree_category", "created_by")
    op.drop_column("driver_tree_category", "description")

    # ===== analysis_session テーブル =====
    op.drop_column("analysis_session", "name")
