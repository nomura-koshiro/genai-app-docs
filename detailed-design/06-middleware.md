# ミドルウェア詳細設計

## 1. 概要

本ドキュメントでは、システム管理機能（SA-001〜SA-043）で使用するミドルウェアの詳細設計を定義する。

### 1.1 ミドルウェア一覧

| ミドルウェア | 対応ユースケース | 説明 |
|-------------|----------------|------|
| ActivityTrackingMiddleware | SA-001〜SA-006 | ユーザー操作履歴の自動記録 |
| MaintenanceModeMiddleware | SA-019〜SA-020 | メンテナンスモード時のアクセス制御 |
| AuditLogMiddleware | SA-012〜SA-016 | 監査ログの自動記録 |

### 1.2 ファイル構成

```
src/app/api/middlewares/
├── __init__.py
├── activity_tracking.py    # 操作履歴記録ミドルウェア
├── audit_log.py           # 監査ログミドルウェア
├── logging.py             # ロギングミドルウェア
├── maintenance_mode.py     # メンテナンスモードミドルウェア
├── metrics.py             # メトリクスミドルウェア
├── rate_limit.py          # レート制限ミドルウェア
└── security_headers.py    # セキュリティヘッダーミドルウェア
```

---

## 2. 操作履歴記録ミドルウェア（ActivityTrackingMiddleware）

### 2.1 概要

全APIリクエストを自動的に記録し、ユーザー操作履歴（user_activity）テーブルに保存する。

### 2.2 実装

```python
"""操作履歴記録ミドルウェア。

全APIリクエストを自動的に記録し、操作履歴として保存します。
"""

import re
import time
import uuid
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.database.session import get_async_session_context
from app.models.admin import ActionType, UserActivity
from app.repositories.admin import UserActivityRepository

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
    EXCLUDE_PATTERNS: list[re.Pattern] = [
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
    RESOURCE_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"/api/v1/projects?/([0-9a-f-]{36})"), "PROJECT"),
        (re.compile(r"/api/v1/analysis/session/([0-9a-f-]{36})"), "ANALYSIS_SESSION"),
        (re.compile(r"/api/v1/driver-tree/tree/([0-9a-f-]{36})"), "DRIVER_TREE"),
        (re.compile(r"/api/v1/user_accounts?/([0-9a-f-]{36})"), "USER"),
        (re.compile(r"/api/v1/admin/projects?/([0-9a-f-]{36})"), "PROJECT"),
        (re.compile(r"/api/v1/admin/sessions?/([0-9a-f-]{36})"), "SESSION"),
        (re.compile(r"/api/v1/admin/announcements?/([0-9a-f-]{36})"), "ANNOUNCEMENT"),
        (re.compile(r"/api/v1/admin/alerts?/([0-9a-f-]{36})"), "ALERT"),
    ]

    def __init__(self, app: ASGIApp):
        """ミドルウェアを初期化します。

        Args:
            app: ASGIアプリケーション
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
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
        request_body: dict | None = None

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

    async def _get_masked_request_body(self, request: Request) -> dict | None:
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
            request._body = body_bytes

            # JSONとしてパース
            import json
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
                key: (
                    "***MASKED***"
                    if key.lower() in self.SENSITIVE_KEYS
                    else self._mask_sensitive_data(value, depth + 1)
                )
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
                import json

                body = json.loads(response.body)
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

        return mapping.get(method, ActionType.OTHER.value)

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
        request_body: dict | None,
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
                repository = UserActivityRepository(session)
                await repository.create(activity)
                await session.commit()

        except Exception as e:
            # 記録失敗はログのみ（リクエスト処理には影響させない）
            logger.error(
                "操作履歴の記録に失敗しました",
                error=str(e),
                path=request.url.path,
                method=request.method,
            )
```

---

## 3. メンテナンスモードミドルウェア（MaintenanceModeMiddleware）

### 3.1 概要

メンテナンスモード時に一般ユーザーのアクセスを制限し、管理者のみアクセス可能にする。

### 3.2 実装

```python
"""メンテナンスモードミドルウェア。

メンテナンスモード中は管理者以外のアクセスを制限します。
"""

import json
import re
from typing import Callable

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
        ADMIN_PATHS: 管理者専用パス
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
    ADMIN_PATH_PATTERN: re.Pattern = re.compile(r"^/api/v1/admin/")

    def __init__(self, app: ASGIApp):
        """ミドルウェアを初期化します。

        Args:
            app: ASGIアプリケーション
        """
        super().__init__(app)
        self._maintenance_cache: dict | None = None
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

    async def _get_maintenance_settings(self) -> dict:
        """メンテナンスモード設定を取得します。

        キャッシュを使用して頻繁なDB問い合わせを防ぎます。

        Returns:
            dict: メンテナンスモード設定
        """
        import time

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

                settings = {
                    "enabled": (
                        json.loads(maintenance_mode.value)
                        if maintenance_mode
                        else False
                    ),
                    "message": (
                        json.loads(maintenance_message.value)
                        if maintenance_message
                        else ""
                    ),
                    "allow_admin_access": (
                        json.loads(allow_admin.value) if allow_admin else True
                    ),
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
```

