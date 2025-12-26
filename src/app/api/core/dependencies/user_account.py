"""UserAccountサービス依存性。

UserAccountServiceのDI定義を提供します。
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services import UserAccountService

__all__ = [
    "UserServiceDep",
    "get_user_service",
]


def get_user_service(db: DatabaseDep) -> UserAccountService:
    """ユーザーサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        UserAccountService: 初期化されたユーザーサービスインスタンス

    Note:
        - この関数はFastAPIのDependsで自動的に呼び出されます
        - サービスインスタンスはリクエストごとに生成されます
    """
    return UserAccountService(db)


UserServiceDep = Annotated[UserAccountService, Depends(get_user_service)]
"""ユーザーサービスの依存性型。

エンドポイント関数にUserAccountServiceインスタンスを自動注入します。
"""
