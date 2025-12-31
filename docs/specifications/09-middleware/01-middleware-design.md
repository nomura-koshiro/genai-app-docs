# ミドルウェア設計書

## 1. 概要

本文書は、genai-app-docsシステムのミドルウェアアーキテクチャを定義します。
ミドルウェアは、HTTPリクエスト/レスポンスの処理パイプラインに介入し、横断的関心事を実装します。

### 1.1 ミドルウェア設計方針

- **関心の分離**: 各ミドルウェアは単一の責務を持つ
- **順序の重要性**: 実行順序により機能の有効性が変わる
- **非同期対応**: 完全な非同期処理
- **パフォーマンス**: 最小限のオーバーヘッド
- **グレースフルデグラデーション**: 外部依存障害時のフォールバック

---

## 2. ミドルウェアスタック全体像

### 2.1 実行順序

::: mermaid
sequenceDiagram
    participant Client
    participant Security as 1. SecurityHeadersMiddleware
    participant CORS as 2. CORSMiddleware
    participant RateLimit as 3. RateLimitMiddleware
    participant Maintenance as 4. MaintenanceModeMiddleware
    participant Logging as 5. LoggingMiddleware
    participant Audit as 6. AuditLogMiddleware
    participant Activity as 7. ActivityTrackingMiddleware
    participant Metrics as 8. PrometheusMetricsMiddleware
    participant Router as Router/Endpoint
    participant Exception as Exception Handlers

    Client->>Security: HTTP Request

    Note over Security: セキュリティヘッダー準備<br/>CSP, HSTS等

    Security->>CORS: Request

    Note over CORS: クロスオリジン検証<br/>プリフライト処理

    CORS->>RateLimit: Request

    Note over RateLimit: レート制限チェック<br/>Redis/メモリ

    RateLimit->>Maintenance: Request

    Note over Maintenance: メンテナンスモードチェック<br/>管理者アクセス許可

    Maintenance->>Logging: Request

    Note over Logging: リクエストログ記録<br/>開始時刻記録

    Logging->>Audit: Request

    Note over Audit: 監査対象判定<br/>セキュリティイベント記録

    Audit->>Activity: Request

    Note over Activity: 操作履歴記録準備<br/>リソース情報抽出

    Activity->>Metrics: Request

    Note over Metrics: メトリクス収集開始<br/>リクエストサイズ記録

    Metrics->>Router: Request

    alt 正常処理
        Router->>Metrics: Response
        Metrics->>Activity: Response
        Activity->>Audit: Response
        Audit->>Logging: Response
        Note over Logging: レスポンスログ記録<br/>実行時間計算
        Logging->>Maintenance: Response
        Maintenance->>RateLimit: Response
        RateLimit->>CORS: Response
        CORS->>Security: Response
        Security->>Client: Response + Headers
    else エラー
        Router->>Exception: Exception
        Exception->>Security: Error Response
        Security->>Client: Error Response
    end
:::

### 2.2 ミドルウェア一覧

| 順序 | ミドルウェア | 実装ファイル | 責務 |
|------|------------|------------|------|
| **1** | SecurityHeadersMiddleware | `api/middlewares/security_headers.py` | セキュリティヘッダー追加 |
| **2** | CORSMiddleware | FastAPI組み込み | クロスオリジン制御 |
| **3** | RateLimitMiddleware | `api/middlewares/rate_limit.py` | レート制限（Redis/メモリ） |
| **4** | MaintenanceModeMiddleware | `api/middlewares/maintenance_mode.py` | メンテナンスモード制御 |
| **5** | LoggingMiddleware | `api/middlewares/logging.py` | 構造化ログ記録 |
| **6** | AuditLogMiddleware | `api/middlewares/audit_log.py` | 監査ログ記録 |
| **7** | ActivityTrackingMiddleware | `api/middlewares/activity_tracking.py` | 操作履歴記録 |
| **8** | PrometheusMetricsMiddleware | `api/middlewares/metrics.py` | メトリクス収集 |

---

## 3. ミドルウェア詳細設計

### 3.1 SecurityHeadersMiddleware

#### 3.1.1 目的

セキュリティベストプラクティスに基づいたHTTPレスポンスヘッダーの自動追加