---

## 4. 監査ログミドルウェア（AuditLogMiddleware）

### 4.1 概要

重要なデータ変更操作を自動的に監査ログに記録する。操作履歴より詳細な変更前後の値を記録。

### 4.2 実装

```python
"""監査ログミドルウェア。

重要なデータ変更操作を監査ログに記録します。
"""

import json
import re
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.database.session import get_async_session_context
from app.models.admin import AuditLog, AuditEventType, AuditSeverity
from app.repositories.admin import AuditLogRepository

logger = get_logger(__name__)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """監査ログミドルウェア。

    データ変更・セキュリティイベントを監査ログに記録します。

    Attributes:
        AUDIT_TARGETS: 監査対象のパスパターンと設定
    """

    # 監査対象のパスパターンと設定
    AUDIT_TARGETS: list[dict] = [
        # プロジェクト変更
        {
            "pattern": re.compile(r"^/api/v1/projects?/([0-9a-f-]{36})$"),
            "methods": {"PUT", "PATCH", "DELETE"},
            "resource_type": "PROJECT",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.INFO,
        },
        # ユーザー変更
        {
            "pattern": re.compile(r"^/api/v1/user_accounts?/([0-9a-f-]{36})$"),
            "methods": {"PUT", "PATCH", "DELETE"},
            "resource_type": "USER",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.INFO,
        },
        # システム設定変更
        {
            "pattern": re.compile(r"^/api/v1/admin/settings/"),
            "methods": {"PATCH", "POST"},
            "resource_type": "SYSTEM_SETTING",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.WARNING,
        },
        # セッション終了（強制ログアウト）
        {
            "pattern": re.compile(r"^/api/v1/admin/sessions/.*/terminate"),
            "methods": {"POST"},
            "resource_type": "SESSION",
            "event_type": AuditEventType.SECURITY,
            "severity": AuditSeverity.WARNING,
        },
        # 一括操作
        {
            "pattern": re.compile(r"^/api/v1/admin/bulk/"),
            "methods": {"POST"},
            "resource_type": "BULK_OPERATION",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.WARNING,
        },
        # データ削除
        {
            "pattern": re.compile(r"^/api/v1/admin/data/cleanup/execute"),
            "methods": {"POST"},
            "resource_type": "DATA_CLEANUP",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.CRITICAL,
        },
        # 代行操作
        {
            "pattern": re.compile(r"^/api/v1/admin/impersonate/"),
            "methods": {"POST"},
            "resource_type": "IMPERSONATION",
            "event_type": AuditEventType.SECURITY,
            "severity": AuditSeverity.CRITICAL,
        },
    ]

    def __init__(self, app: ASGIApp):
        """ミドルウェアを初期化します。

        Args:
            app: ASGIアプリケーション
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """リクエストを処理し、必要に応じて監査ログを記録します。

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/エンドポイント

        Returns:
            Response: HTTPレスポンス
        """
        path = request.url.path
        method = request.method

        # 監査対象かチェック
        audit_config = self._get_audit_config(path, method)
        if not audit_config:
            return await call_next(request)

        # リクエストボディを取得
        request_body = None
        if method in {"POST", "PUT", "PATCH"}:
            try:
                request_body = await request.json()
            except Exception:
                pass

        # リクエスト処理
        response = await call_next(request)

        # 成功時のみ監査ログを記録（2xxのみ）
        if 200 <= response.status_code < 300:
            await self._record_audit_log(
                request=request,
                request_body=request_body,
                response=response,
                audit_config=audit_config,
            )

        return response

    def _get_audit_config(self, path: str, method: str) -> dict | None:
        """パスとメソッドから監査設定を取得します。

        Args:
            path: URLパス
            method: HTTPメソッド

        Returns:
            dict | None: 監査設定（該当なしの場合None）
        """
        for config in self.AUDIT_TARGETS:
            if method in config["methods"] and config["pattern"].match(path):
                return config
        return None

    def _extract_resource_id(self, path: str, pattern: re.Pattern) -> str | None:
        """パスからリソースIDを抽出します。

        Args:
            path: URLパス
            pattern: 正規表現パターン

        Returns:
            str | None: リソースID
        """
        match = pattern.search(path)
        if match and match.groups():
            return match.group(1)
        return None

    def _infer_action(self, method: str) -> str:
        """HTTPメソッドからアクションを推定します。

        Args:
            method: HTTPメソッド

        Returns:
            str: アクション種別
        """
        mapping = {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE",
        }
        return mapping.get(method, "OTHER")

    def _get_changed_fields(
        self,
        old_value: dict | None,
        new_value: dict | None,
    ) -> list[str]:
        """変更されたフィールドを特定します。

        Args:
            old_value: 変更前の値
            new_value: 変更後の値

        Returns:
            list[str]: 変更されたフィールド名のリスト
        """
        if not old_value or not new_value:
            return []

        changed = []
        all_keys = set(old_value.keys()) | set(new_value.keys())

        for key in all_keys:
            old_val = old_value.get(key)
            new_val = new_value.get(key)
            if old_val != new_val:
                changed.append(key)

        return changed

    async def _record_audit_log(
        self,
        request: Request,
        request_body: dict | None,
        response: Response,
        audit_config: dict,
    ) -> None:
        """監査ログを記録します。

        Args:
            request: HTTPリクエスト
            request_body: リクエストボディ
            response: HTTPレスポンス
            audit_config: 監査設定
        """
        try:
            import uuid

            # リソースIDを抽出
            resource_id = self._extract_resource_id(
                request.url.path,
                audit_config["pattern"],
            )

            # ユーザーIDを取得
            user_id = None
            if hasattr(request.state, "user") and request.state.user:
                user_id = request.state.user.id

            # 監査ログを作成
            audit_log = AuditLog(
                user_id=user_id,
                event_type=audit_config["event_type"].value,
                action=self._infer_action(request.method),
                resource_type=audit_config["resource_type"],
                resource_id=uuid.UUID(resource_id) if resource_id else None,
                old_value=None,  # 変更前の値は別途取得が必要
                new_value=request_body,
                changed_fields=list(request_body.keys()) if request_body else None,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", "")[:500],
                severity=audit_config["severity"].value,
                metadata={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                },
            )

            # DB保存
            async with get_async_session_context() as session:
                repository = AuditLogRepository(session)
                await repository.create(audit_log)
                await session.commit()

        except Exception as e:
            logger.error(
                "監査ログの記録に失敗しました",
                error=str(e),
                path=request.url.path,
            )

    def _get_client_ip(self, request: Request) -> str | None:
        """クライアントIPアドレスを取得します。

        Args:
            request: HTTPリクエスト

        Returns:
            str | None: クライアントIPアドレス
        """
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return None
```

