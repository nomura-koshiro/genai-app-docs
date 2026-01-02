"""検索サービス依存性。

GlobalSearchServiceのDI定義を提供します。
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services.search import GlobalSearchService

__all__ = [
    "GlobalSearchServiceDep",
    "get_global_search_service",
]


def get_global_search_service(db: DatabaseDep) -> GlobalSearchService:
    """グローバル検索サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        GlobalSearchService: 初期化されたグローバル検索サービスインスタンス
    """
    return GlobalSearchService(db)


GlobalSearchServiceDep = Annotated[GlobalSearchService, Depends(get_global_search_service)]
"""グローバル検索サービスの依存性型。

エンドポイント関数にGlobalSearchServiceインスタンスを自動注入します。
"""
