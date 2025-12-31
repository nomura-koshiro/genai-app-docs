# セキュリティ実装詳細書

## 1. 概要

本文書は、genai-app-docsシステムのセキュリティ実装の詳細を定義します。
OWASP Top 10対策、セキュリティヘッダー、レート制限、パスワードハッシュなどの具体的な実装を記載します。

### 1.1 セキュリティ設計原則

- **多層防御（Defense in Depth）**: 複数のセキュリティ層による保護
- **最小権限の原則**: 必要最小限の権限のみ付与
- **セキュアバイデフォルト**: デフォルト設定で安全
- **Fail Secure**: エラー時は安全側に倒す

---

## 2. セキュリティアーキテクチャ

### 2.1 多層防御モデル

::: mermaid
graph TB
    subgraph "Layer 1: ネットワーク層"
        L1A[HTTPS強制<br/>TLS 1.2+]
        L1B[CORS制御]
    end

    subgraph "Layer 2: アプリケーション境界"
        L2A[レート制限<br/>100req/min]
        L2B[セキュリティヘッダー<br/>CSP, HSTS等]
        L2C[メンテナンスモード<br/>アクセス制御]
    end

    subgraph "Layer 3: 認証・認可"
        L3A[Azure AD JWT認証]
        L3B[RBAC<br/>2層ロール]
        L3C[メンバーシップ検証]
    end

    subgraph "Layer 4: データ層"
        L4A[SQLインジェクション対策<br/>ORM + バリデーション]
        L4B[XSS対策<br/>Pydantic]
        L4C[パスワードハッシュ<br/>bcrypt 12ラウンド]
    end

    subgraph "Layer 5: 監視層"
        L5A[構造化ログ<br/>LoggingMiddleware]
        L5B[監査ログ<br/>AuditLogMiddleware]
        L5C[操作履歴<br/>ActivityTrackingMiddleware]
    end

    Client[Client] --> L1A
    L1A --> L1B
    L1B --> L2A
    L2A --> L2B
    L2B --> L2C
    L2C --> L3A
    L3A --> L3B
    L3B --> L3C
    L3C --> L4A
    L4A --> L4B
    L4B --> L4C
    L4C --> L5A
    L5A --> L5B
    L5B --> L5C

    style L1A fill:#F44336
    style L2A fill:#FF9800
    style L3A fill:#FFC107
    style L4A fill:#8BC34A
    style L5A fill:#4CAF50
:::

---

## 3. OWASP Top 10 対策

### 3.1 対策一覧

::: mermaid
graph TB
    OWASP[OWASP Top 10 2021]

    OWASP --> A01[A01: Broken Access Control]
    OWASP --> A02[A02: Cryptographic Failures]
    OWASP --> A03[A03: Injection]
    OWASP --> A04[A04: Insecure Design]
    OWASP --> A05[A05: Security Misconfiguration]
    OWASP --> A06[A06: Vulnerable Components]
    OWASP --> A07[A07: Auth Failures]
    OWASP --> A08[A08: Software Integrity]
    OWASP --> A09[A09: Logging Failures]
    OWASP --> A10[A10: SSRF]

    A01 --> A01_OK[✅ RBAC + メンバーシップ検証]
    A02 --> A02_OK[✅ HTTPS + bcrypt + JWT]
    A03 --> A03_OK[✅ ORM + Pydantic]
    A04 --> A04_OK[✅ セキュアアーキテクチャ]
    A05 --> A05_OK[✅ セキュリティヘッダー]
    A06 --> A06_OK[✅ 依存関係管理 uv.lock]
    A07 --> A07_OK[✅ Azure AD + レート制限]
    A08 --> A08_OK[✅ 依存関係検証]
    A09 --> A09_OK[✅ structlog + 監査ログ]
    A10 --> A10_OK[✅ URL検証 + ホワイトリスト]

    style A01_OK fill:#4CAF50
    style A02_OK fill:#4CAF50
    style A03_OK fill:#4CAF50
