"""ユーザー関連のビジネスロジックサービス。

このモジュールは、ユーザー管理機能に関連するビジネスロジックを提供します。

主なサービス:
    - UserAccountService: ユーザー管理サービス（ユーザー作成、更新、認証、ロール管理）
    - RoleHistoryService: ロール変更履歴サービス

使用例:
    >>> from app.services.user_account import UserAccountService
    >>> from app.schemas.user_account import UserAccountUpdate
    >>>
    >>> async with get_db() as db:
    ...     user_service = UserAccountService(db)
    ...     user = await user_service.get_by_email("user@example.com")
    ...     updated = await user_service.update(
    ...         user_id=user.id,
    ...         user_update=UserAccountUpdate(full_name="新しい名前")
    ...     )
"""

from app.services.user_account.role_history import RoleHistoryService
from app.services.user_account.user_account import UserAccountService

__all__ = ["RoleHistoryService", "UserAccountService"]
