"""管理機能 API v1 エンドポイント。

このパッケージには、管理機能用のエンドポイントが含まれています。

提供される機能:
    - カテゴリマスタのCRUD
    - 検証マスタのCRUD
    - 課題マスタのCRUD
"""

from app.api.routes.v1.admin.category import admin_category_router
from app.api.routes.v1.admin.issue import admin_issue_router
from app.api.routes.v1.admin.validation import admin_validation_router

__all__ = [
    "admin_category_router",
    "admin_validation_router",
    "admin_issue_router",
]
