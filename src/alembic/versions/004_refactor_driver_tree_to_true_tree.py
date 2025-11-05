"""refactor driver tree to true tree structure

Revision ID: 004
Revises: 003
Create Date: 2025-11-05 15:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Driver Treeを多対多関係から真の木構造に変更します。

    変更内容:
    1. driver_tree_children テーブルを削除（多対多関連が不要に）
    2. driver_trees テーブルに name カラムを追加
    3. driver_trees.operator カラムを削除（ノード側に移動）
    4. driver_trees.root_node_id を NULL 許可に変更
    5. driver_tree_nodes テーブルに tree_id, parent_id, operator カラムを追加
    6. 必要なインデックスと外部キー制約を追加
    """
    # 1. driver_tree_children テーブルを削除
    op.drop_table("driver_tree_children")

    # 2. driver_trees テーブルに name カラムを追加
    op.add_column(
        "driver_trees",
        sa.Column(
            "name",
            sa.String(200),
            nullable=True,
            comment="ツリー名（任意、例：「売上分析」「粗利分析」）",
        ),
    )

    # 3. driver_trees.operator カラムを削除
    op.drop_column("driver_trees", "operator")

    # 4. driver_trees.root_node_id の外部キー制約を一時削除し、NULL許可に変更
    op.drop_constraint(
        "driver_trees_root_node_id_fkey",
        "driver_trees",
        type_="foreignkey",
    )
    op.alter_column(
        "driver_trees",
        "root_node_id",
        existing_type=UUID(as_uuid=True),
        nullable=True,
    )

    # 5. driver_tree_nodes テーブルに新しいカラムを追加
    op.add_column(
        "driver_tree_nodes",
        sa.Column(
            "tree_id",
            UUID(as_uuid=True),
            nullable=True,  # 一時的にNULL許可（既存データ対応）
            comment="所属するツリーのID",
        ),
    )
    op.add_column(
        "driver_tree_nodes",
        sa.Column(
            "parent_id",
            UUID(as_uuid=True),
            nullable=True,
            comment="親ノードID（Noneの場合はルートノード）",
        ),
    )
    op.add_column(
        "driver_tree_nodes",
        sa.Column(
            "operator",
            sa.String(10),
            nullable=True,
            comment="親ノードとの演算子（+, -, *, /, %など）",
        ),
    )

    # 6. 外部キー制約とインデックスを追加
    op.create_foreign_key(
        "driver_tree_nodes_tree_id_fkey",
        "driver_tree_nodes",
        "driver_trees",
        ["tree_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "driver_tree_nodes_parent_id_fkey",
        "driver_tree_nodes",
        "driver_tree_nodes",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "driver_trees_root_node_id_fkey",
        "driver_trees",
        "driver_tree_nodes",
        ["root_node_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "idx_driver_tree_nodes_tree_id",
        "driver_tree_nodes",
        ["tree_id"],
    )
    op.create_index(
        "idx_driver_tree_nodes_parent_id",
        "driver_tree_nodes",
        ["parent_id"],
    )

    # 7. tree_id を NOT NULL に変更（既存データがない場合のみ安全）
    # 注意: 既存データがある場合は、データ移行スクリプトを実行してから実行すること
    op.alter_column(
        "driver_tree_nodes",
        "tree_id",
        existing_type=UUID(as_uuid=True),
        nullable=False,
    )


def downgrade() -> None:
    """変更を元に戻します。

    警告: このダウングレードはデータ損失を伴います。
    親子関係の情報（parent_id, operator）は失われます。
    """
    # 7. tree_id を NULL 許可に戻す
    op.alter_column(
        "driver_tree_nodes",
        "tree_id",
        existing_type=UUID(as_uuid=True),
        nullable=True,
    )

    # 6. インデックスと外部キー制約を削除
    op.drop_index("idx_driver_tree_nodes_parent_id", table_name="driver_tree_nodes")
    op.drop_index("idx_driver_tree_nodes_tree_id", table_name="driver_tree_nodes")

    op.drop_constraint(
        "driver_trees_root_node_id_fkey",
        "driver_trees",
        type_="foreignkey",
    )
    op.drop_constraint(
        "driver_tree_nodes_parent_id_fkey",
        "driver_tree_nodes",
        type_="foreignkey",
    )
    op.drop_constraint(
        "driver_tree_nodes_tree_id_fkey",
        "driver_tree_nodes",
        type_="foreignkey",
    )

    # 5. driver_tree_nodes テーブルから新しいカラムを削除
    op.drop_column("driver_tree_nodes", "operator")
    op.drop_column("driver_tree_nodes", "parent_id")
    op.drop_column("driver_tree_nodes", "tree_id")

    # 4. driver_trees.root_node_id を NOT NULL に戻す
    op.alter_column(
        "driver_trees",
        "root_node_id",
        existing_type=UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "driver_trees_root_node_id_fkey",
        "driver_trees",
        "driver_tree_nodes",
        ["root_node_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 3. driver_trees.operator カラムを追加
    op.add_column(
        "driver_trees",
        sa.Column(
            "operator",
            sa.String(10),
            nullable=True,
            comment="演算子（+, -, *, /, %など）",
        ),
    )

    # 2. driver_trees テーブルから name カラムを削除
    op.drop_column("driver_trees", "name")

    # 1. driver_tree_children テーブルを再作成
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
