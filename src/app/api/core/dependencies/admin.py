"""Admin管理サービス依存性。

Admin管理関連サービスのDI定義を提供します。
- AdminCategoryService
- AdminValidationService
- AdminIssueService
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services.admin import AdminCategoryService, AdminIssueService, AdminValidationService

__all__ = [
    "AdminCategoryServiceDep",
    "AdminValidationServiceDep",
    "AdminIssueServiceDep",
    "get_admin_category_service",
    "get_admin_validation_service",
    "get_admin_issue_service",
]


def get_admin_category_service(db: DatabaseDep) -> AdminCategoryService:
    """カテゴリ管理サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        AdminCategoryService: 初期化されたカテゴリ管理サービスインスタンス
    """
    return AdminCategoryService(db)


def get_admin_validation_service(db: DatabaseDep) -> AdminValidationService:
    """検証マスタ管理サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        AdminValidationService: 初期化された検証マスタ管理サービスインスタンス
    """
    return AdminValidationService(db)


def get_admin_issue_service(db: DatabaseDep) -> AdminIssueService:
    """課題マスタ管理サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        AdminIssueService: 初期化された課題マスタ管理サービスインスタンス
    """
    return AdminIssueService(db)


AdminCategoryServiceDep = Annotated[AdminCategoryService, Depends(get_admin_category_service)]
"""カテゴリ管理サービスの依存性型。"""

AdminValidationServiceDep = Annotated[AdminValidationService, Depends(get_admin_validation_service)]
"""検証マスタ管理サービスの依存性型。"""

AdminIssueServiceDep = Annotated[AdminIssueService, Depends(get_admin_issue_service)]
"""課題マスタ管理サービスの依存性型。"""