---

## 5. ミドルウェア登録

### 5.1 アプリケーションへの登録

```python
# src/app/main.py

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.middlewares import (
    ActivityTrackingMiddleware,
    AuditLogMiddleware,
    MaintenanceModeMiddleware,
)
from app.core.config import settings


def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成します。"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # ミドルウェア登録（順序重要：下から上に実行される）

    # 1. 操作履歴記録（最も内側で実行）
    app.add_middleware(ActivityTrackingMiddleware)

    # 2. 監査ログ記録
    app.add_middleware(AuditLogMiddleware)

    # 3. メンテナンスモードチェック
    app.add_middleware(MaintenanceModeMiddleware)

    # 4. CORSミドルウェア（最も外側で実行）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ルーター登録
    from app.api.routes import api_router
    app.include_router(api_router)

    return app
```

### 5.2 ミドルウェアパッケージ初期化

```python
# src/app/api/middlewares/__init__.py

from .activity_tracking import ActivityTrackingMiddleware
from .audit_log import AuditLogMiddleware
from .logging import LoggingMiddleware
from .maintenance_mode import MaintenanceModeMiddleware
from .metrics import PrometheusMetricsMiddleware
from .rate_limit import RateLimitMiddleware
from .security_headers import SecurityHeadersMiddleware

__all__ = [
    "ActivityTrackingMiddleware",
    "AuditLogMiddleware",
    "LoggingMiddleware",
    "MaintenanceModeMiddleware",
    "PrometheusMetricsMiddleware",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
]
```

---

## 6. 設定

### 6.1 環境変数

```python
# src/app/core/config.py に追加

class Settings(BaseSettings):
    # ... 既存設定 ...

    # 操作履歴設定
    ACTIVITY_TRACKING_ENABLED: bool = True
    ACTIVITY_TRACKING_EXCLUDE_PATHS: list[str] = ["/health", "/metrics"]

    # メンテナンスモード設定
    MAINTENANCE_MODE_CACHE_TTL: int = 30  # 秒

    # 監査ログ設定
    AUDIT_LOG_ENABLED: bool = True
```

