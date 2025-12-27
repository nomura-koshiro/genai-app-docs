"""管理機能 API v1 エンドポイント。

このパッケージには、管理機能用のエンドポイントが含まれています。

提供される機能:
    - カテゴリマスタのCRUD
    - 検証マスタのCRUD
    - 課題マスタのCRUD
    - グラフ軸マスタのCRUD
    - ダミー数式マスタのCRUD
    - ダミーチャートマスタのCRUD
    - ロール一覧取得
"""

from app.api.routes.v1.admin.category import admin_category_router
from app.api.routes.v1.admin.dummy_chart import admin_dummy_chart_router
from app.api.routes.v1.admin.dummy_formula import admin_dummy_formula_router
from app.api.routes.v1.admin.graph_axis import admin_graph_axis_router
from app.api.routes.v1.admin.issue import admin_issue_router
from app.api.routes.v1.admin.role import admin_role_router
from app.api.routes.v1.admin.validation import admin_validation_router

__all__ = [
    "admin_category_router",
    "admin_dummy_chart_router",
    "admin_dummy_formula_router",
    "admin_graph_axis_router",
    "admin_issue_router",
    "admin_role_router",
    "admin_validation_router",
]
