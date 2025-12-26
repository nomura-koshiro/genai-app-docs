"""分析ステップ管理サービス。

このモジュールは、分析ステップの作成、取得、削除などの
ステップ関連のビジネスロジックを提供します。

主な機能:
    - 分析ステップの作成・管理
    - ステップ一覧の取得
    - ステップの削除
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import AnalysisStep
from app.repositories import AnalysisSessionRepository, AnalysisStepRepository
from app.schemas import AnalysisStepCreate

logger = get_logger(__name__)


class AnalysisStepService:
    """分析ステップ管理サービスクラス。

    このサービスは、分析ステップの作成、取得、削除などの
    ステップ関連の操作を提供します。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
        session_repository: AnalysisSessionRepositoryインスタンス
        step_repository: AnalysisStepRepositoryインスタンス
    """

    def __init__(self, db: AsyncSession):
        """分析ステップサービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.session_repository = AnalysisSessionRepository(db)
        self.step_repository = AnalysisStepRepository(db)

    @measure_performance
    @transactional
    async def create_step(
        self,
        session_id: uuid.UUID,
        step_data: AnalysisStepCreate,
    ) -> AnalysisStep:
        """新しい分析ステップを作成します。

        このメソッドは以下の処理を実行します：
        1. セッションの存在確認
        2. 次のステップ順序番号の取得
        3. ステップレコードの作成
        4. 作成イベントのロギング

        Args:
            session_id (uuid.UUID): セッションのUUID
            step_data (AnalysisStepCreate): ステップ作成用のPydanticスキーマ
                - step_name: ステップ名（例: "売上フィルタリング"）
                - step_type: ステップタイプ（filter/aggregate/transform/summary）
                - data_source: データソース（original/step_0/step_1/...）
                - config: ステップ設定（JSONB）

        Returns:
            AnalysisStep: 作成されたステップモデルインスタンス
                - id: 自動生成されたUUID
                - step_order: 自動採番された順序番号
                - is_active: True（デフォルト）
                - created_at, updated_at: 自動生成されたタイムスタンプ

        Raises:
            NotFoundError: セッションが存在しない場合
            ValidationError: ステップ設定が不正な場合
            Exception: データベース操作で予期しないエラーが発生した場合

        Example:
            >>> step_data = AnalysisStepCreate(
            ...     step_name="売上フィルタリング",
            ...     step_type="filter",
            ...     data_source="original",
            ...     config={
            ...         "category_filter": {"地域": ["東京", "大阪"]}
            ...     }
            ... )
            >>> step = await step_service.create_step(
            ...     session_id=session_id,
            ...     step_data=step_data
            ... )
            >>> print(f"Created step: {step.step_name} (order: {step.step_order})")
            Created step: 売上フィルタリング (order: 0)

        Note:
            - step_orderは自動的に採番されます（0から開始）
            - すべての操作は構造化ログに記録されます
            - @transactionalデコレータにより自動コミットされます
        """
        logger.info(
            "分析ステップを作成中",
            session_id=str(session_id),
            step_name=step_data.step_name,
            step_type=step_data.step_type,
            data_source=step_data.data_source,
            action="create_analysis_step",
        )

        try:
            # セッションの存在確認
            session = await self.session_repository.get(session_id)
            if not session:
                logger.warning(
                    "セッションが見つかりません",
                    session_id=str(session_id),
                )
                raise NotFoundError(
                    "セッションが見つかりません",
                    details={"session_id": str(session_id)},
                )

            # 次のステップ順序番号を取得
            next_order = await self.step_repository.get_next_order(session_id)

            # ステップを作成
            step = await self.step_repository.create(
                session_id=session_id,
                step_name=step_data.step_name,
                step_type=step_data.step_type,
                step_order=next_order,
                data_source=step_data.data_source,
                config=step_data.config,
                result_data_path=None,
                result_chart=None,
                result_formula=None,
                is_active=True,
            )

            logger.info(
                "分析ステップを正常に作成しました",
                session_id=str(session_id),
                step_id=str(step.id),
                step_name=step.step_name,
                step_order=step.step_order,
            )

            return step

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(
                "分析ステップ作成中に予期しないエラーが発生しました",
                session_id=str(session_id),
                step_name=step_data.step_name,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def list_session_steps(self, session_id: uuid.UUID, is_active: bool | None = None) -> list[AnalysisStep]:
        """セッションの分析ステップ一覧を取得します。

        Args:
            session_id (uuid.UUID): セッションのUUID
            is_active (bool | None): アクティブフラグフィルタ
                None: すべてのステップ
                True: アクティブなステップのみ
                False: 非アクティブなステップのみ

        Returns:
            list[AnalysisStep]: ステップのリスト（step_order昇順）

        Example:
            >>> steps = await step_service.list_session_steps(session_id)
            >>> for step in steps:
            ...     print(f"Step {step.step_order}: {step.step_name}")
            Step 0: 売上フィルタリング
            Step 1: 地域別集計
        """
        logger.debug(
            "セッションステップ一覧を取得中",
            session_id=str(session_id),
            is_active=is_active,
            action="list_session_steps",
        )

        steps = await self.step_repository.list_by_session(
            session_id=session_id,
            is_active=is_active,
        )

        logger.debug(
            "セッションステップ一覧を正常に取得しました",
            session_id=str(session_id),
            count=len(steps),
        )

        return steps

    @measure_performance
    @transactional
    async def delete_step(self, step_id: uuid.UUID) -> None:
        """分析ステップを削除します。

        Args:
            step_id (uuid.UUID): 削除するステップのUUID

        Raises:
            NotFoundError: ステップが存在しない場合

        Example:
            >>> await step_service.delete_step(step_id)
            >>> print("Step deleted")

        Note:
            - 論理削除ではなく物理削除されます
            - @transactionalデコレータにより自動コミットされます
        """
        logger.info(
            "分析ステップを削除中",
            step_id=str(step_id),
            action="delete_step",
        )

        step = await self.step_repository.get(step_id)
        if not step:
            logger.warning("ステップが見つかりません", step_id=str(step_id))
            raise NotFoundError(
                "ステップが見つかりません",
                details={"step_id": str(step_id)},
            )

        await self.step_repository.delete(step_id)

        logger.info(
            "分析ステップを削除しました",
            step_id=str(step_id),
            step_name=step.step_name,
        )
