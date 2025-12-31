# 認証・認可設計書

## 1. 概要

本文書は、genai-app-docsシステムの認証（Authentication）および認可（Authorization）設計を定義します。
システムは環境に応じて認証方式を切り替え、柔軟かつセキュアな運用を実現します。

### 1.1 認証・認可の設計方針

- **マルチモード認証**: 開発モード（モックトークン） / 本番モード（Azure AD）
- **エンタープライズ認証**: Azure AD統合によるSSO対応
- **JWT標準準拠**: RFC 7519準拠のJWT実装
- **ゼロトラスト原則**: すべてのリクエストで認証・認可を実施

---

## 2. 認証方式の全体像

### 2.1 認証モード切り替え

::: mermaid
graph TB
    Start[アプリケーション起動]
    Start --> Config{AUTH_MODE環境変数}

    Config -->|development| DevMode[開発モード]
    Config -->|production| ProdMode[本番モード]

    DevMode --> DevAuth[モックトークン認証<br/>dev_auth.py]
    ProdMode --> AzureAuth[Azure AD認証<br/>azure_ad.py]

    DevAuth --> MockToken[固定トークン<br/>DEV_MOCK_TOKEN]
    DevAuth --> MockUser[モックユーザー<br/>DEV_MOCK_USER_EMAIL]

    AzureAuth --> JWT[JWT検証<br/>RS256署名]
    AzureAuth --> AzureAD[Azure AD<br/>OpenID Connect]

    MockToken --> GetUser[UserAccount取得/作成]
    JWT --> GetUser

    GetUser --> Authz[認可チェック<br/>RBAC]
    Authz --> Endpoint[エンドポイント処理]

    style DevMode fill:#FFF9C4
    style ProdMode fill:#C5E1A5
    style DevAuth fill:#FFE082
    style AzureAuth fill:#AED581
:::

### 2.2 認証モード比較

| 項目 | 開発モード | 本番モード |
|------|----------|-----------|
| **実装ファイル** | `src/app/core/security/dev_auth.py` | `src/app/core/security/azure_ad.py` |
| **認証方式** | 固定トークン文字列照合 | Azure AD JWT検証 |
| **トークン形式** | `Bearer mock-access-token-dev-12345` | `Bearer <Azure_AD_JWT>` |
| **トークン検証** | 文字列一致のみ | JWT署名・有効期限・発行者検証 |
| **ユーザー識別** | モックメールアドレス | Azure AD Object ID (azure_oid) |
| **設定環境変数** | `DEV_MOCK_TOKEN`  `DEV_MOCK_USER_EMAIL` | `AZURE_TENANT_ID`  `AZURE_CLIENT_ID`  `AZURE_CLIENT_SECRET` |
| **セキュリティレベル** | ⚠️ 低（開発専用） | ✅ 高（エンタープライズ級） |
| **使用環境** | ローカル開発 | ステージング、本番 |

---

## 3. 開発モード認証

### 3.1 開発モード認証フロー

::: mermaid
sequenceDiagram
    participant Client
    participant API
    participant DevAuth as dev_auth.py
    participant UserService
    participant DB

    Client->>API: Request<br/>Authorization: Bearer mock-access-token-dev-12345

    API->>DevAuth: トークン検証
    DevAuth->>DevAuth: token == DEV_MOCK_TOKEN?

    alt トークン一致
        DevAuth->>UserService: get_or_create_by_email()
        UserService->>DB: SELECT users WHERE email = ?
        alt ユーザー存在
            DB-->>UserService: UserAccount
        else ユーザー未存在
            UserService->>DB: INSERT INTO users
            DB-->>UserService: 新規UserAccount
        end
        UserService-->>DevAuth: UserAccount
        DevAuth-->>API: current_user
        API->>API: RBAC認可チェック
        API-->>Client: 200 OK
    else トークン不一致
        DevAuth-->>API: 401 Unauthorized
        API-->>Client: 401 Unauthorized
    end
:::

### 3.2 実装詳細

**実装**: `src/app/core/security/dev_auth.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.models.user_account import UserAccount

security = HTTPBearer()

async def dev_token_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """開発モード用トークン検証"""

    token = credentials.credentials

    # 固定トークンとの比較
    if token != settings.DEV_MOCK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mock token"
        )

    return token

async def get_current_user_dev(
    token: str = Depends(dev_token_auth),
    db: AsyncSession = Depends(get_db)
) -> UserAccount:
    """開発モード用ユーザー取得"""

    # モックユーザーメールアドレスを使用
    email = settings.DEV_MOCK_USER_EMAIL

    # ユーザー取得または作成
    user = await user_service.get_or_create_by_email(
        db,
        email=email,
        display_name="Development User",
        system_role=SystemUserRole.SYSTEM_ADMIN  # 開発時は管理者権限
    )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    return user
:::

### 3.3 環境変数設定

**.env.local:**

```bash
# 認証モード
AUTH_MODE=development

