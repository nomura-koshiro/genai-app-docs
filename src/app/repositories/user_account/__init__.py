"""ユーザー関連のリポジトリモジュール。

このモジュールは、ユーザー管理機能に関連するデータアクセス層を提供します。

主なリポジトリ:
    - UserAccountRepository: ユーザーのCRUD操作（メール検索、認証等）
    - RoleHistoryRepository: ロール変更履歴の操作

使用例:
    >>> from app.repositories.user_account import UserAccountRepository
    >>> async with get_db() as db:
    ...     user_repo = UserAccountRepository(db)
    ...     user = await user_repo.get_by_email("user@example.com")
"""

from app.repositories.user_account.role_history import RoleHistoryRepository
from app.repositories.user_account.user_account import UserAccountRepository

__all__ = ["RoleHistoryRepository", "UserAccountRepository"]
