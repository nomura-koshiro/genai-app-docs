"""共通スキーマパッケージ。

このパッケージは、APIエンドポイントで共通的に使用されるスキーマを提供します。

主なモジュール:
    - responses: 汎用レスポンススキーマ（MessageResponse, ProblemDetails, HealthResponse）
    - filters: フィルタ・検索・ページネーションパラメータ
    - error: エラーレスポンススキーマ

使用方法:
    >>> from app.schemas.common import PaginationParams, SortParams, ListQueryParams
    >>>
    >>> @router.get("/items")
    >>> async def list_items(
    ...     params: ListQueryParams = Depends(),
    ... ):
    ...     return await service.list(**params.model_dump())
"""

# エラーレスポンススキーマ
from app.schemas.common.error import (
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    ConflictErrorResponse,
    ErrorDetail,
    ErrorResponse,
    InternalErrorResponse,
    NotFoundErrorResponse,
    ValidationErrorResponse,
)

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

# 共通レスポンススキーマ
from app.schemas.common.responses import (
    HealthResponse,
    MessageResponse,
    ProblemDetails,
)

# ユーザーコンテキストスキーマ
from app.schemas.common.user_context import (
    NavigationInfo,
    NotificationBadgeInfo,
    PermissionsInfo,
    SidebarInfo,
    UserContextInfo,
    UserContextResponse,
)

__all__ = [
    # 共通レスポンス
    "MessageResponse",
    "ProblemDetails",
    "HealthResponse",
    # エラーレスポンス
    "ErrorDetail",
    "ErrorResponse",
    "NotFoundErrorResponse",
    "ValidationErrorResponse",
    "AuthorizationErrorResponse",
    "AuthenticationErrorResponse",
    "ConflictErrorResponse",
    "InternalErrorResponse",
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
    # ユーザーコンテキスト
    "NavigationInfo",
    "NotificationBadgeInfo",
    "PermissionsInfo",
    "SidebarInfo",
    "UserContextInfo",
    "UserContextResponse",
]