# 開発モード設定
DEV_MOCK_TOKEN=mock-access-token-dev-12345
DEV_MOCK_USER_EMAIL=dev.user@example.com
```

### 3.4 開発モードの利点

✅ **セットアップ不要**: Azure AD設定なしで即座に開発開始
✅ **高速テスト**: トークン取得プロセスのスキップ
✅ **オフライン開発**: インターネット接続不要
✅ **簡易デバッグ**: 認証エラーの除外

⚠️ **注意**: 本番環境では絶対に使用しないこと

---

## 4. 本番モード認証（Azure AD）

### 4.1 Azure AD認証フロー

::: mermaid
sequenceDiagram
    participant User
    participant Browser
    participant AzureAD as Azure AD
    participant API
    participant AzureAuthLib as azure_ad.py
    participant UserService
    participant DB

    User->>Browser: ログイン要求
    Browser->>AzureAD: Authorization Code Flow開始

    AzureAD->>AzureAD: ユーザー認証<br/>（MFA等）
    AzureAD-->>Browser: Authorization Code

    Browser->>AzureAD: トークン要求<br/>（Authorization Code）
    AzureAD-->>Browser: Access Token (JWT)<br/>Refresh Token

    Browser->>API: API Request<br/>Authorization: Bearer <JWT>

    API->>AzureAuthLib: JWT検証
    AzureAuthLib->>AzureAD: 公開鍵取得<br/>（JWKS Endpoint）
    AzureAD-->>AzureAuthLib: 公開鍵

    AzureAuthLib->>AzureAuthLib: JWT署名検証<br/>（RS256）
    AzureAuthLib->>AzureAuthLib: 有効期限検証<br/>（exp claim）
    AzureAuthLib->>AzureAuthLib: 発行者検証<br/>（iss claim）
    AzureAuthLib->>AzureAuthLib: オーディエンス検証<br/>（aud claim）

    alt JWT有効
        AzureAuthLib->>AzureAuthLib: azure_oid抽出
        AzureAuthLib->>UserService: get_or_create_by_azure_oid()
        UserService->>DB: SELECT users WHERE azure_oid = ?
        alt ユーザー存在
            DB-->>UserService: UserAccount
        else 初回ログイン
            UserService->>DB: INSERT INTO users
            DB-->>UserService: 新規UserAccount
        end
        UserService-->>AzureAuthLib: UserAccount
        AzureAuthLib-->>API: current_user
        API->>API: RBAC認可チェック
        API-->>Browser: 200 OK + Data
    else JWT無効
        AzureAuthLib-->>API: 401 Unauthorized
        API-->>Browser: 401 Unauthorized
    end
:::

### 4.2 JWT構造

**JWT Header:**

```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "key-id-from-azure"
}
:::

**JWT Payload（Claims）:**

```json
{
  "iss": "https://login.microsoftonline.com/{tenant_id}/v2.0",
  "aud": "{client_id}",
  "exp": 1705324800,
  "iat": 1705321200,
  "nbf": 1705321200,
  "sub": "user-subject-id",
  "oid": "12345678-1234-1234-1234-123456789abc",
  "email": "user@example.com",
  "name": "山田 太郎",
  "preferred_username": "user@example.com",
  "scp": "user_impersonation",
  "tid": "{tenant_id}"
}
```

**重要なClaim:**

| Claim | 説明 | 用途 |
|-------|------|------|
| **oid** | Azure AD Object ID | ユーザー一意識別子（主キー相当） |
| **email** | メールアドレス | 表示用、通知用 |
| **name** | 表示名 | UI表示用 |
| **exp** | 有効期限（UNIXタイムスタンプ） | トークン失効判定 |
| **iss** | 発行者 | Azure AD検証 |
| **aud** | オーディエンス | アプリケーション検証 |
| **scp** | スコープ | 権限範囲 |

### 4.3 実装詳細

**実装**: `src/app/core/security/azure_ad.py`

