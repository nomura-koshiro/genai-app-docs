"""分析ステップ管理サービス。

このモジュールは、分析ステップの追加、削除、実行、設定管理などの
ステップ関連の機能を提供します。

主な機能:
    - 全ステップのクリア（clear）
    - ステップの追加（add_step）
    - ステップの削除（delete_step）
    - ステップの実行（apply）
    - ステップ設定の取得（get_config）
    - ステップ設定の更新（set_config）

使用例:
    >>> from app.services.analysis.agent.step_manager import AnalysisStepManager
    >>>
    >>> async with get_db() as db:
    ...     step_manager = AnalysisStepManager(db, session_id)
    ...
    ...     # ステップ追加
    ...     await step_manager.add_step("売上フィルタ", "filter", "original")
    ...
    ...     # 設定更新と実行
    ...     overview = await step_manager.set_config(0, {
    ...         "category_filter": {"地域": ["東京", "大阪"]}
    ...     })
"""

import uuid
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.repositories.analysis import AnalysisSessionRepository, AnalysisStepRepository
from app.services.analysis.agent.executor import AnalysisStepExecutor
from app.services.analysis.agent.steps import (
    AggregationStep,
    FilterStep,
    SummaryStep,
    TransformStep,
)

logger = get_logger(__name__)


class AnalysisStepManager:
    """分析ステップ管理クラス。

    ステップの追加、削除、実行、設定管理などの機能を提供します。

    Attributes:
        db (AsyncSession): データベースセッション
        session_id (uuid.UUID): セッションID
        session_repository (AnalysisSessionRepository): セッションリポジトリ
        step_repository (AnalysisStepRepository): ステップリポジトリ
        step_executor (AnalysisStepExecutor): ステップ実行サービス
        validation (dict | None): validation_config（施策・課題設定）

    Example:
        >>> async with get_db() as db:
        ...     step_manager = AnalysisStepManager(db, session_id)
        ...     await step_manager.add_step("フィルタ", "filter", "original")
    """

    def __init__(self, db: AsyncSession, session_id: uuid.UUID):
        """分析ステップ管理を初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
            session_id (uuid.UUID): セッションのUUID

        Note:
            - セッションの存在確認は行わないため、呼び出し側で確認すること
            - validation_configはセッションから自動的にロードされます
        """
        self.db = db
        self.session_id = session_id
        self.session_repository = AnalysisSessionRepository(db)
        self.step_repository = AnalysisStepRepository(db)
        self.step_executor = AnalysisStepExecutor(db)
        self.validation: dict[str, Any] | None = None

        logger.info(
            "分析ステップ管理を初期化しました",
            session_id=str(session_id),
        )

    async def _load_validation(self) -> None:
        """validation_configをセッションから読み込みます。

        Note:
            - 内部用メソッド
            - validation_configが未ロードの場合のみロード
        """
        if self.validation is None:
            session = await self.session_repository.get(self.session_id)
            if session:
                self.validation = session.validation_config or {}

    @measure_performance
    async def clear(self) -> None:
        """全てのステップと会話履歴をクリアします。

        このメソッドは以下を実行します：
        1. すべてのステップを削除（論理削除）
        2. チャット履歴を初期化（agent_prompt, initial_msgのみ残す）
        3. スナップショット履歴を初期化（空のステップ配列）

        処理フロー:
            1. 全ステップをDBから取得
            2. 各ステップを論理削除（is_active=False）
            3. セッションを取得
            4. validation_configから初期メッセージを取得
            5. チャット履歴を初期化（agent_prompt + initial_msg）
            6. スナップショット履歴を初期化（[[]]）
            7. 変更をフラッシュ

        Raises:
            NotFoundError: 以下の場合に発生
                - セッションが存在しない
            Exception: 以下の場合に発生
                - DB操作でエラーが発生

        Example:
            >>> await step_manager.clear()

        Note:
            - ステップは論理削除されます（is_active=False）
            - ファイルは削除されません
            - validation_configは保持されます
            - チャット履歴はagent_promptとinitial_msgのみ残ります
        """
        logger.info(
            "ステップと会話履歴をクリア中",
            session_id=str(self.session_id),
            action="clear",
        )

        try:
            # すべてのステップを削除
            all_steps = await self.step_repository.list_by_session(
                self.session_id, is_active=True
            )
            for step in all_steps:
                await self.step_repository.delete(step.id)

            await self.db.flush()

            # セッションを取得
            session = await self.session_repository.get(self.session_id)
            if not session:
                raise NotFoundError(
                    f"セッションが見つかりません: {self.session_id}",
                    details={"session_id": str(self.session_id)},
                )

            # チャット履歴を初期化
            await self._load_validation()
            initial_history = []

            if self.validation and "agent_prompt" in self.validation:
                if self.validation["agent_prompt"]:
                    initial_history.append(
                        {
                            "role": "system",
                            "message": self.validation["agent_prompt"],
                            "snapshot_id": 0,
                        }
                    )

            if self.validation and "initial_msg" in self.validation:
                if self.validation["initial_msg"]:
                    initial_history.append(
                        {
                            "role": "assistant",
                            "message": self.validation["initial_msg"],
                            "snapshot_id": 0,
                        }
                    )

            session.chat_history = initial_history

            # スナップショット履歴を初期化（空のステップ配列として）
            initial_snapshot: list[dict[str, Any]] = []
            session.snapshot_history = [initial_snapshot]

            await self.db.flush()

            logger.info(
                "クリアが完了しました",
                session_id=str(self.session_id),
            )

        except Exception as e:
            logger.error(
                "クリア中にエラーが発生しました",
                session_id=str(self.session_id),
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def add_step(self, name: str, type: str, data: str = "original") -> None:
        """新しいステップを追加します。

        このメソッドは以下の処理を実行します：
        1. data_sourceの検証（'original'または'step_N'形式）
        2. data_sourceが'step_N'の場合、参照先ステップの結果データを確認
        3. ステップタイプの検証（filter, aggregate, transform, summary）
        4. ステップクラスから初期configを取得
        5. 次のstep_orderを取得
        6. ステップをDBに作成

        Args:
            name (str): ステップの名前（例: "売上フィルタ"）
            type (str): ステップのタイプ
                - 'filter': フィルタステップ
                - 'aggregate': 集計ステップ
                - 'transform': 変換ステップ
                - 'summary': サマリステップ
            data (str): 使うデータの名前（デフォルト: "original"）
                - 'original': 元データ
                - 'step_0', 'step_1', ...: ステップの結果

        Raises:
            ValueError: 以下の場合に発生
                - ステップタイプが未知（filter, aggregate, transform, summary以外）
                - data_sourceの形式が不正（'original'または'step_N'以外）
                - data_sourceのインデックスが範囲外
                - 参照先ステップに結果データがない
            ValidationError: 以下の場合に発生
                - データソースの検証に失敗

        Example:
            >>> # 元データを使うフィルタステップ
            >>> await step_manager.add_step("売上フィルタ", "filter", "original")
            >>>
            >>> # step_0の結果を使う集計ステップ
            >>> await step_manager.add_step("地域別集計", "aggregate", "step_0")
            >>>
            >>> # step_1の結果を使うサマリステップ
            >>> await step_manager.add_step("売上サマリ", "summary", "step_1")

        Note:
            - ステップは自動的にstep_order順に並びます
            - ステップの初期設定（config）は各ステップクラスで設定されます
            - data_sourceが'step_N'の場合、Nは0から始まるインデックスです
        """
        logger.info(
            "ステップを追加中",
            session_id=str(self.session_id),
            name=name,
            type=type,
            data=data,
            action="add_step",
        )

        try:
            # データソースが 'original' 以外の場合、インデックスを確認
            if data != "original":
                if not data.startswith("step_"):
                    raise ValueError(
                        f"Invalid data source format: {data}. "
                        f"Expected 'original' or 'step_0', 'step_1', ..."
                    )

                data_index = int(data.split("_")[1])
                all_steps = await self.step_repository.list_by_session(
                    self.session_id, is_active=True
                )

                if data_index < 0 or data_index >= len(all_steps):
                    raise ValueError(f"Invalid data source index: {data}")

                # 結果データがあるか確認
                if not all_steps[data_index].result_data_path:
                    raise ValueError(
                        f"Step {data_index} does not have result data yet"
                    )

            # ステップタイプの検証と初期設定
            step_classes = {
                "filter": FilterStep,
                "aggregate": AggregationStep,
                "transform": TransformStep,
                "summary": SummaryStep,
            }

            if type not in step_classes:
                raise ValueError(
                    f"Unknown step type: {type}. "
                    f"Valid types: {list(step_classes.keys())}"
                )

            # ステップクラスのインスタンスを作成して初期configを取得
            step_instance = step_classes[type]()
            initial_config = step_instance.get_config()

            # 次のstep_orderを取得
            next_order = await self.step_repository.get_next_order(self.session_id)

            # ステップを作成
            await self.step_repository.create(
                session_id=self.session_id,
                step_name=name,
                step_type=type,
                step_order=next_order,
                data_source=data,
                config=initial_config,
                result_data_path=None,
                result_chart=None,
                result_formula=None,
                is_active=True,
            )

            await self.db.flush()

            logger.info(
                "ステップ追加が完了しました",
                session_id=str(self.session_id),
                step_name=name,
                step_type=type,
                step_order=next_order,
            )

        except (ValueError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "ステップ追加中にエラーが発生しました",
                session_id=str(self.session_id),
                name=name,
                type=type,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def delete_step(self, step_index: int) -> None:
        """指定したステップを削除します。

        このメソッドは指定されたインデックスのステップを物理削除します。

        Args:
            step_index (int): 削除するステップのインデックス（step_order）

        Raises:
            IndexError: 以下の場合に発生
                - step_indexが範囲外（負の値または総ステップ数以上）
            NotFoundError: 以下の場合に発生
                - ステップが見つからない

        Example:
            >>> # ステップ0を削除
            >>> await step_manager.delete_step(0)
            >>>
            >>> # ステップ2を削除
            >>> await step_manager.delete_step(2)

        Note:
            - ステップは物理削除されます
            - 後続ステップのstep_orderは自動的に振り直されません
            - 削除したステップを参照している後続ステップがある場合、
              そのステップの実行時にエラーが発生する可能性があります
        """
        logger.info(
            "ステップを削除中",
            session_id=str(self.session_id),
            step_index=step_index,
            action="delete_step",
        )

        try:
            # すべてのステップを取得
            all_steps = await self.step_repository.list_by_session(
                self.session_id, is_active=True
            )

            if step_index < 0 or step_index >= len(all_steps):
                raise IndexError(
                    f"Step index out of range: {step_index}. "
                    f"Valid range: 0-{len(all_steps) - 1}"
                )

            # ステップを削除
            target_step = all_steps[step_index]
            await self.step_repository.delete(target_step.id)
            await self.db.flush()

            logger.info(
                "ステップ削除が完了しました",
                session_id=str(self.session_id),
                step_index=step_index,
                step_id=str(target_step.id),
            )

        except (IndexError, NotFoundError):
            raise
        except Exception as e:
            logger.error(
                "ステップ削除中にエラーが発生しました",
                session_id=str(self.session_id),
                step_index=step_index,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def apply(self, step_index: int, include_following: bool = True) -> None:
        """指定したステップの設定を適用し、結果を更新します。

        このメソッドはAnalysisStepExecutor.execute_step()を呼び出します。

        処理フロー:
            1. 全ステップをDBから取得
            2. step_indexの範囲チェック
            3. AnalysisStepExecutorでステップを実行
            4. include_following=Trueの場合、後続ステップも順次実行
            5. 実行結果をストレージとDBに保存

        Args:
            step_index (int): 設定を適用するステップのインデックス
            include_following (bool): このステップ以降のステップも実行するか
                - True: 後続ステップも順次実行（デフォルト）
                - False: 指定されたステップのみ実行

        Raises:
            IndexError: 以下の場合に発生
                - step_indexが範囲外（負の値または総ステップ数以上）
            NotFoundError: 以下の場合に発生
                - ステップが見つからない
            ValidationError: 以下の場合に発生
                - ステップ設定が不正
                - データソースが見つからない

        Example:
            >>> # ステップ0のみ実行
            >>> await step_manager.apply(0, include_following=False)
            >>>
            >>> # ステップ0以降をすべて実行
            >>> await step_manager.apply(0, include_following=True)
            >>>
            >>> # ステップ1以降をすべて実行
            >>> await step_manager.apply(1)

        Note:
            - table_filter用の参照DataFrameは自動的に渡されます
            - 実行結果はストレージとDBに保存されます
            - include_following=Trueの場合、依存関係に沿って順次実行されます
        """
        logger.info(
            "ステップを実行中",
            session_id=str(self.session_id),
            step_index=step_index,
            include_following=include_following,
            action="apply_step",
        )

        try:
            # すべてのステップを取得
            all_steps = await self.step_repository.list_by_session(
                self.session_id, is_active=True
            )

            if step_index < 0 or step_index >= len(all_steps):
                raise IndexError(
                    f"Step index out of range: {step_index}. "
                    f"Valid range: 0-{len(all_steps) - 1}"
                )

            step = all_steps[step_index]

            # AnalysisStepExecutorで実行
            await self.step_executor.execute_step(
                session_id=self.session_id,
                step=step,
                include_following=include_following,
            )

            logger.info(
                "ステップ実行が完了しました",
                session_id=str(self.session_id),
                step_index=step_index,
                step_id=str(step.id),
            )

        except (IndexError, NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "ステップ実行中にエラーが発生しました",
                session_id=str(self.session_id),
                step_index=step_index,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def get_config(self, step_index: int) -> dict[str, Any]:
        """指定したステップの設定を取得します。

        Args:
            step_index (int): 設定を取得するステップのインデックス

        Returns:
            dict[str, Any]: ステップの設定（config）
                - フィルタステップ: category_filter, numeric_filter, table_filter
                - 集計ステップ: axis, column
                - 変換ステップ: operations
                - サマリステップ: formulas, chart, table

        Raises:
            IndexError: 以下の場合に発生
                - step_indexが範囲外（負の値または総ステップ数以上）

        Example:
            >>> config = await step_manager.get_config(0)
            >>> print(config)
            {"category_filter": {"地域": ["東京", "大阪"]}, ...}
            >>>
            >>> # 設定を確認
            >>> category_filter = config.get("category_filter", {})
            >>> print(category_filter)
            {"地域": ["東京", "大阪"]}

        Note:
            - configの構造はステップタイプによって異なります
            - 空の設定の場合は{}が返されます
        """
        logger.debug(
            "ステップ設定を取得中",
            session_id=str(self.session_id),
            step_index=step_index,
        )

        all_steps = await self.step_repository.list_by_session(
            self.session_id, is_active=True
        )

        if step_index < 0 or step_index >= len(all_steps):
            raise IndexError(f"Step index out of range: {step_index}")

        result = all_steps[step_index].config

        logger.debug(
            "ステップ設定を取得しました",
            session_id=str(self.session_id),
            step_index=step_index,
        )

        return result

    @measure_performance
    async def set_config(
        self, step_index: int, config: dict[str, Any], source_data: pd.DataFrame
    ) -> str:
        """指定したステップに設定を追加し、適用します。

        このメソッドは設定をセット後、自動的にapply()を呼び出します。

        処理フロー:
            1. 全ステップをDBから取得
            2. step_indexの範囲チェック
            3. ステップクラスで設定を検証（validate_config）
            4. DBに設定を更新
            5. apply()を呼び出してステップを実行
            6. get_step_overview()で概要を取得して返す

        Args:
            step_index (int): 設定を追加するステップのインデックス
            config (dict[str, Any]): 設定の内容
                - フィルタステップ: category_filter, numeric_filter, table_filter
                - 集計ステップ: axis, column
                - 変換ステップ: operations
                - サマリステップ: formulas, chart, table
            source_data (pd.DataFrame): ソースデータ（設定検証用）

        Returns:
            str: ステップの概要（get_step_overview()の結果）

        Raises:
            IndexError: 以下の場合に発生
                - step_indexが範囲外
            ValidationError: 以下の場合に発生
                - 設定が不正（例: 存在しないカラムを指定）
                - データ型が不正

        Example:
            >>> overview = await step_manager.set_config(0, {
            ...     "category_filter": {"地域": ["東京", "大阪"]},
            ...     "numeric_filter": {"enable_min": False, "enable_max": False},
            ...     "table_filter": {"enable": False}
            ... }, source_df)
            >>> print(overview)
            現在の分析ステップ:

            Step 0: 売上フィルタ (filter)
              - データソース: original
              - カテゴリーフィルタ: 地域: ['東京', '大阪']
              ...

        Note:
            - 設定はステップクラスで検証されます
            - 検証に失敗した場合、設定は更新されません
            - 検証に成功した場合、自動的にステップが実行されます
        """
        logger.info(
            "ステップ設定を更新中",
            session_id=str(self.session_id),
            step_index=step_index,
            action="set_config",
        )

        try:
            # すべてのステップを取得
            all_steps = await self.step_repository.list_by_session(
                self.session_id, is_active=True
            )

            if step_index < 0 or step_index >= len(all_steps):
                raise IndexError(f"Step index out of range: {step_index}")

            step = all_steps[step_index]

            # ステップクラスのインスタンスを作成して設定を検証
            step_classes = {
                "filter": FilterStep,
                "aggregate": AggregationStep,
                "transform": TransformStep,
                "summary": SummaryStep,
            }

            step_instance = step_classes[step.step_type]()
            await step_instance.validate_config(config, source_data)

            # 設定を更新
            await self.step_repository.update(step, config=config)
            await self.db.flush()

            # 適用（実行）
            await self.apply(step_index)

            # 概要を返す（ここでは仮の概要を返す）
            overview = f"Step {step_index} の設定が更新されました"

            logger.info(
                "ステップ設定更新が完了しました",
                session_id=str(self.session_id),
                step_index=step_index,
            )

            return overview

        except (IndexError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "ステップ設定更新中にエラーが発生しました",
                session_id=str(self.session_id),
                step_index=step_index,
                error=str(e),
                exc_info=True,
            )
            raise
