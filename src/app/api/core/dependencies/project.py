"""Projectサービス依存性。

Project関連サービスのDI定義を提供します。
- ProjectService
- ProjectFileService
- ProjectMemberService
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services import ProjectFileService, ProjectMemberService, ProjectService

__all__ = [
    "ProjectServiceDep",
    "ProjectFileServiceDep",
    "ProjectMemberServiceDep",
    "get_project_service",
    "get_project_file_service",
    "get_project_member_service",
]


def get_project_service(db: DatabaseDep) -> ProjectService:
    """プロジェクトサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        ProjectService: 初期化されたプロジェクトサービスインスタンス

    Note:
        - この関数はFastAPIのDependsで自動的に呼び出されます
        - サービスインスタンスはリクエストごとに生成されます
    """
    return ProjectService(db)


def get_project_file_service(db: DatabaseDep) -> ProjectFileService:
    """プロジェクトファイルサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        ProjectFileService: 初期化されたプロジェクトファイルサービスインスタンス

    Note:
        - この関数はFastAPIのDependsで自動的に呼び出されます
        - サービスインスタンスはリクエストごとに生成されます
    """
    return ProjectFileService(db)


def get_project_member_service(db: DatabaseDep) -> ProjectMemberService:
    """プロジェクトメンバーサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        ProjectMemberService: 初期化されたプロジェクトメンバーサービスインスタンス

    Note:
        - この関数はFastAPIのDependsで自動的に呼び出されます
        - サービスインスタンスはリクエストごとに生成されます
    """
    return ProjectMemberService(db)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
"""プロジェクトサービスの依存性型。

エンドポイント関数にProjectServiceインスタンスを自動注入します。
"""

ProjectFileServiceDep = Annotated[ProjectFileService, Depends(get_project_file_service)]
"""プロジェクトファイルサービスの依存性型。

エンドポイント関数にProjectFileServiceインスタンスを自動注入します。
"""

ProjectMemberServiceDep = Annotated[ProjectMemberService, Depends(get_project_member_service)]
"""プロジェクトメンバーサービスの依存性型。

エンドポイント関数にProjectMemberServiceインスタンスを自動注入します。
"""