```python
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from app.core.config import settings

# Azure AD認証スキーム
azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.AZURE_CLIENT_ID,
    tenant_id=settings.AZURE_TENANT_ID,
    scopes={
        f"api://{settings.AZURE_CLIENT_ID}/user_impersonation": "User impersonation"
    },
    auto_error=True
)

async def get_current_user_azure(
    auth_token = Depends(azure_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserAccount:
    """Azure AD認証済みユーザー取得"""

    # azure_oid（Azure AD Object ID）を取得
    azure_oid = auth_token.claims.get("oid")
    email = auth_token.claims.get("email")
    name = auth_token.claims.get("name")

    if not azure_oid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing oid claim"
        )

    # ユーザー取得または作成
    user = await user_service.get_or_create_by_azure_oid(
        db,
        azure_oid=azure_oid,
        email=email,
        display_name=name,
        system_role=SystemUserRole.USER  # デフォルトは一般ユーザー
    )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    # 最終ログイン日時更新
    await user_service.update_last_login(db, user.id)

    return user
```

### 4.4 Azure AD設定

**.env.production:**

```bash
# 認証モード
AUTH_MODE=production

# Azure AD設定
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789abc
AZURE_CLIENT_ID=87654321-4321-4321-4321-cba987654321
AZURE_CLIENT_SECRET=your-client-secret-here

# Azure AD エンドポイント（自動設定）
# https://login.microsoftonline.com/{AZURE_TENANT_ID}/v2.0
```

**Azure AD App Registration設定:**

1. **Authentication**:
   - Redirect URIs: `http://localhost:8000/oauth2/callback` (開発)
   - Redirect URIs: `https://your-domain.com/oauth2/callback` (本番)
   - Implicit grant: ID tokens, Access tokens

2. **API permissions**:
   - Microsoft Graph: `User.Read` (委任)
   - API: `api://{CLIENT_ID}/user_impersonation` (委任)

3. **Expose an API**:
   - Application ID URI: `api://{CLIENT_ID}`
   - Scopes: `user_impersonation`

### 4.5 JWT検証プロセス

::: mermaid
graph TB
    Start[JWT受信] --> Step1[1. Header解析]
    Step1 --> Step2[2. 署名検証<br/>RS256 with Azure公開鍵]
    Step2 --> Step3[3. 有効期限検証<br/>exp > 現在時刻?]
    Step3 --> Step4[4. 発行者検証<br/>iss == Azure AD?]
    Step4 --> Step5[5. オーディエンス検証<br/>aud == CLIENT_ID?]
    Step5 --> Step6[6. Claims抽出<br/>oid, email, name]
    Step6 --> Success[✅ 検証成功]

    Step2 -->|署名無効| Fail[❌ 401 Unauthorized]
    Step3 -->|期限切れ| Fail
    Step4 -->|発行者不一致| Fail
    Step5 -->|オーディエンス不一致| Fail

    style Success fill:#4CAF50
    style Fail fill:#F44336
:::

**検証項目詳細:**

1. **署名検証（RS256）**:
   - Azure ADの公開鍵（JWKS Endpoint）を使用
   - 署名改ざん検知
   - 実装: `fastapi-azure-auth`が自動実行

2. **有効期限検証（exp）**:
   - `exp` claim > 現在時刻（UNIX timestamp）
   - タイムゾーン: UTC
   - 有効期限: デフォルト1時間

3. **発行者検証（iss）**:
   - `iss` == `https://login.microsoftonline.com/{tenant_id}/v2.0`
   - テナント検証

4. **オーディエンス検証（aud）**:
   - `aud` == `{AZURE_CLIENT_ID}`
   - トークンの対象アプリケーション確認

5. **スコープ検証（scp）**:
   - `scp` に `user_impersonation` が含まれるか

---

## 5. ユーザー自動作成

### 5.1 初回ログイン時のユーザー作成

::: mermaid
sequenceDiagram
    participant AzureAD
    participant API
    participant UserService
    participant DB

    AzureAD->>API: JWT (初回ログインユーザー)
    API->>UserService: get_or_create_by_azure_oid()

    UserService->>DB: SELECT * FROM users<br/>WHERE azure_oid = ?
    DB-->>UserService: NULL（未存在）

    UserService->>UserService: ユーザー情報準備<br/>email, display_name, system_role

    UserService->>DB: INSERT INTO users<br/>(azure_oid, email, display_name,<br/>system_role=USER, is_active=TRUE)
    DB-->>UserService: 新規UserAccount

    UserService->>DB: UPDATE users<br/>SET last_login = NOW()<br/>WHERE id = ?

    UserService-->>API: UserAccount
    API-->>AzureAD: 200 OK
:::

### 5.2 実装

**実装**: `src/app/services/user_account/user_account/` ディレクトリ（Facadeパターン）

- `__init__.py` - UserAccountService（Facade）
- `auth.py` - UserAccountAuthService（認証関連操作）
- `crud.py` - UserAccountCrudService（CRUD操作）

