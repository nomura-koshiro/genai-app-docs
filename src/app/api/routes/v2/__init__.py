"""API v2 エンドポイント。

このパッケージには、API v2のビジネスロジック用エンドポイントが含まれています。
v2ではパス構造を整理・統一しています。

パス変更一覧（v1 → v2）:
    - /project/{id}/analysis/session → /project/{id}/session
    - /project/{id}/analysis/template → /project/{id}/template
    - /project/{id}/driver-tree/tree → /project/{id}/tree
    - /project/{id}/driver-tree/node → /project/{id}/node
    - /project/{id}/driver-tree/file → /project/{id}/tree-file
    - /project/{id}/driver-tree/category → /project/{id}/tree-category
    - /project/{id}/driver-tree/formula → /project/{id}/tree-formula
    - /user_account → /user
"""

from app.api.routes.v2.project import (
    project_router,
    project_file_router,
    project_member_router,
)
from app.api.routes.v2.session import session_router
from app.api.routes.v2.template import template_router
from app.api.routes.v2.tree import (
    tree_router,
    tree_file_router,
    tree_node_router,
)
from app.api.routes.v2.user import user_router
from app.api.routes.v2.dashboard import dashboard_router

__all__ = [
    # Dashboard API
    "dashboard_router",
    # Project API
    "project_router",
    "project_file_router",
    "project_member_router",
    # Session API
    "session_router",
    # Template API
    "template_router",
    # Tree API
    "tree_router",
    "tree_file_router",
    "tree_node_router",
    # User API
    "user_router",
]
