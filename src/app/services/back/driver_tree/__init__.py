"""Driver Tree関連のビジネスロジックサービス。

このモジュールは、Driver Tree（KPIツリー）機能に関連するビジネスロジックを提供します。

主なサービス:
    - DriverTreeService: Driver Tree管理サービス（ツリー作成、ノード操作、計算式管理）

使用例:
    >>> from app.services.driver_tree import DriverTreeService
    >>> from app.schemas.driver_tree import DriverTreeNodeCreate
    >>>
    >>> async with get_db() as db:
    ...     tree_service = DriverTreeService(db)
    ...     tree = await tree_service.create_tree(project_id, "売上KPIツリー")
    ...     node = await tree_service.add_node(
    ...         tree_id=tree.id,
    ...         node_data=DriverTreeNodeCreate(name="売上高", node_type="kpi")
    ...     )
"""

from app.services.driver_tree.driver_tree import DriverTreeService

__all__ = ["DriverTreeService"]
