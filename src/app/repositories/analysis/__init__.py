"""分析関連のリポジトリモジュール。

このモジュールは、分析機能に関連するデータアクセス層を提供します。

主なリポジトリ:
    - AnalysisSessionRepository: 分析セッションのCRUD操作
    - AnalysisFileRepository: 分析ファイルのCRUD操作
    - AnalysisSnapshotRepository: 分析スナップショットのCRUD操作
    - AnalysisStepRepository: 分析ステップのCRUD操作
    - AnalysisChatRepository: 分析チャットのCRUD操作
    - AnalysisIssueRepository: 分析課題テンプレートのCRUD操作
    - AnalysisValidationRepository: 分析バリデーションのCRUD操作

使用例:
    >>> from app.repositories.analysis import AnalysisSessionRepository
    >>> async with get_db() as db:
    ...     session_repo = AnalysisSessionRepository(db)
    ...     session = await session_repo.get(session_id)
"""

from app.repositories.analysis.analysis_chat import AnalysisChatRepository
from app.repositories.analysis.analysis_file import AnalysisFileRepository
from app.repositories.analysis.analysis_session import AnalysisSessionRepository
from app.repositories.analysis.analysis_snapshot import AnalysisSnapshotRepository
from app.repositories.analysis.analysis_step import AnalysisStepRepository
from app.repositories.analysis.analysis_template import (
    AnalysisIssueRepository,
    AnalysisValidationRepository,
)
from app.repositories.analysis.analysis_template_repository import AnalysisTemplateRepository

__all__ = [
    "AnalysisChatRepository",
    "AnalysisFileRepository",
    "AnalysisSessionRepository",
    "AnalysisSnapshotRepository",
    "AnalysisStepRepository",
    "AnalysisIssueRepository",
    "AnalysisValidationRepository",
    "AnalysisTemplateRepository",
]
