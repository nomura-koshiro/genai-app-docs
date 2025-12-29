"""ユーザー操作履歴のPydanticスキーマ。

このモジュールは、ユーザー操作履歴に関するリクエスト/レスポンススキーマを定義します。

主なスキーマ:
    - UserActivityCreate: UI操作履歴の作成リクエスト
    - UserActivityResponse: 操作履歴レスポンス
    - UserActivityListResponse: 操作履歴一覧レスポンス
    - UserActivitySearchParams: 検索パラメータ

使用方法:
    >>> from app.schemas.system import UserActivityCreate, UserActivityResponse
    >>>
    >>> # UI操作イベント作成
    >>> activity = UserActivityCreate(
    ...     action="button_click",
    ...     page_path="/projects/123",
    ...     metadata={"button_id": "save_button"}
    ... )
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseCamelCaseModel, BaseCamelCaseORMModel


class UserInfo(BaseCamelCaseORMModel):
    """ユーザー情報（埋め込み用）。

    操作履歴に埋め込むユーザー情報を定義します。

    Attributes:
        id: ユーザーID
        email: メールアドレス
        display_name: 表示名
    """

    id: uuid.UUID = Field(..., description="ユーザーID")
    email: str = Field(..., description="メールアドレス")
    display_name: str | None = Field(default=None, description="表示名")


class UserActivityCreate(BaseCamelCaseModel):
    """UI操作履歴作成リクエストスキーマ。

    フロントエンドからUI操作イベントを送信する際に使用します。

    Attributes:
        action: 操作内容（button_click, page_view, form_submit等）
        page_path: ページパス
        resource_type: リソース種別（project, session等）
        resource_id: 対象リソースのID
        metadata: 追加メタデータ

    Example:
        >>> activity = UserActivityCreate(
        ...     action="button_click",
        ...     page_path="/projects/123",
        ...     resource_type="project",
        ...     resource_id=uuid.UUID("..."),
        ...     metadata={"button_id": "save_button", "form_data": {...}}
        ... )

    Note:
        - event_typeは自動的に"ui_action"に設定されます
        - user_id、ip_address、user_agentはサーバーで設定されます
    """

    action: str = Field(..., max_length=100, description="操作内容")
    page_path: str | None = Field(default=None, max_length=255, description="ページパス")
    resource_type: str | None = Field(default=None, max_length=50, description="リソース種別")
    resource_id: uuid.UUID | None = Field(default=None, description="リソースID")
    status: str = Field(default="success", max_length=20, description="処理結果")
    error_type: str | None = Field(default=None, max_length=100, description="エラー種別")
    error_message: str | None = Field(default=None, description="エラーメッセージ")
    metadata: dict[str, Any] | None = Field(default=None, description="追加メタデータ")


class UserActivityResponse(BaseCamelCaseORMModel):
    """操作履歴レスポンススキーマ。

    操作履歴の詳細情報を返す際に使用します。

    Attributes:
        id: 操作履歴ID
        user_id: ユーザーID
        event_type: イベント種別
        action: 操作内容
        resource_type: リソース種別
        resource_id: リソースID
        endpoint: APIエンドポイント
        method: HTTPメソッド
        page_path: ページパス
        status: 処理結果
        status_code: HTTPステータスコード
        error_type: エラー種別
        error_message: エラーメッセージ
        duration_ms: 処理時間
        ip_address: クライアントIPアドレス
        user_agent: ユーザーエージェント
        metadata: 追加メタデータ
        created_at: 記録日時
        user: ユーザー情報（オプション）
    """

    id: uuid.UUID = Field(..., description="操作履歴ID")
    user_id: uuid.UUID = Field(..., description="ユーザーID")
    event_type: str = Field(..., description="イベント種別")
    action: str = Field(..., description="操作内容")
    resource_type: str | None = Field(default=None, description="リソース種別")
    resource_id: uuid.UUID | None = Field(default=None, description="リソースID")
    endpoint: str | None = Field(default=None, description="APIエンドポイント")
    method: str | None = Field(default=None, description="HTTPメソッド")
    page_path: str | None = Field(default=None, description="ページパス")
    status: str = Field(..., description="処理結果")
    status_code: int | None = Field(default=None, description="HTTPステータスコード")
    error_type: str | None = Field(default=None, description="エラー種別")
    error_message: str | None = Field(default=None, description="エラーメッセージ")
    duration_ms: int | None = Field(default=None, description="処理時間（ミリ秒）")
    ip_address: str | None = Field(default=None, description="クライアントIPアドレス")
    user_agent: str | None = Field(default=None, description="ユーザーエージェント")
    metadata: dict[str, Any] | None = Field(default=None, description="追加メタデータ")
    created_at: datetime = Field(..., description="記録日時")
    user: UserInfo | None = Field(default=None, description="ユーザー情報")


class UserActivityListResponse(BaseCamelCaseModel):
    """操作履歴一覧レスポンススキーマ。

    操作履歴一覧APIのレスポンス形式を定義します。

    Attributes:
        activities: 操作履歴リスト
        total: 総件数
        skip: スキップ数
        limit: 取得件数
    """

    activities: list[UserActivityResponse] = Field(..., description="操作履歴リスト")
    total: int = Field(..., description="総件数")
    skip: int = Field(..., description="スキップ数")
    limit: int = Field(..., description="取得件数")


class UserActivitySearchParams(BaseCamelCaseModel):
    """操作履歴検索パラメータスキーマ。

    管理者が操作履歴を検索する際のパラメータを定義します。

    Attributes:
        user_id: ユーザーID（オプション）
        event_type: イベント種別（オプション）
        action: 操作内容（オプション）
        resource_type: リソース種別（オプション）
        status: ステータス（オプション）
        start_date: 検索開始日時（オプション）
        end_date: 検索終了日時（オプション）
        skip: スキップ数
        limit: 取得件数

    Example:
        >>> params = UserActivitySearchParams(
        ...     user_id=user.id,
        ...     status="error",
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 31),
        ...     limit=50
        ... )
    """

    user_id: uuid.UUID | None = Field(default=None, description="ユーザーID")
    event_type: str | None = Field(default=None, description="イベント種別")
    action: str | None = Field(default=None, description="操作内容")
    resource_type: str | None = Field(default=None, description="リソース種別")
    status: str | None = Field(default=None, description="ステータス")
    start_date: datetime | None = Field(default=None, description="検索開始日時")
    end_date: datetime | None = Field(default=None, description="検索終了日時")
    skip: int = Field(default=0, ge=0, description="スキップ数")
    limit: int = Field(default=50, ge=1, le=100, description="取得件数")


class UserActivitySummary(BaseCamelCaseModel):
    """操作履歴サマリースキーマ。

    ユーザーの操作履歴サマリー情報を返す際に使用します。

    Attributes:
        total_activities: 総操作数
        error_count: エラー数
        api_call_count: API呼び出し数
        ui_action_count: UI操作数
        last_activity_at: 最終操作日時
    """

    total_activities: int = Field(..., description="総操作数")
    error_count: int = Field(..., description="エラー数")
    api_call_count: int = Field(..., description="API呼び出し数")
    ui_action_count: int = Field(..., description="UI操作数")
    last_activity_at: datetime | None = Field(default=None, description="最終操作日時")