---

## 7. パフォーマンス考慮

### 7.1 非同期処理

- 操作履歴・監査ログの記録は非同期で実行
- レスポンス返却をブロックしない設計

### 7.2 キャッシュ

- メンテナンスモード設定は30秒TTLでキャッシュ
- DB問い合わせ頻度を削減

### 7.3 除外パス

- ヘルスチェックなど頻繁にアクセスされるパスは除外
- 不要なDB書き込みを防止

---

## 8. テスト

### 8.1 ユニットテスト例

```python
"""ミドルウェアのテスト。"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middlewares import (
    ActivityTrackingMiddleware,
    MaintenanceModeMiddleware,
)


class TestActivityTrackingMiddleware:
    """操作履歴記録ミドルウェアのテスト。"""

    def test_should_skip_health_endpoint(self):
        """ヘルスチェックエンドポイントは除外されること。"""
        middleware = ActivityTrackingMiddleware(app=MagicMock())
        assert middleware._should_skip("/health") is True
        assert middleware._should_skip("/healthz") is True

    def test_should_not_skip_api_endpoint(self):
        """APIエンドポイントは記録されること。"""
        middleware = ActivityTrackingMiddleware(app=MagicMock())
        assert middleware._should_skip("/api/v1/projects") is False

    def test_mask_sensitive_data(self):
        """機密情報がマスクされること。"""
        middleware = ActivityTrackingMiddleware(app=MagicMock())

        data = {
            "email": "test@example.com",
            "password": "secret123",
            "token": "jwt_token",
        }

        masked = middleware._mask_sensitive_data(data)

        assert masked["email"] == "test@example.com"
        assert masked["password"] == "***MASKED***"
        assert masked["token"] == "***MASKED***"

    def test_extract_resource_info(self):
        """リソース情報が正しく抽出されること。"""
        middleware = ActivityTrackingMiddleware(app=MagicMock())

        resource_type, resource_id = middleware._extract_resource_info(
            "/api/v1/projects/550e8400-e29b-41d4-a716-446655440000"
        )

        assert resource_type == "PROJECT"
        assert str(resource_id) == "550e8400-e29b-41d4-a716-446655440000"

    def test_infer_action_type(self):
        """アクション種別が正しく推定されること。"""
        middleware = ActivityTrackingMiddleware(app=MagicMock())

        assert middleware._infer_action_type("GET", 200) == "READ"
        assert middleware._infer_action_type("POST", 201) == "CREATE"
        assert middleware._infer_action_type("PATCH", 200) == "UPDATE"
        assert middleware._infer_action_type("DELETE", 204) == "DELETE"
        assert middleware._infer_action_type("GET", 404) == "ERROR"


class TestMaintenanceModeMiddleware:
    """メンテナンスモードミドルウェアのテスト。"""

    @pytest.mark.asyncio
    async def test_allows_health_endpoint_during_maintenance(self):
        """メンテナンス中もヘルスチェックはアクセス可能であること。"""
        # テスト実装
        pass

    @pytest.mark.asyncio
    async def test_blocks_api_during_maintenance(self):
        """メンテナンス中はAPIがブロックされること。"""
        # テスト実装
        pass

    @pytest.mark.asyncio
    async def test_allows_admin_during_maintenance(self):
        """メンテナンス中も管理者はアクセス可能であること。"""
        # テスト実装
        pass
```

---

## 9. 実装時の注意事項

### 9.1 エラーハンドリング

- ミドルウェア内のエラーは握りつぶさない
- ログ記録失敗時もリクエスト処理は継続

### 9.2 リクエストボディ

- リクエストボディは一度しか読めないため注意
- 読み取り後は`request._body`にキャッシュ

### 9.3 セッション管理

- 各ミドルウェアで独自のDBセッションを使用
- リクエストスコープのセッションとは分離

### 9.4 順序依存

- メンテナンスモードは認証前にチェック
- 監査ログは認証後にユーザー情報を取得

---

## 10. ミドルウェア実行順序と認証依存関係

### 10.1 ミドルウェア実行順序図

