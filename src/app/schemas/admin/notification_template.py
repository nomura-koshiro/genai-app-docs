"""通知テンプレートスキーマ。

このモジュールは、通知テンプレートのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel

# ================================================================================
# リクエストスキーマ
# ================================================================================


class NotificationTemplateCreate(BaseCamelCaseModel):
    """通知テンプレート作成リクエストスキーマ。"""

    name: str = Field(..., min_length=1, max_length=100, description="テンプレート名")
    event_type: str = Field(..., min_length=1, max_length=50, description="イベント種別")
    subject: str = Field(..., min_length=1, max_length=200, description="件名テンプレート")
    body: str = Field(..., min_length=1, description="本文テンプレート")
    variables: list[str] = Field(default_factory=list, description="利用可能変数リスト")
    is_active: bool = Field(default=True, description="有効フラグ")


class NotificationTemplateUpdate(BaseCamelCaseModel):
    """通知テンプレート更新リクエストスキーマ。"""

    name: str | None = Field(default=None, max_length=100, description="テンプレート名")
    subject: str | None = Field(default=None, max_length=200, description="件名テンプレート")
    body: str | None = Field(default=None, description="本文テンプレート")
    variables: list[str] | None = Field(default=None, description="利用可能変数リスト")
    is_active: bool | None = Field(default=None, description="有効フラグ")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class NotificationTemplateResponse(BaseCamelCaseORMModel):
    """通知テンプレートレスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="テンプレートID")
    name: str = Field(..., description="テンプレート名")
    event_type: str = Field(..., description="イベント種別")
    subject: str = Field(..., description="件名テンプレート")
    body: str = Field(..., description="本文テンプレート")
    variables: list[str] = Field(..., description="利用可能変数リスト")
    is_active: bool = Field(..., description="有効フラグ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class NotificationTemplateListResponse(BaseCamelCaseModel):
    """通知テンプレート一覧レスポンススキーマ。"""

    items: list[NotificationTemplateResponse] = Field(..., description="テンプレートリスト")
    total: int = Field(..., description="総件数")
