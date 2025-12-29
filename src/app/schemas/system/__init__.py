"""システム関連のPydanticスキーマ。

このモジュールは、システム管理に関連するリクエスト/レスポンススキーマを提供します。

主なスキーマ:
    ユーザー操作履歴:
        - UserActivityCreate: 操作履歴作成リクエスト（UI操作用）
        - UserActivityResponse: 操作履歴レスポンス
        - UserActivityListResponse: 操作履歴一覧レスポンス
        - UserActivitySearchParams: 検索パラメータ
"""

from app.schemas.system.user_activity import (
    UserActivityCreate,
    UserActivityListResponse,
    UserActivityResponse,
    UserActivitySearchParams,
    UserActivitySummary,
    UserInfo,
)

__all__ = [
    "UserActivityCreate",
    "UserActivityResponse",
    "UserActivityListResponse",
    "UserActivitySearchParams",
    "UserActivitySummary",
    "UserInfo",
]
