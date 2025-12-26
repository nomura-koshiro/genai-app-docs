# 認証実装

JWT、OAuth2、パスワードハッシュを使用した認証について説明します。

## 認証フロー図

以下の図は、ログインから認証済みリクエストまでの全体的な流れを示しています。

::: mermaid
sequenceDiagram
    participant C as クライアント
    participant API as FastAPI<br/>Router
    participant US as SampleUserService
    participant UR as SampleUserRepository
    participant DB as PostgreSQL
    participant SEC as Security<br/>Module

    Note over C,SEC: ログインフロー

    C->>+API: POST /api/auth/login<br/>{email, password}
    API->>+US: authenticate(email, password)
    US->>+UR: get_by_email(email)
    UR->>+DB: SELECT * FROM sample_users<br/>WHERE email = ?
    DB-->>-UR: SampleUser record
    UR-->>-US: SampleUser object

    US->>+SEC: verify_password(plain, hashed)
    SEC-->>-US: True/False

    alt パスワード一致
        US-->>-API: SampleUser object
        API->>+SEC: create_access_token({sub: user_id})
        SEC-->>-API: JWT token
        API-->>-C: {access_token, token_type}
    else パスワード不一致
        US-->>API: ValidationError
        API-->>C: 401 Unauthorized
    end

    Note over C,SEC: 認証済みリクエストフロー

    C->>+API: GET /api/v1/sample-users/me<br/>Header: Authorization: Bearer <token>
    API->>+SEC: decode_access_token(token)
    SEC-->>-API: {sub: user_id, exp: ...}

    alt トークン有効
        API->>+US: get_user(user_id)
        US->>+UR: get(user_id)
        UR->>+DB: SELECT * FROM sample_users<br/>WHERE id = ?
        DB-->>-UR: SampleUser record
        UR-->>-US: SampleUser object
        US-->>-API: SampleUser object
        API-->>-C: 200 OK<br/>{id, email, username}
    else トークン無効
        SEC-->>API: None
        API-->>C: 401 Unauthorized
    end

    style C fill:#81d4fa,stroke:#01579b,stroke-width:3px,color:#000
    style API fill:#ffb74d,stroke:#e65100,stroke-width:3px,color:#000
    style US fill:#ce93d8,stroke:#4a148c,stroke-width:3px,color:#000
    style UR fill:#81c784,stroke:#1b5e20,stroke-width:3px,color:#000
    style DB fill:#64b5f6,stroke:#01579b,stroke-width:3px,color:#000
    style SEC fill:#f06292,stroke:#880e4f,stroke-width:3px,color:#000
:::

**認証フローの詳細**:

### 1. ログインフロー

1. **クライアント** → **API**: メールアドレスとパスワードを送信
2. **API** → **UserService**: 認証処理を依頼
3. **UserService** → **UserRepository**: メールアドレスでユーザー検索
4. **UserRepository** → **PostgreSQL**: データベースクエリ実行
5. **UserService** → **Security**: パスワード検証（bcrypt）
6. **パスワード一致時**:
   - **API** → **Security**: JWTトークン生成
   - **API** → **クライアント**: アクセストークンを返却
7. **パスワード不一致時**:
   - **API** → **クライアント**: 401 Unauthorized

### 2. 認証済みリクエストフロー

1. **クライアント** → **API**: Authorization ヘッダーにトークンを含めてリクエスト
2. **API** → **Security**: JWTトークンをデコード・検証
3. **トークン有効時**:
   - **API** → **UserService**: ユーザーIDからユーザー情報を取得
   - **UserService** → **UserRepository** → **PostgreSQL**: ユーザー取得
   - **API** → **クライアント**: ユーザー情報を返却
4. **トークン無効時**:
   - **API** → **クライアント**: 401 Unauthorized

### セキュリティのポイント

- **パスワードハッシュ化**: bcryptを使用して不可逆的にハッシュ化
- **JWT有効期限**: デフォルト30分（設定可能）
- **トークン検証**: すべての認証済みエンドポイントで実施
- **HTTPSのみ**: 本番環境では必須
- **ヘッダー形式**: `Authorization: Bearer <token>`

## パスワードハッシュ化

```python
# src/app/core/security/password.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """パスワードをハッシュ化。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証。"""
    return pwd_context.verify(plain_password, hashed_password)


# 使用例
hashed = hash_password("mypassword123")
is_valid = verify_password("mypassword123", hashed)  # True
```

## JWTトークン生成

```python
from datetime import datetime, timedelta, timezone
from jose import jwt

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """JWTアクセストークンを作成。"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """JWTトークンをデコード。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None
```

