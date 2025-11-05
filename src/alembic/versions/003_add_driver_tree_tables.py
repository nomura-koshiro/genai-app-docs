"""add driver tree tables

Revision ID: 003
Revises: 002
Create Date: 2025-11-05 14:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Driver Tree機能用のテーブルを作成します。

    作成するテーブル:
    - driver_tree_nodes: ドライバーツリーのノード管理テーブル
    - driver_trees: ドライバーツリー管理テーブル
    - driver_tree_children: ツリーと子ノードの関連テーブル（多対多）
    - driver_tree_categories: 業種別テンプレート管理テーブル

    これらのテーブルは、KPI分解ツリー機能を提供します。
    """
    # driver_tree_nodes テーブル作成
    op.create_table(
        "driver_tree_nodes",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            comment="ノードの一意識別子",
        ),
        sa.Column(
            "label",
            sa.String(100),
            nullable=False,
            comment="ノードのラベル（KPI名や計算要素名）",
        ),
        sa.Column(
            "x",
            sa.Integer,
            nullable=True,
            comment="X座標（ツリー表示用）",
        ),
        sa.Column(
            "y",
            sa.Integer,
            nullable=True,
            comment="Y座標（ツリー表示用）",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="作成日時",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="更新日時",
        ),
    )

    # driver_tree_nodes テーブルのインデックス作成
    op.create_index(
        "idx_driver_tree_nodes_label",
        "driver_tree_nodes",
        ["label"],
    )

    # driver_trees テーブル作成
    op.create_table(
        "driver_trees",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            comment="ツリーの一意識別子",
        ),
        sa.Column(
            "root_node_id",
            UUID(as_uuid=True),
            nullable=False,
            comment="ルートノードID",
        ),
        sa.Column(
            "operator",
            sa.String(10),
            nullable=True,
            comment="演算子（+, -, *, /, %など）",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="作成日時",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="更新日時",
        ),
        sa.ForeignKeyConstraint(
            ["root_node_id"],
            ["driver_tree_nodes.id"],
            ondelete="CASCADE",
        ),
    )

    # driver_trees テーブルのインデックス作成
    op.create_index(
        "idx_driver_trees_root_node",
        "driver_trees",
        ["root_node_id"],
    )

    # driver_tree_children テーブル作成（多対多関連テーブル）
    op.create_table(
        "driver_tree_children",
        sa.Column(
            "driver_tree_id",
            UUID(as_uuid=True),
            nullable=False,
            comment="ドライバーツリーID",
        ),
        sa.Column(
            "child_node_id",
            UUID(as_uuid=True),
            nullable=False,
            comment="子ノードID",
        ),
        sa.ForeignKeyConstraint(
            ["driver_tree_id"],
            ["driver_trees.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["child_node_id"],
            ["driver_tree_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("driver_tree_id", "child_node_id"),
    )

    # driver_tree_categories テーブル作成
    op.create_table(
        "driver_tree_categories",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            comment="カテゴリーの一意識別子",
        ),
        sa.Column(
            "industry_class",
            sa.String(100),
            nullable=False,
            comment="業種大分類（例: 製造業、サービス業）",
        ),
        sa.Column(
            "industry",
            sa.String(100),
            nullable=False,
            comment="業種（例: 自動車製造、ホテル業）",
        ),
        sa.Column(
            "tree_type",
            sa.String(100),
            nullable=False,
            comment="ツリータイプ（例: 生産_製造数量×出荷率型）",
        ),
        sa.Column(
            "kpi",
            sa.String(100),
            nullable=False,
            comment="KPI名（例: 粗利、営業利益）",
        ),
        sa.Column(
            "formulas",
            ARRAY(sa.String),
            nullable=False,
            comment="数式のリスト（例: ['粗利 = 売上 - 原価']）",
        ),
        sa.Column(
            "metadata",
            JSONB,
            nullable=False,
            comment="その他のメタデータ（JSONB）",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="作成日時",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="更新日時",
        ),
    )

    # driver_tree_categories テーブルのインデックス作成
    op.create_index(
        "idx_driver_tree_categories_industry_class",
        "driver_tree_categories",
        ["industry_class"],
    )
    op.create_index(
        "idx_driver_tree_categories_industry",
        "driver_tree_categories",
        ["industry"],
    )
    op.create_index(
        "idx_driver_tree_categories_tree_type",
        "driver_tree_categories",
        ["tree_type"],
    )
    op.create_index(
        "idx_driver_tree_categories_kpi",
        "driver_tree_categories",
        ["kpi"],
    )


def downgrade() -> None:
    """Driver Tree機能用のテーブルを削除します。

    ロールバック時にすべてのテーブルとインデックスを削除します。
    外部キー制約により、driver_tree_children → driver_trees → driver_tree_nodes の順で削除します。
    """
    # driver_tree_categories テーブル削除
    op.drop_index(
        "idx_driver_tree_categories_kpi",
        table_name="driver_tree_categories",
    )
    op.drop_index(
        "idx_driver_tree_categories_tree_type",
        table_name="driver_tree_categories",
    )
    op.drop_index(
        "idx_driver_tree_categories_industry",
        table_name="driver_tree_categories",
    )
    op.drop_index(
        "idx_driver_tree_categories_industry_class",
        table_name="driver_tree_categories",
    )
    op.drop_table("driver_tree_categories")

    # driver_tree_children テーブル削除
    op.drop_table("driver_tree_children")

    # driver_trees テーブル削除
    op.drop_index(
        "idx_driver_trees_root_node",
        table_name="driver_trees",
    )
    op.drop_table("driver_trees")

    # driver_tree_nodes テーブル削除
    op.drop_index(
        "idx_driver_tree_nodes_label",
        table_name="driver_tree_nodes",
    )
    op.drop_table("driver_tree_nodes")