:::

### 3.2 対策詳細

| OWASP ID | 脅威 | 対策 | 実装場所 |
|----------|------|------|----------|
| **A01** | Broken Access Control | RBAC、メンバーシップ検証、権限チェック | `dependencies.py`, `rbac_design.md` |
| **A02** | Cryptographic Failures | HTTPS強制、bcrypt、JWT | `security_headers.py`, `password.py`, `jwt.py` |
| **A03** | Injection | SQLAlchemyパラメータ化クエリ、Pydanticバリデーション | `base.py`, `schemas/` |
| **A04** | Insecure Design | レイヤードアーキテクチャ、多層防御 | `system-architecture.md` |
| **A05** | Security Misconfiguration | セキュリティヘッダー、CORS、デフォルト設定 | `security_headers.py`, `config.py` |
| **A06** | Vulnerable Components | uv.lock、定期更新、脆弱性スキャン | `uv.lock`, `pyproject.toml` |
| **A07** | Auth Failures | Azure AD、レート制限、アカウントロック | `azure_ad.py`, `rate_limit.py` |
| **A08** | Software Integrity | 依存関係ロック、ハッシュ検証 | `uv.lock` |
| **A09** | Logging Failures | structlog、監査ログ、エラーログ | `logging.py`, `audit_log` |
| **A10** | SSRF | URL検証、ホワイトリスト、プロキシ制限 | （将来実装） |

---

## 4. セキュリティヘッダー

### 4.1 実装済みセキュリティヘッダー

**実装**: `src/app/api/middlewares/security_headers.py`

::: mermaid
graph LR
    Request[Request] --> Middleware[SecurityHeadersMiddleware]

    Middleware --> H1[X-Content-Type-Options]
    Middleware --> H2[X-Frame-Options]
    Middleware --> H3[X-XSS-Protection]
    Middleware --> H4[Strict-Transport-Security]
    Middleware --> H5[Content-Security-Policy]
    Middleware --> H6[Referrer-Policy]
    Middleware --> H7[Permissions-Policy]

    H1 --> Response[Response + Headers]
    H2 --> Response
    H3 --> Response
    H4 --> Response
    H5 --> Response
    H6 --> Response
    H7 --> Response

    style Middleware fill:#FF9800
    style Response fill:#4CAF50
:::

### 4.2 セキュリティヘッダー詳細

| ヘッダー | 設定値 | 目的 | 対策する脅威 |
|---------|--------|------|-------------|
| **X-Content-Type-Options** | `nosniff` | MIMEタイプスニッフィング無効化 | MIME Type攻撃 |
| **X-Frame-Options** | `DENY` | iframe埋め込み禁止 | Clickjacking |
| **X-XSS-Protection** | `1; mode=block` | XSSフィルタ有効化（レガシー） | XSS攻撃 |
| **Strict-Transport-Security** | `max-age=31536000; includeSubDomains` | HTTPS強制（1年間） | 中間者攻撃 |
| **Content-Security-Policy** | `default-src 'self'` | リソース読み込み制限 | XSS、データインジェクション |
| **Referrer-Policy** | `strict-origin-when-cross-origin` | リファラー情報制限 | 情報漏洩 |
| **Permissions-Policy** | `geolocation=(), camera=(), microphone=()` | ブラウザ機能制限 | 権限悪用 |

### 4.3 実装コード