::: mermaid
graph TB
    Request[HTTP Request]
    Request --> Next[次のミドルウェア<br/>エンドポイント処理]

    Next --> Response[Response]

    Response --> H1[X-Content-Type-Options:<br/>nosniff]
    H1 --> H2[X-Frame-Options:<br/>DENY]
    H2 --> H3[X-XSS-Protection:<br/>1; mode=block]
    H3 --> H4{DEBUG?}

    H4 -->|No| H5[Strict-Transport-Security:<br/>max-age=31536000]
    H4 -->|Yes| H6{CSP有効?}

    H5 --> H6
    H6 -->|Yes| H7[Content-Security-Policy]
    H6 -->|No| FinalResponse

    H7 --> FinalResponse[Response + Headers]

    style FinalResponse fill:#4CAF50
:::

#### 3.1.2 実装

**実装**: `src/app/api/middlewares/security_headers.py`

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダー追加ミドルウェア"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 基本的なセキュリティヘッダー
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 本番環境のみ: HSTS
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # CSP（オプション）
        if settings.ENABLE_CSP:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )

        return response
```

#### 3.1.3 追加ヘッダー

| ヘッダー | 値 | 説明 | 環境 |
|---------|-----|------|------|
| **X-Content-Type-Options** | `nosniff` | MIMEタイプスニッフィング防止 | 全環境 |
| **X-Frame-Options** | `DENY` | クリックジャッキング防止 | 全環境 |
| **X-XSS-Protection** | `1; mode=block` | XSSフィルター有効化 | 全環境 |
| **Strict-Transport-Security** | `max-age=31536000; includeSubDomains` | HTTPS強制 | 本番のみ |
| **Content-Security-Policy** | CSPルール | コンテンツソース制限 | 設定時のみ |

---

### 3.2 CORSMiddleware

#### 3.2.1 目的

クロスオリジンリクエストの制御とプリフライトリクエスト処理

::: mermaid
graph TB
    Request[HTTP Request] --> Origin{Originヘッダー}

    Origin -->|許可リスト内| Preflight{OPTIONS?}
    Origin -->|許可リスト外| Reject[403 Forbidden]

    Preflight -->|Yes| PreflightResponse[200 OK<br/>Access-Control-Allow-*]
    Preflight -->|No| Normal[通常処理]

    Normal --> Response[Response + CORS Headers]

    style PreflightResponse fill:#4CAF50
    style Reject fill:#F44336
:::

#### 3.2.2 設定

**実装**: `src/app/core/app_factory.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or [],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Accept", "Content-Type", "Authorization", "X-API-Key"],
)
```

#### 3.2.3 レスポンスヘッダー

| ヘッダー | 値 | 説明 |
|---------|-----|------|
| **Access-Control-Allow-Origin** | 設定に依存 | 許可するオリジン |
| **Access-Control-Allow-Credentials** | `true` | Cookie送信許可 |
| **Access-Control-Allow-Methods** | `GET, POST, ...` | 許可するHTTPメソッド |
| **Access-Control-Allow-Headers** | `Accept, Content-Type, Authorization, X-API-Key` | 許可するヘッダー |

---

### 3.3 RateLimitMiddleware

#### 3.3.1 目的

APIリクエストのレート制限によるサービス保護

::: mermaid
graph TB
    Request[HTTP Request]

    Request --> DebugCheck{DEBUG?}

    DebugCheck -->|Yes| Skip[制限スキップ]
    DebugCheck -->|No| Identify[クライアント識別<br/>User ID / API Key / IP]

    Identify --> CheckBackend{Redisチェック}

    CheckBackend -->|利用可能| Redis[Redis<br/>Sorted Set]
    CheckBackend -->|利用不可| Memory[Memory<br/>インメモリ]

    Redis --> Check{制限内?}
    Memory --> Check

    Check -->|Yes| Consume[リクエスト記録]
    Check -->|No| Reject[429 Too Many Requests<br/>Retry-After]

    Consume --> AddHeaders[ヘッダー追加<br/>X-RateLimit-*]
    AddHeaders --> Next[次のミドルウェア]

    Skip --> Next

    style Reject fill:#F44336
    style Next fill:#4CAF50
:::

#### 3.3.2 実装

**実装**: `src/app/api/middlewares/rate_limit.py`

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redisベースのリクエストレート制限ミドルウェア"""

    def __init__(self, app, calls: int = 100, period: int = 60, max_memory_entries: int = 10000):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.max_memory_entries = max_memory_entries
        self._memory_store: dict[str, list[float]] = {}

    def _get_client_identifier(self, request: Request) -> str:
        """クライアント識別子を取得"""
        # 優先順位: 認証済みユーザー → APIキー → IPアドレス
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()}"

        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 開発環境ではスキップ
        if settings.DEBUG:
            return await call_next(request)

        client_identifier = self._get_client_identifier(request)

        # Redisまたはインメモリでレート制限チェック
        # ...（省略）

        response = await call_next(request)

        # レート制限ヘッダーを追加
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response
```

