"""ユーザー関連のPydanticスキーマ。

このモジュールは、ユーザー管理機能に関連するリクエスト/レスポンススキーマを提供します。

主なスキーマ:
    - UserAccountResponse: ユーザー詳細レスポンス
    - UserAccountUpdate: ユーザー更新リクエスト
    - UserAccountListResponse: ユーザー一覧レスポンス

使用例:
    >>> from app.schemas.user_account import UserAccountUpdate, UserAccountResponse
    >>> user_update = UserAccountUpdate(full_name="新しい名前")
    >>> # API経由でユーザー情報を更新
"""

from app.schemas.user_account.user_account import (
    UserAccountListResponse,
    UserAccountResponse,
    UserAccountRoleUpdate,
    UserAccountUpdate,
)

__all__ = ["UserAccountListResponse", "UserAccountResponse", "UserAccountRoleUpdate", "UserAccountUpdate"]