```python
# src/app/api/middlewares/security_headers.py

from collections.abc import Callable
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = structlog.get_logger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダー追加ミドルウェア"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 基本的なセキュリティヘッダー
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 本番環境のみ: HSTS (HTTP Strict Transport Security)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Content Security Policy (CSP) - 設定で有効化
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

---

## 5. レート制限

### 5.1 レート制限アーキテクチャ

::: mermaid
sequenceDiagram
    participant Client
    participant RateLimitMiddleware
    participant Redis
    participant Endpoint

    Client->>RateLimitMiddleware: Request

    RateLimitMiddleware->>RateLimitMiddleware: クライアント識別<br/>(IP or User ID)

    RateLimitMiddleware->>Redis: GET rate_limit:{client_id}
    Redis-->>RateLimitMiddleware: current_count

    alt 制限内
        RateLimitMiddleware->>Redis: INCR rate_limit:{client_id}
        RateLimitMiddleware->>Redis: EXPIRE rate_limit:{client_id} 60

        RateLimitMiddleware->>RateLimitMiddleware: ヘッダー追加<br/>X-RateLimit-*

        RateLimitMiddleware->>Endpoint: Request
        Endpoint-->>RateLimitMiddleware: Response
        RateLimitMiddleware-->>Client: 200 OK + Headers
    else 制限超過
        RateLimitMiddleware-->>Client: 429 Too Many Requests<br/>Retry-After: 60
    end
:::

### 5.2 レート制限設定

**実装**: `src/app/api/middlewares/rate_limit.py`

| パラメータ | 設定値 | 説明 |
|----------|--------|------|
| **制限値** | 100リクエスト | 1分あたりの最大リクエスト数 |
| **ウィンドウ** | 60秒 | レート制限の時間枠 |
| **識別方法** | User ID → API Key → IP | 優先順位に従って識別 |
| **バックエンド** | Redis / Memory | Redisが利用可能ならRedis、なければインメモリ |
| **アルゴリズム** | Sliding Window | スライディングウィンドウアルゴリズム |
| **最大メモリエントリ** | 10000 | インメモリストアの上限 |

### 5.3 実装コード

```python
# src/app/api/middlewares/rate_limit.py

import hashlib
import time
from collections.abc import Callable
import structlog
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.cache import cache_manager
from app.core.config import settings

logger = structlog.get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redisベースのリクエストレート制限ミドルウェア（スライディングウィンドウ）"""

    def __init__(self, app, calls: int = 100, period: int = 60, max_memory_entries: int = 10000):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.max_memory_entries = max_memory_entries
        self._memory_store: dict[str, list[float]] = {}

    def _get_client_identifier(self, request: Request) -> str:
        """クライアント識別子取得（優先順位: User ID → API Key → IP）"""
        # 認証済みユーザー
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        # APIキー（ハッシュ化）
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()}"

        # IPアドレス（X-Forwarded-For対応）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 開発環境ではレート制限をスキップ
        if settings.DEBUG:
            return await call_next(request)

        client_identifier = self._get_client_identifier(request)
        current_time = int(time.time())

        try:
            # Redisが利用できない場合はインメモリフォールバック
            if not cache_manager.is_redis_available():
                is_limited, request_count = self._check_rate_limit_memory(
                    client_identifier, current_time
                )
                if is_limited:
                    return self._create_rate_limit_response()

                response = await call_next(request)
                remaining = max(0, self.calls - request_count - 1)
                response.headers["X-RateLimit-Limit"] = str(self.calls)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(current_time + self.period)
                return response

            # Redis Sorted Setを使用したスライディングウィンドウ
            cache_key = f"rate_limit:{client_identifier}"
            window_start = current_time - self.period

            await cache_manager.zremrangebyscore(cache_key, 0, window_start)
            request_count = await cache_manager.zcard(cache_key)

            if request_count >= self.calls:
                return self._create_rate_limit_response()

            # 現在のリクエストを追加
            request_id = f"{current_time}:{hashlib.sha256(str(time.time()).encode()).hexdigest()}"
            await cache_manager.zadd(cache_key, {request_id: current_time})
            await cache_manager.expire_key(cache_key, self.period)

            response = await call_next(request)

            # レート制限ヘッダー
            remaining = max(0, self.calls - request_count - 1)
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(current_time + self.period)

            return response

        except Exception as e:
            logger.exception("レート制限エラー", error=str(e))
            # エラー時はインメモリフォールバック
            return await call_next(request)

    def _create_rate_limit_response(self) -> JSONResponse:
        """レート制限超過レスポンス"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "details": {
                    "limit": self.calls,
                    "period": self.period,
                    "retry_after": self.period,
                },
            },
            headers={"Retry-After": str(self.period)},
        )