#### 3.3.3 設定

| パラメータ | デフォルト値 | 説明 |
|----------|-------------|------|
| **calls** | 100 | 期間ごとの最大リクエスト数 |
| **period** | 60 | レート制限の期間（秒） |
| **max_memory_entries** | 10000 | インメモリストアの最大エントリ数 |
| **バックエンド** | Redis / Memory | Redisが利用可能ならRedis、なければメモリ |
| **アルゴリズム** | Sliding Window | スライディングウィンドウ |

#### 3.3.4 クライアント識別の優先順位

1. **認証済みユーザー**: `user:{user_id}`
2. **APIキー**: `apikey:{SHA256ハッシュ}`
3. **IPアドレス**: `ip:{ip_address}`

---

### 3.4 MaintenanceModeMiddleware

#### 3.4.1 目的

メンテナンスモード中は管理者以外のアクセスを制限

::: mermaid
graph TB
    Request[HTTP Request]
    Request --> AllowedPath{常時許可パス?}

    AllowedPath -->|Yes| Next[次のミドルウェア]
    AllowedPath -->|No| CheckMaintenance{メンテナンス中?}

    CheckMaintenance -->|No| Next
    CheckMaintenance -->|Yes| CheckAdmin{管理者アクセス許可?}

    CheckAdmin -->|Yes| IsAdmin{システム管理者?}
    CheckAdmin -->|No| Reject[503 Service Unavailable]

    IsAdmin -->|Yes| Next
    IsAdmin -->|No| IsAdminPath{管理者パス?}

    IsAdminPath -->|Yes| Next
    IsAdminPath -->|No| Reject

    style Reject fill:#F44336
    style Next fill:#4CAF50
:::

#### 3.4.2 実装

**実装**: `src/app/api/middlewares/maintenance_mode.py`

```python
class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """メンテナンスモードミドルウェア"""

    # メンテナンス中も常にアクセス可能なパス
    ALWAYS_ALLOWED_PATHS: set[str] = {
        "/health", "/healthz", "/ready",
        "/docs", "/openapi.json", "/redoc",
    }

    # 管理者専用パスパターン
    ADMIN_PATH_PATTERN: re.Pattern[str] = re.compile(r"^/api/v1/admin/")

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._maintenance_cache: dict[str, bool | str] | None = None
        self._cache_ttl: float = 0  # 30秒TTL

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # 常にアクセス可能なパスはスキップ
        if path in self.ALWAYS_ALLOWED_PATHS:
            return await call_next(request)

        # メンテナンスモード設定を取得（キャッシュ付き）
        maintenance_settings = await self._get_maintenance_settings()

        if not maintenance_settings.get("enabled", False):
            return await call_next(request)

        # システム管理者または管理者パスへのアクセスは許可
        if maintenance_settings.get("allow_admin_access", True):
            if hasattr(request.state, "user") and request.state.user:
                if request.state.user.is_system_admin():
                    return await call_next(request)
            if self.ADMIN_PATH_PATTERN.match(path):
                return await call_next(request)

        # 503 Service Unavailableを返す
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "code": "MAINTENANCE_MODE",
                "message": maintenance_settings.get("message", "システムはメンテナンス中です"),
                "details": {"retry_after": 3600},
            },
            headers={"Retry-After": "3600"},
        )
```

#### 3.4.3 設定

| 設定キー | カテゴリ | 説明 |
|---------|---------|------|
| **maintenance_mode** | MAINTENANCE | メンテナンスモード有効/無効 |
| **maintenance_message** | MAINTENANCE | メンテナンスメッセージ |
| **allow_admin_access** | MAINTENANCE | 管理者アクセス許可 |

