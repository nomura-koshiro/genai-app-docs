"""分析ステップモデル用のデータアクセスリポジトリ。

このモジュールは、AnalysisStepモデルに特化したデータベース操作を提供します。
BaseRepositoryを継承し、分析ステップ固有のクエリメソッド（セッション別検索、
ステップ順序管理、結果更新など）を追加しています。

主な機能:
    - セッション別のステップ一覧取得（順序付き）
    - ステップ結果の更新（データパス、チャート、数式）
    - 次のステップ順序の取得
    - 基本的なCRUD操作（BaseRepositoryから継承）

使用例:
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> from app.repositories.analysis import AnalysisStepRepository
    >>>
    >>> async with get_db() as db:
    ...     step_repo = AnalysisStepRepository(db)
    ...     steps = await step_repo.list_by_session(session_id)
    ...     for step in steps:
    ...         print(f"Step {step.step_order}: {step.step_name}")
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analysis import AnalysisStep
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class AnalysisStepRepository(BaseRepository[AnalysisStep, uuid.UUID]):
    """AnalysisStepモデル用のリポジトリクラス。

    このリポジトリは、BaseRepositoryの共通CRUD操作に加えて、
    分析ステップ管理に特化したクエリメソッドを提供します。

    分析ステップ検索機能:
        - list_by_session(): セッション別のステップ一覧（順序付き）
        - get_next_order(): 次のステップ順序番号を取得
        - update_result(): ステップ結果を更新

    継承されるメソッド（BaseRepositoryから）:
        - get(id): IDによるステップ取得
        - get_multi(): ページネーション付き一覧取得
        - create(): 新規ステップ作成
        - update(): ステップ情報更新
        - delete(): ステップ削除
        - count(): ステップ数カウント

    Example:
        >>> async with get_db() as db:
        ...     step_repo = AnalysisStepRepository(db)
        ...
        ...     # セッションのステップ一覧（順序付き）
        ...     steps = await step_repo.list_by_session(session_id)
        ...     for step in steps:
        ...         print(f"Step {step.step_order}: {step.step_name}")
        ...
        ...     # 次のステップ順序を取得
        ...     next_order = await step_repo.get_next_order(session_id)
        ...
        ...     # 新規ステップ作成
        ...     new_step = await step_repo.create(
        ...         session_id=session_id,
        ...         step_name="売上フィルタリング",
        ...         step_type="filter",
        ...         step_order=next_order,
        ...         data_source="original",
        ...         config={"category_filter": {"地域": ["東京", "大阪"]}}
        ...     )
        ...     await db.commit()

    Note:
        - すべてのメソッドは非同期（async/await）です
        - flush()のみ実行し、commit()は呼び出し側の責任です
        - ステップの順序は step_order フィールドで管理されます
    """

    def __init__(self, db: AsyncSession):
        """分析ステップリポジトリを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション
                - DIコンテナから自動的に注入されます
                - トランザクションスコープはリクエスト単位で管理されます

        Note:
            - 親クラス（BaseRepository）の__init__を呼び出し、
              AnalysisStepモデルとセッションを設定します
        """
        super().__init__(AnalysisStep, db)

    async def get(self, id: uuid.UUID) -> AnalysisStep | None:
        """UUIDによって分析ステップを取得します。

        Args:
            id (uuid.UUID): ステップのUUID

        Returns:
            AnalysisStep | None: 該当するステップインスタンス、見つからない場合はNone

        Example:
            >>> step = await step_repo.get(step_id)
            >>> if step:
            ...     print(f"Step: {step.step_name} (Type: {step.step_type})")
            Step: 売上フィルタリング (Type: filter)
        """
        return await self.db.get(self.model, id)

    async def list_by_session(
        self,
        session_id: uuid.UUID,
        is_active: bool | None = None,
    ) -> list[AnalysisStep]:
        """特定セッションに属する分析ステップの一覧を取得します（順序付き）。

        このメソッドは、指定されたセッションに紐づくステップのみを
        フィルタリングし、step_order昇順でソートして返します。

        クエリの最適化:
            - session_idにインデックスが設定されているため高速
            - step_order昇順でソート（ステップの実行順序）

        Args:
            session_id (uuid.UUID): セッションのUUID
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのステップ
                True: アクティブなステップのみ
                False: 非アクティブなステップのみ

        Returns:
            list[AnalysisStep]: ステップのリスト（step_order昇順）
                - 指定されたセッションに属するステップのみ
                - step_order昇順でソートされます（0, 1, 2, ...）
                - 0件の場合は空のリストを返します

        Example:
            >>> steps = await step_repo.list_by_session(session_id)
            >>> for i, step in enumerate(steps):
            ...     print(f"{i}. {step.step_name} ({step.step_type})")
            0. 売上フィルタリング (filter)
            1. 地域別集計 (aggregate)
            2. 結果サマリー (summary)

        Note:
            - step_order昇順でソート（分析の実行順序）
            - step_orderは0から開始します
        """
        query = select(AnalysisStep).where(AnalysisStep.session_id == session_id)

        if is_active is not None:
            query = query.where(AnalysisStep.is_active == is_active)

        query = query.order_by(AnalysisStep.step_order.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_next_order(self, session_id: uuid.UUID) -> int:
        """セッション内の次のステップ順序番号を取得します。

        このメソッドは、指定されたセッション内の最大step_orderを取得し、
        次に使用すべき順序番号（max + 1）を返します。新規ステップ追加時に使用されます。

        Args:
            session_id (uuid.UUID): セッションのUUID

        Returns:
            int: 次のステップ順序番号
                - セッションにステップが存在しない場合: 0
                - ステップが存在する場合: max(step_order) + 1

        Example:
            >>> # セッションに3つのステップがある場合（0, 1, 2）
            >>> next_order = await step_repo.get_next_order(session_id)
            >>> print(f"Next order: {next_order}")
            Next order: 3
            >>>
            >>> # 新しいステップを追加
            >>> new_step = await step_repo.create(
            ...     session_id=session_id,
            ...     step_order=next_order,
            ...     step_name="新しいステップ",
            ...     step_type="filter"
            ... )

        Note:
            - セッション内の最大step_orderを取得するため、O(1)クエリ
            - ステップが存在しない場合は0を返します
        """
        from sqlalchemy import func

        result = await self.db.execute(select(func.max(AnalysisStep.step_order)).where(AnalysisStep.session_id == session_id))
        max_order = result.scalar_one_or_none()
        return 0 if max_order is None else max_order + 1

    async def update_result(
        self,
        step_id: uuid.UUID,
        result_data_path: str | None = None,
        result_chart: dict[str, Any] | None = None,
        result_formula: list[dict[str, Any]] | None = None,
    ) -> AnalysisStep | None:
        """ステップの分析結果を更新します。

        このメソッドは、ステップの実行結果（データパス、チャート、数式）を
        更新します。エージェントがステップを実行した後に呼び出されます。

        Args:
            step_id (uuid.UUID): ステップのUUID
            result_data_path (str | None): 結果データのストレージパス
                - 例: "analysis/{session_id}/step_0_result.csv"
            result_chart (dict[str, Any] | None): 結果チャート（Plotly JSON）
                - PlotlyのグラフオブジェクトをJSON形式で保存
            result_formula (list[dict[str, Any]] | None): 結果数式のリスト
                - 例: [{"name": "売上合計", "value": "1000"}]

        Returns:
            AnalysisStep | None: 更新されたステップ、ステップが存在しない場合はNone

        Example:
            >>> step = await step_repo.update_result(
            ...     step_id=step_id,
            ...     result_data_path="analysis/{session_id}/step_0.csv",
            ...     result_chart={"data": [...], "layout": {...}},
            ...     result_formula=[{"name": "売上合計", "value": "1000万円"}]
            ... )
            >>> print(f"Result updated: {step.step_name}")
            Result updated: 売上フィルタリング

        Note:
            - flush()のみ実行し、commit()は呼び出し側の責任
            - Noneを指定したフィールドは更新されません（既存値を保持）
        """
        step = await self.get(step_id)
        if not step:
            logger.warning("ステップが見つかりません", step_id=str(step_id))
            return None

        # 結果を更新
        if result_data_path is not None:
            step.result_data_path = result_data_path
        if result_chart is not None:
            step.result_chart = result_chart
        if result_formula is not None:
            step.result_formula = result_formula

        await self.db.flush()
        await self.db.refresh(step)

        logger.debug(
            "ステップ結果を更新しました",
            step_id=str(step_id),
            has_data=result_data_path is not None,
            has_chart=result_chart is not None,
            has_formula=result_formula is not None,
        )

        return step

    async def count_by_session(self, session_id: uuid.UUID, is_active: bool | None = None) -> int:
        """セッション別のステップ数をカウントします。

        Args:
            session_id (uuid.UUID): セッションのUUID
            is_active (bool | None): アクティブフラグフィルタ

        Returns:
            int: 条件に一致するステップ数

        Example:
            >>> total_steps = await step_repo.count_by_session(session_id)
            >>> print(f"Total steps: {total_steps}")
            Total steps: 5
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(AnalysisStep).where(AnalysisStep.session_id == session_id)

        if is_active is not None:
            query = query.where(AnalysisStep.is_active == is_active)

        result = await self.db.execute(query)
        return result.scalar_one()
