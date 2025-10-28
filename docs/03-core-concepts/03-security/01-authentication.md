# セキュリティ - 認証・認可

このドキュメントでは、AI Agent Applicationにおける認証・認可機能の実装について説明します。

## 目次

- [パスワードハッシュ化](#パスワードハッシュ化)
- [JWT認証](#jwt認証)
- [パスワード強度検証](#パスワード強度検証)
- [認証依存性注入](#認証依存性注入)
- [APIキー生成](#apiキー生成)

---

## パスワードハッシュ化

**実装場所**: `src/app/core/security/`

### アルゴリズム

- **bcrypt**: パスワードハッシュアルゴリズム
- **コスト**: 自動（デフォルト12ラウンド）
- **Salt**: ランダムsalt自動生成
- **レインボーテーブル攻撃耐性**: あり

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# パスワードのハッシュ化
hashed = hash_password("SecurePass123!")  # → $2b$12$KIX...

# パスワードの検証
is_valid = verify_password("SecurePass123!", hashed)  # → True
```

**セキュリティ特性**:

- 定時間比較（タイミング攻撃対策）
- bcryptのsalt自動処理
- 同じパスワードでも毎回異なるハッシュ生成

**参照**: `src/app/core/security/password.py`, `jwt.py`, `api_key.py`

---

## JWT認証

**実装場所**: `src/app/core/security/`

### トークン生成

```python
def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str
```

**トークンに含まれるフィールド**:

- `sub`: Subject（user_id）
- `exp`: 有効期限（UTC）
- `iat`: 発行時刻（UTC）
- `type`: トークンタイプ（"access"）

**アルゴリズム**: HS256（HMAC-SHA256）

**デフォルト有効期限**: 30分（`ACCESS_TOKEN_EXPIRE_MINUTES`）

### トークン検証

```python
def decode_access_token(token: str) -> dict[str, Any] | None
```

**検証項目**:

1. 署名の検証（SECRET_KEYとの一致）
2. 有効期限の検証（exp）
3. アルゴリズムの検証（HS256）
4. subフィールドの存在確認

**無効なトークンの場合**: `None`を返し、警告ログを記録

**参照**: `src/app/core/security/password.py`, `jwt.py`, `api_key.py`

---

## パスワード強度検証

**実装場所**: `src/app/core/security/password.py`, `jwt.py`, `api_key.py`

### パスワード要件（必須）

- 最小8文字
- 大文字を1つ以上含む（A-Z）
- 小文字を1つ以上含む（a-z）
- 数字を1つ以上含む（0-9）

### 推奨事項

- 特殊文字を1つ以上含む（!@#$%^&*(),.?":{}|<>）
- 12文字以上

```python
is_valid, error = validate_password_strength("password")
# → (False, "パスワードには大文字を含めてください")

is_valid, error = validate_password_strength("SecurePass123!")
# → (True, "")
```

**参照**: `src/app/core/security/password.py`, `jwt.py`, `api_key.py`

---

## 認証依存性注入

**実装場所**: `src/app/api/dependencies.py`

### 階層的な認証チェック

```python
# 基本認証
async def get_current_user(token: str = Depends(oauth2_scheme)) -> SampleUser

# アクティブユーザー
async def get_current_active_user(current_user: SampleUser = Depends(get_current_user)) -> SampleUser

# スーパーユーザー
async def get_current_superuser(current_user: SampleUser = Depends(get_current_user)) -> SampleUser

# オプション認証（ゲスト対応）
async def get_current_user_optional(authorization: str | None = Header(None)) -> SampleUser | None
```

### 認証フロー

1. Authorizationヘッダーから`Bearer <token>`を抽出
2. JWTトークンをデコードして検証
3. ペイロードから`user_id`を抽出
4. データベースからユーザー情報を取得
5. アクティブ状態・権限チェック

---

## APIキー生成

**実装場所**: `src/app/core/security/password.py`, `jwt.py`, `api_key.py`

```python
def generate_api_key() -> str
```

**特性**:

- 長さ: 32バイト（URL-safeなbase64エンコードで約43文字）
- 文字セット: A-Za-z0-9_-（URL-safe）
- エントロピー: 256ビット
- `secrets.token_urlsafe()`を使用（暗号学的に安全）

**使用例**:

```python
api_key = generate_api_key()
# データベースにはハッシュ化して保存
hashed_api_key = hash_password(api_key)
```

**セキュリティ実装**:

生成されたAPIキーとリフレッシュトークンは、データベースに**ハッシュ化して保存**されます。

---

## トークンとAPIキーのハッシュ化保存

**実装場所**: `src/app/models/sample_user.py`, `src/app/api/routes/v1/sample_users.py`

### データベーススキーマ

```python
# src/app/models/sample_user.py
class SampleUser(Base):
    # リフレッシュトークン（ハッシュ化して保存）
    refresh_token_hash: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None
    )
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # APIキー（ハッシュ化して保存）
    api_key_hash: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None, index=True
    )
    api_key_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
```

### ログイン時のリフレッシュトークンハッシュ化

**実装場所**: `src/app/api/routes/v1/sample_users.py:204-212`

```python
# JWTトークンを生成
access_token = create_access_token(data={"sub": str(user.id)})
refresh_token = create_refresh_token(data={"sub": str(user.id)})

# リフレッシュトークンをハッシュ化してデータベースに保存
user.refresh_token_hash = hash_password(refresh_token)
user.refresh_token_expires_at = datetime.now(UTC) + timedelta(days=7)
await db.commit()

# クライアントには平文のrefresh_tokenを返す（一度だけ）
return TokenWithRefresh(
    access_token=access_token,
    refresh_token=refresh_token,  # 平文（最初で最後）
    token_type="bearer",
)
```

### リフレッシュトークン検証

**実装場所**: `src/app/api/routes/v1/sample_users.py:411-414`

```python
# クライアントから受け取った平文トークンと、DBのハッシュを比較
if not user.refresh_token_hash or not verify_password(
    request_data.refresh_token, user.refresh_token_hash
):
    raise AuthenticationError("リフレッシュトークンが一致しません")
```

### APIキー生成時のハッシュ化

**実装場所**: `src/app/api/routes/v1/sample_users.py:453-458`

```python
# APIキー生成
api_key = generate_api_key()
created_at = datetime.now(UTC)

# ハッシュ化してデータベースに保存
current_user.api_key_hash = hash_password(api_key)
current_user.api_key_created_at = created_at
await db.commit()

# クライアントには平文のapi_keyを返す（一度だけ）
return APIKeyResponse(
    api_key=api_key,  # 平文（最初で最後）
    created_at=created_at,
    message="APIキーは一度しか表示されません。安全に保管してください。",
)
```

### セキュリティ効果

1. **平文保存の防止**: トークンが漏洩してもデータベースから復元不可能
2. **bcrypt使用**: パスワードと同じハッシュアルゴリズムで保護
3. **一度だけ表示**: ユーザーに最初の一度だけ平文を表示
4. **検証時**: `verify_password()`で定時間比較（タイミング攻撃対策）

---

## 関連ドキュメント

- [セキュリティ概要](./03-security.md) - セキュリティ機能の全体像
- [リクエスト保護](./03-security-request-protection.md) - CORS、レート制限、入力バリデーション
- [データ保護](./03-security-data-protection.md) - データベース、ファイルアップロード
- [インフラストラクチャ](./03-security-infrastructure.md) - エラーハンドリング、環境設定
- [ベストプラクティス](./03-security-best-practices.md) - セキュリティ強化の推奨事項

---