#### 3.4.4 常時許可パス

- `/health`, `/healthz`, `/ready` - ヘルスチェック
- `/docs`, `/openapi.json`, `/redoc` - APIドキュメント

---

### 3.5 LoggingMiddleware

#### 3.5.1 目的

すべてのHTTPリクエスト/レスポンスの構造化ログ記録

::: mermaid
graph TB
    Request[HTTP Request]
    Request --> StartLog[リクエストログ<br/>method, path, client]

    StartLog --> StartTime[開始時刻記録]
    StartTime --> Next[次のミドルウェア]

    Next --> Response[Response]

    Response --> EndTime[終了時刻記録]
    EndTime --> CalcDuration[実行時間計算<br/>duration]

    CalcDuration --> EndLog[レスポンスログ<br/>status_code, duration]

    EndLog --> AddHeader[X-Process-Time<br/>ヘッダー追加]

    style StartLog fill:#4CAF50
    style EndLog fill:#8BC34A
:::

#### 3.5.2 実装

**実装**: `src/app/api/middlewares/logging.py`

```python
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
import time

logger = structlog.get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """構造化ログミドルウェア"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # リクエストログ
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client=request.client.host if request.client else None,
        )

        response = await call_next(request)

        # 処理時間計算
        duration = time.time() - start_time

        # レスポンスログ
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=f"{duration:.3f}s",
        )

        # カスタムヘッダーを追加
        response.headers["X-Process-Time"] = str(duration)

        return response
```

#### 3.5.3 ログ出力例

**開発環境（カラー付きコンソール）:**

```text
Request started: GET /api/v1/projects method=GET path=/api/v1/projects client=127.0.0.1
Request completed: GET /api/v1/projects - 200 method=GET path=/api/v1/projects status_code=200 duration=0.234s
```

**本番環境（JSON）:**

```json
{
  "event": "Request started: GET /api/v1/projects",
  "method": "GET",
  "path": "/api/v1/projects",
  "query_params": "skip=0&limit=20",
  "client": "192.168.1.100",
  "timestamp": "2025-01-15T12:00:00.123Z"
}
```

---

### 3.6 AuditLogMiddleware

#### 3.6.1 目的

重要なデータ変更操作とセキュリティイベントを監査ログに記録

::: mermaid
graph TB
    Request[HTTP Request]
    Request --> CheckAudit{監査対象?}

    CheckAudit -->|No| Next[次のミドルウェア]
    CheckAudit -->|Yes| GetBody[リクエストボディ取得]

    GetBody --> Process[リクエスト処理]
    Process --> CheckSuccess{成功? 2xx}

    CheckSuccess -->|No| Return[レスポンス返却]
    CheckSuccess -->|Yes| RecordAudit[監査ログ記録<br/>DB保存]

    RecordAudit --> Return

    Next --> Return

    style RecordAudit fill:#FF9800
:::

#### 3.6.2 実装

**実装**: `src/app/api/middlewares/audit_log.py`

```python
class AuditLogMiddleware(BaseHTTPMiddleware):
    """監査ログミドルウェア"""

    # 監査対象のパスパターンと設定
    AUDIT_TARGETS: list[dict[str, Any]] = [
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

    async def dispatch(self, request: Request, call_next) -> Response:
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
            await self._record_audit_log(request, request_body, response, audit_config)

        return response
```

#### 3.6.3 監査対象

| リソース | HTTPメソッド | イベント種別 | 重要度 |
|---------|-------------|-------------|--------|
| **PROJECT** | PUT, PATCH, DELETE | DATA_CHANGE | INFO |
| **USER** | PUT, PATCH, DELETE | DATA_CHANGE | INFO |
| **SYSTEM_SETTING** | PATCH, POST | DATA_CHANGE | WARNING |
| **SESSION** | POST (terminate) | SECURITY | WARNING |
| **BULK_OPERATION** | POST | DATA_CHANGE | WARNING |
| **DATA_CLEANUP** | POST | DATA_CHANGE | CRITICAL |
| **IMPERSONATION** | POST | SECURITY | CRITICAL |

---

### 3.7 ActivityTrackingMiddleware

#### 3.7.1 目的

全APIリクエストを自動的に記録し、操作履歴として保存

