"""分析状態管理サービス（ファサード）。

このモジュールは、分析状態管理の統一インターフェースを提供します。
各機能は専門のサービスクラスに委譲されています。

元ファイル:
    C:/developments/camp-backend-code-analysis/app/agents/analysis/state.py

リファクタリング後の構成:
    - AnalysisDataManager: データ管理（data_manager.py）
    - AnalysisOverviewProvider: 概要生成（overview_provider.py）
    - AnalysisStepManager: ステップ管理（step_manager.py）
    - AnalysisSnapshotManager: スナップショット管理（snapshot_manager.py）
    - AnalysisState: ファサード（このファイル）

主な機能:
    - データアップロード・削除管理
    - ステップの追加・削除・実行
    - ステップ設定の取得・更新
    - データ概要の取得
    - スナップショット管理

使用例:
    >>> from app.services.analysis.agent.state import AnalysisState
    >>>
    >>> async with get_db() as db:
    ...     state = AnalysisState(db, session_id)
    ...
    ...     # データアップロード
    ...     await state.upload_data({
    ...         "id": file_id,
    ...         "file_name": "sales.csv",
    ...         "table_name": "売上データ",
    ...         "table_axis": ["地域", "商品"],
    ...         "data": df
    ...     })
    ...
    ...     # ステップ追加
    ...     await state.add_step("売上フィルタ", "filter", "original")
    ...
    ...     # ステップ設定と実行
    ...     await state.set_config(0, {
    ...         "category_filter": {"地域": ["東京", "大阪"]}
    ...     })
"""

import uuid
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

from .data_manager import AnalysisDataManager
from .overview_provider import AnalysisOverviewProvider
from .snapshot_manager import AnalysisSnapshotManager
from .step_manager import AnalysisStepManager

logger = get_logger(__name__)


class AnalysisState:
    """DB永続化版の分析状態管理ファサードクラス。

    このクラスは既存のAPIを維持しながら、各機能を専門のマネージャークラスに委譲します。

    Attributes:
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): セッションID
        data_manager (AnalysisDataManager): データ管理マネージャー
        overview_provider (AnalysisOverviewProvider): 概要生成プロバイダー
        step_manager (AnalysisStepManager): ステップ管理マネージャー
        snapshot_manager (AnalysisSnapshotManager): スナップショット管理マネージャー

    Example:
        >>> async with get_db() as db:
        ...     state = AnalysisState(db, session_id)
        ...     await state.set_source_data(df)
        ...     await state.add_step("フィルタ", "filter", "original")
    """

    def __init__(self, db: AsyncSession, session_id: uuid.UUID):
        """分析状態管理を初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
            session_id (uuid.UUID): セッションのUUID

        Note:
            - セッションの存在確認は行わないため、呼び出し側で確認すること
        """
        self.db = db
        self.session_id = session_id

        # 専門マネージャーの初期化
        self.data_manager = AnalysisDataManager(db, session_id)
        self.overview_provider = AnalysisOverviewProvider(db, session_id)
        self.step_manager = AnalysisStepManager(db, session_id)
        self.snapshot_manager = AnalysisSnapshotManager(db, session_id)

        logger.info(
            "分析状態管理ファサードを初期化しました",
            session_id=str(session_id),
        )

    # ===== Data Management Methods (AnalysisDataManager) =====

    async def upload_data(self, upload_file: dict[str, Any]) -> None:
        """アップロードされたデータを登録します。"""
        return await self.data_manager.upload_data(upload_file)

    async def delete_data(self, id: str) -> None:
        """指定されたIDのアップロードデータを削除します。"""
        return await self.data_manager.delete_data(id)

    async def set_source_data(self, data: pd.DataFrame) -> None:
        """アップロードされたデータを元に、元のデータフレームを設定します。"""
        return await self.data_manager.set_source_data(data)

    async def get_source_data(self, step_index: int | None = None) -> pd.DataFrame:
        """ステップのデータソースを取得します。"""
        return await self.data_manager.get_source_data(step_index)

    # ===== Overview Methods (AnalysisOverviewProvider) =====

    async def get_data_overview(self) -> str:
        """original_df及び全てのステップの結果データの概要を取得します。"""
        return await self.overview_provider.get_data_overview()

    async def get_step_overview(self, index: int | None = None) -> str:
        """現在の全ての分析ステップの概要を取得します。"""
        return await self.overview_provider.get_step_overview(index)

    # ===== Step Management Methods (AnalysisStepManager) =====

    async def clear(self) -> None:
        """全てのステップと会話履歴をクリアします。"""
        return await self.step_manager.clear()

    async def add_step(self, name: str, type: str, data: str = "original") -> None:
        """新しいステップを追加します。"""
        return await self.step_manager.add_step(name, type, data)

    async def delete_step(self, step_index: int) -> None:
        """指定したステップを削除します。"""
        return await self.step_manager.delete_step(step_index)

    async def apply(self, step_index: int, include_following: bool = True) -> None:
        """指定したステップの設定を適用し、結果を更新します。"""
        return await self.step_manager.apply(step_index, include_following)

    async def get_config(self, step_index: int) -> dict[str, Any]:
        """指定したステップの設定を取得します。"""
        return await self.step_manager.get_config(step_index)

    async def set_config(self, step_index: int, config: dict[str, Any]) -> str:
        """指定したステップに設定を追加し、適用します。

        このメソッドは複数のマネージャーを組み合わせて動作します：
        1. データマネージャーからソースデータを取得
        2. ステップマネージャーで設定を更新・実行
        3. 概要プロバイダーから結果概要を取得

        Args:
            step_index (int): 設定を追加するステップのインデックス
            config (dict[str, Any]): 設定の内容

        Returns:
            str: ステップの概要（get_step_overview()の結果）

        Raises:
            IndexError: step_indexが範囲外の場合
            ValidationError: 設定が不正な場合
        """
        # ソースデータを取得
        source_data = await self.data_manager.get_source_data(step_index)

        # 設定を更新・実行
        await self.step_manager.set_config(step_index, config, source_data)

        # 概要を取得して返す
        overview = await self.overview_provider.get_step_overview(step_index)
        return overview

    # ===== Snapshot Management Methods (AnalysisSnapshotManager) =====

    async def get_snapshot_id(self) -> int:
        """現在のスナップショットIDを取得します。"""
        return await self.snapshot_manager.get_snapshot_id()

    async def save_snapshot(self, current_snapshot: bool = False) -> int:
        """現在のステップの状態をスナップショットとして保存します。"""
        return await self.snapshot_manager.save_snapshot(current_snapshot)

    async def revert_snapshot(self, snapshot_id: int) -> None:
        """指定したスナップショットIDの状態に戻します。"""
        return await self.snapshot_manager.revert_snapshot(snapshot_id)