## 認証エンドポイント

```python
# src/app/api/routes/auth.py
from fastapi import APIRouter, Depends
from app.schemas.sample_user import SampleUserLogin, Token
from app.api.core import SampleUserServiceDep
from app.core.security import create_access_token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    login_data: SampleUserLogin,
    user_service: SampleUserServiceDep,
) -> Token:
    """ログイン。"""
    # ユーザー認証
    user = await user_service.authenticate(
        login_data.email,
        login_data.password
    )

    # トークン生成
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(access_token=access_token, token_type="bearer")
```

## 認証依存性

```python
# src/app/api/dependencies.py
from fastapi import Depends, Header, HTTPException
from app.core.security import decode_access_token


async def get_current_user(
    authorization: str | None = Header(None),
    user_service: SampleUserServiceDep = None,
) -> SampleUser:
    """現在の認証済みユーザーを取得。"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # "Bearer <token>" から token を抽出
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    # トークンデコード
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # ユーザー取得
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await user_service.get_user(int(user_id))
    return user


CurrentSampleUserDep = Annotated[SampleUser, Depends(get_current_user)]


# 使用例
@router.get("/me", response_model=SampleUserResponse)
async def get_me(current_user: CurrentSampleUserDep) -> SampleUserResponse:
    """現在のユーザー情報を取得。"""
    return SampleUserResponse.model_validate(current_user)
```

## 2つの認証システムの共存

本プロジェクトは、**JWT認証（レガシー）** と **Azure AD認証（本番）** の2つの認証システムが共存しています。

### 認証システムの比較

| 項目 | JWT認証 | Azure AD認証 |
|------|---------|-------------|
| **用途** | レガシー・開発環境 | 本番環境 |
| **対象モデル** | `SampleUser` (int型ID) | `UserAccount` (UUID型ID) |
| **トークン発行** | 自前実装（python-jose） | Azure AD（Microsoft Entra ID） |
| **認証方式** | パスワード認証 + JWTトークン | Azure ADトークン |
| **実装ファイル** | `src/app/core/security/jwt.py` | `src/app/core/security/azure_ad.py` |
| **依存性型** | `CurrentUserDep` | `CurrentUserAzureDep` |

### AUTH_MODEによる切り替えメカニズム

環境変数`AUTH_MODE`で認証方式を切り替えます：

```bash
# 開発モード（モックトークン検証）
AUTH_MODE=development
DEV_MOCK_TOKEN=mock-access-token-dev-12345

# 本番モード（Azure AD認証）
AUTH_MODE=production
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
```

### Azure AD認証（本番環境）

本番環境では、Azure AD（Microsoft Entra ID）を使用したBearerトークン認証を使用します。

#### トークン検証の仕組み

```python
# src/app/core/security/azure_ad.py
from fastapi import Security
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from fastapi_azure_auth.user import User as AzureUser

# Azure AD認証スキーム（本番モードのみ初期化）
if settings.AUTH_MODE == "production":
    azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
        app_client_id=settings.AZURE_CLIENT_ID,
        tenant_id=settings.AZURE_TENANT_ID,
        scopes={
            f'api://{settings.AZURE_CLIENT_ID}/access_as_user': 'Access API as user',
        },
        allow_guest_users=False,
    )


async def get_current_azure_user(
    user: AzureUser = Security(get_azure_scheme_dependency, scopes=['access_as_user'])
) -> AzureUser:
    """Azure ADから認証済みユーザーを取得（本番モード）。"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Azure AD authentication failed"
        )
    return user
```

### 開発モード認証（開発環境）

開発環境では、モックトークンによる簡易認証を使用します。

```python
# src/app/core/security/dev_auth.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


class DevUser:
    """開発モード用のモックユーザー（Azure AD Userと互換）。"""

    def __init__(self):
        self.oid = settings.DEV_MOCK_USER_OID
        self.email = settings.DEV_MOCK_USER_EMAIL
        self.name = settings.DEV_MOCK_USER_NAME
        self.roles = []


async def get_current_dev_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> DevUser:
    """開発モード用の認証（トークンチェックのみ）。"""
    token = credentials.credentials

    if token != settings.DEV_MOCK_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid development token"
        )

    return DevUser()
```

### 自動的に実行される検証

fastapi-azure-authライブラリは、以下のセキュリティチェックを**自動的に**実行します：