::: mermaid
graph TB
    Request[HTTP Request]
    Request --> SkipCheck{除外パス?}

    SkipCheck -->|Yes| Next[次のミドルウェア]
    SkipCheck -->|No| GetBody[リクエストボディ取得<br/>機密情報マスク]

    GetBody --> Process[リクエスト処理]
    Process --> RecordActivity[操作履歴記録]

    RecordActivity --> Return[レスポンス返却]

    Next --> ReturnDirect[レスポンス返却]

    style RecordActivity fill:#4CAF50
:::

#### 3.7.2 実装

**実装**: `src/app/api/middlewares/activity_tracking.py`

```python
class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    """ユーザー操作履歴を自動記録するミドルウェア"""

    # 除外する固定パス
    EXCLUDE_PATHS: set[str] = {
        "/health", "/healthz", "/ready", "/metrics",
        "/docs", "/openapi.json", "/redoc", "/favicon.ico",
    }

    # 除外するパスパターン
    EXCLUDE_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"^/static/"),
        re.compile(r"^/assets/"),
        re.compile(r"^/_next/"),
    ]

    # マスク対象の機密情報キー
    SENSITIVE_KEYS: set[str] = {
        "password", "token", "secret", "api_key", "apikey",
        "credential", "authorization", "access_token",
        "refresh_token", "session_token",
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

    async def dispatch(self, request: Request, call_next) -> Response:
        # 除外パスチェック
        if self._should_skip(request.url.path):
            return await call_next(request)

        start_time = time.perf_counter()
        response_status = 500
        error_message = None
        request_body = None

        try:
            # リクエストボディの取得（マスク処理付き）
            if request.method in {"POST", "PUT", "PATCH"}:
                request_body = await self._get_masked_request_body(request)

            response = await call_next(request)
            response_status = response.status_code

            # エラーレスポンスの場合、エラー情報を抽出
            if response_status >= 400:
                error_message, _ = await self._extract_error_info(response)

            return response

        except Exception as e:
            response_status = 500
            error_message = str(e)
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
                duration_ms=duration_ms,
            )
```

#### 3.7.3 記録内容

| フィールド | 説明 |
|-----------|------|
| **user_id** | 認証済みユーザーID |
| **action_type** | CREATE, READ, UPDATE, DELETE, ERROR |
| **resource_type** | PROJECT, USER, SESSION等 |
| **resource_id** | リソースのUUID |
| **endpoint** | APIエンドポイント |
| **method** | HTTPメソッド |
| **request_body** | マスク済みリクエストボディ |
| **response_status** | HTTPステータスコード |
| **error_message** | エラーメッセージ |
| **ip_address** | クライアントIPアドレス |
| **user_agent** | ユーザーエージェント |
| **duration_ms** | 処理時間（ミリ秒） |

#### 3.7.4 除外パス

**固定パス:**

- `/health`, `/healthz`, `/ready` - ヘルスチェック
- `/metrics` - Prometheusメトリクス
- `/docs`, `/openapi.json`, `/redoc` - APIドキュメント
- `/favicon.ico` - ファビコン

**パターン:**

- `/static/*` - 静的ファイル
- `/assets/*` - アセット
- `/_next/*` - Next.js

---

### 3.8 PrometheusMetricsMiddleware

#### 3.8.1 目的

Prometheusメトリクスの自動収集

::: mermaid
graph TB
    Request[HTTP Request]
    Request --> GetSize[リクエストサイズ記録]

    GetSize --> Normalize[パス正規化<br/>/users/123 → /users/{id}]

    Normalize --> RecordSize[http_request_size_bytes<br/>観測値記録]

    RecordSize --> StartTime[開始時刻記録]

    StartTime --> Next[次のミドルウェア]

    Next --> Response[Response]

    Response --> RecordDuration[http_request_duration_seconds<br/>処理時間記録]

    RecordDuration --> RecordCount[http_requests_total<br/>カウンター増加]

    RecordCount --> RecordResponseSize[http_response_size_bytes<br/>観測値記録]

    style RecordCount fill:#4CAF50
    style RecordDuration fill:#8BC34A
:::

#### 3.8.2 実装

**実装**: `src/app/api/middlewares/metrics.py`

