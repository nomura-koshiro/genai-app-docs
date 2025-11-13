# セキュリティ - リクエスト保護

このドキュメントでは、camp-backendにおけるHTTPリクエストレベルのセキュリティ保護機能について説明します。

## 目次

- [CORS設定](#cors設定)
- [レート制限](#レート制限)
- [入力バリデーション](#入力バリデーション)

---

## CORS設定

**実装場所**: `src/app/core/app_factory.py:118-124`

### ミドルウェア設定

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 環境別の許可オリジン

**実装場所**: `src/app/core/config.py:316-324`

#### 本番環境（production）

- `ALLOWED_ORIGINS`の明示的な設定が**必須**
- 未設定の場合は`ValueError`で起動時にエラー
- 例: `["https://example.com", "https://api.example.com"]`

#### ステージング環境（staging）

- デフォルト: `["https://staging.example.com"]`
- 環境変数で上書き可能

#### 開発環境（development）

- デフォルト: `["http://localhost:3000", "http://localhost:5173"]`
- 環境変数で上書き可能

### セキュリティバリデーション

```python
if self.ENVIRONMENT == "production":
    if self.ALLOWED_ORIGINS is None:
        raise ValueError("ALLOWED_ORIGINS must be explicitly set in production environment")
```

**参照**: `src/app/core/config.py:317-324`

---

## レート制限

**実装場所**: `src/app/api/middlewares/rate_limit.py`

### 実装詳細

#### アルゴリズム

- **スライディングウィンドウ**: 固定ウィンドウより精度が高い
- **Redis Sorted Set使用**: 複数ワーカー/サーバー間で共有
- **デフォルト制限**: 100リクエスト/60秒

#### クライアント識別（優先順位）

1. **認証済みユーザーID**: `user:{user_id}`
2. **APIキー**: `apikey:{SHA256ハッシュ}`
3. **IPアドレス**: `ip:{ip_address}`（X-Forwarded-For対応）

**実装場所**: `src/app/api/middlewares/rate_limit.py:110-179`

```python
def _get_client_identifier(self, request: Request) -> str:
    # 1. 認証済みユーザー
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # 2. APIキー
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()}"

    # 3. IPアドレス（X-Forwarded-For対応）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return f"ip:{client_ip}"
```

### レート制限超過時のレスポンス

**HTTPステータス**: 429 Too Many Requests

```json
{
  "error": "Rate limit exceeded",
  "details": {
    "limit": 100,
    "period": 60,
    "retry_after": 60
  }
}
```

**ヘッダー**: `Retry-After: 60`

### レート制限ヘッダー

すべてのレスポンスに以下のヘッダーを追加:

- `X-RateLimit-Limit`: リクエスト制限数（例: 100）
- `X-RateLimit-Remaining`: 残りリクエスト数（例: 50）
- `X-RateLimit-Reset`: リセット時刻（Unixタイムスタンプ）

**実装場所**: `src/app/api/middlewares/rate_limit.py:278-281`

### グレースフルデグラデーション

- **開発環境**（DEBUG=True）: レート制限を無効化
- **Redis接続エラー時**: 制限をスキップ（可用性優先）

**実装場所**: `src/app/api/middlewares/rate_limit.py:230-246`

```python
# 開発環境ではスキップ
if settings.DEBUG:
    return await call_next(request)

# Redis接続エラー時もスキップ
if not cache_manager._redis:
    logger.warning("Redis not available, skipping rate limit")
    return await call_next(request)
```

---

## 入力バリデーション

### 1. Pydanticスキーマバリデーション

**実装場所**: `src/app/schemas/sample_user.py`

#### ユーザー登録

```python
class SampleUserCreate(BaseModel):
    email: EmailStr  # 自動フォーマット検証
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=100)
```

**検証項目**:

- `email`: EmailStr型で自動フォーマット検証
- `username`: 3-50文字
- `password`: 8-100文字（Pydantic）+ 強度検証（サービス層）

### 2. ファイルアップロードバリデーション

**実装場所**: `src/app/api/routes/files.py`

#### セキュリティ制限

**ブロックリスト**（50行目）:

```python
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".ps1", ".dll"}
```

**許可MIME types**（52-61行目）:

```python
ALLOWED_MIME_TYPES = {
    # 画像
    "image/jpeg", "image/png", "image/gif", "image/webp",
    # ドキュメント
    "application/pdf",
    "text/plain", "text/markdown",
    # アーカイブ
    "application/zip",
}
```

**ファイルサイズ制限**: 10MB（デフォルト）

#### ファイル名サニタイゼーション

**実装場所**: `src/app/api/routes/files.py:64-95`

```python
def sanitize_filename(filename: str) -> str:
    # 危険な文字を除去（英数字、スペース、ハイフン、ドット以外）
    filename = re.sub(r"[^\w\s\-\.]", "", filename)

    # パストラバーサル対策
    filename = Path(filename).name

    return filename
```

**セキュリティ効果**:

- `../../etc/passwd` → `passwd`
- パストラバーサル攻撃を防止
- コマンドインジェクション対策

---

## 関連ドキュメント

- [セキュリティ概要](./03-security.md) - セキュリティ機能の全体像
- [認証・認可](./03-security-authentication.md) - パスワードハッシュ化、JWT認証
- [データ保護](./03-security-data-protection.md) - データベース、ファイルアップロード
- [インフラストラクチャ](./03-security-infrastructure.md) - エラーハンドリング、環境設定
- [ベストプラクティス](./03-security-best-practices.md) - セキュリティ強化の推奨事項

---
