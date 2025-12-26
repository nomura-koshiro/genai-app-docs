"""データアクセス層のリポジトリモジュール。

このモジュールは、全てのリポジトリクラスを集約してエクスポートします。

リポジトリカテゴリ:
    1. **分析 (Analysis)**: 分析セッション、ファイル、スナップショット等
    2. **ドライバーツリー (Driver Tree)**: ツリー、ノード、数式、施策等
    3. **プロジェクト (Project)**: プロジェクト、ファイル、メンバー
    4. **ユーザーアカウント (User Account)**: ユーザー管理

使用例:
    >>> from app.repositories import AnalysisSessionRepository, ProjectRepository
    >>> async with get_db() as db:
    ...     session_repo = AnalysisSessionRepository(db)
    ...     project_repo = ProjectRepository(db)
"""

from app.repositories.analysis import (
    AnalysisFileRepository,
    AnalysisIssueRepository,
    AnalysisSessionRepository,
    AnalysisSnapshotRepository,
    AnalysisStepRepository,
    AnalysisValidationRepository,
)
from app.repositories.driver_tree import (
    DriverTreeFileRepository,
    DriverTreeFormulaRepository,
    DriverTreeNodeRepository,
    DriverTreePolicyRepository,
    DriverTreeRepository,
)
from app.repositories.project import (
    ProjectFileRepository,
    ProjectMemberRepository,
    ProjectRepository,
)
from app.repositories.user_account import UserAccountRepository

__all__ = [
    # Analysis
    "AnalysisFileRepository",
    "AnalysisIssueRepository",
    "AnalysisSessionRepository",
    "AnalysisSnapshotRepository",
    "AnalysisStepRepository",
    "AnalysisValidationRepository",
    # Driver Tree
    "DriverTreeRepository",
    "DriverTreeFileRepository",
    "DriverTreeNodeRepository",
    "DriverTreeFormulaRepository",
    "DriverTreePolicyRepository",
    # Project
    "ProjectRepository",
    "ProjectFileRepository",
    "ProjectMemberRepository",
    # User Account
    "UserAccountRepository",
]
