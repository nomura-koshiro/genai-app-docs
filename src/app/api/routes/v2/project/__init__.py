"""プロジェクトAPI v2エンドポイント。

v1と同じパス構造を維持（/project）。
"""

from app.api.routes.v1.project.project import projects_router as project_router
from app.api.routes.v1.project.project_file import project_files_router as project_file_router
from app.api.routes.v1.project.project_member import project_members_router as project_member_router

__all__ = [
    "project_router",
    "project_file_router",
    "project_member_router",
]
