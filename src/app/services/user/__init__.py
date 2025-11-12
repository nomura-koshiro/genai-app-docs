"""ユーザー関連のビジネスロジックサービス。

このモジュールは、ユーザー管理機能に関連するビジネスロジックを提供します。

主なサービス:
    - UserService: ユーザー管理サービス（ユーザー作成、更新、認証、ロール管理）

使用例:
    >>> from app.services.user import UserService
    >>> from app.schemas.user import UserUpdate
    >>>
    >>> async with get_db() as db:
    ...     user_service = UserService(db)
    ...     user = await user_service.get_by_email("user@example.com")
    ...     updated = await user_service.update(
    ...         user_id=user.id,
    ...         user_update=UserUpdate(full_name="新しい名前")
    ...     )
"""

from app.services.user.user import UserService

__all__ = ["UserService"]