```python
async def get_or_create_by_azure_oid(
    self,
    db: AsyncSession,
    azure_oid: str,
    email: str,
    display_name: str | None = None,
    system_role: SystemUserRole = SystemUserRole.USER
) -> UserAccount:
    """Azure AD Object IDでユーザー取得または作成"""

    # 既存ユーザー検索
    user = await self.repo.get_by_azure_oid(db, azure_oid)

    if user:
        # 既存ユーザーの場合、情報更新（email/display_name変更対応）
        if user.email != email or user.display_name != display_name:
            user = await self.repo.update(
                db,
                db_obj=user,
                email=email,
                display_name=display_name
            )
        return user

    # 新規ユーザー作成
    user = await self.repo.create(
        db,
        azure_oid=azure_oid,
        email=email,
        display_name=display_name or email,
        system_role=system_role,
        is_active=True
    )

    await db.commit()

    logger.info(
        "New user created",
        user_id=user.id,
        azure_oid=azure_oid,
        email=email
    )

    return user
:::

### 5.3 自動作成の利点

✅ **シームレスなオンボーディング**: 初回ログイン時に自動登録
✅ **管理コスト削減**: 手動ユーザー登録不要
✅ **Azure AD同期**: Azure ADの情報を自動反映
✅ **セキュリティ**: Azure ADで承認されたユーザーのみアクセス可能

---

## 6. トークン更新（Refresh Token）

### 6.1 リフレッシュトークンフロー

::: mermaid
sequenceDiagram
    participant Client
    participant API
    participant AzureAD

    Client->>API: Request<br/>Authorization: Bearer <Expired_Token>
    API->>API: JWT検証
    API-->>Client: 401 Unauthorized<br/>{"detail": "Token expired"}

    Client->>AzureAD: POST /token<br/>grant_type=refresh_token<br/>refresh_token=<RT>
    AzureAD->>AzureAD: Refresh Token検証
    AzureAD-->>Client: 200 OK<br/>access_token: <New_JWT><br/>refresh_token: <New_RT>

    Client->>API: Request<br/>Authorization: Bearer <New_JWT>
    API->>API: JWT検証（成功）
    API-->>Client: 200 OK + Data
:::

### 6.2 トークン有効期限

| トークン種別 | 有効期限 | 説明 |
|------------|---------|------|
| **Access Token (JWT)** | 1時間（デフォルト） | API呼び出しに使用 |
| **Refresh Token** | 14日〜90日 | Access Token更新に使用 |
| **ID Token** | 1時間 | ユーザー情報取得用 |

**設定変更:**

Azure AD Portal → App Registration → Token configuration → Token lifetime policies

---

## 7. 認証エラーハンドリング

### 7.1 エラーコード一覧

::: mermaid
graph TB
    Auth[認証エラー] --> E401[401 Unauthorized]
    Auth --> E403[403 Forbidden]

    E401 --> E401A[トークン欠落]
    E401 --> E401B[トークン無効]
    E401 --> E401C[トークン期限切れ]
    E401 --> E401D[署名検証失敗]

    E403 --> E403A[ユーザー無効<br/>is_active=False]
    E403 --> E403B[権限不足<br/>RBAC拒否]

    style E401 fill:#FF9800
    style E403 fill:#F44336
:::

### 7.2 エラーレスポンス例

#### 7.2.1 トークン欠落（401）

```json
{
  "type": "https://httpstatuses.com/401",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Not authenticated",
  "instance": "/api/v1/projects"
}
:::

#### 7.2.2 トークン期限切れ（401）

```json
{
  "type": "https://httpstatuses.com/401",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Token expired",
  "instance": "/api/v1/projects",
  "errors": [
    {
      "code": "token_expired",
      "message": "Access token has expired. Please refresh your token."
    }
  ]
}
```

#### 7.2.3 ユーザー無効（403）

```json
{
  "type": "https://httpstatuses.com/403",
  "title": "Forbidden",
  "status": 403,
  "detail": "User is inactive",
  "instance": "/api/v1/projects"
}
```

#### 7.2.4 権限不足（403）

```json
{
  "type": "https://httpstatuses.com/403",
  "title": "Forbidden",
  "status": 403,
  "detail": "Insufficient permissions",
  "instance": "/api/v1/projects/123",
  "errors": [
    {
      "code": "insufficient_permissions",
      "message": "Only project managers can delete projects",
      "required_role": "project_manager",
      "current_role": "member"
    }
  ]
}
```

---

## 8. セキュリティベストプラクティス

### 8.1 トークンセキュリティ

