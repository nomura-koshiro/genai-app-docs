"""監査ログスキーマ。

このモジュールは、監査ログのリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel

# ================================================================================
# フィルタ・クエリスキーマ
# ================================================================================


class AuditLogFilter(BaseCamelCaseModel):
    """監査ログフィルタスキーマ。

    Attributes:
        event_type (str | None): イベント種別
        user_id (UUID | None): ユーザーID
        resource_type (str | None): リソース種別
        resource_id (UUID | None): リソースID
        severity (str | None): 重要度
        start_date (datetime | None): 開始日時
        end_date (datetime | None): 終了日時
        page (int): ページ番号
        limit (int): 取得件数
    """

    event_type: str | None = Field(default=None, description="イベント種別")
    user_id: uuid.UUID | None = Field(default=None, description="ユーザーID")
    resource_type: str | None = Field(default=None, description="リソース種別")
    resource_id: uuid.UUID | None = Field(default=None, description="リソースID")
    severity: str | None = Field(default=None, description="重要度")
    start_date: datetime | None = Field(default=None, description="開始日時")
    end_date: datetime | None = Field(default=None, description="終了日時")
    page: int = Field(default=1, ge=1, description="ページ番号")
    limit: int = Field(default=50, ge=1, le=100, description="取得件数")


class AuditLogExportFilter(BaseCamelCaseModel):
    """監査ログエクスポートフィルタスキーマ。"""

    format: str = Field(default="csv", description="出力形式（csv/json）")
    event_type: str | None = Field(default=None, description="イベント種別フィルタ")
    start_date: datetime | None = Field(default=None, description="開始日時")
    end_date: datetime | None = Field(default=None, description="終了日時")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class AuditLogResponse(BaseCamelCaseORMModel):
    """監査ログレスポンススキーマ。

    Attributes:
        id (UUID): 監査ログID
        user_id (UUID | None): ユーザーID
        user_name (str | None): ユーザー名
        user_email (str | None): ユーザーメール
        event_type (str): イベント種別
        action (str): アクション
        resource_type (str): リソース種別
        resource_id (UUID | None): リソースID
        old_value (dict | None): 変更前の値
        new_value (dict | None): 変更後の値
        changed_fields (list | None): 変更フィールド
        ip_address (str | None): IPアドレス
        user_agent (str | None): ユーザーエージェント
        severity (str): 重要度
        metadata (dict | None): メタデータ
        created_at (datetime): 作成日時
    """

    id: uuid.UUID = Field(..., description="監査ログID")
    user_id: uuid.UUID | None = Field(default=None, description="ユーザーID")
    user_name: str | None = Field(default=None, description="ユーザー名")
    user_email: str | None = Field(default=None, description="ユーザーメール")
    event_type: str = Field(..., description="イベント種別")
    action: str = Field(..., description="アクション")
    resource_type: str = Field(..., description="リソース種別")
    resource_id: uuid.UUID | None = Field(default=None, description="リソースID")
    old_value: dict | None = Field(default=None, description="変更前の値")
    new_value: dict | None = Field(default=None, description="変更後の値")
    changed_fields: list | None = Field(default=None, description="変更フィールド")
    ip_address: str | None = Field(default=None, description="IPアドレス")
    user_agent: str | None = Field(default=None, description="ユーザーエージェント")
    severity: str = Field(..., description="重要度")
    metadata: dict | None = Field(default=None, description="メタデータ")
    created_at: datetime = Field(..., description="作成日時")


class AuditLogListResponse(BaseCamelCaseModel):
    """監査ログ一覧レスポンススキーマ。"""

    items: list[AuditLogResponse] = Field(..., description="監査ログリスト")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="ページ番号")
    limit: int = Field(..., description="取得件数")
    total_pages: int = Field(..., description="総ページ数")
