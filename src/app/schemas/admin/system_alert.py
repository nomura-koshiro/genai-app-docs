"""システムアラートスキーマ。

このモジュールは、システムアラートのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel

# ================================================================================
# リクエストスキーマ
# ================================================================================


class SystemAlertCreate(BaseCamelCaseModel):
    """システムアラート作成リクエストスキーマ。"""

    name: str = Field(..., min_length=1, max_length=100, description="アラート名")
    condition_type: str = Field(..., description="条件種別")
    threshold: dict[str, Any] = Field(..., description="閾値設定")
    comparison_operator: str = Field(..., description="比較演算子")
    notification_channels: list[str] = Field(..., description="通知先")
    is_enabled: bool = Field(default=True, description="有効フラグ")


class SystemAlertUpdate(BaseCamelCaseModel):
    """システムアラート更新リクエストスキーマ。"""

    name: str | None = Field(default=None, max_length=100, description="アラート名")
    threshold: dict[str, Any] | None = Field(default=None, description="閾値設定")
    comparison_operator: str | None = Field(default=None, description="比較演算子")
    notification_channels: list[str] | None = Field(default=None, description="通知先")
    is_enabled: bool | None = Field(default=None, description="有効フラグ")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class SystemAlertResponse(BaseCamelCaseORMModel):
    """システムアラートレスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="アラートID")
    name: str = Field(..., description="アラート名")
    condition_type: str = Field(..., description="条件種別")
    threshold: dict[str, Any] = Field(..., description="閾値設定")
    comparison_operator: str = Field(..., description="比較演算子")
    notification_channels: list[str] = Field(..., description="通知先")
    is_enabled: bool = Field(..., description="有効フラグ")
    last_triggered_at: datetime | None = Field(default=None, description="最終発火日時")
    trigger_count: int = Field(..., description="発火回数")
    created_by: uuid.UUID = Field(..., description="作成者ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class SystemAlertListResponse(BaseCamelCaseModel):
    """システムアラート一覧レスポンススキーマ。"""

    items: list[SystemAlertResponse] = Field(..., description="アラートリスト")
    total: int = Field(..., description="総件数")