| 検証項目 | 説明 | 期限切れ時の動作 |
|---------|------|----------------|
| **JWT署名** | Azure ADの公開鍵で署名を検証 | HTTP 401 Unauthorized |
| **有効期限（exp）** | トークンの`exp`クレームを現在時刻と比較 | HTTP 401 Unauthorized（ExpiredSignatureError） |
| **発行者（iss）** | `iss`クレームがAzure ADテナントと一致するか確認 | HTTP 401 Unauthorized |
| **オーディエンス（aud）** | `aud`クレームがクライアントIDと一致するか確認 | HTTP 401 Unauthorized |
| **スコープ（scp）** | 要求されたスコープが含まれているか確認 | HTTP 403 Forbidden |

### トークン有効期限チェック

トークンの有効期限チェックは、fastapi-azure-authが内部で使用している
**python-joseライブラリにより自動的に実行**されます。

```python
# JWT検証フロー（自動実行）
1. クライアントがBearerトークンを送信
   ↓
2. SingleTenantAzureAuthorizationCodeBearerがトークンを受信
   ↓
3. python-joseによるJWT検証
   - Base64デコード
   - 署名検証（Azure AD公開鍵）
   - expクレーム検証（現在時刻 < exp）★ 自動実行
   - issクレーム検証
   - audクレーム検証
   ↓
4. スコープ検証（access_as_user）
   ↓
5. AzureUserオブジェクト生成
   ↓
6. get_current_azure_user()に渡される
```

### 期限切れトークンのエラーレスポンス

```json
// Authorization: Bearer <expired-token>
// HTTP 401 Unauthorized
{
  "detail": "Token signature has expired"
}
```

### 実装ファイル一覧

認証関連の実装ファイルは以下の通りです：

| ファイルパス | 説明 | 認証方式 |
|------------|------|---------|
| `src/app/core/security/jwt.py` | JWT認証（SampleUser用） | JWT（レガシー） |
| `src/app/core/security/azure_ad.py` | Azure AD認証（UserAccount用） | Azure AD（本番） |
| `src/app/core/security/dev_auth.py` | 開発モード認証（モック） | モックトークン（開発） |
| `src/app/api/core/dependencies.py` | 依存性注入定義 | 全認証方式 |

### 認証モードの切り替え（既存のまま維持）

環境変数`AUTH_MODE`で認証方式を切り替えます：

```bash
# 開発モード（モックトークン認証）
AUTH_MODE=development
DEV_MOCK_TOKEN=mock-access-token-dev-12345
DEV_MOCK_USER_OID=dev-azure-oid-12345
DEV_MOCK_USER_EMAIL=dev.user@example.com

# 本番モード（Azure AD認証）
AUTH_MODE=production
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
```

### なぜ明示的な有効期限チェックが不要か

1. **ライブラリレベルでの検証**: fastapi-azure-authはpython-joseを使用し、JWTデコード時に自動的に`exp`クレームを検証
2. **FastAPIセキュリティ統合**: Security依存性により、エンドポイント実行前に自動的にトークン検証が実行
3. **標準的な実装**: JWT RFC 7519に準拠した標準的な有効期限検証

### エンドポイント実装例（2つの認証システム）

#### JWT認証エンドポイント（レガシー）

```python
# src/app/api/routes/sample_users.py
from fastapi import APIRouter
from app.api.core import CurrentUserDep
from app.schemas.sample_user import SampleUserResponse

router = APIRouter()


@router.get("/me", response_model=SampleUserResponse)
async def get_current_user_info(
    current_user: CurrentUserDep,  # JWT認証（SampleUser）
) -> SampleUserResponse:
    """現在のユーザー情報を取得（JWT認証）。"""
    return SampleUserResponse.model_validate(current_user)
```

#### Azure AD認証エンドポイント（本番）

```python
# src/app/api/routes/users.py
from fastapi import APIRouter
from app.api.core import CurrentUserAzureDep
from app.schemas.user_account import UserAccountResponse

router = APIRouter()


@router.get("/me", response_model=UserAccountResponse)
async def get_current_user_info_azure(
    current_user: CurrentUserAzureDep,  # Azure AD認証（UserAccount）
) -> UserAccountResponse:
    """現在のユーザー情報を取得（Azure AD認証）。"""
    return UserAccountResponse.model_validate(current_user)
```

### 参考ドキュメント

詳細は以下のドキュメントを参照してください：

- `azure-entra-id-backend-implementation.md`: 実装詳細
- [fastapi-azure-auth GitHub](https://github.com/Intility/fastapi-azure-auth)
- [python-jose JWT検証](https://github.com/mpdavis/python-jose)

## 参考リンク

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/)
- [Passlib Documentation](https://passlib.readthedocs.io/)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [Azure AD Authentication](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
