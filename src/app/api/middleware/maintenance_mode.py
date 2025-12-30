"""メンテナンスモードミドルウェア。

メンテナンスモード中は管理者以外のアクセスを制限します。
"""

import json
import re
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.database.session import get_async_session_context
from app.models.admin import SettingCategory
from app.models.user_account import SystemRole
from app.repositories.admin import SystemSettingRepository

logger = get_logger(__name__)


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """メンテナンスモードミドルウェア。

    メンテナンスモード中は管理者以外のアクセスを503で拒否します。

    Attributes:
        ALWAYS_ALLOWED_PATHS: メンテナンス中も常にアクセス可能なパス
        ADMIN_PATH_PATTERN: 管理者専用パスパターン
    """

    # メンテナンス中も常にアクセス可能なパス
    ALWAYS_ALLOWED_PATHS: set[str] = {
        "/health",
        "/healthz",
        "/ready",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    # 管理者専用パスパターン
    ADMIN_PATH_PATTERN: re.Pattern[str] = re.compile(r"^/api/v1/admin/")

    def __init__(self, app: ASGIApp) -> None:
        """ミドルウェアを初期化します。

        Args:
            app: ASGIアプリケーション
        """
        super().__init__(app)
        self._maintenance_cache: dict[str, bool | str] | None = None
        self._cache_ttl: float = 0

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """リクエストを処理し、メンテナンスモードをチェックします。

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/エンドポイント

        Returns:
            Response: HTTPレスポンス
        """
        path = request.url.path

        # 常にアクセス可能なパスはスキップ
        if path in self.ALWAYS_ALLOWED_PATHS:
            return await call_next(request)

        # メンテナンスモード設定を取得
        maintenance_settings = await self._get_maintenance_settings()

        if not maintenance_settings.get("enabled", False):
            return await call_next(request)

        # メンテナンスモード中
        allow_admin_access = maintenance_settings.get("allow_admin_access", True)
        maintenance_message = maintenance_settings.get(
            "message",
            "システムはメンテナンス中です。しばらくお待ちください。",
        )

        # 管理者アクセスが許可されている場合
        if allow_admin_access:
            # 認証済みユーザーかチェック
            if hasattr(request.state, "user") and request.state.user:
                user = request.state.user
                # システム管理者の場合はアクセス許可
                if user.system_role == SystemRole.ADMIN:
                    return await call_next(request)

            # 管理者パスへのアクセスは認証後に判定
            if self.ADMIN_PATH_PATTERN.match(path):
                return await call_next(request)

        # 503 Service Unavailableを返す
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "code": "MAINTENANCE_MODE",
                "message": maintenance_message,
                "details": {
                    "retry_after": 3600,  # 1時間後に再試行推奨
                },
            },
            headers={
                "Retry-After": "3600",
            },
        )

    async def _get_maintenance_settings(self) -> dict[str, bool | str]:
        """メンテナンスモード設定を取得します。

        キャッシュを使用して頻繁なDB問い合わせを防ぎます。

        Returns:
            dict: メンテナンスモード設定
        """
        current_time = time.time()

        # キャッシュが有効な場合はキャッシュを返す（30秒TTL）
        if self._maintenance_cache and current_time < self._cache_ttl:
            return self._maintenance_cache

        try:
            async with get_async_session_context() as session:
                repository = SystemSettingRepository(session)

                # メンテナンスモード設定を取得
                maintenance_mode = await repository.get_by_category_and_key(
                    category=SettingCategory.MAINTENANCE,
                    key="maintenance_mode",
                )

                maintenance_message = await repository.get_by_category_and_key(
                    category=SettingCategory.MAINTENANCE,
                    key="maintenance_message",
                )

                allow_admin = await repository.get_by_category_and_key(
                    category=SettingCategory.MAINTENANCE,
                    key="allow_admin_access",
                )

                settings: dict[str, bool | str] = {
                    "enabled": (json.loads(maintenance_mode.value) if maintenance_mode else False),
                    "message": (json.loads(maintenance_message.value) if maintenance_message else ""),
                    "allow_admin_access": (json.loads(allow_admin.value) if allow_admin else True),
                }

                # キャッシュを更新
                self._maintenance_cache = settings
                self._cache_ttl = current_time + 30  # 30秒TTL

                return settings

        except Exception as e:
            logger.error(
                "メンテナンスモード設定の取得に失敗しました",
                error=str(e),
            )
            # エラー時はメンテナンスモードOFFとして扱う
            return {"enabled": False}

    def clear_cache(self) -> None:
        """キャッシュをクリアします。

        設定変更時に呼び出して即時反映させます。
        """
        self._maintenance_cache = None
        self._cache_ttl = 0
