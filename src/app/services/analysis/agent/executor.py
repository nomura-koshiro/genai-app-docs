"""分析ステップ実行管理サービス。

このモジュールは、分析ステップの実行を管理するサービスを提供します。
camp-backend-code-analysisのAnalysisState.apply()に相当する処理を実装しています。

主な機能:
    - ステップの実行順序制御
    - データフローの管理（ステップ間のデータ受け渡し）
    - 結果のストレージ保存
    - エラーハンドリング

使用例:
    >>> from app.services.analysis.agent.executor import AnalysisStepExecutor
    >>>
    >>> executor = AnalysisStepExecutor(db_session)
    >>> result = await executor.execute_step(
    ...     session_id=session_id,
    ...     step=step,
    ...     include_following=True
    ... )
"""

import uuid
from typing import Any

import pandas as pd
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import async_timeout, measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.analysis import AnalysisStep
from app.repositories.analysis import AnalysisFileRepository, AnalysisSessionRepository, AnalysisStepRepository
from app.schemas.analysis.config import FilterConfig
from app.services.analysis.agent.steps.base import AnalysisStepResult, BaseAnalysisStep
from app.services.analysis.agent.storage import AnalysisStorageService

logger = get_logger(__name__)


class AnalysisStepExecutor:
    """分析ステップの実行を管理するサービスクラス。

    このサービスは、分析ステップの実行順序制御、データフローの管理、
    結果の保存などを担当します。

    Attributes:
        db (AsyncSession): データベースセッション
        session_repo (AnalysisSessionRepository): セッションリポジトリ
        step_repo (AnalysisStepRepository): ステップリポジトリ
        file_repo (AnalysisFileRepository): ファイルリポジトリ
        storage_service (AnalysisStorageService): ストレージサービス

    Example:
        >>> executor = AnalysisStepExecutor(db_session)
        >>> result = await executor.execute_step(
        ...     session_id=session_id,
        ...     step=step
        ... )
    """

    def __init__(self, db: AsyncSession):
        """AnalysisStepExecutorを初期化します。

        Args:
            db (AsyncSession): データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.session_repo = AnalysisSessionRepository(db)
        self.step_repo = AnalysisStepRepository(db)
        self.file_repo = AnalysisFileRepository(db)
        self.storage_service = AnalysisStorageService()

    @measure_performance
    @async_timeout(seconds=600.0)  # 10分タイムアウト
    async def execute_step(
        self,
        session_id: uuid.UUID,
        step: AnalysisStep,
        include_following: bool = False,
    ) -> dict[str, Any]:
        """単一ステップを実行して結果を保存します。

        このメソッドは以下の処理を実行します：
        1. ソースデータの取得（original または前のステップの結果）
        2. ステップタイプに応じた実行
        3. 結果のストレージ保存
        4. データベースへの結果メタデータ保存
        5. （オプション）後続ステップの連鎖実行

        Args:
            session_id (uuid.UUID): セッションのUUID
            step (AnalysisStep): 実行対象のステップ
            include_following (bool): 後続ステップも実行するか
                - True: このステップ以降のすべてのステップを順次実行
                - False: このステップのみ実行
                デフォルト: False

        Returns:
            dict[str, Any]: 実行結果
                - step_id: ステップのUUID
                - step_order: ステップの順序
                - result_data_path: 結果データのストレージパス
                - result_chart: チャート情報（summaryのみ）
                - result_formula: 計算式結果（summaryのみ）
                - rows_count: 結果データの行数
                - columns_count: 結果データの列数

        Raises:
            NotFoundError: 以下の場合に発生
                - セッションが存在しない
                - ソースデータが見つからない（data_sourceで指定されたファイル/ステップ）
            ValidationError: 以下の場合に発生
                - ステップ設定が不正
                - データ検証エラー
                - データソースの参照エラー
            Exception: 予期しないエラーが発生した場合

        Example:
            >>> # 単一ステップのみ実行
            >>> result = await executor.execute_step(
            ...     session_id=session_id,
            ...     step=filter_step,
            ...     include_following=False
            ... )
            >>> print(f"Filtered rows: {result['rows_count']}")
            Filtered rows: 100
            >>>
            >>> # このステップ以降を連鎖実行
            >>> result = await executor.execute_step(
            ...     session_id=session_id,
            ...     step=filter_step,
            ...     include_following=True
            ... )

        Note:
            - タイムアウトは10分です
            - 大規模データセットの場合、タイムアウトする可能性があります
            - include_following=Trueの場合、後続ステップの実行に失敗しても、
              このステップの結果は保存されます
        """
        logger.info(
            "分析ステップを実行中",
            session_id=str(session_id),
            step_id=str(step.id),
            step_type=step.step_type,
            step_order=step.step_order,
            data_source=step.data_source,
            include_following=include_following,
            action="execute_analysis_step",
        )

        try:
            # セッションの存在確認
            session = await self.session_repo.get(session_id)
            if not session:
                logger.warning("セッションが見つかりません", session_id=str(session_id))
                raise NotFoundError(
                    "セッションが見つかりません",
                    details={"session_id": str(session_id)},
                )

            # ソースデータの取得
            source_data = await self._load_source_data(session_id, step.data_source)

            logger.debug(
                "ソースデータを読み込みました",
                session_id=str(session_id),
                step_id=str(step.id),
                data_source=step.data_source,
                rows=len(source_data),
                columns=len(source_data.columns),
            )

            # ステップ実行クラスの取得
            step_executor = self._get_step_executor(step.step_type)

            # 設定の検証
            await step_executor.validate_config(step.config, source_data)

            # ステップ実行
            # filterステップでtable_filterが有効な場合、参照DataFrameを取得して渡す
            kwargs = {}
            if step.step_type == "filter":
                try:
                    filter_config = FilterConfig.model_validate(step.config)
                    if (
                        filter_config.table_filter is not None
                        and filter_config.table_filter.enable
                    ):
                        table_df_source = filter_config.table_filter.table_df
                        if table_df_source:
                            logger.debug(
                                "table_filter用の参照DataFrameを取得中",
                                session_id=str(session_id),
                                step_id=str(step.id),
                                table_df_source=table_df_source,
                            )

                            # table_df_source（例: "step_1"）から参照DataFrameを取得
                            table_filter_df = await self._load_source_data(
                                session_id, table_df_source
                            )

                            kwargs["table_filter_df"] = table_filter_df

                            logger.debug(
                                "table_filter用の参照DataFrameを取得しました",
                                session_id=str(session_id),
                                step_id=str(step.id),
                                table_df_source=table_df_source,
                                rows=len(table_filter_df),
                                columns=len(table_filter_df.columns),
                            )
                except PydanticValidationError:
                    # Pydantic検証エラーの場合は、table_filterを使用しない
                    pass

            result = await step_executor.execute(
                source_data=source_data,
                config=step.config,
                **kwargs,
            )

            logger.info(
                "ステップ実行完了",
                session_id=str(session_id),
                step_id=str(step.id),
                step_type=step.step_type,
                has_result_data=result.result_data is not None,
                has_chart=result.result_chart is not None,
                has_formula=result.result_formula is not None,
            )

            # 結果の保存
            save_result = await self._save_result(session_id, step, result)

            # 後続ステップの実行（オプション）
            if include_following:
                await self._execute_following_steps(session_id, step.step_order)

            logger.info(
                "ステップ実行・保存が完了しました",
                session_id=str(session_id),
                step_id=str(step.id),
                result_data_path=save_result["result_data_path"],
            )

            return save_result

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                "ステップ実行中に予期しないエラーが発生しました",
                session_id=str(session_id),
                step_id=str(step.id),
                step_type=step.step_type,
                error=str(e),
                exc_info=True,
            )
            raise

    async def _load_source_data(
        self,
        session_id: uuid.UUID,
        data_source: str,
    ) -> pd.DataFrame:
        """ソースデータを読み込みます。

        data_sourceの形式に応じて、適切なデータを取得します：
        - "original": セッションの元ファイルから読み込み
        - "step_0", "step_1", ...: 指定されたステップの結果から読み込み

        Args:
            session_id (uuid.UUID): セッションのUUID
            data_source (str): データソース
                - "original": 元ファイル
                - "step_{index}": ステップの結果

        Returns:
            pd.DataFrame: 読み込まれたデータフレーム

        Raises:
            NotFoundError: データソースが見つからない場合
            ValidationError: data_sourceの形式が不正な場合

        Example:
            >>> # 元ファイルから読み込み
            >>> df = await executor._load_source_data(session_id, "original")
            >>>
            >>> # ステップ0の結果から読み込み
            >>> df = await executor._load_source_data(session_id, "step_0")
        """
        logger.debug(
            "ソースデータを読み込み中",
            session_id=str(session_id),
            data_source=data_source,
        )

        # セッションを取得
        session = await self.session_repo.get(session_id)
        if not session:
            raise NotFoundError(
                "セッションが見つかりません",
                details={"session_id": str(session_id)},
            )

        if data_source == "original":
            # セッションの元ファイルから読み込み
            # original_file_idが設定されている場合はそれを使用、なければ最初のファイルを使用
            if session.original_file_id:
                file = await self.file_repo.get(session.original_file_id)
                if not file:
                    raise NotFoundError(
                        "指定されたファイルが見つかりません",
                        details={
                            "session_id": str(session_id),
                            "original_file_id": str(session.original_file_id),
                        },
                    )
                logger.debug(
                    "original_file_idからファイルを取得しました",
                    session_id=str(session_id),
                    file_id=str(file.id),
                )
            else:
                # フォールバック: 最初のアップロードファイルを使用
                files = await self.file_repo.list_by_session(session_id, is_active=True)
                if not files:
                    raise NotFoundError(
                        "セッションにファイルがアップロードされていません",
                        details={"session_id": str(session_id)},
                    )
                file = files[0]
                logger.debug(
                    "original_file_idが未設定のため、最初のファイルを使用します",
                    session_id=str(session_id),
                    file_id=str(file.id),
                )

            df = await self.storage_service.load_dataframe(file.storage_path)

            logger.debug(
                "元ファイルから読み込みました",
                session_id=str(session_id),
                file_id=str(file.id),
                rows=len(df),
            )

            return df

        elif data_source.startswith("step_"):
            # ステップの結果から読み込み
            try:
                step_index = int(data_source.split("_")[1])
            except (IndexError, ValueError) as e:
                raise ValidationError(
                    f"data_sourceの形式が不正です: {data_source}",
                    details={"data_source": data_source},
                ) from e

            # ステップを取得
            steps = await self.step_repo.list_by_session(session_id, is_active=True)
            target_step = None
            for s in steps:
                if s.step_order == step_index:
                    target_step = s
                    break

            if not target_step:
                raise NotFoundError(
                    f"ステップが見つかりません: {data_source}",
                    details={"data_source": data_source, "step_index": step_index},
                )

            if not target_step.result_data_path:
                raise ValidationError(
                    f"ステップの結果データが存在しません: {data_source}",
                    details={
                        "data_source": data_source,
                        "step_id": str(target_step.id),
                    },
                )

            # 結果データを読み込み
            df = await self.storage_service.load_dataframe(target_step.result_data_path)

            logger.debug(
                "ステップ結果から読み込みました",
                session_id=str(session_id),
                data_source=data_source,
                step_id=str(target_step.id),
                rows=len(df),
            )

            return df

        else:
            raise ValidationError(
                f"未知のdata_source形式です: {data_source}",
                details={"data_source": data_source},
            )

    def _get_step_executor(self, step_type: str) -> BaseAnalysisStep:
        """ステップタイプに応じた実行クラスを取得します。

        Args:
            step_type (str): ステップタイプ
                - "filter": FilterStep
                - "aggregate": AggregationStep
                - "transform": TransformStep
                - "summary": SummaryStep

        Returns:
            BaseAnalysisStep: ステップ実行クラスのインスタンス

        Raises:
            ValidationError: 未知のステップタイプの場合

        Example:
            >>> executor = self._get_step_executor("filter")
            >>> isinstance(executor, FilterStep)
            True
        """
        from app.services.analysis.agent.steps import (
            AggregationStep,
            FilterStep,
            SummaryStep,
            TransformStep,
        )

        step_executors = {
            "filter": FilterStep,
            "aggregate": AggregationStep,
            "transform": TransformStep,
            "summary": SummaryStep,
        }

        if step_type not in step_executors:
            raise ValidationError(
                f"未知のステップタイプです: {step_type}",
                details={
                    "step_type": step_type,
                    "supported_types": list(step_executors.keys()),
                },
            )

        logger.debug(f"ステップ実行クラスを取得: {step_type}")

        return step_executors[step_type]()

    @transactional
    async def _save_result(
        self,
        session_id: uuid.UUID,
        step: AnalysisStep,
        result: AnalysisStepResult,
    ) -> dict[str, Any]:
        """実行結果をストレージとデータベースに保存します。

        Args:
            session_id (uuid.UUID): セッションのUUID
            step (AnalysisStep): ステップ
            result (AnalysisStepResult): 実行結果

        Returns:
            dict[str, Any]: 保存結果
                - step_id: ステップのUUID
                - step_order: ステップの順序
                - result_data_path: 結果データのストレージパス
                - result_chart: チャート情報
                - result_formula: 計算式結果
                - rows_count: 行数
                - columns_count: 列数

        Raises:
            Exception: ストレージ保存やDB更新でエラーが発生した場合
        """
        logger.debug(
            "実行結果を保存中",
            session_id=str(session_id),
            step_id=str(step.id),
            has_result_data=result.result_data is not None,
        )

        result_data_path = None
        rows_count = 0
        columns_count = 0

        # 結果データをストレージに保存
        if result.result_data is not None:
            result_data_path = await self.storage_service.save_dataframe(
                session_id=session_id,
                filename=f"step_{step.step_order}_result",
                df=result.result_data,
                prefix="results",
            )

            rows_count = len(result.result_data)
            columns_count = len(result.result_data.columns)

            logger.debug(
                "結果データを保存しました",
                session_id=str(session_id),
                step_id=str(step.id),
                storage_path=result_data_path,
                rows=rows_count,
                columns=columns_count,
            )

        # result_formulaをdictのリストに変換（ResultFormula → dict）
        result_formula_dicts = None
        if result.result_formula:
            result_formula_dicts = [formula.model_dump() for formula in result.result_formula]

        # データベースに結果メタデータを保存
        await self.step_repo.update(
            step,
            result_data_path=result_data_path,
            result_chart=result.result_chart,
            result_formula=result_formula_dicts,
        )

        logger.info(
            "実行結果を保存しました",
            session_id=str(session_id),
            step_id=str(step.id),
            result_data_path=result_data_path,
        )

        return {
            "step_id": step.id,
            "step_order": step.step_order,
            "result_data_path": result_data_path,
            "result_chart": result.result_chart,
            "result_formula": result_formula_dicts,
            "rows_count": rows_count,
            "columns_count": columns_count,
        }

    async def _execute_following_steps(
        self,
        session_id: uuid.UUID,
        current_step_order: int,
    ) -> None:
        """後続ステップを順次実行します。

        このメソッドは、指定されたステップより後のすべてのステップを
        順序通りに実行します。

        Args:
            session_id (uuid.UUID): セッションのUUID
            current_step_order (int): 現在のステップの順序

        Raises:
            Exception: ステップ実行でエラーが発生した場合

        Note:
            - 後続ステップの実行に失敗しても、現在のステップの結果は保存されています
            - エラーはログに記録されますが、例外は再スローされます
        """
        logger.info(
            "後続ステップを実行中",
            session_id=str(session_id),
            current_step_order=current_step_order,
        )

        # 後続ステップを取得
        all_steps = await self.step_repo.list_by_session(session_id, is_active=True)
        following_steps = [s for s in all_steps if s.step_order > current_step_order]

        logger.debug(
            "後続ステップ数",
            session_id=str(session_id),
            count=len(following_steps),
        )

        # 順次実行
        for following_step in following_steps:
            try:
                await self.execute_step(
                    session_id=session_id,
                    step=following_step,
                    include_following=False,  # 再帰を避ける
                )
            except Exception as e:
                logger.error(
                    "後続ステップの実行に失敗しました",
                    session_id=str(session_id),
                    step_id=str(following_step.id),
                    step_order=following_step.step_order,
                    error=str(e),
                    exc_info=True,
                )
                # エラーを再スロー（後続ステップの失敗を通知）
                raise
