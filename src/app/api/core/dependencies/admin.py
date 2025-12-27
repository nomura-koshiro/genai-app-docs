"""Admin管理サービス依存性。

Admin管理関連サービスのDI定義を提供します。
- AdminCategoryService
- AdminValidationService
- AdminIssueService
- AdminGraphAxisService
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services.admin import (
    AdminCategoryService,
    AdminDummyChartService,
    AdminDummyFormulaService,
    AdminGraphAxisService,
    AdminIssueService,
    AdminValidationService,
)

__all__ = [
    "AdminCategoryServiceDep",
    "AdminDummyChartServiceDep",
    "AdminDummyFormulaServiceDep",
    "AdminGraphAxisServiceDep",
    "AdminIssueServiceDep",
    "AdminValidationServiceDep",
    "get_admin_category_service",
    "get_admin_dummy_chart_service",
    "get_admin_dummy_formula_service",
    "get_admin_graph_axis_service",
    "get_admin_issue_service",
    "get_admin_validation_service",
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


def get_admin_graph_axis_service(db: DatabaseDep) -> AdminGraphAxisService:
    """グラフ軸マスタ管理サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        AdminGraphAxisService: 初期化されたグラフ軸マスタ管理サービスインスタンス
    """
    return AdminGraphAxisService(db)


AdminGraphAxisServiceDep = Annotated[AdminGraphAxisService, Depends(get_admin_graph_axis_service)]
"""グラフ軸マスタ管理サービスの依存性型。"""


def get_admin_dummy_formula_service(db: DatabaseDep) -> AdminDummyFormulaService:
    """ダミー数式マスタ管理サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        AdminDummyFormulaService: 初期化されたダミー数式マスタ管理サービスインスタンス
    """
    return AdminDummyFormulaService(db)


AdminDummyFormulaServiceDep = Annotated[AdminDummyFormulaService, Depends(get_admin_dummy_formula_service)]
"""ダミー数式マスタ管理サービスの依存性型。"""


def get_admin_dummy_chart_service(db: DatabaseDep) -> AdminDummyChartService:
    """ダミーチャートマスタ管理サービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        AdminDummyChartService: 初期化されたダミーチャートマスタ管理サービスインスタンス
    """
    return AdminDummyChartService(db)


AdminDummyChartServiceDep = Annotated[AdminDummyChartService, Depends(get_admin_dummy_chart_service)]
"""ダミーチャートマスタ管理サービスの依存性型。"""
