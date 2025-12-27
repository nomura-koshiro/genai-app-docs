"""管理機能のPydanticスキーマ。

このモジュールは、管理機能（カテゴリ、検証、課題マスタ、ロール）のスキーマを提供します。
"""

from app.schemas.admin.category import (
    DriverTreeCategoryCreate,
    DriverTreeCategoryListResponse,
    DriverTreeCategoryResponse,
    DriverTreeCategoryUpdate,
)
from app.schemas.admin.issue import (
    AnalysisIssueCreate,
    AnalysisIssueListResponse,
    AnalysisIssueResponse,
    AnalysisIssueUpdate,
)
from app.schemas.admin.role import (
    AllRolesResponse,
    ProjectRoleListResponse,
    RoleInfo,
    SystemRoleListResponse,
)
from app.schemas.admin.validation import (
    AnalysisValidationCreate,
    AnalysisValidationListResponse,
    AnalysisValidationResponse,
    AnalysisValidationUpdate,
)

__all__ = [
    # Category
    "DriverTreeCategoryCreate",
    "DriverTreeCategoryListResponse",
    "DriverTreeCategoryResponse",
    "DriverTreeCategoryUpdate",
    # Issue
    "AnalysisIssueCreate",
    "AnalysisIssueListResponse",
    "AnalysisIssueResponse",
    "AnalysisIssueUpdate",
    # Role
    "AllRolesResponse",
    "ProjectRoleListResponse",
    "RoleInfo",
    "SystemRoleListResponse",
    # Validation
    "AnalysisValidationCreate",
    "AnalysisValidationListResponse",
    "AnalysisValidationResponse",
    "AnalysisValidationUpdate",
]