::: mermaid
mindmap
  root((Token Security))
    保存
      LocalStorage❌
      SessionStorage❌
      HTTPOnlyクッキー✅
      メモリ内のみ✅
    送信
      HTTPS必須✅
      HTTPは禁止❌
      ヘッダーのみ✅
      URLパラメータ❌
    検証
      署名検証必須✅
      有効期限チェック✅
      発行者検証✅
      オーディエンス検証✅
    ログ
      トークン本体記録❌
      トークンハッシュ記録✅
      ユーザーID記録✅
:::

### 8.2 推奨事項

#### 8.2.1 トークン保存

❌ **避けるべき方法:**

- LocalStorage: XSS攻撃に脆弱
- SessionStorage: XSS攻撃に脆弱
- URLパラメータ: ログに残る、共有される

✅ **推奨方法:**

- HTTPOnlyクッキー（CSRF対策必須）
- メモリ内のみ（SPA）
- Secure Storage（モバイルアプリ）

#### 8.2.2 トークン送信

✅ **推奨:**

```http
Authorization: Bearer <JWT>
```

❌ **非推奨:**

```http
GET /api/v1/projects?token=<JWT>
```

#### 8.2.3 トークンログ

❌ **避けるべき:**

```python
logger.info(f"Token: {token}")  # トークン本体の記録
```

✅ **推奨:**

```python
import hashlib

token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
logger.info(f"Token hash: {token_hash}", user_id=user.id)
```

### 8.3 HTTPS強制

**実装**: `src/app/api/middlewares/security_headers.py`

```python
# Strict-Transport-Security ヘッダー追加
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
```

### 8.4 CORS設定

**実装**: `src/app/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # ["https://app.example.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## 9. 認証テスト

### 9.1 テストシナリオ

::: mermaid
graph TB
    Test[認証テスト]

    Test --> T1[正常系]
    Test --> T2[異常系]

    T1 --> T1A[有効トークン<br/>200 OK]
    T1 --> T1B[初回ログイン<br/>ユーザー自動作成]
    T1 --> T1C[システム管理者<br/>全権限]

    T2 --> T2A[トークンなし<br/>401 Unauthorized]
    T2 --> T2B[無効トークン<br/>401 Unauthorized]
    T2 --> T2C[期限切れトークン<br/>401 Unauthorized]
    T2 --> T2D[無効ユーザー<br/>403 Forbidden]
    T2 --> T2E[権限不足<br/>403 Forbidden]

    style T1 fill:#4CAF50
    style T2 fill:#FF9800
:::

### 9.2 テストコード例

**実装**: `tests/app/core/security/test_azure_ad.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_authenticated_request_success(client: AsyncClient, valid_jwt: str):
    """有効なJWTで認証成功"""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {valid_jwt}"}
    )
    assert response.status_code == 200
    assert "id" in response.json()

@pytest.mark.asyncio
async def test_missing_token_returns_401(client: AsyncClient):
    """トークンなしで401エラー"""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    """無効トークンで401エラー"""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-token-12345"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_expired_token_returns_401(client: AsyncClient, expired_jwt: str):
    """期限切れトークンで401エラー"""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_jwt}"}
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_inactive_user_returns_403(
    client: AsyncClient,
    valid_jwt: str,
    inactive_user_azure_oid: str
):
    """無効ユーザーで403エラー"""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {valid_jwt}"}
    )
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()
:::

---

## 10. まとめ

### 10.1 認証・認可設計の特徴

✅ **マルチモード認証**: 開発/本番で認証方式切り替え
✅ **Azure AD統合**: エンタープライズSSO対応
✅ **JWT標準準拠**: RFC 7519準拠のJWT実装
✅ **自動ユーザー作成**: 初回ログイン時に自動登録
✅ **包括的な検証**: 署名・有効期限・発行者・オーディエンス検証
✅ **セキュアなトークン管理**: HTTPS強制、ログ保護
✅ **RBAC統合**: 認証後の認可チェック

### 10.2 今後の拡張提案

- **Multi-Factor Authentication (MFA)**: Azure AD MFA強制
- **トークンリフレッシュ自動化**: クライアント側での自動更新
- **ログアウト機能**: トークン無効化
- **監査ログ強化**: ログイン履歴、失敗試行の追跡
- **API Key認証**: サーバー間通信用
- **OpenID Connect完全対応**: ID Tokenの活用

---

**ドキュメント管理情報:**

- **作成日**: 2025年（リバースエンジニアリング実施）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - RBAC設計書: `03-security/01-rbac-design.md`
  - セキュリティ実装詳細書: `03-security/03-security-implementation.md`
  - API仕様書: `04-api/01-api-specifications.md`
