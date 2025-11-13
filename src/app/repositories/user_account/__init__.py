"""ユーザー関連のリポジトリモジュール。

このモジュールは、ユーザー管理機能に関連するデータアクセス層を提供します。

主なリポジトリ:
    - UserRepository: ユーザーのCRUD操作（メール検索、認証等）

使用例:
    >>> from app.repositories.user_account import UserRepository
    >>> async with get_db() as db:
    ...     user_repo = UserRepository(db)
    ...     user = await user_repo.get_by_email("user@example.com")
"""

from app.repositories.user_account.user_account import UserRepository

__all__ = ["UserRepository"]
