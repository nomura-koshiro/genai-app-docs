"""操作履歴記録ミドルウェア。

全APIリクエストを自動的に記録し、操作履歴として保存します。
"""

import json
import re
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.database import get_async_session_context
from app.core.logging import get_logger
from app.models import ActionType, UserActivity

logger = get_logger(__name__)


class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    """ユーザー操作履歴を自動記録するミドルウェア。

    全リクエストの基本情報を記録し、エラー発生時もエラー情報を含めて記録します。
    除外パスは記録をスキップします。

    Attributes:
        EXCLUDE_PATHS: 除外する固定パスのリスト
        EXCLUDE_PATTERNS: 除外するパスパターン（正規表現）
        SENSITIVE_KEYS: マスク対象の機密情報キー
        RESOURCE_PATTERNS: リソース情報抽出用パターン
    """

    # 除外する固定パス
    EXCLUDE_PATHS: set[str] = {
        "/health",
        "/healthz",
        "/ready",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }

    # 除外するパスパターン（正規表現）
    EXCLUDE_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"^/static/"),
        re.compile(r"^/assets/"),
        re.compile(r"^/_next/"),
    ]

    # マスク対象の機密情報キー
    SENSITIVE_KEYS: set[str] = {
        "password",
        "token",
        "secret",
        "api_key",
        "apikey",
        "credential",
        "authorization",
        "access_token",
        "refresh_token",
        "session_token",
    }

    # リソース情報抽出用パターン
    RESOURCE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"/api/v1/projects?/([0-9a-f-]{36})"), "PROJECT"),
        (re.compile(r"/api/v1/analysis/session/([0-9a-f-]{36})"), "ANALYSIS_SESSION"),
        (re.compile(r"/api/v1/driver-tree/tree/([0-9a-f-]{36})"), "DRIVER_TREE"),
        (re.compile(r"/api/v1/user_accounts?/([0-9a-f-]{36})"), "USER"),
        (re.compile(r"/api/v1/admin/projects?/([0-9a-f-]{36})"), "PROJECT"),
        (re.compile(r"/api/v1/admin/sessions?/([0-9a-f-]{36})"), "SESSION"),
        (re.compile(r"/api/v1/admin/announcements?/([0-9a-f-]{36})"), "ANNOUNCEMENT"),
        (re.compile(r"/api/v1/admin/alerts?/([0-9a-f-]{36})"), "ALERT"),
    ]

    def __init__(self, app: ASGIApp) -> None:
        """ミドルウェアを初期化します。

        Args:
            app: ASGIアプリケーション
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """リクエストを処理し、操作履歴を記録します。

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/エンドポイント

        Returns:
            Response: HTTPレスポンス
        """
        # 除外パスチェック
        if self._should_skip(request.url.path):
            return await call_next(request)

        start_time = time.perf_counter()
        response_status = 500
        error_message: str | None = None
        error_code: str | None = None
        request_body: dict[str, Any] | None = None

        try:
            # リクエストボディの取得（POSTなどのみ）
            if request.method in {"POST", "PUT", "PATCH"}:
                request_body = await self._get_masked_request_body(request)

            # リクエスト処理
            response = await call_next(request)
            response_status = response.status_code

            # エラーレスポンスの場合、エラー情報を抽出
            if response_status >= 400:
                error_message, error_code = await self._extract_error_info(response)

            return response

        except Exception as e:
            response_status = 500
            error_message = str(e)
            error_code = type(e).__name__
            logger.exception(
                "リクエスト処理中にエラーが発生しました",
                path=request.url.path,
                method=request.method,
            )
            raise

        finally:
            # 処理時間計算
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            # 操作履歴を非同期で記録
            await self._record_activity(
                request=request,
                request_body=request_body,
                response_status=response_status,
                error_message=error_message,
                error_code=error_code,
                duration_ms=duration_ms,
            )

    def _should_skip(self, path: str) -> bool:
        """パスが除外対象かどうかを判定します。

        Args:
            path: URLパス

        Returns:
            bool: 除外対象の場合True
        """
        # 固定パスチェック
        if path in self.EXCLUDE_PATHS:
            return True

        # パターンチェック
        for pattern in self.EXCLUDE_PATTERNS:
            if pattern.match(path):
                return True

        return False

    async def _get_masked_request_body(self, request: Request) -> dict[str, Any] | None:
        """リクエストボディを取得し、機密情報をマスクします。

        注意: リクエストボディは一度しか読めないため、読み取り後はキャッシュします。
        これにより、エンドポイントでもボディを再度読み取ることが可能になります。

        Args:
            request: HTTPリクエスト

        Returns:
            dict | None: マスク済みリクエストボディ
        """
        try:
            # ボディをバイト列として取得
            body_bytes = await request.body()

            # リクエストにキャッシュして再利用可能にする
            # FastAPIは内部で_bodyをチェックするため、これで再読み取りが可能
            request._body = body_bytes  # type: ignore[attr-defined]

            # JSONとしてパース
            body = json.loads(body_bytes)
            return self._mask_sensitive_data(body)
        except Exception:
            return None

    def _mask_sensitive_data(self, data: Any, depth: int = 0) -> Any:
        """機密情報をマスクします。

        Args:
            data: マスク対象データ
            depth: ネスト深度（無限ループ防止）

        Returns:
            Any: マスク済みデータ
        """
        if depth > 10:  # 深すぎるネストは打ち切り
            return "***NESTED***"

        if isinstance(data, dict):
            return {
                key: ("***MASKED***" if key.lower() in self.SENSITIVE_KEYS else self._mask_sensitive_data(value, depth + 1))
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item, depth + 1) for item in data]
        else:
            return data

    async def _extract_error_info(
        self,
        response: Response,
    ) -> tuple[str | None, str | None]:
        """レスポンスからエラー情報を抽出します。

        Args:
            response: HTTPレスポンス

        Returns:
            tuple[str | None, str | None]: (エラーメッセージ, エラーコード)
        """
        try:
            # StreamingResponseの場合はボディを読めないのでスキップ
            if hasattr(response, "body"):
                body_data = response.body
                # memoryviewの場合はbytesに変換
                if isinstance(body_data, memoryview):
                    body_data = bytes(body_data)
                body = json.loads(body_data)
                return (
                    body.get("message") or body.get("detail"),
                    body.get("code") or body.get("error_code"),
                )
        except Exception:
            pass

        return None, None

    def _extract_resource_info(self, path: str) -> tuple[str | None, uuid.UUID | None]:
        """URLパスからリソース情報を抽出します。

        Args:
            path: URLパス

        Returns:
            tuple[str | None, uuid.UUID | None]: (リソース種別, リソースID)
        """
        for pattern, resource_type in self.RESOURCE_PATTERNS:
            match = pattern.search(path)
            if match:
                try:
                    resource_id = uuid.UUID(match.group(1))
                    return resource_type, resource_id
                except ValueError:
                    continue

        return None, None

    def _infer_action_type(self, method: str, status_code: int) -> str:
        """HTTPメソッドとステータスコードからアクション種別を推定します。

        Args:
            method: HTTPメソッド
            status_code: HTTPステータスコード

        Returns:
            str: アクション種別
        """
        if status_code >= 400:
            return ActionType.ERROR.value

        mapping = {
            "GET": ActionType.READ.value,
            "POST": ActionType.CREATE.value,
            "PUT": ActionType.UPDATE.value,
            "PATCH": ActionType.UPDATE.value,
            "DELETE": ActionType.DELETE.value,
        }

        return mapping.get(method, ActionType.READ.value)

    def _get_client_ip(self, request: Request) -> str | None:
        """クライアントIPアドレスを取得します。

        X-Forwarded-Forヘッダーを優先し、なければ直接接続元を使用。

        Args:
            request: HTTPリクエスト

        Returns:
            str | None: クライアントIPアドレス
        """
        # プロキシ経由の場合
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # 最初のIPがオリジナルクライアント
            return forwarded_for.split(",")[0].strip()

        # 直接接続の場合
        if request.client:
            return request.client.host

        return None

    async def _record_activity(
        self,
        request: Request,
        request_body: dict[str, Any] | None,
        response_status: int,
        error_message: str | None,
        error_code: str | None,
        duration_ms: int,
    ) -> None:
        """操作履歴をデータベースに記録します。

        Args:
            request: HTTPリクエスト
            request_body: リクエストボディ
            response_status: レスポンスステータス
            error_message: エラーメッセージ
            error_code: エラーコード
            duration_ms: 処理時間（ミリ秒）
        """
        try:
            # リソース情報を抽出
            resource_type, resource_id = self._extract_resource_info(request.url.path)

            # アクション種別を推定
            action_type = self._infer_action_type(request.method, response_status)

            # ユーザーIDを取得（認証済みの場合）
            user_id = None
            if hasattr(request.state, "user") and request.state.user:
                user_id = request.state.user.id

            # 操作履歴オブジェクトを作成
            activity = UserActivity(
                user_id=user_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                endpoint=request.url.path,
                method=request.method,
                request_body=request_body,
                response_status=response_status,
                error_message=error_message,
                error_code=error_code,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", "")[:500],
                duration_ms=duration_ms,
            )

            # 非同期でDB保存
            async with get_async_session_context() as session:
                session.add(activity)
                await session.commit()

        except Exception as e:
            # 記録失敗はログのみ（リクエスト処理には影響させない）
            logger.error(
                "操作履歴の記録に失敗しました",
                error=str(e),
                path=request.url.path,
                method=request.method,
            )
