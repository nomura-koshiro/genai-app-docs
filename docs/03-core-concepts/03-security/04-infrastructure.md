# セキュリティ - インフラストラクチャ

このドキュメントでは、camp-backendにおけるインフラストラクチャレベルのセキュリティ機能について説明します。

## 目次

- [エラーハンドリング](#エラーハンドリング)
- [環境設定管理](#環境設定管理)
- [セキュリティヘッダー](#セキュリティヘッダー)

---

## エラーハンドリング

### 1. カスタム例外階層

**実装場所**: `src/app/core/exceptions.py`

```text
AppException（基底クラス）
├── NotFoundError (404)
├── ValidationError (422)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── DatabaseError (500)
└── ExternalServiceError (502)
```

### 2. 統一エラーレスポンス

**実装場所**: `src/app/api/middlewares/error_handler.py`

#### ErrorHandlerMiddleware

- **カスタム例外**: 適切なHTTPステータスコード + 詳細情報
- **予期しない例外**: 500エラーに変換（詳細情報は非公開）
- **すべてエラーログに記録**（トレースバック付き）

#### レスポンス形式

```json
{
  "error": "エラーメッセージ",
  "details": {"追加情報": "値"}
}
```

**セキュリティ効果**:

- 予期しない例外の詳細を外部に公開しない
- 一貫したエラーレスポンス形式
- すべてのエラーをログに記録（監査証跡）

---

## 環境設定管理

**実装場所**: `src/app/core/config.py`

### 1. 設定ファイル構造

#### 環境別.envファイル

- `.env.local`（開発環境）
- `.env.staging`（ステージング環境）
- `.env.production`（本番環境）

#### 優先順位

1. 環境変数（最優先）
2. `.env.{environment}`（環境別）
3. `.env`（共通設定）
4. Settingsクラスのデフォルト値

**実装場所**: `src/app/core/config.py:69-129`

### 2. セキュリティ設定の検証

#### SECRET_KEY検証（326-342行目）

```python
if self.ENVIRONMENT == "production":
    if not self.SECRET_KEY or "dev-secret-key" in self.SECRET_KEY:
        raise ValueError(
            "SECRET_KEY must be set in production environment. "
            "Generate one with: openssl rand -hex 32"
        )
```

**検証項目**:

- 本番環境では必須
- デフォルトキーは使用不可
- 最小32文字（Fieldのmin_length制約）

#### ALLOWED_ORIGINS検証（317-324行目）

```python
if self.ENVIRONMENT == "production":
    if self.ALLOWED_ORIGINS is None:
        raise ValueError("ALLOWED_ORIGINS must be explicitly set in production environment")
```

### 3. 機密情報管理

- `.gitignore`に`.env*`含む（機密情報をGit管理から除外）
- `.env.*.example`ファイルでテンプレート提供
- パスワード・APIキーは環境変数で設定

#### 本番環境での必須設定

```ini
# .env.production
ENVIRONMENT=production
SECRET_KEY=<openssl rand -hex 32で生成>
ALLOWED_ORIGINS=["https://example.com"]
DATABASE_URL=postgresql+asyncpg://...
```

---

## セキュリティヘッダー

### SecurityHeadersMiddleware

**実装場所**: `src/app/api/middlewares/security_headers.py`

すべてのHTTPレスポンスに対して、以下のセキュリティヘッダーを自動的に追加します。

#### 実装されているヘッダー

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # X-Content-Type-Options: ブラウザのコンテンツスニッフィング防止
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: クリックジャッキング攻撃を防止
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: 古いブラウザのXSS防御機能を有効化
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS: 本番環境のみHTTPSを強制
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response
```

**ミドルウェア登録**: `src/app/core/app_factory.py:170-171`

```python
from app.api.middlewares.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
```

#### ヘッダーの効果

| ヘッダー | 設定値 | 効果 |
|---------|-------|------|
| `X-Content-Type-Options` | `nosniff` | ブラウザのMIMEタイプ推測を無効化し、コンテンツスニッフィング攻撃を防止 |
| `X-Frame-Options` | `DENY` | iframe内での表示を禁止し、クリックジャッキング攻撃を防止 |
| `X-XSS-Protection` | `1; mode=block` | 古いブラウザのXSS防御機能を有効化（モダンブラウザはCSPで対応） |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HTTPS接続を1年間強制（本番環境のみ） |

### 追加可能なヘッダー（コメントアウト済み）

**Content-Security-Policy（CSP）**は実装されていますが、デフォルトでは無効化されています。

```python
# response.headers["Content-Security-Policy"] = (
#     "default-src 'self'; "
#     "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
#     "style-src 'self' 'unsafe-inline';"
# )
```

CSPを有効化する場合は、フロントエンドの要件に応じてポリシーを調整してください。

---

## 関連ドキュメント

- [セキュリティ概要](./03-security.md) - セキュリティ機能の全体像
- [認証・認可](./03-security-authentication.md) - パスワードハッシュ化、JWT認証
- [リクエスト保護](./03-security-request-protection.md) - CORS、レート制限、入力バリデーション
- [データ保護](./03-security-data-protection.md) - データベース、ファイルアップロード
- [ベストプラクティス](./03-security-best-practices.md) - セキュリティ強化の推奨事項

---