```python
from prometheus_client import Counter, Histogram

# HTTPメトリクス
http_requests_total = Counter(
    "http_requests_total",
    "HTTPリクエスト総数",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTPリクエスト処理時間（秒）",
    ["method", "endpoint"],
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTPリクエストサイズ（バイト）",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTPレスポンスサイズ（バイト）",
    ["method", "endpoint"],
)

class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Prometheusメトリクス収集ミドルウェア"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_size = int(request.headers.get("content-length", 0))
        method = request.method
        endpoint = self._normalize_path(request.url.path)

        http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)

        start_time = time.time()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        if response is not None:
            response_size = int(response.headers.get("content-length", 0))
            http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)

        return response

    def _normalize_path(self, path: str) -> str:
        """パスパラメータを正規化（UUID、数値を{id}に置換）"""
        parts = path.split("/")
        normalized_parts = []

        for part in parts:
            if not part:
                normalized_parts.append(part)
            elif part.isdigit():
                normalized_parts.append("{id}")
            elif re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", part, re.IGNORECASE):
                normalized_parts.append("{id}")
            elif re.match(r"^[a-zA-Z0-9_-]{32,}$", part):
                normalized_parts.append("{id}")
            else:
                normalized_parts.append(part)

        return "/".join(normalized_parts)
```

#### 3.8.3 収集メトリクス

| メトリクス | 型 | 説明 | ラベル |
|----------|-----|------|--------|
| **http_requests_total** | Counter | リクエスト総数 | method, endpoint, status_code |
| **http_request_duration_seconds** | Histogram | レスポンスタイム | method, endpoint |
| **http_request_size_bytes** | Histogram | リクエストサイズ | method, endpoint |
| **http_response_size_bytes** | Histogram | レスポンスサイズ | method, endpoint |
| **db_query_duration_seconds** | Histogram | DBクエリ時間 | operation |
| **chat_messages_total** | Counter | チャットメッセージ数 | role |
| **file_uploads_total** | Counter | ファイルアップロード数 | content_type |

**メトリクス出力例:**

```prometheus
# HELP http_requests_total HTTPリクエスト総数
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/projects",status_code="200"} 1234

# HELP http_request_duration_seconds HTTPリクエスト処理時間（秒）
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/projects",le="0.1"} 800
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/projects",le="0.5"} 950
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/projects",le="1.0"} 990
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/projects",le="+Inf"} 1000
```

---

## 4. ミドルウェア実行順序の重要性

### 4.1 順序の理由

::: mermaid
graph TB
    Why[実行順序の重要性]

    Why --> R1[1. SecurityHeaders<br/>最外層]
    Why --> R2[2. CORS<br/>クロスオリジン]
    Why --> R3[3. RateLimit<br/>早期拒否]
    Why --> R4[4. Maintenance<br/>メンテナンス制御]
    Why --> R5[5. Logging<br/>全リクエスト記録]
    Why --> R6[6. AuditLog<br/>監査記録]
    Why --> R7[7. ActivityTracking<br/>操作履歴]
    Why --> R8[8. Metrics<br/>メトリクス]

    R1 --> E1[すべてのレスポンスに<br/>セキュリティヘッダー追加]

    R2 --> E2[クロスオリジンチェック<br/>プリフライト処理]

    R3 --> E3[無駄な処理を避ける<br/>レート制限超過は即座に拒否]

    R4 --> E4[メンテナンス中の<br/>アクセス制御]

    R5 --> E5[すべてのリクエスト記録<br/>デバッグ・監視]

    R6 --> E6[重要な操作の<br/>監査証跡]

    R7 --> E7[ユーザー操作の<br/>詳細記録]

    R8 --> E8[パフォーマンス<br/>メトリクス収集]

    style R1 fill:#9C27B0
    style R2 fill:#F44336
    style R3 fill:#FF9800
    style R4 fill:#FFC107
    style R5 fill:#CDDC39
    style R6 fill:#8BC34A
    style R7 fill:#4CAF50
    style R8 fill:#2196F3
:::

### 4.2 誤った順序の影響

| 誤った順序 | 問題 |
|----------|------|
| **RateLimit → CORS** | CORSプリフライトが失敗してレート制限が効かない |
| **Logging → RateLimit** | レート制限で拒否されたリクエストがログに記録されない |
| **Metrics → Maintenance** | メンテナンス503がメトリクスに含まれない |
| **AuditLog → ActivityTracking** | 監査対象でない操作が先に記録される |