```

### 5.4 クライアント識別の優先順位

| 優先順位 | 識別方法 | フォーマット | 説明 |
|---------|---------|-------------|------|
| 1 | 認証済みユーザー | `user:{user_id}` | 最も信頼性が高い |
| 2 | APIキー | `apikey:{SHA256ハッシュ}` | セキュリティのためハッシュ化 |
| 3 | IPアドレス | `ip:{ip_address}` | X-Forwarded-For対応 |

### 5.5 グレースフルデグラデーション

```python
# Redis障害時のフォールバック戦略
try:
    if not cache_manager.is_redis_available():
        # インメモリフォールバック
        is_limited, count = self._check_rate_limit_memory(client_id, current_time)
        ...
except Exception:
    # エラー時は制限をスキップ（可用性優先）
    return await call_next(request)
```

**特徴:**

- Redis障害時は自動的にインメモリストアにフォールバック
- インメモリストアはLRU戦略でメモリリーク防止（最大10000エントリ）
- 致命的エラー時は制限をスキップし可用性を優先

---

## 6. パスワードハッシュ

### 6.1 bcryptハッシュ

**実装**: `src/app/core/security/password.py`

::: mermaid
graph LR
    PlainPassword[平文パスワード] --> bcrypt[bcrypt<br/>12 rounds]
    bcrypt --> Hash[ハッシュ値<br/>$2b$12$...]

    Hash --> Verify[検証時]
    PlainPassword2[入力パスワード] --> Verify
    Verify --> Result{一致?}
    Result -->|Yes| OK[認証成功]
    Result -->|No| NG[認証失敗]

    style PlainPassword fill:#FF9800
    style Hash fill:#4CAF50
    style OK fill:#4CAF50
    style NG fill:#F44336
:::

### 6.2 実装コード

```python
# src/app/core/security/password.py

from passlib.context import CryptContext

# bcryptコンテキスト（12ラウンド）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """パスワードハッシュ化（bcrypt 12ラウンド）"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワード検証（タイミング攻撃対策済み）"""
    return pwd_context.verify(plain_password, hashed_password)
:::

### 6.3 bcrypt設定

| パラメータ | 設定値 | 説明 |
|----------|--------|------|
| **アルゴリズム** | bcrypt | 業界標準のパスワードハッシュアルゴリズム |
| **ラウンド数** | 12 | 計算コスト（2^12 = 4096イテレーション） |
| **ソルト** | 自動生成 | ハッシュごとにランダムソルト |
| **タイミング攻撃対策** | 実装済み | 検証時間を一定に保つ |

### 6.4 パスワードポリシー

**推奨事項:**

```python
# src/app/schemas/user.py (Pydanticバリデーション)

from pydantic import BaseModel, Field, validator
import re

class PasswordPolicy(BaseModel):
    """パスワードポリシー"""

    password: str = Field(..., min_length=8, max_length=128)

    @validator("password")
    def validate_password(cls, v):
        """パスワード強度検証"""

        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        return v
```

**注意**: 現在の実装ではSampleUser（旧実装）のみパスワード認証を使用。本番ではAzure AD認証を使用するため、パスワードポリシーは適用されません。

---

## 7. SQLインジェクション対策

### 7.1 対策レイヤー

::: mermaid
graph TB
    Request[API Request]
    Request --> L1[Layer 1: Pydanticバリデーション]
    L1 --> L2[Layer 2: SQLAlchemy ORM]
    L2 --> L3[Layer 3: パラメータ化クエリ]
    L3 --> DB[(PostgreSQL)]

    L1 --> V1[型検証<br/>形式検証<br/>範囲検証]
    L2 --> V2[ORM抽象化<br/>生SQLなし]
    L3 --> V3[プリペアドステートメント<br/>自動エスケープ]

    style L1 fill:#4CAF50
    style L2 fill:#8BC34A
    style L3 fill:#AED581
:::

### 7.2 実装例

#### 7.2.1 Pydanticバリデーション

```python
# src/app/schemas/project.py

from pydantic import BaseModel, Field, validator
from uuid import UUID
import re

class ProjectCreate(BaseModel):
    """プロジェクト作成スキーマ"""

    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=2000)

    @validator("code")
    def validate_code(cls, v):
        """プロジェクトコード検証（英数字とアンダースコアのみ）"""
        if not re.match(r"^[A-Z0-9_]+$", v):
            raise ValueError("Code must contain only uppercase letters, digits, and underscores")
        return v
:::

#### 7.2.2 SQLAlchemyパラメータ化クエリ

```python
# src/app/repositories/base.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_by_filter(
    self,
    db: AsyncSession,
    **filters
) -> list[ModelType]:
    """フィルタ検索（安全なパラメータ化クエリ）"""

    stmt = select(self.model)

    for key, value in filters.items():
        # モデル属性の検証
        if hasattr(self.model, key):
            # パラメータ化クエリ（SQLインジェクション対策）
            stmt = stmt.where(getattr(self.model, key) == value)
        else:
            logger.warning(f"Invalid filter key: {key}")

    result = await db.execute(stmt)
    return list(result.scalars().all())
```

### 7.3 禁止事項

❌ **絶対に使用しない:**

```python
# 危険: 文字列連結によるSQL構築
query = f"SELECT * FROM users WHERE email = '{email}'"  # SQLインジェクション脆弱性

# 危険: 生SQL実行
await db.execute(text(f"DELETE FROM users WHERE id = {user_id}"))  # SQLインジェクション脆弱性
```

✅ **正しい方法:**

```python
# 安全: パラメータ化クエリ
stmt = select(User).where(User.email == email)
result = await db.execute(stmt)

# 安全（生SQLが必要な場合）: バインドパラメータ
await db.execute(
    text("DELETE FROM users WHERE id = :user_id"),
    {"user_id": user_id}
)
```

---

## 8. XSS（クロスサイトスクリプティング）対策

### 8.1 対策手法

::: mermaid
graph LR
    Input[ユーザー入力] --> Validation[Pydanticバリデーション]
    Validation --> Sanitize[サニタイゼーション<br/>不要]
    Sanitize --> Store[(データベース)]

    Store --> API[API Response]
    API --> JSON[JSON形式]
    JSON --> Client[クライアント<br/>自動エスケープ]

    style Validation fill:#4CAF50
    style JSON fill:#8BC34A
:::

### 8.2 実装詳細

#### 8.2.1 Pydanticによる入力検証

```python
# src/app/schemas/analysis.py

from pydantic import BaseModel, Field, validator
import bleach

class ChatMessage(BaseModel):
    """チャットメッセージスキーマ"""

    message: str = Field(..., min_length=1, max_length=5000)

    @validator("message")
    def validate_message(cls, v):
        """メッセージ検証（HTMLタグ除去）"""

        # HTMLタグをエスケープ（bleach使用）
        cleaned = bleach.clean(v, tags=[], strip=True)

        return cleaned
:::

#### 8.2.2 Content-Type強制

```python
# src/app/main.py

from fastapi.responses import JSONResponse

app = FastAPI(default_response_class=JSONResponse)

# すべてのレスポンスはJSON形式（application/json）
# HTMLレスポンスは返さない → XSS対策
```

#### 8.2.3 Content-Security-Policyヘッダー

```http
Content-Security-Policy: default-src 'self'; script-src 'self'
```

---

## 9. CSRF（クロスサイトリクエストフォージェリ）対策

### 9.1 対策手法

**API設計による対策（CSRF不要）:**

- **Bearer Token認証**: Cookieを使用しないため、CSRF攻撃の対象外
- **CORS制御**: 許可されたオリジンのみアクセス可能
- **SameSite Cookie（将来）**: Cookieを使用する場合はSameSite属性設定

::: mermaid
graph LR
    Client[SPA Client<br/>app.example.com]
    Client -->|Bearer Token<br/>in Header| API[API Server<br/>api.example.com]

    Attacker[Attacker Site<br/>evil.com]
    Attacker -.->|CORS Blocked| API

    style Client fill:#4CAF50
    style Attacker fill:#F44336
    style API fill:#2196F3
:::

### 9.2 CORS設定

**実装**: `src/app/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # ["https://app.example.com"]
    allow_credentials=True,  # Cookieを使用する場合
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,  # プリフライトキャッシュ（1時間）
)
:::

---

## 10. ファイルアップロードセキュリティ

### 10.1 ファイルアップロード対策

::: mermaid
graph TB
    Upload[ファイルアップロード]

    Upload --> C1[1. ファイルサイズ検証<br/>最大100MB]
    C1 --> C2[2. Content-Type検証<br/>MIMEタイプ]
    C2 --> C3[3. ファイル拡張子検証<br/>ホワイトリスト]
    C3 --> C4[4. ウイルススキャン<br/>将来実装]
    C4 --> C5[5. 安全なファイル名生成<br/>UUID]
    C5 --> C6[6. ストレージ分離<br/>uploads/]
    C6 --> Success[✅ アップロード成功]

    style C1 fill:#4CAF50
    style C5 fill:#8BC34A
    style Success fill:#4CAF50
:::

### 10.2 実装コード

```python
# src/app/api/routes/v1/projects/files.py

from fastapi import UploadFile, HTTPException, status
from uuid import uuid4
import os

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".txt", ".json"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

async def validate_upload_file(file: UploadFile):
    """ファイルアップロード検証"""

    # 1. ファイルサイズ検証
    file.file.seek(0, 2)  # ファイル末尾へ移動
    file_size = file.file.tell()
    file.file.seek(0)  # ファイル先頭へ戻る

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit"
        )

    # 2. ファイル拡張子検証
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension {ext} is not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # 3. Content-Type検証
    if file.content_type not in ["text/csv", "application/vnd.ms-excel", ...]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type"
        )

    # 4. 安全なファイル名生成
    safe_filename = f"{uuid4()}{ext}"

    return safe_filename, file_size
:::

---

## 11. 監査ログ・操作履歴

### 11.1 2つのミドルウェアによる記録

システムでは2つのミドルウェアで操作を記録します：

| ミドルウェア | 目的 | 記録対象 |
|------------|------|---------|
| **AuditLogMiddleware** | 重要な操作の監査記録 | データ変更、セキュリティイベント |
| **ActivityTrackingMiddleware** | 全操作の履歴記録 | 全APIリクエスト |

::: mermaid
mindmap
  root((監査・操作記録))
    AuditLogMiddleware
      プロジェクト変更
      ユーザー変更
      システム設定変更
      セッション終了
      一括操作
      データ削除
      代行操作
    ActivityTrackingMiddleware
      全APIリクエスト
      リクエストボディ
      レスポンスステータス
      処理時間
      エラー情報
:::

### 11.2 AuditLogMiddleware

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
        # システム設定変更
        {
            "pattern": re.compile(r"^/api/v1/admin/settings/"),
            "methods": {"PATCH", "POST"},
            "resource_type": "SYSTEM_SETTING",
            "event_type": AuditEventType.DATA_CHANGE,
            "severity": AuditSeverity.WARNING,
        },
        # 代行操作（最高重要度）
        {
            "pattern": re.compile(r"^/api/v1/admin/impersonate/"),
            "methods": {"POST"},
            "resource_type": "IMPERSONATION",
            "event_type": AuditEventType.SECURITY,
            "severity": AuditSeverity.CRITICAL,
        },
    ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # 監査対象かチェック
        audit_config = self._get_audit_config(request.url.path, request.method)
        if not audit_config:
            return await call_next(request)

        # リクエスト処理
        response = await call_next(request)

        # 成功時のみ監査ログを記録（2xxのみ）
        if 200 <= response.status_code < 300:
            await self._record_audit_log(request, response, audit_config)

        return response
