"""サポートツールサービス。

このモジュールは、管理者向けサポートツール機能を提供します。
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.decorators import measure_performance, transactional
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.admin.system_setting_repository import SystemSettingRepository
from app.repositories.admin.user_session_repository import UserSessionRepository
from app.repositories.user_account.user_account import UserAccountRepository
from app.schemas.admin.health_check import (
    ComponentHealth,
    HealthCheckDetailResponse,
    HealthCheckResponse,
)
from app.schemas.admin.support_tools import (
    DebugModeResponse,
    ImpersonateEndResponse,
    ImpersonateResponse,
    ImpersonateUserInfo,
)

logger = get_logger(__name__)


class SupportToolsService:
    """サポートツールサービス。

    管理者向けサポートツール機能を提供します。

    メソッド:
        - start_impersonation: ユーザー代行を開始
        - end_impersonation: ユーザー代行を終了
        - enable_debug_mode: デバッグモードを有効化
        - disable_debug_mode: デバッグモードを無効化
        - simple_health_check: 簡易ヘルスチェック
        - detailed_health_check: 詳細ヘルスチェック
    """

    def __init__(self, db: AsyncSession):
        """サービスを初期化します。"""
        self.db = db
        self.user_repository = UserAccountRepository(db)
        self.session_repository = UserSessionRepository(db)
        self.setting_repository = SystemSettingRepository(db)

    # ================================================================================
    # ユーザー代行機能
    # ================================================================================

    @measure_performance
    @transactional
    async def start_impersonation(
        self,
        target_user_id: uuid.UUID,
        reason: str,
        admin_user_id: uuid.UUID,
    ) -> ImpersonateResponse:
        """ユーザー代行を開始します。

        Args:
            target_user_id: 代行対象ユーザーID
            reason: 代行理由
            admin_user_id: 管理者ユーザーID

        Returns:
            ImpersonateResponse: 代行開始レスポンス

        Raises:
            NotFoundError: 対象ユーザーが見つからない場合
        """
        logger.warning(
            "ユーザー代行を開始",
            target_user_id=str(target_user_id),
            admin_user_id=str(admin_user_id),
            reason=reason,
            action="start_impersonation",
        )

        # 対象ユーザーの存在確認
        target_user = await self.user_repository.get(target_user_id)
        if target_user is None:
            raise NotFoundError(
                "対象ユーザーが見つかりません",
                details={"user_id": str(target_user_id)},
            )

        # 代行トークンを生成
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # 代行セッションを作成（1時間有効）
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        await self.session_repository.create(
            user_id=target_user_id,
            session_token_hash=token_hash,
            login_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
            expires_at=expires_at,
            is_active=True,
            ip_address=None,
            user_agent="Impersonation Session",
            device_info={"impersonated_by": str(admin_user_id), "reason": reason},
        )

        logger.warning(
            "ユーザー代行セッションを作成しました",
            target_user_id=str(target_user_id),
            admin_user_id=str(admin_user_id),
            expires_at=expires_at.isoformat(),
        )

        return ImpersonateResponse(
            impersonation_token=token,
            target_user=ImpersonateUserInfo(
                id=target_user.id,
                name=target_user.display_name or "",
            ),
            expires_at=expires_at,
        )

    @measure_performance
    @transactional
    async def end_impersonation(
        self,
        token: str,
        admin_user_id: uuid.UUID,
    ) -> ImpersonateEndResponse:
        """ユーザー代行を終了します。

        Args:
            token: 代行トークン
            admin_user_id: 管理者ユーザーID

        Returns:
            ImpersonateEndResponse: 代行終了レスポンス
        """
        logger.info(
            "ユーザー代行を終了",
            admin_user_id=str(admin_user_id),
            action="end_impersonation",
        )

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        session = await self.session_repository.get_by_token_hash(token_hash)

        if session:
            await self.session_repository.terminate_session(
                session.id,
                reason="IMPERSONATION_ENDED",
            )

        return ImpersonateEndResponse(
            success=True,
            message="ユーザー代行を終了しました",
        )

    # ================================================================================
    # デバッグモード
    # ================================================================================

    @measure_performance
    @transactional
    async def enable_debug_mode(
        self,
        admin_user_id: uuid.UUID,
    ) -> DebugModeResponse:
        """デバッグモードを有効化します。

        Args:
            admin_user_id: 管理者ユーザーID

        Returns:
            DebugModeResponse: デバッグモード状態
        """
        logger.warning(
            "デバッグモードを有効化",
            admin_user_id=str(admin_user_id),
            action="enable_debug_mode",
        )

        await self.setting_repository.set_value(
            category="DEBUG",
            key="debug_mode",
            value=True,
            updated_by=admin_user_id,
        )

        return DebugModeResponse(
            enabled=True,
            message="デバッグモードが有効化されました",
        )

    @measure_performance
    @transactional
    async def disable_debug_mode(
        self,
        admin_user_id: uuid.UUID,
    ) -> DebugModeResponse:
        """デバッグモードを無効化します。

        Args:
            admin_user_id: 管理者ユーザーID

        Returns:
            DebugModeResponse: デバッグモード状態
        """
        logger.info(
            "デバッグモードを無効化",
            admin_user_id=str(admin_user_id),
            action="disable_debug_mode",
        )

        await self.setting_repository.set_value(
            category="DEBUG",
            key="debug_mode",
            value=False,
            updated_by=admin_user_id,
        )

        return DebugModeResponse(
            enabled=False,
            message="デバッグモードが無効化されました",
        )

    # ================================================================================
    # ヘルスチェック
    # ================================================================================

    @measure_performance
    async def simple_health_check(self) -> HealthCheckResponse:
        """簡易ヘルスチェックを実行します。

        Returns:
            HealthCheckResponse: ヘルスチェック結果
        """
        try:
            # データベース接続確認
            await self.db.execute(text("SELECT 1"))
            return HealthCheckResponse(status="healthy")
        except Exception as e:
            logger.error("ヘルスチェック失敗", error=str(e))
            return HealthCheckResponse(status="unhealthy")

    @measure_performance
    async def detailed_health_check(self) -> HealthCheckDetailResponse:
        """詳細ヘルスチェックを実行します。

        Returns:
            HealthCheckDetailResponse: 詳細ヘルスチェック結果
        """
        components: list[ComponentHealth] = []
        overall_status = "healthy"

        # データベースチェック
        db_status = await self._check_database()
        components.append(db_status)
        if db_status.status != "healthy":
            overall_status = "unhealthy"

        # Redisチェック
        redis_status = await self._check_redis()
        components.append(redis_status)
        if redis_status.status != "healthy":
            if overall_status == "healthy":
                overall_status = "degraded"

        # ストレージチェック
        storage_status = await self._check_storage()
        components.append(storage_status)
        if storage_status.status != "healthy":
            if overall_status == "healthy":
                overall_status = "degraded"

        return HealthCheckDetailResponse(
            status=overall_status,
            components=components,
            timestamp=datetime.now(UTC),
        )

    async def _check_database(self) -> ComponentHealth:
        """データベース接続をチェックします。"""
        start = datetime.now(UTC)
        try:
            await self.db.execute(text("SELECT 1"))
            latency_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            return ComponentHealth(
                name="database",
                status="healthy",
                latency_ms=latency_ms,
            )
        except Exception as e:
            return ComponentHealth(
                name="database",
                status="unhealthy",
                error=str(e),
            )

    async def _check_redis(self) -> ComponentHealth:
        """Redis接続をチェックします。"""
        try:
            from app.core.cache import cache_manager

            if not cache_manager.is_redis_available():
                return ComponentHealth(
                    name="redis",
                    status="unhealthy",
                    error="Redis is not configured",
                )

            start = datetime.now(UTC)
            # exists() を使用してRedis接続を確認
            await cache_manager.exists("health_check")
            latency_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            return ComponentHealth(
                name="redis",
                status="healthy",
                latency_ms=latency_ms,
            )
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status="unhealthy",
                error=str(e),
            )

    async def _check_storage(self) -> ComponentHealth:
        """ストレージ接続をチェックします。"""
        try:
            # TODO: 実際のストレージ接続チェック
            return ComponentHealth(
                name="storage",
                status="healthy",
                latency_ms=0,
            )
        except Exception as e:
            return ComponentHealth(
                name="storage",
                status="unhealthy",
                error=str(e),
            )
