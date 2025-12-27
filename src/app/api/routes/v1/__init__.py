"""API v1 エンドポイント。

このパッケージには、API v1のビジネスロジック用エンドポイントが含まれています。
"""

from app.api.routes.v1.admin import (
    admin_category_router,
    admin_issue_router,
    admin_validation_router,
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
    # Admin API
    "admin_category_router",
    "admin_validation_router",
    "admin_issue_router",
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
