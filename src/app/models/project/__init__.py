"""プロジェクト関連のSQLAlchemyモデル。

このモジュールは、プロジェクト管理機能に関連するデータベースモデルを提供します。

主なモデル:
    - Project: プロジェクトメインモデル（タイトル、説明、ステータス等）
    - ProjectMember: プロジェクトメンバー（ユーザーとプロジェクトの紐付け、ロール管理）
    - ProjectFile: プロジェクトファイル（アップロードファイルのメタデータ）

Enum定義はapp.models.enumsパッケージで一元管理されています:
    - ProjectRole: プロジェクトロール（owner, manager, member, viewer）

使用例:
    >>> from app.models.project import Project, ProjectMember
    >>> from app.models.enums import ProjectRole
    >>> project = Project(
    ...     name="新規施策検討",
    ...     description="市場拡大施策の分析",
    ...     created_by=user_id
    ... )
    >>> member = ProjectMember(
    ...     project_id=project.id,
    ...     user_id=user_id,
    ...     role=ProjectRole.PROJECT_MANAGER
    ... )
"""

from app.models.project.project import Project
from app.models.project.project_file import ProjectFile
from app.models.project.project_member import ProjectMember

__all__ = ["Project", "ProjectFile", "ProjectMember"]