```text
リクエスト
    │
    ▼
┌─────────────────────────────────┐
│  1. ActivityTrackingMiddleware  │  ← 最外層（全リクエスト記録）
│     - request.state.request_id  │
│       を設定                    │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  2. MaintenanceModeMiddleware   │  ← 認証前にチェック
│     - DB不要（設定キャッシュ）  │
│     - 管理者は認証前に判定不可  │
│       → IPアドレスで許可       │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  3. AuthenticationMiddleware    │  ← 認証処理（既存）
│     - request.state.user を設定 │
│     - JWT検証、ユーザー情報取得 │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  4. AuditLogMiddleware          │  ← 認証後（user情報参照）
│     - request.state.user を参照 │
│     - セキュリティイベント記録  │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  5. エンドポイント処理          │
└─────────────────────────────────┘
    │
    ▼
レスポンス
```

### 10.2 request.state の依存関係

各ミドルウェアが設定・参照する `request.state` 属性：

| 属性 | 設定元 | 参照元 | 説明 |
|------|--------|--------|------|
| `request_id` | ActivityTrackingMiddleware | 全ミドルウェア | リクエスト追跡用ID |
| `user` | AuthenticationMiddleware | AuditLogMiddleware, エンドポイント | 認証済みユーザー |
| `start_time` | ActivityTrackingMiddleware | ActivityTrackingMiddleware | 処理時間計測用 |

### 10.3 FastAPI への登録順序

```python
# src/app/main.py

from fastapi import FastAPI
from app.api.middlewares import (
    ActivityTrackingMiddleware,
    MaintenanceModeMiddleware,
    AuditLogMiddleware,
)

app = FastAPI()

# 注意: add_middleware は逆順に実行される
# 最後に追加したものが最初に実行される

# 4. AuditLogMiddleware（最後に追加 = 認証後に実行）
app.add_middleware(AuditLogMiddleware)

# 3. AuthenticationMiddleware（既存の認証ミドルウェア）
# ※ 既存の認証処理

# 2. MaintenanceModeMiddleware
app.add_middleware(MaintenanceModeMiddleware)

# 1. ActivityTrackingMiddleware（最初に追加 = 最外層）
app.add_middleware(ActivityTrackingMiddleware)
```

### 10.4 認証状態による分岐処理

```python
# AuditLogMiddleware での認証状態チェック例

async def dispatch(self, request: Request, call_next):
    # request.state.user は AuthenticationMiddleware で設定される
    # 認証が失敗した場合は None または未設定

    user = getattr(request.state, "user", None)

    if user is None:
        # 未認証リクエスト
        # - 公開エンドポイントへのアクセス
        # - 認証失敗したリクエスト
        user_id = None
        user_info = {"anonymous": True}
    else:
        # 認証済みリクエスト
        user_id = user.id
        user_info = {
            "user_id": str(user.id),
            "email": user.email,
            "system_role": user.system_role.value,
        }

    # 監査ログにユーザー情報を記録
    await self._record_audit_log(
        request=request,
        user_id=user_id,
        user_info=user_info,
    )

    response = await call_next(request)
    return response
```

### 10.5 メンテナンスモード時の管理者許可

```python
# MaintenanceModeMiddleware での管理者許可処理

class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    # 管理者アクセス許可IPアドレス（環境変数から設定）
    ADMIN_ALLOWED_IPS: set[str] = set()

    async def dispatch(self, request: Request, call_next):
        if not await self._is_maintenance_mode():
            return await call_next(request)

        # メンテナンスモード中

        # 1. 許可されたIPアドレスからのアクセスは通過
        client_ip = self._get_client_ip(request)
        if client_ip in self.ADMIN_ALLOWED_IPS:
            return await call_next(request)

        # 2. ヘルスチェックエンドポイントは常に許可
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)

        # 3. メンテナンス画面へのアクセスは許可
        if request.url.path.startswith("/maintenance"):
            return await call_next(request)

        # 4. それ以外は503を返す
        return JSONResponse(
            status_code=503,
            content={
                "error": "ServiceUnavailable",
                "message": await self._get_maintenance_message(),
            },
        )

    def _get_client_ip(self, request: Request) -> str:
        """クライアントIPアドレスを取得。"""
        # X-Forwarded-For ヘッダーを考慮
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
```

### 10.6 ミドルウェア間のエラー伝播

```python
# エラー発生時のミドルウェア間の動作

class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request.state.request_id = str(uuid.uuid4())
        request.state.start_time = start_time

        response = None
        error_info = None

        try:
            response = await call_next(request)
        except Exception as e:
            # 内側のミドルウェアまたはエンドポイントで発生した例外
            error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
            raise  # 例外は再スロー
        finally:
            # エラー発生時もログは記録
            duration_ms = int((time.time() - start_time) * 1000)
            await self._record_activity(
                request=request,
                response=response,
                duration_ms=duration_ms,
                error_info=error_info,
            )

        return response
```
