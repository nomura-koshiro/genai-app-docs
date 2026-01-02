"""セッション管理サービス。

このモジュールは、ユーザーセッションの管理機能を提供します。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.admin.user_session_repository import UserSessionRepository
from app.schemas.admin.session_management import (
    DeviceInfo,
    SessionFilter,
    SessionListResponse,
    SessionResponse,
    SessionStatistics,
    SessionUserInfo,
)

logger = get_logger(__name__)


class SessionManagementService:
    """セッション管理サービス。

    ユーザーセッションの一覧取得・強制終了機能を提供します。

    メソッド:
        - list_sessions: セッション一覧を取得
        - list_user_sessions: ユーザーのセッション一覧を取得
        - terminate_session: セッションを終了
        - terminate_all_user_sessions: ユーザーの全セッションを終了
        - get_statistics: セッション統計を取得
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.repository = UserSessionRepository(db)

    @measure_performance
    async def list_sessions(
        self,
        filter_params: SessionFilter,
    ) -> SessionListResponse:
        """セッション一覧を取得します。

        Args:
            filter_params: フィルタパラメータ

        Returns:
            SessionListResponse: セッション一覧
        """
        logger.info(
            "セッション一覧を取得中",
            filters=filter_params.model_dump(exclude_unset=True),
            action="list_sessions",
        )

        sessions = await self.repository.list_active(
            user_id=filter_params.user_id,
            ip_address=filter_params.ip_address,
            skip=(filter_params.page - 1) * filter_params.limit,
            limit=filter_params.limit,
        )

        active_count = await self.repository.count_active()
        logins_today = await self.repository.count_logins_today()

        items = [self._to_response(s) for s in sessions]

        return SessionListResponse(
            items=items,
            total=active_count,
            statistics=SessionStatistics(
                active_sessions=active_count,
                logins_today=logins_today,
            ),
        )

    @measure_performance
    async def list_user_sessions(
        self,
        user_id: uuid.UUID,
    ) -> list[SessionResponse]:
        """ユーザーのセッション一覧を取得します。

        Args:
            user_id: ユーザーID

        Returns:
            list[SessionResponse]: セッションリスト
        """
        logger.info(
            "ユーザーのセッション一覧を取得中",
            user_id=str(user_id),
            action="list_user_sessions",
        )

        sessions = await self.repository.list_by_user(user_id, active_only=True)
        return [self._to_response(s) for s in sessions]

    @measure_performance
    @transactional
    async def terminate_session(
        self,
        session_id: uuid.UUID,
        reason: str,
        terminated_by: uuid.UUID,
    ) -> SessionResponse:
        """セッションを終了します。

        Args:
            session_id: セッションID
            reason: 終了理由
            terminated_by: 終了実行者ID

        Returns:
            SessionResponse: 終了したセッション

        Raises:
            NotFoundError: セッションが見つからない場合
        """
        logger.info(
            "セッションを終了中",
            session_id=str(session_id),
            reason=reason,
            terminated_by=str(terminated_by),
            action="terminate_session",
        )

        session = await self.repository.terminate_session(session_id, reason)
        if session is None:
            raise NotFoundError(
                "セッションが見つかりません",
                details={"session_id": str(session_id)},
            )

        logger.warning(
            "セッションを強制終了しました",
            session_id=str(session_id),
            user_id=str(session.user_id),
            terminated_by=str(terminated_by),
        )

        return self._to_response(session)

    @measure_performance
    @transactional
    async def terminate_all_user_sessions(
        self,
        user_id: uuid.UUID,
        reason: str,
        terminated_by: uuid.UUID,
    ) -> int:
        """ユーザーの全セッションを終了します。

        Args:
            user_id: ユーザーID
            reason: 終了理由
            terminated_by: 終了実行者ID

        Returns:
            int: 終了したセッション数
        """
        logger.info(
            "ユーザーの全セッションを終了中",
            user_id=str(user_id),
            reason=reason,
            terminated_by=str(terminated_by),
            action="terminate_all_user_sessions",
        )

        count = await self.repository.terminate_all_user_sessions(user_id, reason)

        logger.warning(
            "ユーザーの全セッションを強制終了しました",
            user_id=str(user_id),
            terminated_count=count,
            terminated_by=str(terminated_by),
        )

        return count

    def _to_response(self, session) -> SessionResponse:
        """モデルをレスポンスに変換します。"""
        device_info = None
        if session.device_info:
            device_info = DeviceInfo(
                os=session.device_info.get("os"),
                browser=session.device_info.get("browser"),
            )

        return SessionResponse(
            id=session.id,
            user=SessionUserInfo(
                id=session.user.id,
                name=session.user.display_name,
                email=session.user.email,
            ),
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_info=device_info,
            login_at=session.login_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            is_active=session.is_active,
        )
