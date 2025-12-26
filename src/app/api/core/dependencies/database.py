"""データベース依存性。

データベースセッションのDI定義を提供します。
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

__all__ = [
    "DatabaseDep",
    "get_db",
]

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
"""データベースセッションの依存性型。

FastAPIのDependsを使用して、エンドポイント関数に非同期データベースセッションを
自動的に注入します。セッションのライフサイクルはリクエストごとに管理されます。
"""
