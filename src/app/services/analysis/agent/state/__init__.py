"""分析状態管理モジュール。

このモジュールは、分析状態管理の統一インターフェース（AnalysisState）と
専門のマネージャークラスを提供します。

主要クラス:
    - AnalysisState: ファサードクラス（推奨）
    - AnalysisDataManager: データ管理
    - AnalysisOverviewProvider: 概要生成
    - AnalysisStepManager: ステップ管理
    - AnalysisSnapshotManager: スナップショット管理

使用例:
    >>> from app.services.analysis.agent.state import AnalysisState
    >>>
    >>> async with get_db() as db:
    ...     state = AnalysisState(db, session_id)
    ...     await state.set_source_data(df)
    ...     await state.add_step("フィルタ", "filter", "original")
"""

from .data_manager import AnalysisDataManager
from .overview_provider import AnalysisOverviewProvider
from .snapshot_manager import AnalysisSnapshotManager
from .state_facade import AnalysisState
from .step_manager import AnalysisStepManager

__all__ = [
    "AnalysisState",
    "AnalysisDataManager",
    "AnalysisOverviewProvider",
    "AnalysisStepManager",
    "AnalysisSnapshotManager",
]
