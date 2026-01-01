"""ドライバーツリーテンプレート関連スキーマ。

このモジュールは、ドライバーツリーテンプレートのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# ドライバーツリーテンプレートスキーマ
# ================================================================================
class DriverTreeTemplateInfo(BaseCamelCaseORMModel):
    """ドライバーツリーテンプレート情報。

    テンプレート一覧表示用の基本情報スキーマです。

    Attributes:
        template_id (UUID): テンプレートID
        name (str): テンプレート名
        description (str | None): 説明
        category (str | None): カテゴリ（業種）
        node_count (int): ノード数
        is_public (bool): 公開フラグ
        usage_count (int): 使用回数
        created_by (UUID | None): 作成者ID
        created_by_name (str | None): 作成者名
        created_at (datetime): 作成日時

    Example:
        >>> {
        ...     "templateId": "...",
        ...     "name": "EC売上モデル",
        ...     "description": "EC事業の売上分解テンプレート",
        ...     "category": "小売・EC",
        ...     "nodeCount": 12,
        ...     "isPublic": true,
        ...     "usageCount": 80,
        ...     "createdBy": "...",
        ...     "createdByName": "山田 太郎",
        ...     "createdAt": "2026-01-01T00:00:00Z"
        ... }
    """

    template_id: uuid.UUID = Field(..., description="テンプレートID")
    name: str = Field(..., description="テンプレート名")
    description: str | None = Field(None, description="説明")
    category: str | None = Field(None, description="カテゴリ（業種）")
    node_count: int = Field(0, description="ノード数")
    is_public: bool = Field(False, description="公開フラグ")
    usage_count: int = Field(0, description="使用回数")
    created_by: uuid.UUID | None = Field(None, description="作成者ID")
    created_by_name: str | None = Field(None, description="作成者名")
    created_at: datetime = Field(..., description="作成日時")


class DriverTreeTemplateListResponse(BaseCamelCaseModel):
    """ドライバーツリーテンプレート一覧レスポンス。

    Attributes:
        templates (list[DriverTreeTemplateInfo]): テンプレート一覧
        total (int): 総件数

    Example:
        >>> {
        ...     "templates": [...],
        ...     "total": 10
        ... }
    """

    templates: list[DriverTreeTemplateInfo] = Field(default_factory=list, description="テンプレート一覧")
    total: int = Field(..., description="総件数")


class DriverTreeTemplateCreateRequest(BaseCamelCaseModel):
    """ドライバーツリーテンプレート作成リクエスト。

    ツリーからテンプレートを作成する際のリクエストスキーマです。

    Attributes:
        name (str): テンプレート名
        description (str | None): 説明
        category (str | None): カテゴリ（業種）
        source_tree_id (UUID): 元ツリーID
        is_public (bool): 公開フラグ

    Example:
        >>> request = DriverTreeTemplateCreateRequest(
        ...     name="EC売上モデル",
        ...     description="EC事業の売上分解テンプレート",
        ...     category="小売・EC",
        ...     source_tree_id=uuid.UUID("..."),
        ...     is_public=True
        ... )
    """

    name: str = Field(..., min_length=1, max_length=255, description="テンプレート名")
    description: str | None = Field(None, description="説明")
    category: str | None = Field(None, max_length=100, description="カテゴリ（業種）")
    source_tree_id: uuid.UUID = Field(..., description="元ツリーID")
    is_public: bool = Field(False, description="公開フラグ")


class DriverTreeTemplateCreateResponse(BaseCamelCaseORMModel):
    """ドライバーツリーテンプレート作成レスポンス。

    Attributes:
        template_id (UUID): テンプレートID
        name (str): テンプレート名
        description (str | None): 説明
        category (str | None): カテゴリ（業種）
        template_config (dict): テンプレート設定
        node_count (int): ノード数
        created_at (datetime): 作成日時

    Example:
        >>> {
        ...     "templateId": "...",
        ...     "name": "EC売上モデル",
        ...     "description": "EC事業の売上分解テンプレート",
        ...     "category": "小売・EC",
        ...     "templateConfig": {...},
        ...     "nodeCount": 12,
        ...     "createdAt": "2026-01-01T00:00:00Z"
        ... }
    """

    template_id: uuid.UUID = Field(..., description="テンプレートID")
    name: str = Field(..., description="テンプレート名")
    description: str | None = Field(None, description="説明")
    category: str | None = Field(None, description="カテゴリ（業種）")
    template_config: dict = Field(..., description="テンプレート設定")
    node_count: int = Field(..., description="ノード数")
    created_at: datetime = Field(..., description="作成日時")


class DriverTreeTemplateDeleteResponse(BaseCamelCaseModel):
    """ドライバーツリーテンプレート削除レスポンス。

    Attributes:
        success (bool): 削除成功フラグ
        deleted_at (datetime): 削除日時

    Example:
        >>> {
        ...     "success": true,
        ...     "deletedAt": "2026-01-01T00:00:00Z"
        ... }
    """

    success: bool = Field(..., description="削除成功フラグ")
    deleted_at: datetime = Field(..., description="削除日時")
