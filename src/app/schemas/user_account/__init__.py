"""ユーザー関連のPydanticスキーマ。

このモジュールは、ユーザー管理機能に関連するリクエスト/レスポンススキーマを提供します。

主なスキーマ:
    - UserResponse: ユーザー詳細レスポンス
    - UserUpdate: ユーザー更新リクエスト
    - UserListResponse: ユーザー一覧レスポンス

使用例:
    >>> from app.schemas.user_account import UserUpdate, UserResponse
    >>> user_update = UserUpdate(full_name="新しい名前")
    >>> # API経由でユーザー情報を更新
"""

from app.schemas.user_account.user_account import UserListResponse, UserResponse, UserUpdate

__all__ = ["UserListResponse", "UserResponse", "UserUpdate"]
