"""システム設定スキーマ。

このモジュールは、システム設定のリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


# ================================================================================
# リクエストスキーマ
# ================================================================================


class SystemSettingUpdate(BaseCamelCaseModel):
    """システム設定更新リクエストスキーマ。"""

    value: Any = Field(..., description="設定値")


class MaintenanceModeEnable(BaseCamelCaseModel):
    """メンテナンスモード有効化リクエストスキーマ。"""

    message: str = Field(
        ..., min_length=1, max_length=500, description="メンテナンスメッセージ"
    )
    allow_admin_access: bool = Field(default=True, description="管理者アクセス許可")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class SystemSettingResponse(BaseCamelCaseORMModel):
    """システム設定レスポンススキーマ。

    Attributes:
        key (str): 設定キー
        value (Any): 設定値
        value_type (str): 値の型
        description (str | None): 説明
        is_editable (bool): 編集可能フラグ
    """

    key: str = Field(..., description="設定キー")
    value: Any = Field(..., description="設定値")
    value_type: str = Field(..., description="値の型")
    description: str | None = Field(default=None, description="説明")
    is_editable: bool = Field(..., description="編集可能フラグ")


class SystemSettingDetailResponse(SystemSettingResponse):
    """システム設定詳細レスポンススキーマ。"""

    id: uuid.UUID = Field(..., description="設定ID")
    category: str = Field(..., description="カテゴリ")
    is_secret: bool = Field(..., description="機密設定フラグ")
    updated_by: uuid.UUID | None = Field(default=None, description="更新者ID")
    updated_at: datetime = Field(..., description="更新日時")


class SystemSettingsByCategoryResponse(BaseCamelCaseModel):
    """カテゴリ別システム設定レスポンススキーマ。"""

    categories: dict[str, list[SystemSettingResponse]] = Field(
        ..., description="カテゴリ別設定"
    )


class MaintenanceModeResponse(BaseCamelCaseModel):
    """メンテナンスモードレスポンススキーマ。"""

    enabled: bool = Field(..., description="メンテナンスモード状態")
    message: str | None = Field(default=None, description="メンテナンスメッセージ")
    allow_admin_access: bool = Field(default=True, description="管理者アクセス許可")
