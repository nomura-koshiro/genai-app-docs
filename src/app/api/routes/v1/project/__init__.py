"""プロジェクト API v1 エンドポイント。

このパッケージには、プロジェクト管理機能用のエンドポイントが含まれています。

提供されるルーター:
    - projects_router: プロジェクト管理（作成、更新、削除、一覧取得）
    - project_files_router: プロジェクトファイル管理（アップロード、削除、一覧）
    - project_members_router: プロジェクトメンバー管理（追加、削除、ロール変更）

主な機能:
    プロジェクト:
        - プロジェクトの作成・更新・削除
        - プロジェクト一覧の取得
        - プロジェクト詳細の取得

    ファイル:
        - ファイルのアップロード
        - ファイル一覧の取得
        - ファイルの削除

    メンバー:
        - メンバーの追加・削除
        - メンバー一括追加・更新
        - ロールの変更（owner, manager, member, viewer）

使用例:
    >>> # プロジェクト作成
    >>> POST /api/v1/projects
    >>> {"name": "新規施策検討", "description": "..."}
    >>>
    >>> # メンバー追加
    >>> POST /api/v1/projects/{project_id}/members
    >>> {"user_id": "...", "role": "manager"}
"""

from app.api.routes.v1.project.project import projects_router
from app.api.routes.v1.project.project_file import project_files_router
from app.api.routes.v1.project.project_member import project_members_router

__all__ = ["projects_router", "project_files_router", "project_members_router"]
