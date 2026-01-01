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
    - システム管理機能（SA-001〜SA-043）
"""

# 既存の管理機能ルーター
# システム管理機能ルーター
from app.api.routes.v1.admin.activity_logs import activity_logs_router
from app.api.routes.v1.admin.audit_logs import audit_logs_router
from app.api.routes.v1.admin.bulk_operations import bulk_operations_router
from app.api.routes.v1.admin.category import admin_category_router
from app.api.routes.v1.admin.data_management import data_management_router
from app.api.routes.v1.admin.dummy_chart import admin_dummy_chart_router
from app.api.routes.v1.admin.dummy_formula import admin_dummy_formula_router
from app.api.routes.v1.admin.graph_axis import admin_graph_axis_router
from app.api.routes.v1.admin.issue import admin_issue_router
from app.api.routes.v1.admin.notifications import notifications_router
from app.api.routes.v1.admin.projects_admin import admin_projects_router
from app.api.routes.v1.admin.role import admin_role_router
from app.api.routes.v1.admin.security import security_router
from app.api.routes.v1.admin.settings import settings_router
from app.api.routes.v1.admin.statistics import statistics_router
from app.api.routes.v1.admin.support_tools import support_tools_router
from app.api.routes.v1.admin.validation import admin_validation_router

__all__ = [
    # 既存の管理機能ルーター
    "admin_category_router",
    "admin_dummy_chart_router",
    "admin_dummy_formula_router",
    "admin_graph_axis_router",
    "admin_issue_router",
    "admin_role_router",
    "admin_validation_router",
    # システム管理機能ルーター
    "activity_logs_router",
    "admin_projects_router",
    "audit_logs_router",
    "bulk_operations_router",
    "data_management_router",
    "notifications_router",
    "security_router",
    "settings_router",
    "statistics_router",
    "support_tools_router",
]
