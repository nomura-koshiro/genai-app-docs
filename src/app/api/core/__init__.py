"""API層のコア機能。

依存性注入、例外ハンドリングなど、FastAPI層の基盤機能を提供します。

主な機能:
    1. **依存性注入**: データベース、サービス、認証ユーザーの注入
    2. **例外ハンドリング**: グローバル例外ハンドラーの登録

使用例:
    >>> from app.api.core import CurrentUserDep, DatabaseDep
    >>> from app.api.core import register_exception_handlers
    >>>
    >>> @router.get("/profile")
    >>> async def get_profile(
    ...     current_user: CurrentUserDep,
    ...     db: DatabaseDep,
    ... ):
    ...     return {"email": current_user.email}
"""

# 依存性注入
from app.api.core.dependencies import (
    AgentServiceDep,
    CurrentSuperuserDep,
    CurrentUserDep,
    CurrentUserOptionalDep,
    DatabaseDep,
    FileServiceDep,
    SessionServiceDep,
    UserServiceDep,
    get_agent_service,
    get_current_active_user,
    get_current_superuser,
    get_current_user_optional,
    get_db,
    get_file_service,
    get_session_service,
    get_user_service,
)

# 例外ハンドラー
from app.api.core.exception_handlers import register_exception_handlers

__all__ = [
    # Database Dependencies
    "DatabaseDep",
    "get_db",
    # Service Dependencies
    "UserServiceDep",
    "get_user_service",
    "AgentServiceDep",
    "get_agent_service",
    "FileServiceDep",
    "get_file_service",
    "SessionServiceDep",
    "get_session_service",
    # Authentication Dependencies
    "CurrentUserDep",
    "get_current_active_user",
    "CurrentSuperuserDep",
    "get_current_superuser",
    "CurrentUserOptionalDep",
    "get_current_user_optional",
    # Exception Handlers
    "register_exception_handlers",
]
