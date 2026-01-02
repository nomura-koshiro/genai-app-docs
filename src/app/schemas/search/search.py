"""グローバル検索関連のPydanticスキーマ。

共通UI設計書（UI-004〜UI-005）に基づく検索機能のスキーマ定義。
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel

__all__ = [
    # Enum
    "SearchTypeEnum",
    # Info schemas
    "SearchResultInfo",
    # Query schemas
    "SearchQuery",
    # Response schemas
    "SearchResponse",
]


class SearchTypeEnum(str, Enum):
    """検索対象タイプ。"""

    PROJECT = "project"
    SESSION = "session"
    FILE = "file"
    TREE = "tree"


class SearchResultInfo(BaseCamelCaseModel):
    """検索結果情報スキーマ。

    各検索結果アイテムの情報を表す。
    """

    type: SearchTypeEnum
    id: UUID
    name: str
    description: str | None = None
    matched_field: str
    highlighted_text: str
    project_id: UUID | None = None
    project_name: str | None = None
    updated_at: datetime
    url: str


class SearchQuery(BaseCamelCaseModel):
    """検索クエリスキーマ。

    グローバル検索のクエリパラメータ。
    """

    q: str = Field(..., min_length=2, max_length=100, description="検索クエリ")
    type: list[SearchTypeEnum] | None = Field(
        default=None, description="検索対象タイプ（複数指定可）"
    )
    project_id: UUID | None = Field(default=None, description="プロジェクトID絞り込み")
    limit: int = Field(default=20, ge=1, le=100, description="取得件数")


class SearchResponse(BaseCamelCaseModel):
    """検索レスポンススキーマ。

    検索結果一覧とメタ情報。
    """

    results: list[SearchResultInfo]
    total: int
    query: str
    types: list[SearchTypeEnum]
