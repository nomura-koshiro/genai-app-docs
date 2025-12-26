"""Driver Tree API v1 エンドポイント。

このパッケージには、Driver Tree（KPIツリー）機能用のエンドポイントが含まれています。

提供される機能:
    - Driver Treeの作成・取得・削除
    - ツリーノードの追加・更新・削除
    - KPI計算式の管理
    - KPI一覧の取得

使用例:
    >>> # Driver Tree作成
    >>> POST /api/v1/driver-trees
    >>> {"project_id": "...", "name": "売上KPIツリー"}
    >>>
    >>> # ノード追加
    >>> POST /api/v1/driver-trees/{tree_id}/nodes
    >>> {"name": "売上高", "node_type": "kpi"}
"""

from app.api.routes.v1.driver_tree.driver_tree import driver_tree_router

__all__ = ["driver_tree_router"]
