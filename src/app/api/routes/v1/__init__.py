"""API v1 エンドポイント。

このパッケージには、API v1のビジネスロジック用エンドポイントが含まれています。
"""

from app.api.routes.v1.admin import (
    # 既存の管理機能ルーター
    admin_category_router,
    admin_dummy_chart_router,
    admin_dummy_formula_router,
    admin_graph_axis_router,
    admin_issue_router,
    admin_role_router,
    admin_validation_router,
    # システム管理機能ルーター
    activity_logs_router,
    audit_logs_router,
    bulk_operations_router,
    data_management_router,
    notifications_router,
    security_router,
    settings_router,
    statistics_router,
    support_tools_router,
)
from app.api.routes.v1.analysis import (
    analysis_sessions_router,
    analysis_templates_router,
)
from app.api.routes.v1.dashboard import dashboard_router
from app.api.routes.v1.driver_tree import (
    driver_tree_files_router,
    driver_tree_nodes_router,
    driver_tree_trees_router,
)
from app.api.routes.v1.project import (
    project_files_router,
    project_members_router,
    projects_router,
)
from app.api.routes.v1.user_accounts import user_accounts_router

__all__ = [
    # Admin API（既存）
    "admin_category_router",
    "admin_dummy_chart_router",
    "admin_dummy_formula_router",
    "admin_graph_axis_router",
    "admin_issue_router",
    "admin_role_router",
    "admin_validation_router",
    # Admin API（システム管理）
    "activity_logs_router",
    "audit_logs_router",
    "bulk_operations_router",
    "data_management_router",
    "notifications_router",
    "security_router",
    "settings_router",
    "statistics_router",
    "support_tools_router",
    # Analysis API
    "analysis_sessions_router",
    "analysis_templates_router",
    # Dashboard API
    "dashboard_router",
    # Driver Tree API
    "driver_tree_files_router",
    "driver_tree_nodes_router",
    "driver_tree_trees_router",
    # Project API
    "project_files_router",
    "project_members_router",
    "projects_router",
    # User Account API
    "user_accounts_router",
]
