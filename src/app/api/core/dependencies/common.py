"""共通サービス依存性。

UserContextService等のDI定義を提供します。
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services.common import UserContextService

__all__ = [
    "UserContextServiceDep",
    "get_user_context_service",
]


def get_user_context_service(db: DatabaseDep) -> UserContextService:
    """ユーザーコンテキストサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        UserContextService: 初期化されたユーザーコンテキストサービスインスタンス
    """
    return UserContextService(db)


UserContextServiceDep = Annotated[UserContextService, Depends(get_user_context_service)]
"""ユーザーコンテキストサービスの依存性型。

エンドポイント関数にUserContextServiceインスタンスを自動注入します。
"""