---

## 5. ミドルウェア登録

### 5.1 登録コード

**実装**: `src/app/core/app_factory.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.middlewares import (
    ActivityTrackingMiddleware,
    AuditLogMiddleware,
    LoggingMiddleware,
    MaintenanceModeMiddleware,
    PrometheusMetricsMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)

def create_app() -> FastAPI:
    app = FastAPI(...)

    # カスタムミドルウェアを登録（実行順序は登録の逆順）
    # ミドルウェア実行順序:
    #   1. SecurityHeadersMiddleware（最外層）
    #   2. CORS
    #   3. RateLimitMiddleware
    #   4. MaintenanceModeMiddleware
    #   5. LoggingMiddleware
    #   6. AuditLogMiddleware
    #   7. ActivityTrackingMiddleware
    #   8. PrometheusMetricsMiddleware（最内層）

    app.add_middleware(PrometheusMetricsMiddleware)
    app.add_middleware(ActivityTrackingMiddleware)
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(MaintenanceModeMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.RATE_LIMIT_CALLS,
        period=settings.RATE_LIMIT_PERIOD,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS or [],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Accept", "Content-Type", "Authorization", "X-API-Key"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    return app
```

**注意**: FastAPIは後に登録したミドルウェアが先に実行されるため、逆順で登録します。

---

## 6. ミドルウェアのパフォーマンス

### 6.1 オーバーヘッド計測

::: mermaid
graph LR
    Total[総処理時間<br/>500ms] --> MW[ミドルウェア<br/>30ms 6%]
    Total --> Endpoint[エンドポイント<br/>470ms 94%]

    MW --> Security[SecurityHeaders<br/>1ms]
    MW --> CORS[CORS<br/>2ms]
    MW --> RateLimit[RateLimit<br/>5ms]
    MW --> Maintenance[Maintenance<br/>3ms]
    MW --> Logging[Logging<br/>3ms]
    MW --> Audit[AuditLog<br/>5ms]
    MW --> Activity[ActivityTracking<br/>8ms]
    MW --> Metrics[Metrics<br/>3ms]

    style Total fill:#2196F3
    style MW fill:#FF9800
    style Endpoint fill:#4CAF50
:::

**オーバーヘッド:**

- **SecurityHeaders**: ~1ms（ヘッダー追加のみ）
- **CORS**: ~2ms（オリジンチェック）
- **RateLimit**: ~5ms（Redis/Memory）
- **MaintenanceMode**: ~3ms（キャッシュ付き設定取得）
- **Logging**: ~3ms（structlog）
- **AuditLog**: ~5ms（条件付きDB書き込み）
- **ActivityTracking**: ~8ms（DB書き込み）
- **Metrics**: ~3ms（prometheus_client）

**合計**: ~30ms（総処理時間の6%程度）

### 6.2 最適化手法

::: mermaid
mindmap
  root((最適化))
    非同期処理
      async/await完全対応
      非ブロッキングI/O
      並列処理可能
    キャッシュ
      Redis接続プール
      メンテナンス設定キャッシュ
      メモリフォールバック
    条件分岐
      HTTPS時のみHSTS
      開発環境でレート制限スキップ
      除外パスで記録スキップ
    バッチ処理
      ログバッファリング
      メトリクス集約
      非同期DB書き込み
:::

---

## 7. エラーハンドリング

### 7.1 ミドルウェアエラー処理

::: mermaid
sequenceDiagram
    participant Client
    participant Middleware
    participant Endpoint
    participant ExceptionHandler

    Client->>Middleware: Request

    alt ミドルウェアエラー
        Middleware->>Middleware: Exception発生
        Middleware->>ExceptionHandler: Exception
        ExceptionHandler-->>Client: Error Response
    else エンドポイントエラー
        Middleware->>Endpoint: Request
        Endpoint->>Endpoint: Exception発生
        Endpoint->>ExceptionHandler: Exception
        ExceptionHandler->>Middleware: Error Response
        Middleware-->>Client: Error Response + Headers
    end
:::

### 7.2 エラーハンドラ実装

