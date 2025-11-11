# 認証設計書（Authentication Design）

## 📋 文書管理情報

| 項目 | 内容 |
|------|------|
| **文書名** | 認証設計書（Authentication Design） |
| **バージョン** | 1.0.0 |
| **作成日** | 2025-01-11 |
| **最終更新日** | 2025-01-11 |
| **作成者** | Claude Code |
| **レビュー状態** | 初版 |

---

## 📑 目次

1. [概要](#1-概要)
2. [認証モード](#2-認証モード)
3. [Azure AD認証（本番環境）](#3-azure-ad認証本番環境)
4. [JWT開発モード認証](#4-jwt開発モード認証)
5. [パスワード認証（レガシー）](#5-パスワード認証レガシー)
6. [認証フロー](#6-認証フロー)
7. [トークン管理](#7-トークン管理)
8. [セキュリティ実装](#8-セキュリティ実装)
9. [エラーハンドリング](#9-エラーハンドリング)
10. [テスト戦略](#10-テスト戦略)
11. [付録](#11-付録)

---

## 1. 概要

### 1.1 目的

本設計書は、genai-app-docs（camp-backend）プロジェクトの認証・認可システムを文書化し、以下を達成することを目的とします：

- **認証方式の明確化**: Azure AD / JWT / パスワード認証の仕組みを説明
- **セキュリティ設計の文書化**: トークン管理、パスワードハッシュ化、検証フローを記録
- **実装ガイドの提供**: 開発者が認証機能を正しく実装・保守できるようにする
- **セキュリティ監査の支援**: 認証設計のレビューとセキュリティ評価を容易にする

### 1.2 適用範囲

本設計書は以下を対象とします：

- ✅ Azure AD認証（本番環境）
- ✅ JWT開発モード認証
- ✅ パスワード認証（レガシー・サンプル用）
- ✅ トークン生成・検証・ライフサイクル
- ✅ パスワードハッシュ化とセキュリティ

以下は**対象外**とし、別の設計書で詳述します：

- ❌ ロールベースアクセス制御（RBAC）の詳細 → [RBAC設計書](./01-rbac-design.md)
- ❌ APIエンドポイントのセキュリティ → [API設計書](../04-api/01-api-design.md)
- ❌ インフラレベルのセキュリティ → Infrastructure設計書

### 1.3 前提条件

本設計書を読むには以下の知識が推奨されます：

- **OAuth 2.0 / OpenID Connect**: 標準的な認証フロー
- **JWT（JSON Web Token）**: トークン構造とクレーム
- **bcrypt**: パスワードハッシュアルゴリズム
- **Azure AD**: Microsoftの認証プロバイダー

---

## 2. 認証モード

### 2.1 認証モード概要

本システムは、環境変数`AUTH_MODE`で認証方式を切り替えます。

```text
AUTH_MODE=development  →  JWT開発モード認証（モックトークン）
AUTH_MODE=production   →  Azure AD認証（本番環境）
```

### 2.2 認証モード比較表

| 項目 | 開発モード（development） | 本番モード（production） |
|------|------------------------|----------------------|
| **認証方式** | モックトークン（固定値） | Azure AD Bearer Token |
| **トークン検証** | 固定文字列比較 | JWT署名検証（Azure AD公開鍵） |
| **ユーザー情報** | 固定モックユーザー | Azure ADから取得 |
| **トークン有効期限** | なし（固定トークン） | 60分（Azure AD標準） |
| **セキュリティ** | ⚠️ 低（開発専用） | ✅ 高（エンタープライズ対応） |
| **設定要件** | DEV_MOCK_TOKEN | AZURE_TENANT_ID, AZURE_CLIENT_ID |

### 2.3 認証モード切り替え設定

**環境変数（`.env.local` / `.env.production`）**:

```bash
# 開発環境（.env.local）
AUTH_MODE=development
DEV_MOCK_TOKEN=mock-access-token-dev-12345
DEV_MOCK_USER_EMAIL=dev.user@example.com
DEV_MOCK_USER_OID=dev-azure-oid-12345
DEV_MOCK_USER_NAME=Development User

# 本番環境（.env.production）
AUTH_MODE=production
AZURE_TENANT_ID=your-azure-tenant-id
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret  # オプション
AZURE_OPENAPI_CLIENT_ID=your-swagger-ui-client-id
```

### 2.4 認証モードバリデーション

**本番環境での開発モード禁止**:

```python
@model_validator(mode="before")
@classmethod
def validate_dev_auth_not_in_production(cls, values: dict[str, Any]) -> dict[str, Any]:
    """本番環境で開発モード認証が有効な場合にエラーを発生させます。"""
    if values.get("ENVIRONMENT") == "production" and values.get("AUTH_MODE") == "development":
        raise ValueError(
            "Development authentication cannot be enabled in production environment. "
            "Set AUTH_MODE=production for production."
        )
    return values
```

**セキュリティポリシー**:

- ✅ `ENVIRONMENT=production` かつ `AUTH_MODE=development` は**禁止**
- ✅ 本番環境では必ず Azure AD認証を使用
- ✅ 開発環境でも Azure AD認証の使用を推奨（条件により）

---

## 3. Azure AD認証（本番環境）

### 3.1 Azure AD認証概要

**Azure AD認証**は、Microsoft Azure Active Directory（現: Microsoft Entra ID）を認証プロバイダーとして使用する、エンタープライズグレードの認証方式です。

**主要特性**:

- ✅ **シングルサインオン（SSO）**: 組織のIDで統一認証
- ✅ **多要素認証（MFA）**: Azure ADでMFA設定可能
- ✅ **トークンベース認証**: OAuth 2.0 / OpenID Connect標準準拠
- ✅ **自動トークンリフレッシュ**: fastapi-azure-authが管理
- ✅ **ロール管理**: Azure ADのアプリロールと連携

### 3.2 Azure AD認証アーキテクチャ

```mermaid
sequenceDiagram
    participant User as ユーザー<br/>（ブラウザ）
    participant Frontend as フロントエンド<br/>（React/Next.js）
    participant Backend as バックエンドAPI<br/>（FastAPI）
    participant AzureAD as Azure AD<br/>（認証プロバイダー）

    User->>Frontend: 1. ログインボタンクリック
    Frontend->>AzureAD: 2. OAuth 2.0認証リクエスト<br/>（Authorization Code Flow）
    AzureAD->>User: 3. ログイン画面表示
    User->>AzureAD: 4. 資格情報入力（email/password + MFA）
    AzureAD->>Frontend: 5. 認証コード返却
    Frontend->>AzureAD: 6. トークン交換<br/>（認証コード → Access Token）
    AzureAD->>Frontend: 7. Access Token + ID Token返却
    Frontend->>Backend: 8. API呼び出し<br/>（Authorization: Bearer {Access Token}）
    Backend->>AzureAD: 9. トークン検証<br/>（JWT署名 + クレーム検証）
    AzureAD->>Backend: 10. 公開鍵 + 検証結果
    Backend->>Backend: 11. ユーザー情報抽出<br/>（oid, email, name, roles）
    Backend->>Backend: 12. DBでユーザー検索/作成
    Backend->>Frontend: 13. APIレスポンス返却
```

### 3.3 Azure AD認証実装

**初期化（`core/security/azure_ad.py`）**:

```python
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer

# Azure AD認証スキーム（本番モードのみ初期化）
azure_scheme: SingleTenantAzureAuthorizationCodeBearer | None = None

if settings.AUTH_MODE == "production":
    azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
        app_client_id=settings.AZURE_CLIENT_ID,
        tenant_id=settings.AZURE_TENANT_ID,
        scopes={
            f"api://{settings.AZURE_CLIENT_ID}/access_as_user": "Access API as user",
        },
        allow_guest_users=False,
    )

async def initialize_azure_scheme():
    """Azure AD認証スキームを初期化（アプリ起動時に実行）。"""
    if settings.AUTH_MODE == "production" and azure_scheme:
        await azure_scheme.openid_config.load_config()
        print("✅ Azure AD authentication initialized")
```

**トークン検証（`core/security/azure_ad.py`）**:

```python
async def get_current_azure_user(
    user: Annotated[AzureUser, Security(get_azure_scheme_dependency, scopes=["access_as_user"])],
) -> AzureUser:
    """Azure ADから認証済みユーザーを取得（本番モードのみ）。

    トークン検証項目:
        - 署名検証: Azure ADの公開鍵による署名検証
        - 有効期限チェック: JWTの`exp`クレームの自動検証
        - 発行者検証: `iss`クレームがAzure ADテナントと一致するか確認
        - オーディエンス検証: `aud`クレームがアプリケーションクライアントIDと一致するか確認
        - スコープ検証: 要求されたスコープ（access_as_user）が含まれているか確認
    """
    if not user:
        raise HTTPException(status_code=401, detail="Azure AD authentication failed")
    return user
```

**ユーザーDB連携（`api/core/dependencies.py`）**:

```python
async def get_authenticated_user_from_azure(
    user_service: AzureUserServiceDep,
    azure_user: Any = Depends(
        get_current_azure_user if settings.AUTH_MODE == "production" else get_current_dev_user
    ),
) -> User:
    """Azure AD または開発モードから認証されたユーザーを取得し、DBのUserモデルと紐付け。"""
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

### 3.4 Azure AD トークンクレーム

**Access Token（JWT）の標準クレーム**:

```json
{
  "aud": "api://your-client-id",
  "iss": "https://login.microsoftonline.com/{tenant-id}/v2.0",
  "iat": 1704067200,
  "nbf": 1704067200,
  "exp": 1704070800,
  "aio": "...",
  "azp": "...",
  "azpacr": "0",
  "name": "John Doe",
  "oid": "12345678-1234-1234-1234-123456789012",
  "preferred_username": "john.doe@company.com",
  "rh": "...",
  "scp": "access_as_user",
  "sub": "...",
  "tid": "{tenant-id}",
  "uti": "...",
  "ver": "2.0"
}
```

**重要なクレーム説明**:

| クレーム | 説明 | 使用箇所 |
|---------|------|---------|
| `oid` | Azure Object ID（ユーザーの一意識別子） | DBのユーザー検索/作成キー |
| `preferred_username` | メールアドレス | ユーザー表示名 |
| `name` | フルネーム | ユーザー表示名 |
| `scp` | スコープ（access_as_user） | API権限検証 |
| `exp` | 有効期限（Unix timestamp） | トークン期限チェック |
| `aud` | オーディエンス（Client ID） | トークンの受取人検証 |

### 3.5 Swagger UI OAuth設定

**Swagger UIでAzure AD認証を使用**:

```python
# core/app_factory.py
swagger_ui_init_oauth = None
if settings.AUTH_MODE == "production":
    swagger_ui_init_oauth = {
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.AZURE_OPENAPI_CLIENT_ID,
        "scopes": f"api://{settings.AZURE_CLIENT_ID}/access_as_user",
    }

app = FastAPI(
    title=settings.APP_NAME,
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth=swagger_ui_init_oauth,
)
```

**Swagger UIでの認証手順**:

1. Swagger UI（`/docs`）を開く
2. 右上の「Authorize」ボタンをクリック
3. Azure ADログイン画面にリダイレクト
4. 認証後、Swagger UIに戻る
5. API呼び出し時に自動的にトークンを送信

---

## 4. JWT開発モード認証

### 4.1 開発モード認証概要

**JWT開発モード認証**は、開発環境で迅速にAPIテストを行うための簡易認証方式です。

**特性**:

- ✅ **固定トークン**: 環境変数`DEV_MOCK_TOKEN`で設定
- ✅ **モックユーザー**: 固定のユーザー情報（email, oid, name）
- ✅ **高速**: トークン検証が文字列比較のみ
- ⚠️ **セキュリティなし**: 本番環境では絶対に使用禁止

### 4.2 開発モード認証フロー

```mermaid
sequenceDiagram
    participant Client as クライアント<br/>（Postman/curl）
    participant Backend as バックエンドAPI<br/>（FastAPI）
    participant DevAuth as DevAuth<br/>（開発モック認証）
    participant DB as データベース

    Client->>Backend: 1. API呼び出し<br/>（Authorization: Bearer mock-access-token-dev-12345）
    Backend->>DevAuth: 2. get_current_dev_user()
    DevAuth->>DevAuth: 3. トークン比較<br/>（token == DEV_MOCK_TOKEN）
    alt トークン一致
        DevAuth->>Backend: 4. DevUserインスタンス返却
        Backend->>DB: 5. Azure OIDでユーザー検索/作成
        DB->>Backend: 6. Userモデル返却
        Backend->>Client: 7. APIレスポンス返却
    else トークン不一致
        DevAuth->>Client: 4. 401 Unauthorized
    end
```

### 4.3 開発モード認証実装

**DevUserクラス（`core/security/dev_auth.py`）**:

```python
class DevUser:
    """開発モード用のモックユーザークラス。

    Azure AD Userと互換性のある構造を持ちます。
    """

    def __init__(self):
        self.oid = settings.DEV_MOCK_USER_OID
        self.preferred_username = settings.DEV_MOCK_USER_EMAIL
        self.email = settings.DEV_MOCK_USER_EMAIL
        self.name = settings.DEV_MOCK_USER_NAME
        self.roles = []

    def __repr__(self):
        return f"<DevUser {self.email}>"
```

**トークン検証（`core/security/dev_auth.py`）**:

```python
async def get_current_dev_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> DevUser:
    """開発モード用の認証（トークンチェックのみ）。"""
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

### 4.4 開発モード使用例

**curlでの認証**:

```bash
# 正しいトークン
curl -H "Authorization: Bearer mock-access-token-dev-12345" \
     http://localhost:8000/api/v1/users/me

# レスポンス
{
  "id": "12345678-1234-1234-1234-123456789012",
  "email": "dev.user@example.com",
  "display_name": "Development User",
  "is_active": true
}
```

**Postmanでの認証**:

1. Authorizationタブ → Type: `Bearer Token`
2. Token: `mock-access-token-dev-12345`
3. Send

---

## 5. パスワード認証（レガシー）

### 5.1 パスワード認証概要

**パスワード認証**は、レガシー機能およびサンプルユーザー（`sample_users`テーブル）専用の認証方式です。

**現在の使用箇所**:

- ✅ `SampleUser` モデル（サンプル/デモ用）
- ✅ レガシー機能の互換性維持

**今後の方針**:

- ⚠️ 新規機能では使用しない
- ⚠️ 本番ユーザー（`User`モデル）はAzure AD認証のみ

### 5.2 パスワードハッシュ化（bcrypt + SHA-256）

**ハッシュ化アルゴリズム**:

```python
def hash_password(password: str) -> str:
    """平文パスワードをbcryptアルゴリズムでハッシュ化します。"""
    # bcryptの72バイト制限に対処するため、SHA-256で事前ハッシュ化
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # bcrypt.hashpw()でハッシュ化（コスト: 12ラウンド）
    hashed = bcrypt.hashpw(password_hash.encode("utf-8"), bcrypt.gensalt())

    return hashed.decode("utf-8")
```

**ハッシュ化の特性**:

| 項目 | 詳細 |
|------|------|
| **アルゴリズム** | bcrypt（コスト: 12ラウンド） |
| **Salt** | ランダム生成（bcrypt自動） |
| **事前ハッシュ** | SHA-256（bcryptの72バイト制限対応） |
| **出力形式** | `$2b$12$[salt][hash]` (約60文字) |
| **セキュリティ** | レインボーテーブル攻撃耐性、ブルートフォース耐性 |

**bcrypt + SHA-256の理由**:

1. **bcryptの72バイト制限**: bcryptは72バイトを超えるパスワードを切り捨てる
2. **マルチバイト文字対応**: 日本語などのマルチバイト文字を正しく処理
3. **長いパスワード対応**: 任意の長さのパスワードを安全に処理
4. **SHA-256**: 常に64文字（64バイト < 72バイト）の16進数文字列を生成

### 5.3 パスワード検証

**検証処理**:

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュ化されたパスワードを照合します。"""
    # bcryptの72バイト制限に対処するため、SHA-256で事前ハッシュ化
    password_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()

    # bcrypt.checkpw()は定時間比較（タイミング攻撃対策）
    return bcrypt.checkpw(
        password_hash.encode("utf-8"),
        hashed_password.encode("utf-8")
    )
```

**セキュリティ特性**:

- ✅ **定時間比較**: タイミング攻撃対策
- ✅ **Salt自動処理**: bcryptがhash内のsaltを自動抽出
- ✅ **ハッシュ形式自動検出**: `$2b$`プレフィックスで検出

### 5.4 パスワード強度検証

**パスワード要件**:

```python
def validate_password_strength(password: str) -> tuple[bool, str]:
    """パスワードの強度を検証します。

    必須要件:
        - 最小8文字
        - 大文字を1つ以上含む（A-Z）
        - 小文字を1つ以上含む（a-z）
        - 数字を1つ以上含む（0-9）

    推奨要件:
        - 特殊文字を1つ以上含む（!@#$%^&*(),.?":{}|<>）
    """
    if len(password) < 8:
        return False, "パスワードは8文字以上である必要があります"

    if not re.search(r"[A-Z]", password):
        return False, "パスワードには大文字を含めてください"

    if not re.search(r"[a-z]", password):
        return False, "パスワードには小文字を含めてください"

    if not re.search(r"\d", password):
        return False, "パスワードには数字を含めてください"

    return True, ""
```

---

## 6. 認証フロー

### 6.1 認証フロー全体像

```mermaid
graph TB
    Start[APIリクエスト]

    Start --> CheckAuthMode{AUTH_MODE?}

    CheckAuthMode -->|development| DevAuth[開発モード認証]
    CheckAuthMode -->|production| AzureAuth[Azure AD認証]

    DevAuth --> DevTokenCheck{トークン一致?}
    DevTokenCheck -->|Yes| DevUser[DevUserインスタンス]
    DevTokenCheck -->|No| Unauthorized1[401 Unauthorized]

    AzureAuth --> AzureTokenValidation[Azure ADトークン検証<br/>署名・有効期限・クレーム]
    AzureTokenValidation --> AzureTokenValid{検証成功?}
    AzureTokenValid -->|Yes| AzureUser[AzureUserインスタンス]
    AzureTokenValid -->|No| Unauthorized2[401 Unauthorized]

    DevUser --> DBLookup[DBでユーザー検索<br/>Azure OID]
    AzureUser --> DBLookup

    DBLookup --> UserExists{ユーザー存在?}
    UserExists -->|Yes| UpdateUser[ユーザー情報更新<br/>email, display_name]
    UserExists -->|No| CreateUser[ユーザー作成<br/>azure_oid, email, roles]

    UpdateUser --> CheckActive{is_active?}
    CreateUser --> CheckActive

    CheckActive -->|Yes| Success[認証成功<br/>Userモデル返却]
    CheckActive -->|No| Forbidden[400 Inactive user]

    Success --> APILogic[APIロジック実行]
    APILogic --> Response[レスポンス返却]

    style Start fill:#e3f2fd
    style Success fill:#c8e6c9
    style Unauthorized1 fill:#ffccbc
    style Unauthorized2 fill:#ffccbc
    style Forbidden fill:#ffccbc
```

### 6.2 Azure AD認証フロー詳細

```mermaid
sequenceDiagram
    participant Client as クライアント
    participant API as FastAPI
    participant Middleware as Middleware<br/>（SecurityHeaders,<br/>RateLimit, Logging）
    participant Depends as Depends<br/>（DI）
    participant AzureAuth as Azure AD<br/>認証モジュール
    participant AzureAD as Azure AD<br/>（Microsoft）
    participant UserSvc as UserService
    participant DB as Database

    Client->>API: 1. API呼び出し<br/>（Authorization: Bearer {token}）

    API->>Middleware: 2. ミドルウェア通過<br/>（CORS, Rate Limit, Logging）

    Middleware->>Depends: 3. 依存性注入<br/>（CurrentUserAzureDep）

    Depends->>AzureAuth: 4. get_current_azure_user()

    AzureAuth->>AzureAuth: 5. トークン抽出<br/>（Bearer {token}）

    AzureAuth->>AzureAD: 6. トークン検証<br/>（JWT署名、exp、iss、aud、scp）

    alt トークン有効
        AzureAD->>AzureAuth: 7. 検証成功 + ユーザー情報<br/>（oid, email, name, roles）

        AzureAuth->>Depends: 8. AzureUserインスタンス

        Depends->>UserSvc: 9. get_or_create_by_azure_oid()

        UserSvc->>DB: 10. SELECT * FROM users<br/>WHERE azure_oid = ?

        alt ユーザー存在
            DB->>UserSvc: 11. Userモデル返却
            UserSvc->>UserSvc: 12. ユーザー情報更新<br/>（email, display_name）
        else ユーザー未存在
            UserSvc->>DB: 11. INSERT INTO users<br/>（azure_oid, email, roles）
            DB->>UserSvc: 12. 新規Userモデル返却
        end

        UserSvc->>DB: 13. COMMIT

        UserSvc->>Depends: 14. Userモデル

        Depends->>API: 15. 認証済みユーザー

        API->>Client: 16. APIレスポンス
    else トークン無効
        AzureAD->>AzureAuth: 7. 検証失敗<br/>（期限切れ/署名不正/スコープ不足）
        AzureAuth->>Client: 8. 401 Unauthorized
    end
```

---

## 7. トークン管理

### 7.1 JWT構造

**JWT（JSON Web Token）の構造**:

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzA0MDcwODAwLCJpYXQiOjE3MDQwNjcyMDAsInR5cGUiOiJhY2Nlc3MifQ.signature

↑ Header                        ↑ Payload                                                              ↑ Signature
```

**Header（ヘッダー）**:

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload（ペイロード）**:

```json
{
  "sub": "1",
  "exp": 1704070800,
  "iat": 1704067200,
  "type": "access"
}
```

**Signature（署名）**:

```text
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  SECRET_KEY
)
```

### 7.2 JWTトークン生成

**アクセストークン生成（`core/security/jwt.py`）**:

```python
def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """JWTアクセストークンを生成します。"""
    to_encode = data.copy()

    # 有効期限設定（デフォルト: 30分）
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    })

    # JWT生成（HS256アルゴリズム）
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt
```

**使用例**:

```python
# ユーザーID 1 のトークン生成
token = create_access_token({"sub": "1"})

# カスタム有効期限（1時間）
token = create_access_token(
    {"sub": "1", "role": "admin"},
    expires_delta=timedelta(hours=1)
)
```

### 7.3 JWTトークン検証

**トークンデコード（`core/security/jwt.py`）**:

```python
def decode_access_token(token: str) -> dict[str, Any] | None:
    """JWTアクセストークンをデコードし、検証します。"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,      # 有効期限検証
                "verify_signature": True,  # 署名検証
            },
        )

        # subフィールドの存在確認
        if "sub" not in payload:
            logger.warning("JWTトークン検証失敗", reason="sub_field_missing")
            return None

        return payload

    except ExpiredSignatureError:
        logger.warning("JWTトークン有効期限切れ")
        return None
    except JWTError as e:
        logger.warning("JWTデコードエラー", error_type=type(e).__name__)
        return None
```

### 7.4 リフレッシュトークン

**リフレッシュトークン生成**:

```python
def create_refresh_token(data: dict[str, Any]) -> str:
    """リフレッシュトークンを生成します（有効期限: 7日間）。"""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt
```

**リフレッシュフロー**:

```mermaid
sequenceDiagram
    participant Client as クライアント
    participant API as /auth/refresh
    participant JWT as JWT Module
    participant DB as Database

    Client->>API: 1. リフレッシュリクエスト<br/>（refresh_token）
    API->>JWT: 2. decode_refresh_token()
    JWT->>JWT: 3. トークン検証<br/>（署名、有効期限、type="refresh"）

    alt トークン有効
        JWT->>API: 4. ペイロード返却<br/>（sub, exp, type）
        API->>DB: 5. ユーザー存在確認<br/>（user_id = payload["sub"]）
        DB->>API: 6. Userモデル返却
        API->>JWT: 7. create_access_token()<br/>（新しいアクセストークン生成）
        JWT->>API: 8. 新しいアクセストークン
        API->>Client: 9. レスポンス<br/>{"access_token": "...", "token_type": "bearer"}
    else トークン無効
        JWT->>API: 4. None返却
        API->>Client: 5. 401 Unauthorized
    end
```

---

## 8. セキュリティ実装

### 8.1 セキュリティ要件

| 要件 | 実装状況 | 対策内容 |
|------|---------|---------|
| **認証強度** | ✅ 実装済み | Azure AD（MFA対応）、bcrypt（コスト: 12） |
| **トークン有効期限** | ✅ 実装済み | Access Token: 60分、Refresh Token: 7日 |
| **トークン検証** | ✅ 実装済み | JWT署名検証、有効期限チェック、クレーム検証 |
| **パスワードハッシュ** | ✅ 実装済み | bcrypt + SHA-256（72バイト制限対応） |
| **タイミング攻撃対策** | ✅ 実装済み | bcrypt.checkpw（定時間比較） |
| **HTTPS必須** | ⚠️ 要設定 | 本番環境ではHTTPSリバースプロキシ必須 |
| **CORS制限** | ✅ 実装済み | 本番環境では厳格なALLOWED_ORIGINS |
| **レート制限** | ✅ 実装済み | 100req/min（RateLimitMiddleware） |

### 8.2 SECRET_KEY管理

**SECRET_KEYの要件**:

```python
SECRET_KEY: str = Field(
    default="dev-secret-key-change-in-production-must-be-32-chars-minimum",
    min_length=32,
    description="Must be set in production. Generate with: openssl rand -hex 32",
)
```

**生成方法**:

```bash
# OpenSSLで生成（推奨）
openssl rand -hex 32
# 出力例: 3f8b2e4d7c1a9b6f5e3d8c2a1b9f7e6d...

# Pythonで生成
python -c "import secrets; print(secrets.token_hex(32))"
```

**セキュリティポリシー**:

- ✅ 本番環境では必ず32文字以上のランダム文字列を使用
- ✅ 環境変数（`.env.production`）で設定
- ✅ Gitにコミットしない（`.gitignore`に追加）
- ✅ 定期的にローテーション（90日ごと推奨）

### 8.3 本番環境セキュリティチェックリスト

**起動時バリデーション（`core/config.py`）**:

```python
def _validate_security_settings(self) -> None:
    """セキュリティ設定のバリデーション。"""
    # 本番環境でのSECRET_KEYチェック
    if self.ENVIRONMENT == "production":
        if not self.SECRET_KEY or "dev-secret-key" in self.SECRET_KEY:
            raise ValueError(
                "本番環境ではSECRET_KEYを設定する必要があります。"
                "生成方法: openssl rand -hex 32"
            )

def _validate_azure_ad_config(self) -> None:
    """Azure AD設定のバリデーション。"""
    if self.AUTH_MODE == "production":
        if not self.AZURE_TENANT_ID:
            raise ValueError("AUTH_MODE=productionの場合、AZURE_TENANT_IDが必要です")
        if not self.AZURE_CLIENT_ID:
            raise ValueError("AUTH_MODE=productionの場合、AZURE_CLIENT_IDが必要です")
```

**本番環境チェックリスト**:

- [ ] `SECRET_KEY`が32文字以上のランダム文字列
- [ ] `AUTH_MODE=production`
- [ ] `AZURE_TENANT_ID`が設定されている
- [ ] `AZURE_CLIENT_ID`が設定されている
- [ ] `ALLOWED_ORIGINS`が明示的に設定されている（ワイルドカード禁止）
- [ ] `DEBUG=False`
- [ ] `HTTPS`が有効化されている（リバースプロキシ）
- [ ] セキュリティヘッダー（HSTS, X-Frame-Options, X-Content-Type-Options）が有効

### 8.4 ログイン試行制限（今後の実装）

**現在の状態**: 未実装（将来の拡張予定）

**実装案**:

```python
# 設定（core/config.py）
MAX_LOGIN_ATTEMPTS: int = 5
ACCOUNT_LOCK_DURATION_HOURS: int = 1

# ロックアウトロジック
async def check_login_attempts(user_id: uuid.UUID) -> None:
    """ログイン試行回数をチェックします。"""
    # Redisで試行回数をカウント
    key = f"login_attempts:{user_id}"
    attempts = await redis.get(key) or 0

    if int(attempts) >= settings.MAX_LOGIN_ATTEMPTS:
        raise AuthenticationError("アカウントがロックされています。1時間後に再試行してください。")

async def increment_login_attempts(user_id: uuid.UUID) -> None:
    """ログイン試行回数をインクリメントします。"""
    key = f"login_attempts:{user_id}"
    await redis.incr(key)
    await redis.expire(key, settings.ACCOUNT_LOCK_DURATION_HOURS * 3600)
```

---

## 9. エラーハンドリング

### 9.1 認証エラーコード

| HTTPステータス | エラーコード | 説明 | 発生箇所 |
|--------------|------------|------|---------|
| 401 Unauthorized | `INVALID_TOKEN` | トークンが無効または期限切れ | Azure AD検証、JWT検証 |
| 401 Unauthorized | `MISSING_AUTHORIZATION` | Authorizationヘッダーが存在しない | Depends |
| 401 Unauthorized | `INVALID_CREDENTIALS` | パスワードが一致しない | パスワード認証 |
| 401 Unauthorized | `EXPIRED_TOKEN` | トークンが期限切れ | JWT検証 |
| 403 Forbidden | `INSUFFICIENT_SCOPE` | 必要なスコープが不足 | Azure AD検証 |
| 403 Forbidden | `INSUFFICIENT_PERMISSION` | 権限不足 | RBAC |
| 400 Bad Request | `INACTIVE_USER` | ユーザーが無効化されている | is_active=False |
| 404 Not Found | `USER_NOT_FOUND` | ユーザーが見つからない | DB検索失敗 |

### 9.2 エラーレスポンス形式

**標準エラーレスポンス**:

```json
{
  "detail": "Invalid or expired token",
  "error_code": "INVALID_TOKEN",
  "timestamp": "2025-01-11T12:00:00Z"
}
```

**実装（`core/exceptions.py`）**:

```python
class AuthenticationError(Exception):
    """認証エラー。"""
    def __init__(self, message: str, error_code: str = "AUTHENTICATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

# 例外ハンドラー（api/core/exception_handlers.py）
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
```

### 9.3 ログ記録

**認証ログ記録（structlog）**:

```python
# 成功ログ
logger.info(
    "ユーザー認証成功",
    user_id=str(user.id),
    email=user.email,
    auth_mode=settings.AUTH_MODE,
)

# 失敗ログ
logger.warning(
    "認証失敗",
    reason="invalid_token",
    auth_mode=settings.AUTH_MODE,
    ip_address=request.client.host,
)
```

---

## 10. テスト戦略

### 10.1 単体テスト

**Azure AD認証のモック**:

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_azure_user():
    """モックAzure ADユーザー。"""
    user = Mock()
    user.oid = "test-azure-oid-12345"
    user.email = "test@example.com"
    user.name = "Test User"
    user.preferred_username = "test@example.com"
    user.roles = ["user"]
    return user

@pytest.mark.asyncio
async def test_get_authenticated_user_from_azure(mock_azure_user, db_session):
    """Azure AD認証ユーザーのDB連携をテストします。"""
    user_service = UserService(db_session)

    # Azure ADユーザーをモック
    with patch("app.core.security.azure_ad.get_current_azure_user", return_value=mock_azure_user):
        user = await get_authenticated_user_from_azure(user_service, mock_azure_user)

        assert user.azure_oid == "test-azure-oid-12345"
        assert user.email == "test@example.com"
```

**JWT検証テスト**:

```python
def test_create_and_decode_access_token():
    """JWTトークンの生成とデコードをテストします。"""
    # トークン生成
    token = create_access_token({"sub": "1", "role": "admin"})

    # トークンデコード
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"

def test_decode_expired_token():
    """有効期限切れトークンの検証をテストします。"""
    # 有効期限が過去のトークン生成
    token = create_access_token(
        {"sub": "1"},
        expires_delta=timedelta(seconds=-1)
    )

    # トークンデコード（失敗するはず）
    payload = decode_access_token(token)
    assert payload is None
```

**パスワードハッシュ化テスト**:

```python
def test_hash_and_verify_password():
    """パスワードのハッシュ化と検証をテストします。"""
    password = "SecurePass123!"

    # ハッシュ化
    hashed = hash_password(password)

    # 検証成功
    assert verify_password(password, hashed) is True

    # 検証失敗（間違ったパスワード）
    assert verify_password("WrongPass123!", hashed) is False
```

### 10.2 統合テスト

**E2Eテスト（Postman/Newman）**:

```json
{
  "info": {
    "name": "Authentication Tests",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Dev Mode Authentication",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer mock-access-token-dev-12345"
          }
        ],
        "url": "{{base_url}}/api/v1/users/me"
      },
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test('Status code is 200', function () {",
              "    pm.response.to.have.status(200);",
              "});",
              "pm.test('User email is correct', function () {",
              "    var jsonData = pm.response.json();",
              "    pm.expect(jsonData.email).to.eql('dev.user@example.com');",
              "});"
            ]
          }
        }
      ]
    }
  ]
}
```

---

## 11. 付録

### 11.1 関連ファイル一覧

#### 認証モジュール

| ファイル | 説明 |
|---------|------|
| `src/app/core/security/azure_ad.py` | Azure AD認証実装 |
| `src/app/core/security/dev_auth.py` | 開発モード認証実装 |
| `src/app/core/security/jwt.py` | JWT生成・検証 |
| `src/app/core/security/password.py` | パスワードハッシュ化・検証 |
| `src/app/api/core/dependencies.py` | 認証依存性注入定義 |

#### 設定ファイル

| ファイル | 説明 |
|---------|------|
| `.env.local.example` | 開発環境設定テンプレート |
| `.env.production.example` | 本番環境設定テンプレート |
| `src/app/core/config.py` | 設定管理 |

### 11.2 参考リンク

#### 公式ドキュメント

- [Azure AD Documentation](https://learn.microsoft.com/en-us/azure/active-directory/)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [OpenID Connect Specification](https://openid.net/connect/)
- [JWT Specification (RFC 7519)](https://datatracker.ietf.org/doc/html/rfc7519)
- [fastapi-azure-auth](https://github.com/Intility/fastapi-azure-auth)
- [python-jose](https://github.com/mpdavis/python-jose)
- [bcrypt](https://pypi.org/project/bcrypt/)

#### セキュリティベストプラクティス

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [NIST Digital Identity Guidelines](https://pages.nist.gov/800-63-3/)

### 11.3 用語集

| 用語 | 説明 |
|------|------|
| **JWT** | JSON Web Token（JSONベースのトークン形式） |
| **Bearer Token** | Authorization: Bearer {token} 形式の認証トークン |
| **OAuth 2.0** | 認可フレームワーク（標準規格） |
| **OpenID Connect** | OAuth 2.0上の認証レイヤー |
| **Azure AD** | Microsoft Azure Active Directory（現: Microsoft Entra ID） |
| **oid** | Azure Object ID（ユーザーの一意識別子） |
| **bcrypt** | パスワードハッシュアルゴリズム |
| **Salt** | ハッシュ化時に追加するランダムデータ |
| **MFA** | Multi-Factor Authentication（多要素認証） |
| **SSO** | Single Sign-On（シングルサインオン） |

### 11.4 クロスリファレンス

本設計書に関連する他の設計書：

| 設計書 | リンク | 関連箇所 |
|-------|--------|---------|
| **RBAC設計書** | [01-rbac-design.md](./01-rbac-design.md) | ロール管理、権限チェック |
| **System設計書** | [01-system-design.md](../01-architecture/01-system-design.md) | 依存性注入、ライフサイクル管理 |
| **API設計書** | [01-api-design.md](../04-api/01-api-design.md) | 認証エンドポイント、エラーレスポンス |

### 11.5 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-01-11 | 初版作成 | Claude Code |

---

**最終更新**: 2025-01-11
**管理者**: Claude Code
**レビュー状態**: 初版
