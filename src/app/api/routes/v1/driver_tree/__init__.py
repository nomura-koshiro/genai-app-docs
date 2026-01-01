"""ドライバーツリー API v1 エンドポイント。

このパッケージには、ドライバーツリー機能用のエンドポイントが含まれています。

提供されるルーター:
    - driver_tree_files_router: ファイル管理（アップロード、シート選択、カラム設定）
    - driver_tree_trees_router: ツリー管理（作成、更新、削除、一覧取得）
    - driver_tree_nodes_router: ノード管理（作成、更新、削除、並び替え）

主な機能:
    ファイル:
        - Excelファイルのアップロード
        - シートの選択
        - データカラムの設定

    ツリー:
        - ドライバーツリーの作成・更新・削除
        - ツリー一覧の取得
        - ツリー詳細の取得
        - ツリーのコピー

    ノード:
        - ノードの作成・更新・削除
        - ノードの並び替え
        - 子ノードの追加
        - 数式・施策の設定

使用例:
    >>> # ファイルアップロード
    >>> POST /api/v1/driver-tree/file
    >>> Content-Type: multipart/form-data
    >>>
    >>> # ツリー作成
    >>> POST /api/v1/driver-tree/tree
    >>> {"name": "売上分析ツリー", "project_id": "..."}
"""

from app.api.routes.v1.driver_tree.driver_tree import driver_tree_trees_router
from app.api.routes.v1.driver_tree.driver_tree_file import driver_tree_files_router
from app.api.routes.v1.driver_tree.driver_tree_node import driver_tree_nodes_router
from app.api.routes.v1.driver_tree.driver_tree_template import driver_tree_templates_router

__all__ = ["driver_tree_files_router", "driver_tree_trees_router", "driver_tree_nodes_router", "driver_tree_templates_router"]
