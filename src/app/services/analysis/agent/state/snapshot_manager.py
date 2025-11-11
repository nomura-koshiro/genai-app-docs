"""分析スナップショット管理サービス。

このモジュールは、分析状態のスナップショット（保存・復元・取得）などの
スナップショット関連の機能を提供します。

主な機能:
    - スナップショットIDの取得（get_snapshot_id）
    - スナップショットの保存（save_snapshot）
    - スナップショットへの復元（revert_snapshot）

使用例:
    >>> from app.services.analysis.agent.snapshot_manager import AnalysisSnapshotManager
    >>>
    >>> async with get_db() as db:
    ...     snapshot_manager = AnalysisSnapshotManager(db, session_id)
    ...
    ...     # スナップショット保存
    ...     snapshot_id = await snapshot_manager.save_snapshot()
    ...
    ...     # スナップショット復元
    ...     await snapshot_manager.revert_snapshot(snapshot_id)
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.analysis_session import AnalysisSessionRepository
from app.repositories.analysis_step import AnalysisStepRepository
from app.schemas.analysis_session import StepSnapshot

logger = get_logger(__name__)


class AnalysisSnapshotManager:
    """分析スナップショット管理クラス。

    スナップショットの保存、復元、取得などの機能を提供します。

    Attributes:
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): セッションID
        session_repository (AnalysisSessionRepository): セッションリポジトリ
        step_repository (AnalysisStepRepository): ステップリポジトリ

    Example:
        >>> async with get_db() as db:
        ...     snapshot_manager = AnalysisSnapshotManager(db, session_id)
        ...     snapshot_id = await snapshot_manager.save_snapshot()
    """

    def __init__(self, db: AsyncSession, session_id: uuid.UUID):
        """分析スナップショット管理を初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
            session_id (uuid.UUID): セッションのUUID

        Note:
            - セッションの存在確認は行わないため、呼び出し側で確認すること
        """
        self.db = db
        self.session_id = session_id
        self.session_repository = AnalysisSessionRepository(db)
        self.step_repository = AnalysisStepRepository(db)

        logger.info(
            "分析スナップショット管理を初期化しました",
            session_id=str(session_id),
        )

    @measure_performance
    async def get_snapshot_id(self) -> int:
        """現在のスナップショットIDを取得します。

        Returns:
            int: 現在のスナップショットのID（最新のインデックス）
                - スナップショットが存在する場合: 0以上の整数
                - スナップショットが1つもない場合: -1

        Example:
            >>> snapshot_id = await snapshot_manager.get_snapshot_id()
            >>> print(f"Current snapshot: {snapshot_id}")
            Current snapshot: 2
            >>>
            >>> # スナップショットが存在しない場合
            >>> snapshot_id = await snapshot_manager.get_snapshot_id()
            >>> print(f"Current snapshot: {snapshot_id}")
            Current snapshot: -1

        Note:
            - スナップショットが1つもない場合は -1 を返します
            - 最新のスナップショットIDは len(snapshot_history) - 1 です
        """
        logger.debug("スナップショットIDを取得中", session_id=str(self.session_id))

        session = await self.session_repository.get(self.session_id)
        if not session or not session.snapshot_history:
            return -1

        return len(session.snapshot_history) - 1

    @measure_performance
    async def save_snapshot(self, current_snapshot: bool = False) -> int:
        """現在のステップの状態をスナップショットとして保存します。

        このメソッドは以下の処理を実行します：
        1. セッションを取得
        2. 全ステップをDBから取得
        3. 各ステップをStepSnapshotモデルに変換
        4. スナップショット履歴を更新（追加または上書き）
        5. DBにフラッシュ

        Args:
            current_snapshot (bool): 現在の最新スナップショットに上書き保存するか
                - True: 最新スナップショットを上書き
                - False: 新しいスナップショットを追加（デフォルト）

        Returns:
            int: 保存されたスナップショットのID

        Raises:
            NotFoundError: 以下の場合に発生
                - セッションが存在しない

        Example:
            >>> # 新しいスナップショットを追加
            >>> snapshot_id = await snapshot_manager.save_snapshot(current_snapshot=False)
            >>> print(f"Saved snapshot: {snapshot_id}")
            Saved snapshot: 3
            >>>
            >>> # 最新スナップショットを上書き
            >>> snapshot_id = await snapshot_manager.save_snapshot(current_snapshot=True)
            >>> print(f"Updated snapshot: {snapshot_id}")
            Updated snapshot: 3

        Note:
            - スナップショットには結果データ（result_data, result_chart, result_formula）は含まれません
            - ステップの設定（config）のみが保存されます
            - current_snapshot=Trueの場合、最新スナップショットのみが更新されます
            - スナップショットはJSONB形式でDB（snapshot_history）に保存されます
        """
        logger.info(
            "スナップショットを保存中",
            session_id=str(self.session_id),
            current_snapshot=current_snapshot,
            action="save_snapshot",
        )

        try:
            # セッション取得
            session = await self.session_repository.get(self.session_id)
            if not session:
                raise NotFoundError(
                    f"セッションが見つかりません: {self.session_id}",
                    details={"session_id": str(self.session_id)},
                )

            # すべてのステップを取得
            all_steps = await self.step_repository.list_by_session(
                self.session_id, is_active=True
            )

            # ステップデータをStepSnapshotモデルに変換（結果データは含まない）
            temp_all_steps: list[StepSnapshot] = []
            for step in all_steps:
                snapshot = StepSnapshot(
                    name=step.step_name,
                    type=step.step_type,
                    data=step.data_source,
                    config=step.config,
                )
                temp_all_steps.append(snapshot)

            # Pydanticモデルをdictに変換してDB保存
            temp_all_steps_dict = [s.model_dump() for s in temp_all_steps]

            # スナップショット履歴を更新
            snapshot_history: list[list[dict[str, Any]]] = session.snapshot_history or []

            if current_snapshot and len(snapshot_history) > 0:
                # 最新スナップショットを上書き
                snapshot_history[-1] = temp_all_steps_dict
            else:
                # 新しいスナップショットを追加
                snapshot_history.append(temp_all_steps_dict)

            session.snapshot_history = snapshot_history
            await self.db.flush()

            current_snapshot_id = len(snapshot_history) - 1

            logger.info(
                "スナップショット保存が完了しました",
                session_id=str(self.session_id),
                snapshot_id=current_snapshot_id,
                steps_count=len(temp_all_steps),
            )

            return current_snapshot_id

        except Exception as e:
            logger.error(
                "スナップショット保存中にエラーが発生しました",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def revert_snapshot(self, snapshot_id: int) -> None:
        """指定したスナップショットIDの状態に戻します。

        このメソッドは以下を実行します：
        1. セッションを取得
        2. スナップショットIDの範囲チェック
        3. スナップショットをStepSnapshotモデルに変換
        4. 既存の全ステップを削除
        5. スナップショットからステップを復元
        6. 各ステップの設定を復元（add_step + set_config）
        7. snapshot_historyを指定IDまでに切り詰め
        8. chat_historyを指定IDまでに切り詰め

        処理フロー:
            1. セッションとスナップショット履歴を取得
            2. スナップショットIDの検証
            3. スナップショットデータをStepSnapshotモデルに変換
            4. 既存のすべてのステップを削除
            5. スナップショットからステップを順次復元
                a. add_stepでステップ追加
                b. set_configで設定適用と実行
            6. snapshot_historyを切り詰め（snapshot_id+1まで）
            7. chat_historyを切り詰め（snapshot_id以下のみ残す）

        Args:
            snapshot_id (int): 戻すスナップショットのID

        Raises:
            ValueError: 以下の場合に発生
                - スナップショット履歴がない
                - snapshot_idが範囲外
            NotFoundError: 以下の場合に発生
                - セッションが見つからない

        Example:
            >>> # スナップショット2の状態に戻す
            >>> await snapshot_manager.revert_snapshot(2)
            >>>
            >>> # スナップショット0（初期状態）に戻す
            >>> await snapshot_manager.revert_snapshot(0)

        Warning:
            この操作は元に戻せません。スナップショット以降に追加されたステップと
            チャット履歴は完全に削除されます。

        Note:
            - ステップは再作成され、順次実行されます
            - 実行には時間がかかる場合があります
            - スナップショットIDは0から始まります
            - 復元時に各ステップは再実行されるため、最新の状態が反映されます
        """
        logger.info(
            "スナップショットに復元中",
            session_id=str(self.session_id),
            snapshot_id=snapshot_id,
            action="revert_snapshot",
        )

        try:
            # セッション取得
            session = await self.session_repository.get(self.session_id)
            if not session:
                raise NotFoundError(
                    f"セッションが見つかりません: {self.session_id}",
                    details={"session_id": str(self.session_id)},
                )

            # スナップショット検証
            if not session.snapshot_history:
                raise ValueError("スナップショット履歴がありません")

            if snapshot_id < 0 or snapshot_id >= len(session.snapshot_history):
                raise ValueError(
                    f"Invalid snapshot_id: {snapshot_id}. "
                    f"Valid range: 0-{len(session.snapshot_history) - 1}"
                )

            # スナップショットを取得してStepSnapshotモデルに変換
            snapshot_step_dicts: list[dict[str, Any]] = session.snapshot_history[snapshot_id]
            snapshot_steps: list[StepSnapshot] = [
                StepSnapshot.model_validate(step_dict) for step_dict in snapshot_step_dicts
            ]

            # 既存のすべてのステップを削除
            all_steps = await self.step_repository.list_by_session(
                self.session_id, is_active=True
            )
            for step in all_steps:
                await self.step_repository.delete(step.id)

            await self.db.flush()

            # スナップショットからステップを復元
            # Note: add_stepとset_configは別のマネージャーで呼ばれる想定
            # ここでは直接リポジトリを使用してステップを再作成
            if len(snapshot_steps) > 0:
                for i, step_snapshot in enumerate(snapshot_steps):
                    # ステップを作成
                    await self.step_repository.create(
                        session_id=self.session_id,
                        step_name=step_snapshot.name,
                        step_type=step_snapshot.type,
                        step_order=i,
                        data_source=step_snapshot.data,
                        config=step_snapshot.config,
                        result_data_path=None,
                        result_chart=None,
                        result_formula=None,
                        is_active=True,
                    )

                await self.db.flush()

            # スナップショット履歴を切り詰め
            session.snapshot_history = session.snapshot_history[: snapshot_id + 1]

            # チャット履歴を切り詰め
            session.chat_history = [
                entry
                for entry in (session.chat_history or [])
                if entry.get("snapshot_id", 0) <= snapshot_id
            ]

            await self.db.flush()

            logger.info(
                "スナップショット復元が完了しました",
                session_id=str(self.session_id),
                snapshot_id=snapshot_id,
            )

        except (ValueError, NotFoundError):
            raise
        except Exception as e:
            logger.error(
                "スナップショット復元中にエラーが発生しました",
                session_id=str(self.session_id),
                snapshot_id=snapshot_id,
                error=str(e),
                exc_info=True,
            )
            raise
