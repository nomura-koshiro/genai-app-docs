"""共通スキーマパッケージ。

このパッケージは、APIエンドポイントで共通的に使用されるスキーマを提供します。

主なモジュール:
    - responses: 汎用レスポンススキーマ（MessageResponse, ProblemDetails, HealthResponse）
    - filters: フィルタ・検索・ページネーションパラメータ

使用方法:
    >>> from app.schemas.common import PaginationParams, SortParams, ListQueryParams
    >>>
    >>> @router.get("/items")
    >>> async def list_items(
    ...     params: ListQueryParams = Depends(),
    ... ):
    ...     return await service.list(**params.model_dump())
"""

# 共通レスポンススキーマ
# フィルタ・検索パラメータ
from app.schemas.common.filters import (
    ActiveFilter,
    DateRangeFilter,
    DateTimeRangeFilter,
    FilterResult,
    ListQueryParams,
    PaginatedResponse,
    PaginationParams,
    SearchParams,
    SortOrder,
    SortParams,
    StatusFilter,
)
from app.schemas.common.responses import (
    HealthResponse,
    MessageResponse,
    ProblemDetails,
)

__all__ = [
    # 共通レスポンス
    "MessageResponse",
    "ProblemDetails",
    "HealthResponse",
    # ページネーション
    "PaginationParams",
    "PaginatedResponse",
    # ソート
    "SortOrder",
    "SortParams",
    # フィルタ
    "DateRangeFilter",
    "DateTimeRangeFilter",
    "StatusFilter",
    "ActiveFilter",
    # 検索
    "SearchParams",
    # 統合
    "ListQueryParams",
    "FilterResult",
]
