"""分析スナップショット管理サービス。

このモジュールは、分析セッションのスナップショット管理（保存・復元・取得）などの
スナップショット関連のビジネスロジックを提供します。

主な機能:
    - スナップショットIDの取得
    - スナップショットの保存
    - スナップショットへの復元
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.decorators import measure_performance, transactional
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.analysis_session import AnalysisSession
from app.repositories.analysis_session import AnalysisSessionRepository

logger = get_logger(__name__)


class AnalysisSnapshotService:
    """分析スナップショット管理サービスクラス。

    このサービスは、スナップショットの保存、復元、取得などの
    スナップショット関連の操作を提供します。

    Attributes:
        db: AsyncSessionインスタンス（データベースセッション）
        session_repository: AnalysisSessionRepositoryインスタンス
    """

    def __init__(self, db: AsyncSession):
        """分析スナップショットサービスを初期化します。

        Args:
            db (AsyncSession): SQLAlchemyの非同期データベースセッション

        Note:
            - データベースセッションはDIコンテナから自動的に注入されます
            - セッションのライフサイクルはFastAPIのDependsによって管理されます
        """
        self.db = db
        self.session_repository = AnalysisSessionRepository(db)

    @measure_performance
    @transactional
    async def restore_snapshot(self, session_id: uuid.UUID, snapshot_id: int) -> AnalysisSession:
        """スナップショットから状態を復元します（準備中）。

        このメソッドは、指定されたスナップショットIDからセッションの状態を復元します。
        Phase 3.1で完全実装予定です。

        Args:
            session_id (uuid.UUID): セッションのUUID
            snapshot_id (int): スナップショットID

        Returns:
            AnalysisSession: 復元されたセッション

        Raises:
            NotFoundError: セッションまたはスナップショットが存在しない場合
            ValidationError: 復元処理でエラーが発生した場合

        Example:
            >>> session = await snapshot_service.restore_snapshot(
            ...     session_id=session_id,
            ...     snapshot_id=2
            ... )
            >>> print(f"Restored to snapshot {snapshot_id}")

        Note:
            - Phase 3.1で実装予定
            - @transactionalデコレータにより自動コミットされます
            - 現在はプレースホルダー実装です
        """
        logger.info(
            "スナップショットから復元中",
            session_id=str(session_id),
            snapshot_id=snapshot_id,
            action="restore_snapshot",
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

            # TODO: Phase 3.1でスナップショット復元ロジック実装
            logger.warning(
                "スナップショット復元機能は現在準備中です",
                session_id=str(session_id),
                snapshot_id=snapshot_id,
            )

            raise ValidationError(
                "スナップショット復元機能は現在準備中です。Phase 3.1で実装予定です。",
                details={"session_id": str(session_id), "snapshot_id": snapshot_id},
            )

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(
                "スナップショット復元中に予期しないエラーが発生しました",
                session_id=str(session_id),
                snapshot_id=snapshot_id,
                error=str(e),
                exc_info=True,
            )
            raise

    @measure_performance
    async def get_snapshot_id(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> int:
        """現在のスナップショットIDを取得。

        Args:
            session_id (uuid.UUID): 分析セッションID
            user_id (uuid.UUID): ユーザーID

        Returns:
            int: 現在のスナップショットID（0から始まる）

        Raises:
            NotFoundError: セッションが存在しない場合
            AuthorizationError: ユーザーに権限がない場合

        Example:
            >>> snapshot_id = await snapshot_service.get_snapshot_id(session_id, user_id)
            >>> print(f"Current snapshot: {snapshot_id}")
        """
        logger.info(
            "スナップショットID取得",
            session_id=str(session_id),
            user_id=str(user_id),
        )

        # セッションの存在確認
        session = await self.session_repository.get(session_id)
        if not session:
            logger.warning(
                "セッションが見つかりません",
                session_id=str(session_id),
            )
            raise NotFoundError(
                f"セッション {session_id} が見つかりません",
                details={"session_id": str(session_id)},
            )

        # 権限チェック
        if session.created_by != user_id:
            logger.warning(
                "セッションへのアクセス権限がありません",
                session_id=str(session_id),
                user_id=str(user_id),
                created_by=str(session.created_by),
            )
            raise AuthorizationError(
                "このセッションにアクセスする権限がありません",
                details={"session_id": str(session_id), "user_id": str(user_id)},
            )

        # AnalysisStateを使用してスナップショットID取得
        from app.services.analysis.agent.state import AnalysisState

        state = AnalysisState(self.db, session_id)
        snapshot_id = await state.get_snapshot_id()

        logger.info(
            "スナップショットID取得成功",
            session_id=str(session_id),
            snapshot_id=snapshot_id,
        )

        return snapshot_id

    @measure_performance
    async def save_snapshot(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        current_snapshot: bool = False,
    ) -> int:
        """現在の状態をスナップショットとして保存。

        分析ステップの現在の状態をスナップショットとして保存します。
        後で revert_snapshot() を使用して、この状態に戻すことができます。

        Args:
            session_id (uuid.UUID): 分析セッションID
            user_id (uuid.UUID): ユーザーID
            current_snapshot (bool): 現在のスナップショットを更新するか（デフォルト: False）
                - False: 新しいスナップショットを作成
                - True: 現在のスナップショットを更新

        Returns:
            int: 保存されたスナップショットID

        Raises:
            NotFoundError: セッションが存在しない場合
            AuthorizationError: ユーザーに権限がない場合
            ValidationError: スナップショット保存に失敗した場合

        Example:
            >>> # 新しいスナップショットを作成
            >>> snapshot_id = await snapshot_service.save_snapshot(session_id, user_id)
            >>> print(f"Saved snapshot {snapshot_id}")

            >>> # 現在のスナップショットを更新
            >>> snapshot_id = await snapshot_service.save_snapshot(
            ...     session_id, user_id, current_snapshot=True
            ... )
        """
        logger.info(
            "スナップショット保存",
            session_id=str(session_id),
            user_id=str(user_id),
            current_snapshot=current_snapshot,
        )

        # セッションの存在確認と権限チェック
        session = await self.session_repository.get(session_id)
        if not session:
            logger.warning(
                "セッションが見つかりません",
                session_id=str(session_id),
            )
            raise NotFoundError(
                f"セッション {session_id} が見つかりません",
                details={"session_id": str(session_id)},
            )

        if session.created_by != user_id:
            logger.warning(
                "セッションへのアクセス権限がありません",
                session_id=str(session_id),
                user_id=str(user_id),
            )
            raise AuthorizationError(
                "このセッションにアクセスする権限がありません",
                details={"session_id": str(session_id), "user_id": str(user_id)},
            )

        try:
            # AnalysisStateを使用してスナップショット保存
            from app.services.analysis.agent.state import AnalysisState

            state = AnalysisState(self.db, session_id)
            snapshot_id = await state.save_snapshot(current_snapshot)

            logger.info(
                "スナップショット保存成功",
                session_id=str(session_id),
                snapshot_id=snapshot_id,
                current_snapshot=current_snapshot,
            )

            return snapshot_id

        except Exception as e:
            logger.error(
                "スナップショット保存中にエラーが発生しました",
                session_id=str(session_id),
                error=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"スナップショットの保存に失敗しました: {e}",
                details={"session_id": str(session_id), "error": str(e)},
            ) from e

    @measure_performance
    async def revert_snapshot(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        snapshot_id: int,
    ) -> None:
        """指定したスナップショットに戻す。

        以前に保存したスナップショットの状態に戻します。
        現在のステップ（スナップショット以降に追加されたもの）は削除されます。

        Args:
            session_id (uuid.UUID): 分析セッションID
            user_id (uuid.UUID): ユーザーID
            snapshot_id (int): 戻すスナップショットID

        Raises:
            NotFoundError: セッションまたはスナップショットが存在しない場合
            AuthorizationError: ユーザーに権限がない場合
            ValidationError: スナップショット復元に失敗した場合

        Warning:
            この操作は元に戻せません。スナップショット以降に追加されたステップは
            完全に削除されます。

        Example:
            >>> # スナップショット2の状態に戻す
            >>> await snapshot_service.revert_snapshot(session_id, user_id, snapshot_id=2)
        """
        logger.info(
            "スナップショット復元",
            session_id=str(session_id),
            user_id=str(user_id),
            snapshot_id=snapshot_id,
        )

        # セッションの存在確認と権限チェック
        session = await self.session_repository.get(session_id)
        if not session:
            logger.warning(
                "セッションが見つかりません",
                session_id=str(session_id),
            )
            raise NotFoundError(
                f"セッション {session_id} が見つかりません",
                details={"session_id": str(session_id)},
            )

        if session.created_by != user_id:
            logger.warning(
                "セッションへのアクセス権限がありません",
                session_id=str(session_id),
                user_id=str(user_id),
            )
            raise AuthorizationError(
                "このセッションにアクセスする権限がありません",
                details={"session_id": str(session_id), "user_id": str(user_id)},
            )

        try:
            # AnalysisStateを使用してスナップショット復元
            from app.services.analysis.agent.state import AnalysisState

            state = AnalysisState(self.db, session_id)
            await state.revert_snapshot(snapshot_id)

            logger.info(
                "スナップショット復元成功",
                session_id=str(session_id),
                snapshot_id=snapshot_id,
            )

        except Exception as e:
            logger.error(
                "スナップショット復元中にエラーが発生しました",
                session_id=str(session_id),
                snapshot_id=snapshot_id,
                error=str(e),
                exc_info=True,
            )
            raise ValidationError(
                f"スナップショットの復元に失敗しました: {e}",
                details={
                    "session_id": str(session_id),
                    "snapshot_id": snapshot_id,
                    "error": str(e),
                },
            ) from e
