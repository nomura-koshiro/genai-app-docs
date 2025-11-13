# セキュリティ - ベストプラクティス

このドキュメントでは、camp-backendにおけるセキュリティ強化の実装状況と推奨事項を説明します。

## 目次

- [実装済み機能](#実装済み機能)
- [追加推奨事項](#追加推奨事項)

---

## 実装済み機能

以下のセキュリティ機能は既に実装されています。

### ✅ 1. セキュリティヘッダーミドルウェア

**実装場所**: `src/app/api/middlewares/security_headers.py`

**追加されるヘッダー**:

```python
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-XSS-Protection"] = "1; mode=block"

# 本番環境のみ
if settings.ENVIRONMENT == "production":
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
```

**効果**:

- クリックジャッキング攻撃の防止（X-Frame-Options）
- MIMEスニッフィング防止（X-Content-Type-Options）
- XSS攻撃の防止（X-XSS-Protection）
- HTTPS強制（HSTS - 本番環境のみ）

---

### ✅ 2. ログイン失敗回数制限

**実装場所**: `src/app/services/sample_user.py` (authenticate メソッド)

**実装内容**:

```python
# ログイン失敗時
user.failed_login_attempts += 1
if user.failed_login_attempts >= 5:
    user.locked_until = datetime.now(UTC) + timedelta(hours=1)
    await db.commit()

# ログイン成功時
user.failed_login_attempts = 0
user.locked_until = None
user.last_login_at = datetime.now(UTC)
user.last_login_ip = client_ip
```

**効果**:

- ブルートフォース攻撃の防止
- アカウントロック（5回失敗で1時間）
- ログイン監査（IPアドレス、日時の記録）

---

### ✅ 3. リフレッシュトークンの実装

**実装場所**:

- `src/app/core/security/jwt.py` (create_refresh_token, decode_refresh_token)
- `src/app/api/routes/v1/sample_users.py` (POST /api/v1/sample-users/refresh)
- `src/app/models/sample_user.py` (refresh_token, refresh_token_expires_at フィールド)

**実装内容**:

- リフレッシュトークンの生成と保存（**bcryptでハッシュ化**）
- アクセストークン更新エンドポイント
- 有効期限管理（7日間）
- データベースとの照合（ハッシュ値で検証）

**使用方法**:

```python
# ログイン時
POST /api/v1/sample-users/sample-login
→ access_token + refresh_token を返却

# トークンリフレッシュ
POST /api/v1/sample-users/refresh
Body: {"refresh_token": "..."}
→ 新しい access_token を返却
```

**セキュリティ効果**:

- 長期セッション対応とセキュリティのバランス
- データベース漏洩時もトークンを復元不可能（ハッシュ化保存）
- 定時間比較によるタイミング攻撃対策

---

### ✅ 4. APIキー認証の実装

**実装場所**:

- `src/app/core/security/api_key.py` (generate_api_key 関数)
- `src/app/api/routes/v1/sample_users.py` (POST /api/v1/sample-users/api-key)
- `src/app/models/sample_user.py` (api_key, api_key_created_at フィールド)

**実装内容**:

- APIキー生成エンドポイント（POST /api/v1/sample-users/api-key）
- ユーザーごとのAPIキー管理（**bcryptでハッシュ化保存**）
- 一度しか表示されない安全な設計

**使用方法**:

```powershell
# APIキー生成（認証必須）
POST /api/v1/sample-users/api-key
Authorization: Bearer <access_token>

# レスポンス
{
  "api_key": "dGhpcyBpcyBh...",
  "created_at": "2025-10-22T00:00:00Z",
  "message": "APIキーは一度しか表示されません。安全に保管してください。"
}
```

**セキュリティ効果**:

- 外部サービス連携、サーバー間通信の認証
- データベース漏洩時もAPIキーを復元不可能（ハッシュ化保存）
- 256ビットのエントロピー（暗号学的に安全）

---

## 追加推奨事項

### 優先度：中

#### 5. 監査ログの強化

**推奨実装**:

- セキュリティイベントの記録（ログイン失敗、権限違反等）
- ログの集中管理（ELKスタック等）
- アラート機能

**現状**: 基本的なロギングは実装済み（structlog使用）

---

### 優先度：低

---

## 優先度：低

### 7. CSRFトークンの実装

**現状**: JSON APIのため不要

**推奨**: フォーム送信がある場合は実装が必要

### 8. ファイルスキャン機能

**推奨**: アップロードファイルのウイルススキャン（ClamAV等）

---

## 関連ドキュメント

- [セキュリティ概要](./03-security.md) - セキュリティ機能の全体像
- [認証・認可](./03-security-authentication.md) - パスワードハッシュ化、JWT認証
- [リクエスト保護](./03-security-request-protection.md) - CORS、レート制限、入力バリデーション
- [データ保護](./03-security-data-protection.md) - データベース、ファイルアップロード
- [インフラストラクチャ](./03-security-infrastructure.md) - エラーハンドリング、環境設定

---
