"""操作履歴スキーマ。

このモジュールは、ユーザー操作履歴のリクエスト/レスポンススキーマを定義します。
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel

# ================================================================================
# フィルタ・クエリスキーマ
# ================================================================================


class ActivityLogFilter(BaseCamelCaseModel):
    """操作履歴フィルタスキーマ。

    Attributes:
        user_id (UUID | None): ユーザーIDで絞り込み
        action_type (str | None): 操作種別で絞り込み
        resource_type (str | None): リソース種別で絞り込み
        start_date (datetime | None): 開始日時
        end_date (datetime | None): 終了日時
        has_error (bool | None): エラーのみ取得
        page (int): ページ番号
        limit (int): 取得件数
    """

    user_id: uuid.UUID | None = Field(default=None, description="ユーザーIDで絞り込み")
    action_type: str | None = Field(default=None, description="操作種別で絞り込み")
    resource_type: str | None = Field(default=None, description="リソース種別で絞り込み")
    start_date: datetime | None = Field(default=None, description="開始日時")
    end_date: datetime | None = Field(default=None, description="終了日時")
    has_error: bool | None = Field(default=None, description="エラーのみ取得")
    page: int = Field(default=1, ge=1, description="ページ番号")
    limit: int = Field(default=50, ge=1, le=100, description="取得件数")


# ================================================================================
# レスポンススキーマ
# ================================================================================


class ActivityLogUserInfo(BaseCamelCaseModel):
    """操作履歴のユーザー情報。"""

    id: uuid.UUID = Field(..., description="ユーザーID")
    name: str = Field(..., description="ユーザー名")
    email: str | None = Field(default=None, description="メールアドレス")


class ActivityLogResponse(BaseCamelCaseORMModel):
    """操作履歴レスポンススキーマ。

    Attributes:
        id (UUID): 操作履歴ID
        user_id (UUID | None): ユーザーID
        user_name (str | None): ユーザー名
        action_type (str): 操作種別
        resource_type (str | None): リソース種別
        resource_id (UUID | None): リソースID
        endpoint (str): APIエンドポイント
        method (str): HTTPメソッド
        response_status (int): HTTPステータス
        error_message (str | None): エラーメッセージ
        error_code (str | None): エラーコード
        ip_address (str | None): IPアドレス
        user_agent (str | None): ユーザーエージェント
        duration_ms (int): 処理時間
        created_at (datetime): 作成日時
    """

    id: uuid.UUID = Field(..., description="操作履歴ID")
    user_id: uuid.UUID | None = Field(default=None, description="ユーザーID")
    user_name: str | None = Field(default=None, description="ユーザー名")
    action_type: str = Field(..., description="操作種別")
    resource_type: str | None = Field(default=None, description="リソース種別")
    resource_id: uuid.UUID | None = Field(default=None, description="リソースID")
    endpoint: str = Field(..., description="APIエンドポイント")
    method: str = Field(..., description="HTTPメソッド")
    response_status: int = Field(..., description="HTTPステータス")
    error_message: str | None = Field(default=None, description="エラーメッセージ")
    error_code: str | None = Field(default=None, description="エラーコード")
    ip_address: str | None = Field(default=None, description="IPアドレス")
    user_agent: str | None = Field(default=None, description="ユーザーエージェント")
    duration_ms: int = Field(..., description="処理時間（ミリ秒）")
    created_at: datetime = Field(..., description="作成日時")


class ActivityLogDetailResponse(ActivityLogResponse):
    """操作履歴詳細レスポンススキーマ。

    ActivityLogResponseに加え、リクエストボディとユーザー詳細情報を含む。
    """

    user_email: str | None = Field(default=None, description="ユーザーメールアドレス")
    request_body: dict | None = Field(default=None, description="リクエストボディ")


class ActivityLogListResponse(BaseCamelCaseModel):
    """操作履歴一覧レスポンススキーマ。

    Attributes:
        items (list[ActivityLogResponse]): 操作履歴リスト
        total (int): 総件数
        page (int): ページ番号
        limit (int): 取得件数
        total_pages (int): 総ページ数
    """

    items: list[ActivityLogResponse] = Field(..., description="操作履歴リスト")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="ページ番号")
    limit: int = Field(..., description="取得件数")
    total_pages: int = Field(..., description="総ページ数")
