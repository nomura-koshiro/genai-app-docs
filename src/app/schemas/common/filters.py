"""共通フィルタ・検索パラメータスキーマ。

このモジュールは、APIエンドポイントで使用される共通のフィルタ・検索パラメータを定義します。
一覧取得APIで統一的なフィルタリング・ページネーション機能を提供します。

主なスキーマ:
    - PaginationParams: ページネーションパラメータ
    - DateRangeFilter: 日付範囲フィルタ
    - SortParams: ソートパラメータ
    - SearchParams: 全文検索パラメータ

使用方法:
    >>> from app.schemas.common.filters import PaginationParams, SortParams
    >>>
    >>> @router.get("/items")
    >>> async def list_items(
    ...     pagination: PaginationParams = Depends(),
    ...     sort: SortParams = Depends(),
    ... ):
    ...     return await service.list(
    ...         skip=pagination.skip,
    ...         limit=pagination.limit,
    ...         sort_by=sort.sort_by,
    ...         sort_order=sort.sort_order,
    ...     )
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel


class SortOrder(str, Enum):
    """ソート順序。"""

    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseCamelCaseModel):
    """ページネーションパラメータ。

    一覧取得APIで使用する標準的なページネーションパラメータです。

    Attributes:
        skip: スキップするレコード数（デフォルト: 0）
        limit: 取得する最大レコード数（デフォルト: 100、最大: 1000）

    Example:
        >>> pagination = PaginationParams(skip=0, limit=20)
        >>> # 1ページ目の20件を取得
    """

    skip: int = Field(default=0, ge=0, description="スキップするレコード数")
    limit: int = Field(default=100, ge=1, le=1000, description="取得する最大レコード数")


class DateRangeFilter(BaseCamelCaseModel):
    """日付範囲フィルタ。

    作成日や更新日での範囲検索に使用します。

    Attributes:
        start_date: 開始日（この日以降）
        end_date: 終了日（この日以前）
        date_field: フィルタ対象のフィールド名（デフォルト: created_at）

    Example:
        >>> date_filter = DateRangeFilter(
        ...     start_date=date(2024, 1, 1),
        ...     end_date=date(2024, 12, 31)
        ... )
    """

    start_date: date | None = Field(default=None, description="開始日（この日以降）")
    end_date: date | None = Field(default=None, description="終了日（この日以前）")
    date_field: str = Field(default="created_at", description="フィルタ対象のフィールド名")


class DateTimeRangeFilter(BaseCamelCaseModel):
    """日時範囲フィルタ。

    作成日時や更新日時での範囲検索に使用します。

    Attributes:
        start_datetime: 開始日時（この日時以降）
        end_datetime: 終了日時（この日時以前）
        datetime_field: フィルタ対象のフィールド名（デフォルト: created_at）

    Example:
        >>> from datetime import datetime, timezone
        >>> datetime_filter = DateTimeRangeFilter(
        ...     start_datetime=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        ...     end_datetime=datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        ... )
    """

    start_datetime: datetime | None = Field(default=None, description="開始日時（この日時以降）")
    end_datetime: datetime | None = Field(default=None, description="終了日時（この日時以前）")
    datetime_field: str = Field(default="created_at", description="フィルタ対象のフィールド名")


class SortParams(BaseCamelCaseModel):
    """ソートパラメータ。

    一覧取得APIで使用する標準的なソートパラメータです。

    Attributes:
        sort_by: ソート対象のフィールド名（デフォルト: created_at）
        sort_order: ソート順序（asc/desc、デフォルト: desc）

    Example:
        >>> sort = SortParams(sort_by="name", sort_order=SortOrder.ASC)
        >>> # 名前の昇順でソート
    """

    sort_by: str = Field(default="created_at", description="ソート対象のフィールド名")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="ソート順序（asc/desc）")


class SearchParams(BaseCamelCaseModel):
    """全文検索パラメータ。

    テキストフィールドの検索に使用します。

    Attributes:
        query: 検索クエリ（部分一致検索）
        search_fields: 検索対象のフィールド名リスト

    Example:
        >>> search = SearchParams(
        ...     query="プロジェクト",
        ...     search_fields=["name", "description"]
        ... )
    """

    query: str | None = Field(default=None, min_length=1, max_length=255, description="検索クエリ")
    search_fields: list[str] | None = Field(default=None, description="検索対象のフィールド名リスト")


class StatusFilter(BaseCamelCaseModel):
    """ステータスフィルタ。

    ステータスでのフィルタリングに使用します。

    Attributes:
        status: フィルタ対象のステータス値
        include_inactive: 非アクティブなレコードを含めるか（デフォルト: False）

    Example:
        >>> status_filter = StatusFilter(status="active", include_inactive=False)
    """

    status: str | None = Field(default=None, description="フィルタ対象のステータス値")
    include_inactive: bool = Field(default=False, description="非アクティブなレコードを含めるか")


class ActiveFilter(BaseCamelCaseModel):
    """アクティブフラグフィルタ。

    is_activeフラグでのフィルタリングに使用します。

    Attributes:
        is_active: アクティブフラグ（Noneの場合はフィルタなし）

    Example:
        >>> active_filter = ActiveFilter(is_active=True)
        >>> # アクティブなレコードのみ取得
    """

    is_active: bool | None = Field(default=None, description="アクティブフラグフィルタ")


class ListQueryParams(BaseCamelCaseModel):
    """一覧取得用クエリパラメータ統合モデル。

    ページネーション、ソート、アクティブフィルタを統合したモデルです。

    Attributes:
        skip: スキップするレコード数
        limit: 取得する最大レコード数
        sort_by: ソート対象のフィールド名
        sort_order: ソート順序
        is_active: アクティブフラグフィルタ

    Example:
        >>> params = ListQueryParams(
        ...     skip=0,
        ...     limit=20,
        ...     sort_by="name",
        ...     sort_order=SortOrder.ASC,
        ...     is_active=True
        ... )
    """

    skip: int = Field(default=0, ge=0, description="スキップするレコード数")
    limit: int = Field(default=100, ge=1, le=1000, description="取得する最大レコード数")
    sort_by: str = Field(default="created_at", description="ソート対象のフィールド名")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="ソート順序")
    is_active: bool | None = Field(default=None, description="アクティブフラグフィルタ")


class FilterResult(BaseCamelCaseModel):
    """フィルタ結果のメタ情報。

    フィルタ適用後の結果に付加するメタ情報です。

    Attributes:
        total: 総件数（フィルタ適用後）
        skip: スキップ数
        limit: 取得件数
        has_more: 次ページがあるか

    Example:
        >>> result = FilterResult(total=100, skip=0, limit=20, has_more=True)
    """

    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数")
    limit: int = Field(..., description="取得件数")
    has_more: bool = Field(..., description="次ページがあるか")

    @classmethod
    def from_query(cls, total: int, skip: int, limit: int) -> "FilterResult":
        """クエリ結果からFilterResultを生成する。

        Args:
            total: 総件数
            skip: スキップ数
            limit: 取得件数

        Returns:
            FilterResult: フィルタ結果メタ情報
        """
        return cls(
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )


class PaginatedResponse(BaseCamelCaseModel):
    """ページネーション付きレスポンス基底クラス。

    一覧取得APIのレスポンスで使用する共通フォーマットです。

    Attributes:
        items: アイテムリスト
        total: 総件数
        skip: スキップ数
        limit: 取得件数
        has_more: 次ページがあるか

    Example:
        >>> class UserListResponse(PaginatedResponse):
        ...     items: list[UserResponse]
    """

    items: list[Any] = Field(default_factory=list, description="アイテムリスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数")
    limit: int = Field(..., description="取得件数")
    has_more: bool = Field(default=False, description="次ページがあるか")

    @classmethod
    def create(cls, items: list[Any], total: int, skip: int, limit: int) -> "PaginatedResponse":
        """ページネーション付きレスポンスを生成する。

        Args:
            items: アイテムリスト
            total: 総件数
            skip: スキップ数
            limit: 取得件数

        Returns:
            PaginatedResponse: ページネーション付きレスポンス
        """
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )
