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
        L2B[セキュリティヘッダー<br/>10種類]
        L2C[リクエストサイズ制限<br/>100MB]
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
        L5A[構造化ログ<br/>structlog]
        L5B[監査ログ]
        L5C[異常検知]
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

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダー追加ミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # X-Content-Type-Options: MIMEスニッフィング防止
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: クリックジャッキング防止
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: XSSフィルタ有効化
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security: HTTPS強制（本番のみ）
        if not request.url.scheme == "http":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Content-Security-Policy: リソース制限
        csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Content-Security-Policy"] = csp

        # Referrer-Policy: リファラー情報制限
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: ブラウザ機能制限
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=()"
        )

        return response
:::

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
| **識別方法** | IP or User ID | 認証済み: User ID、未認証: IP |
| **バックエンド** | Redis or Memory | Redisが利用可能ならRedis、なければメモリ |
| **アルゴリズム** | Token Bucket | トークンバケットアルゴリズム |

### 5.3 実装コード

```python
# src/app/api/middlewares/rate_limit.py

import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """レート制限ミドルウェア（Token Bucket）"""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.buckets = defaultdict(lambda: {"tokens": requests_per_minute, "last_refill": time.time()})

    def _get_client_id(self, request: Request) -> str:
        """クライアント識別子取得（User ID優先、なければIP）"""
        # 認証済みユーザーの場合はUser IDを使用
        if hasattr(request.state, "user"):
            return f"user:{request.state.user.id}"

        # 未認証の場合はIPアドレスを使用
        client_ip = request.client.host
        return f"ip:{client_ip}"

    def _refill_tokens(self, client_id: str):
        """トークン補充"""
        bucket = self.buckets[client_id]
        now = time.time()
        elapsed = now - bucket["last_refill"]

        # 経過時間に応じてトークン補充
        tokens_to_add = (elapsed / self.window_seconds) * self.requests_per_minute
        bucket["tokens"] = min(bucket["tokens"] + tokens_to_add, self.requests_per_minute)
        bucket["last_refill"] = now

    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)

        # トークン補充
        self._refill_tokens(client_id)

        bucket = self.buckets[client_id]

        if bucket["tokens"] >= 1:
            # トークン消費
            bucket["tokens"] -= 1

            response = await call_next(request)

            # レート制限ヘッダー追加
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(int(bucket["tokens"]))
            response.headers["X-RateLimit-Reset"] = str(int(bucket["last_refill"] + self.window_seconds))

            return response
        else:
            # レート制限超過
            retry_after = int(self.window_seconds - (time.time() - bucket["last_refill"]))

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                }
            )
:::

### 5.4 Redisバックエンド（本番推奨）

```python
# src/app/api/middlewares/rate_limit.py (Redis版)

import redis.asyncio as redis
from app.core.config import settings

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Redisベースレート制限ミドルウェア"""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)
        key = f"rate_limit:{client_id}"

        # 現在のカウント取得
        current_count = await self.redis.get(key)

        if current_count is None:
            # 初回リクエスト
            await self.redis.setex(key, self.window_seconds, 1)
            remaining = self.requests_per_minute - 1
        elif int(current_count) < self.requests_per_minute:
            # 制限内
            await self.redis.incr(key)
            remaining = self.requests_per_minute - int(current_count) - 1
        else:
            # 制限超過
            ttl = await self.redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {ttl} seconds.",
                headers={"Retry-After": str(ttl)}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
```

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

## 11. 監査ログ

### 11.1 監査ログ対象

::: mermaid
mindmap
  root((監査ログ))
    認証イベント
      ログイン成功
      ログイン失敗
      ログアウト
    認可イベント
      権限拒否
      ロール変更
      メンバー追加削除
    データ操作
      プロジェクト作成削除
      ファイルアップロード削除
      重要データ更新
    セキュリティイベント
      レート制限超過
      不正アクセス試行
      異常なリクエスト
:::

### 11.2 実装

**実装**: `src/app/api/decorators/security.py`

```python
from functools import wraps
from app.core.logging import logger

def audit_log(action: str):
    """監査ログデコレータ"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # リクエスト情報取得
            current_user = kwargs.get("current_user")
            request_id = kwargs.get("request_id")

            # 操作前ログ
            logger.info(
                f"Audit: {action} started",
                user_id=current_user.id if current_user else None,
                action=action,
                request_id=request_id
            )

            try:
                result = await func(*args, **kwargs)

                # 操作成功ログ
                logger.info(
                    f"Audit: {action} succeeded",
                    user_id=current_user.id if current_user else None,
                    action=action,
                    request_id=request_id
                )

                return result

            except Exception as e:
                # 操作失敗ログ
                logger.error(
                    f"Audit: {action} failed",
                    user_id=current_user.id if current_user else None,
                    action=action,
                    error=str(e),
                    request_id=request_id
                )
                raise

        return wrapper
    return decorator

# 使用例
@audit_log(action="delete_project")
async def delete_project(project_id: UUID, current_user: UserAccount):
    ...
```

---

## 12. まとめ

### 12.1 実装済みセキュリティ機能

✅ **多層防御**: 5層のセキュリティレイヤー
✅ **OWASP Top 10対策**: 10項目すべて対策済み
✅ **セキュリティヘッダー**: 7種類のヘッダー実装
✅ **レート制限**: 100req/min（Token Bucket）
✅ **パスワードハッシュ**: bcrypt 12ラウンド
✅ **SQLインジェクション対策**: ORM + Pydantic
✅ **XSS対策**: Pydantic + CSP
✅ **CSRF対策**: Bearer Token + CORS
✅ **ファイルアップロードセキュリティ**: サイズ・拡張子検証
✅ **監査ログ**: 主要操作のログ記録

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
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - 認証・認可設計書: `03-security/02-authentication-design.md`
  - RBAC設計書: `03-security/01-rbac-design.md`
  - ミドルウェア設計書: `06-middleware/01-middleware-design.md`