**実装**: `src/app/api/core/exception_handlers.py`

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def register_exception_handlers(app: FastAPI):
    """例外ハンドラ登録（RFC 9457準拠）"""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": f"https://httpstatuses.com/{exc.status_code}",
                "title": exc.detail,
                "status": exc.status_code,
                "instance": str(request.url.path),
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)

        return JSONResponse(
            status_code=500,
            content={
                "type": "https://httpstatuses.com/500",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred",
                "instance": str(request.url.path),
            }
        )
```

---

## 8. テスト

### 8.1 ミドルウェアテスト戦略

::: mermaid
graph TB
    Test[ミドルウェアテスト]

    Test --> Unit[ユニットテスト]
    Test --> Integration[統合テスト]

    Unit --> U1[個別機能テスト]
    Unit --> U2[エラーケース]
    Unit --> U3[境界値テスト]

    Integration --> I1[実行順序テスト]
    Integration --> I2[エンドツーエンドテスト]
    Integration --> I3[パフォーマンステスト]

    style Unit fill:#4CAF50
    style Integration fill:#2196F3
:::

### 8.2 テストコード例

**実装**: `tests/app/api/middlewares/`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rate_limit_allows_within_limit(client: AsyncClient):
    """制限内リクエストは許可"""
    for _ in range(100):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_rate_limit_blocks_over_limit(client: AsyncClient):
    """制限超過リクエストは拒否"""
    for _ in range(100):
        await client.get("/api/v1/projects")

    response = await client.get("/api/v1/projects")
    assert response.status_code == 429
    assert "Retry-After" in response.headers

@pytest.mark.asyncio
async def test_maintenance_mode_blocks_non_admin(client: AsyncClient):
    """メンテナンスモード中は非管理者アクセスを拒否"""
    # メンテナンスモード有効化
    # ...
    response = await client.get("/api/v1/projects")
    assert response.status_code == 503
    assert response.json()["code"] == "MAINTENANCE_MODE"

@pytest.mark.asyncio
async def test_activity_tracking_records_request(client: AsyncClient, db_session):
    """操作履歴が正しく記録される"""
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200

    # 操作履歴を確認
    activity = await db_session.execute(
        select(UserActivity).order_by(UserActivity.created_at.desc()).limit(1)
    )
    record = activity.scalar_one()
    assert record.endpoint == "/api/v1/projects"
    assert record.method == "GET"
```

---

## 9. まとめ

### 9.1 ミドルウェア設計の特徴

✅ **明確な実行順序**: SecurityHeaders → CORS → RateLimit → Maintenance → Logging → AuditLog → ActivityTracking → Metrics
✅ **関心の分離**: 各ミドルウェアが単一の責務を持つ
✅ **非同期対応**: 完全な非同期処理による高性能
✅ **グレースフルデグラデーション**: Redis障害時のメモリフォールバック
✅ **低オーバーヘッド**: 総処理時間の6%程度
✅ **包括的なログ**: すべてのリクエスト/レスポンスを記録
✅ **監査証跡**: 重要な操作の監査ログ記録
✅ **操作履歴**: 全ユーザー操作の自動記録
✅ **メトリクス収集**: Prometheus統合による監視
✅ **セキュリティ強化**: CSP、HSTS等のセキュリティヘッダー
✅ **メンテナンスモード**: 管理者アクセスを許可しつつサービス停止

### 9.2 ミドルウェア一覧（最終版）

| 順序 | ミドルウェア | 責務 |
|------|------------|------|
| 1 | SecurityHeadersMiddleware | セキュリティヘッダー追加 |
| 2 | CORSMiddleware | クロスオリジン制御 |
| 3 | RateLimitMiddleware | レート制限 |
| 4 | MaintenanceModeMiddleware | メンテナンスモード制御 |
| 5 | LoggingMiddleware | 構造化ログ記録 |
| 6 | AuditLogMiddleware | 監査ログ記録 |
| 7 | ActivityTrackingMiddleware | 操作履歴記録 |
| 8 | PrometheusMetricsMiddleware | メトリクス収集 |

---

**ドキュメント管理情報:**

- **作成日**: 2025年
- **最終更新日**: 2026年1月（実装に合わせて更新）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `../04-architecture/01-system-architecture.md`
  - セキュリティ実装詳細書: `../05-security/03-security-implementation.md`
  - API仕様書: `../11-features/01-api-overview/01-api-overview.md`
