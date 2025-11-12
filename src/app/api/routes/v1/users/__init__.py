"""ユーザー API v1 エンドポイント。

このパッケージには、ユーザー管理機能用のエンドポイントが含まれています。

提供される機能:
    - ユーザー一覧の取得
    - ユーザー詳細の取得
    - ユーザー情報の更新
    - ユーザーの削除

使用例:
    >>> # ユーザー一覧取得
    >>> GET /api/v1/users
    >>> {"users": [...], "total": 10}
    >>>
    >>> # ユーザー情報更新
    >>> PUT /api/v1/users/{user_id}
    >>> {"full_name": "新しい名前"}
"""

from app.api.routes.v1.users.users import router

__all__ = ["router"]
