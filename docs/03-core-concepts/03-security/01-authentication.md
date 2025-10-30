# セキュリティ - 認証・認可

このドキュメントでは、camp-backendにおける認証・認可機能の実装について説明します。

## 目次

- [認証モードの選択](#認証モードの選択)
- [Azure AD認証（本番環境）](#azure-ad認証本番環境)
- [開発モード認証](#開発モード認証)
- [レガシー: JWT認証（参考）](#レガシー-jwt認証参考)
- [パスワードハッシュ化](#パスワードハッシュ化)
- [APIキー生成](#apiキー生成)

---

## 認証モードの選択

camp-backendは環境に応じて2つの認証モードを提供します。

### 認証モードの設定

**環境変数**: `AUTH_MODE`

```bash
# 本番環境: Azure AD認証（必須）
AUTH_MODE=production

# 開発環境: モック認証（開発のみ）
AUTH_MODE=development
```

**実装場所**: `src/app/core/config.py`

```python
AUTH_MODE: Literal["development", "production"] = Field(
    default="development",
    description="Authentication mode: development (JWT) or production (Azure AD)",
)
```

### セキュリティ検証

本番環境では開発モード認証が自動的に禁止されます：

```python
@model_validator(mode="after")
def validate_dev_auth_not_in_production(self) -> Settings:
    """本番環境で開発モード認証が有効な場合にエラーを発生させます。"""
    if self.ENVIRONMENT == "production" and self.AUTH_MODE == "development":
        raise ValueError(
            "Development authentication cannot be enabled in production environment. "
            "Set AUTH_MODE=production for production."
        )
    return self
```

---

## Azure AD認証（本番環境）

本番環境では、**Azure AD Bearer認証**を使用します。`fastapi-azure-auth`ライブラリにより、Azure ADトークンの自動検証を実現します。

### 必要な環境変数

```bash
# 認証モード
AUTH_MODE=production

# Azure AD設定
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-backend-client-id
AZURE_CLIENT_SECRET=your-client-secret  # オプション
AZURE_OPENAPI_CLIENT_ID=your-swagger-client-id
```

**実装場所**: `src/app/core/config.py`

```python
# 認証モード切り替え
AUTH_MODE: Literal["development", "production"] = Field(
    default="development",
    description="Authentication mode: development (JWT) or production (Azure AD)",
)

# Azure AD設定（本番モード用）
AZURE_TENANT_ID: str | None = Field(
    default=None,
    description="Azure AD Tenant ID",
)
AZURE_CLIENT_ID: str | None = Field(
    default=None,
    description="Azure AD Application (client) ID for backend",
)
AZURE_CLIENT_SECRET: str | None = Field(
    default=None,
    description="Azure AD Client Secret (optional for token validation)",
)
AZURE_OPENAPI_CLIENT_ID: str | None = Field(
    default=None,
    description="Azure AD Application (client) ID for Swagger UI",
)
```

### Azure ADトークン自動検証

**実装場所**: `src/app/api/core/dependencies.py`

Azure AD認証は`fastapi-azure-auth`により自動的に処理されます：

```python
from app.core.security.azure_ad import get_current_azure_user, AzureUser

# 本番環境でのみ有効
if settings.AUTH_MODE == "production":
    from app.core.security.azure_ad import AzureUser as AuthUserType
    from app.core.security.azure_ad import get_current_azure_user
```

### AzureUserクラス

Azure ADから取得されるユーザー情報：

- **oid**: Azure AD Object ID（一意識別子）
- **email**: メールアドレス
- **preferred_username**: ユーザー名
- **name**: 表示名
- **roles**: ロールリスト（Azure AD App Roles）

### 自動ユーザー同期

Azure AD認証されたユーザーは、自動的にデータベースのUserモデルと同期されます：

**実装場所**: `src/app/api/core/dependencies.py`

```python
async def get_authenticated_user_from_azure(
    user_service: AzureUserServiceDep,
    azure_user: Any = Depends(
        get_current_azure_user if settings.AUTH_MODE == "production" else get_current_dev_user
    ),
) -> User:
    """Azure AD または開発モードから認証されたユーザーを取得し、DBのUserモデルと紐付け。

    環境変数AUTH_MODEに応じて以下を切り替え:
    - production: Azure ADトークン検証
    - development: モックトークン検証

    Args:
        user_service: Azure AD用ユーザーサービス（自動注入）
        azure_user: Azure ADまたはDevユーザー（自動注入）

    Returns:
        User: データベースのユーザーモデル（新しいAzure AD対応モデル）

    Note:
        - Azure OIDでユーザーを検索、存在しない場合は自動作成します
        - 既存ユーザーの場合、メール/表示名が変わっていれば更新します
    """
    # Azure OIDでユーザーを検索（または作成）
    user = await user_service.get_or_create_by_azure_oid(
        azure_oid=azure_user.oid,
        email=azure_user.email or azure_user.preferred_username,
        display_name=getattr(azure_user, "name", None),
        roles=getattr(azure_user, "roles", []),
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found or could not be created")

    return user
```

### エンドポイントでの使用方法

**依存性注入型の定義**:

```python
# src/app/api/core/dependencies.py
CurrentUserAzureDep = Annotated[User, Depends(get_current_active_user_azure)]
"""Azure AD認証済みアクティブユーザーの依存性型。

この依存性を使用すると、エンドポイントはAzure AD認証（本番）またはモック認証（開発）を
自動的に実行します。環境変数AUTH_MODEで切り替えます。
"""
```

**エンドポイント実装例**:

```python
from fastapi import APIRouter
from app.api.core.dependencies import CurrentUserAzureDep

router = APIRouter()

@router.get("/profile")
async def get_profile(user: CurrentUserAzureDep):
    """Azure AD認証されたユーザーのプロフィールを取得。

    本番環境ではAzure ADトークンを検証、開発環境ではモックトークンを使用。
    """
    return {
        "email": user.email,
        "azure_oid": user.azure_oid,
        "display_name": user.display_name,
        "roles": user.roles,
        "is_active": user.is_active,
    }
```

### Userモデル（Azure AD対応）

**実装場所**: `src/app/models/user.py`

```python
class User(Base, TimestampMixin):
    """Azure AD認証用ユーザーモデル。

    SampleUserとは異なる新しいモデル:
    - プライマリキーがUUID型
    - azure_oidフィールドを持つ
    - パスワード認証は含まない（Azure ADのみ）
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    azure_oid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    roles: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

---

## 開発モード認証

開発環境では、**モック認証**を使用して簡易的な認証を提供します。

### 必要な環境変数

```bash
# 認証モード
AUTH_MODE=development

# モックトークン設定（オプション）
DEV_MOCK_TOKEN=mock-access-token-dev-12345
DEV_MOCK_USER_EMAIL=dev.user@example.com
DEV_MOCK_USER_OID=dev-azure-oid-12345
DEV_MOCK_USER_NAME=Development User
```

**実装場所**: `src/app/core/config.py`

```python
# 開発モード設定
DEV_MOCK_TOKEN: str = Field(
    default="mock-access-token-dev-12345",
    description="Development mode mock token",
)
DEV_MOCK_USER_EMAIL: str = Field(
    default="dev.user@example.com",
    description="Development mode mock user email",
)
DEV_MOCK_USER_OID: str = Field(
    default="dev-azure-oid-12345",
    description="Development mode mock Azure Object ID",
)
DEV_MOCK_USER_NAME: str = Field(
    default="Development User",
    description="Development mode mock user name",
)
```

### DevUserクラス

**実装場所**: `src/app/core/security/dev_auth.py`

```python
class DevUser:
    """開発モード用のモックユーザークラス。

    Azure AD Userと互換性のある構造を持ちます。
    """

    def __init__(self):
        """DevUserインスタンスを初期化します。

        環境変数から以下の設定を読み込みます:
            - DEV_MOCK_USER_OID: Azure Object ID
            - DEV_MOCK_USER_EMAIL: メールアドレス
            - DEV_MOCK_USER_NAME: 表示名
        """
        self.oid = settings.DEV_MOCK_USER_OID
        self.preferred_username = settings.DEV_MOCK_USER_EMAIL
        self.email = settings.DEV_MOCK_USER_EMAIL
        self.name = settings.DEV_MOCK_USER_NAME
        self.roles = []
```

### モック認証の動作

**実装場所**: `src/app/core/security/dev_auth.py`

```python
async def get_current_dev_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> DevUser:
    """開発モード用の認証（トークンチェックのみ）。

    Authorizationヘッダーから受け取ったBearerトークンが
    環境変数DEV_MOCK_TOKENと一致するかをチェックします。
    """
    token = credentials.credentials

    # モックトークンと一致するかチェック
    if token != settings.DEV_MOCK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid development token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return DevUser()
```

### エンドポイントでの使用方法

開発モードでも同じ`CurrentUserAzureDep`を使用できます：

```python
@router.get("/dev-test")
async def dev_test(user: CurrentUserAzureDep):
    """開発モードでテスト。

    Authorization: Bearer mock-access-token-dev-12345
    """
    return {"email": user.email, "oid": user.azure_oid}
```

### セキュリティ考慮事項

- **本番環境では絶対に使用しない**: `validate_dev_auth_not_in_production()`で自動検証
- **固定トークン**: モックトークンは固定値（セキュアではない）
- **開発専用**: ローカル開発環境でのみ使用

---

## レガシー: JWT認証（参考）

以下は、SampleUserモデル用のレガシー認証機能です。段階的に Azure AD 認証に移行中です。

### トークン生成

**実装場所**: `src/app/core/security/jwt.py`

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

### 認証依存性注入（SampleUser用）

**実装場所**: `src/app/api/dependencies.py`

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

**認証フロー**:

1. Authorizationヘッダーから`Bearer <token>`を抽出
2. JWTトークンをデコードして検証
3. ペイロードから`user_id`を抽出
4. データベースからユーザー情報を取得
5. アクティブ状態・権限チェック

---

## パスワードハッシュ化

**実装場所**: `src/app/core/security/password.py`

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

### パスワード強度検証

**パスワード要件（必須）**:

- 最小8文字
- 大文字を1つ以上含む（A-Z）
- 小文字を1つ以上含む（a-z）
- 数字を1つ以上含む（0-9）

**推奨事項**:

- 特殊文字を1つ以上含む（!@#$%^&*(),.?":{}|<>）
- 12文字以上

```python
is_valid, error = validate_password_strength("password")
# → (False, "パスワードには大文字を含めてください")

is_valid, error = validate_password_strength("SecurePass123!")
# → (True, "")
```

---

## APIキー生成

**実装場所**: `src/app/core/security/api_key.py`

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

### APIキーのハッシュ化保存

**実装場所**: `src/app/models/sample_user.py`

```python
class SampleUser(Base):
    # APIキー（ハッシュ化して保存）
    api_key_hash: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None, index=True
    )
    api_key_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
```

**APIキー生成時のハッシュ化**（`src/app/api/routes/v1/sample_users.py`）:

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
    api_key=api_key,
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

- [セキュリティ概要](./README.md) - セキュリティ機能の全体像
- [リクエスト保護](./02-request-protection.md) - CORS、レート制限、入力バリデーション
- [データ保護](./03-data-protection.md) - データベース、ファイルアップロード
- [インフラストラクチャ](./04-infrastructure.md) - エラーハンドリング、環境設定
- [ベストプラクティス](./05-best-practices.md) - セキュリティ強化の推奨事項

---
