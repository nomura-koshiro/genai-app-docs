"""DriverTreeサービス依存性。

DriverTree関連サービスのDI定義を提供します。
- DriverTreeFileService
- DriverTreeService
- DriverTreeNodeService
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services.driver_tree import (
    DriverTreeFileService,
    DriverTreeNodeService,
    DriverTreeService,
)

__all__ = [
    "DriverTreeFileServiceDep",
    "DriverTreeServiceDep",
    "DriverTreeNodeServiceDep",
    "get_driver_tree_file_service",
    "get_driver_tree_service",
    "get_driver_tree_node_service",
]


def get_driver_tree_file_service(db: DatabaseDep) -> DriverTreeFileService:
    """ドライバーツリーファイルサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        DriverTreeFileService: 初期化されたドライバーツリーファイルサービスインスタンス
    """
    return DriverTreeFileService(db)


def get_driver_tree_service(db: DatabaseDep) -> DriverTreeService:
    """ドライバーツリーサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        DriverTreeService: 初期化されたドライバーツリーサービスインスタンス
    """
    return DriverTreeService(db)


def get_driver_tree_node_service(db: DatabaseDep) -> DriverTreeNodeService:
    """ドライバーツリーノードサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        DriverTreeNodeService: 初期化されたドライバーツリーノードサービスインスタンス
    """
    return DriverTreeNodeService(db)


DriverTreeFileServiceDep = Annotated[DriverTreeFileService, Depends(get_driver_tree_file_service)]
"""ドライバーツリーファイルサービスの依存性型。

エンドポイント関数にDriverTreeFileServiceインスタンスを自動注入します。
"""

DriverTreeServiceDep = Annotated[DriverTreeService, Depends(get_driver_tree_service)]
"""ドライバーツリーサービスの依存性型。

エンドポイント関数にDriverTreeServiceインスタンスを自動注入します。
"""

DriverTreeNodeServiceDep = Annotated[DriverTreeNodeService, Depends(get_driver_tree_node_service)]
"""ドライバーツリーノードサービスの依存性型。

エンドポイント関数にDriverTreeNodeServiceインスタンスを自動注入します。
"""
