"""Analysisサービス依存性。

Analysis関連サービスのDI定義を提供します。
- AnalysisTemplateService
- AnalysisSessionService
"""

from typing import Annotated

from fastapi import Depends

from app.api.core.dependencies.database import DatabaseDep
from app.services.analysis import AnalysisSessionService, AnalysisTemplateService

__all__ = [
    "AnalysisTemplateServiceDep",
    "AnalysisSessionServiceDep",
    "get_analysis_template_service",
    "get_analysis_session_service",
]


def get_analysis_template_service(db: DatabaseDep) -> AnalysisTemplateService:
    """分析テンプレートサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        AnalysisTemplateService: 初期化された分析テンプレートサービスインスタンス
    """
    return AnalysisTemplateService(db)


def get_analysis_session_service(db: DatabaseDep) -> AnalysisSessionService:
    """分析セッションサービスインスタンスを生成するDIファクトリ関数。

    Args:
        db (AsyncSession): データベースセッション（自動注入）

    Returns:
        AnalysisSessionService: 初期化された分析セッションサービスインスタンス
    """
    return AnalysisSessionService(db)


AnalysisTemplateServiceDep = Annotated[AnalysisTemplateService, Depends(get_analysis_template_service)]
"""分析テンプレートサービスの依存性型。

エンドポイント関数にAnalysisTemplateServiceインスタンスを自動注入します。
"""

AnalysisSessionServiceDep = Annotated[AnalysisSessionService, Depends(get_analysis_session_service)]
"""分析セッションサービスの依存性型。

エンドポイント関数にAnalysisSessionServiceインスタンスを自動注入します。
"""
