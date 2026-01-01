"""システムお知らせスキーマ。

このモジュールは、システムお知らせのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel

# ================================================================================
# リクエストスキーマ
# ================================================================================


class AnnouncementCreate(BaseCamelCaseModel):
    """お知らせ作成リクエストスキーマ。

    Attributes:
        title (str): タイトル
        content (str): 本文
        announcement_type (str): 種別
        priority (int): 優先度
        start_at (datetime): 表示開始日時
        end_at (datetime | None): 表示終了日時
        target_roles (list | None): 対象ロール
    """

    title: str = Field(..., min_length=1, max_length=200, description="タイトル")
    content: str = Field(..., min_length=1, description="本文")
    announcement_type: str = Field(..., description="種別（INFO/WARNING/MAINTENANCE）")
    priority: int = Field(default=5, ge=1, le=10, description="優先度（1が最高）")
    start_at: datetime = Field(..., description="表示開始日時")
    end_at: datetime | None = Field(default=None, description="表示終了日時")
    target_roles: list[str] | None = Field(default=None, description="対象ロール")


class AnnouncementUpdate(BaseCamelCaseModel):
    """お知らせ更新リクエストスキーマ。"""

    title: str | None = Field(default=None, max_length=200, description="タイトル")
    content: str | None = Field(default=None, description="本文")
    announcement_type: str | None = Field(default=None, description="種別")
    priority: int | None = Field(default=None, ge=1, le=10, description="優先度")
    start_at: datetime | None = Field(default=None, description="表示開始日時")
    end_at: datetime | None = Field(default=None, description="表示終了日時")
    is_active: bool | None = Field(default=None, description="有効フラグ")
    target_roles: list[str] | None = Field(default=None, description="対象ロール")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class AnnouncementResponse(BaseCamelCaseORMModel):
    """お知らせレスポンススキーマ。

    Attributes:
        id (UUID): お知らせID
        title (str): タイトル
        content (str): 本文
        announcement_type (str): 種別
        priority (int): 優先度
        start_at (datetime): 表示開始日時
        end_at (datetime | None): 表示終了日時
        is_active (bool): 有効フラグ
        target_roles (list | None): 対象ロール
        created_by (UUID): 作成者ID
        created_by_name (str | None): 作成者名
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
    """

    id: uuid.UUID = Field(..., description="お知らせID")
    title: str = Field(..., description="タイトル")
    content: str = Field(..., description="本文")
    announcement_type: str = Field(..., description="種別")
    priority: int = Field(..., description="優先度")
    start_at: datetime = Field(..., description="表示開始日時")
    end_at: datetime | None = Field(default=None, description="表示終了日時")
    is_active: bool = Field(..., description="有効フラグ")
    target_roles: list[str] | None = Field(default=None, description="対象ロール")
    created_by: uuid.UUID = Field(..., description="作成者ID")
    created_by_name: str | None = Field(default=None, description="作成者名")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class AnnouncementListResponse(BaseCamelCaseModel):
    """お知らせ一覧レスポンススキーマ。"""

    items: list[AnnouncementResponse] = Field(..., description="お知らせリスト")
    total: int = Field(..., description="総件数")