```

### 11.3 ActivityTrackingMiddleware

**実装**: `src/app/api/middlewares/activity_tracking.py`

```python
class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    """ユーザー操作履歴を自動記録するミドルウェア"""

    # 除外パス
    EXCLUDE_PATHS: set[str] = {
        "/health", "/healthz", "/ready", "/metrics",
        "/docs", "/openapi.json", "/redoc", "/favicon.ico",
    }

    # 機密情報キー（マスク対象）
    SENSITIVE_KEYS: set[str] = {
        "password", "token", "secret", "api_key",
        "credential", "authorization",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        if self._should_skip(request.url.path):
            return await call_next(request)

        start_time = time.perf_counter()

        # リクエストボディ取得（機密情報マスク）
        request_body = await self._get_masked_request_body(request)

        response = await call_next(request)

        # 処理時間計算
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # 操作履歴を記録
        await self._record_activity(
            request=request,
            request_body=request_body,
            response_status=response.status_code,
            duration_ms=duration_ms,
        )

        return response
```

### 11.4 監査対象と重要度

| リソース | HTTPメソッド | イベント種別 | 重要度 |
|---------|-------------|-------------|--------|
| **PROJECT** | PUT, PATCH, DELETE | DATA_CHANGE | INFO |
| **USER** | PUT, PATCH, DELETE | DATA_CHANGE | INFO |
| **SYSTEM_SETTING** | PATCH, POST | DATA_CHANGE | WARNING |
| **SESSION** | POST (terminate) | SECURITY | WARNING |
| **BULK_OPERATION** | POST | DATA_CHANGE | WARNING |
| **DATA_CLEANUP** | POST | DATA_CHANGE | CRITICAL |
| **IMPERSONATION** | POST | SECURITY | CRITICAL |

### 11.5 操作履歴の記録内容

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

---

## 12. まとめ

### 12.1 実装済みセキュリティ機能

✅ **多層防御**: 5層のセキュリティレイヤー
✅ **OWASP Top 10対策**: 10項目すべて対策済み
✅ **セキュリティヘッダー**: CSP, HSTS等（本番環境で有効）
✅ **レート制限**: 100req/min（Sliding Window、Redis/Memoryフォールバック）
✅ **メンテナンスモード**: 管理者アクセスを許可しつつサービス停止
✅ **パスワードハッシュ**: bcrypt 12ラウンド
✅ **SQLインジェクション対策**: ORM + Pydantic
✅ **XSS対策**: Pydantic + CSP
✅ **CSRF対策**: Bearer Token + CORS
✅ **ファイルアップロードセキュリティ**: サイズ・拡張子検証
✅ **監査ログ**: AuditLogMiddlewareによる重要操作の記録
✅ **操作履歴**: ActivityTrackingMiddlewareによる全操作の記録

### 12.2 今後の改善提案

- **WAF導入**: Web Application Firewall
- **ウイルススキャン**: アップロードファイルのスキャン
- **DDoS対策**: CloudFlare等のCDN/WAF
- **ペネトレーションテスト**: 定期的な脆弱性診断
- **セキュリティ監視**: SIEM（Security Information and Event Management）
- **インシデントレスポンス**: セキュリティインシデント対応手順

---

**ドキュメント管理情報:**

- **作成日**: 2025年（リバースエンジニアリング実施）
- **最終更新日**: 2026年1月（ミドルウェア実装更新）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - 認証・認可設計書: `05-security/02-authentication-design.md`
  - RBAC設計書: `05-security/01-rbac-design.md`
  - ミドルウェア設計書: `09-middleware/01-middleware-design.md`
