# 環境設定ガイド

このガイドでは、ローカル、ステージング、本番環境での設定方法を説明します。

## 環境変数ファイルの構成

プロジェクトは環境ごとに異なる`.env`ファイルをサポートします。

### ファイル一覧

| ファイル名 | 用途 | Git管理 |
|-----------|------|---------|
| `.env.local` | ローカル開発環境 | ❌ 除外 |
| `.env.staging` | ステージング環境 | ❌ 除外 |
| `.env.production` | 本番環境 | ❌ 除外 |
| `.env.local.example` | ローカル環境のテンプレート | ✅ 管理 |
| `.env.staging.example` | ステージング環境のテンプレート | ✅ 管理 |
| `.env.production.example` | 本番環境のテンプレート | ✅ 管理 |

## セットアップ手順

### ローカル開発環境

```powershell
# テンプレートをコピー
Copy-Item .env.local.example .env.local

# 設定を編集
notepad .env.local
```

主な設定：

- `DATABASE_URL`: localhostのPostgreSQL
- `REDIS_URL`: localhostのRedis
- `STORAGE_BACKEND`: local
- `DEBUG`: true

### ステージング環境

```powershell
# テンプレートをコピー
Copy-Item .env.staging.example .env.staging

# 設定を編集（本番に近い設定）
notepad .env.staging
```

主な設定：

- `DATABASE_URL`: ステージングDBのURL
- `REDIS_URL`: ステージングRedisのURL
- `STORAGE_BACKEND`: azure
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI
- `DEBUG`: false

### 本番環境

```powershell
# テンプレートをコピー
Copy-Item .env.production.example .env.production

# 設定を編集（セキュアな値を使用）
notepad .env.production
```

重要な設定：

- `SECRET_KEY`: `openssl rand -hex 32`で生成
- `ALLOWED_ORIGINS`: 本番ドメインのみ許可
- `STORAGE_BACKEND`: azure
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI
- `LANGCHAIN_TRACING_V2`: true（監視有効化）
- **Azure AD認証設定**:
  - `AUTH_MODE`: `production`（本番モード）
  - `AZURE_TENANT_ID`: Azure ADテナントID
  - `AZURE_CLIENT_ID`: バックエンドのアプリケーション（クライアント）ID
  - `AZURE_OPENAPI_CLIENT_ID`: Swagger UIのアプリケーションID（オプション）

## 認証モードの設定

プロジェクトは、開発環境と本番環境で異なる認証方式をサポートしています。

### 開発モード（Development）

```powershell
# .env.local
AUTH_MODE=development
DEV_MOCK_TOKEN=mock-access-token-dev-12345
DEV_MOCK_USER_EMAIL=dev.user@example.com
DEV_MOCK_USER_OID=dev-azure-oid-12345
DEV_MOCK_USER_NAME=Development User
```

**特徴**:

- モックトークンを使用（Azure AD不要）
- 開発・テストに最適
- 本番環境では使用禁止（バリデーションエラーが発生）

### 本番モード（Production）

```powershell
# .env.production
AUTH_MODE=production
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-backend-client-id
AZURE_OPENAPI_CLIENT_ID=your-swagger-client-id
```

**特徴**:

- Azure AD Bearer認証
- トークン有効期限の自動検証
- Swagger UIでのOAuth2統合

### セキュリティバリデーション

本番環境で開発モード認証を有効にすると、アプリケーション起動時にエラーが発生します：

```python
# src/app/core/config.py
@model_validator(mode='after')
def validate_dev_auth_not_in_production(self) -> 'Settings':
    """本番環境で開発モード認証が有効な場合にエラーを発生させます。"""
    if self.ENVIRONMENT == "production" and self.AUTH_MODE == "development":
        raise ValueError(
            "Development authentication cannot be enabled in production environment. "
            "Set AUTH_MODE=production for production."
        )
    return self
```

---

## 環境の切り替え

### 環境変数による切り替え

`ENVIRONMENT`環境変数を設定して起動します。

```powershell
# ローカル開発（デフォルト）
uv run uvicorn app.main:app --reload

# ステージング
$env:ENVIRONMENT="staging"; uv run uvicorn app.main:app

# 本番
$env:ENVIRONMENT="production"; uv run uvicorn app.main:app
```

### 起動確認

起動時に読み込まれた設定ファイルが表示されます：

```text
Starting camp-backend v0.1.0
Environment: development
Loaded config from: /path/to/.env.local
Database: postgresql+asyncpg://postgres:***@localhost:5432/app_db
Redis cache connected: redis://localhost:6379/0
```

## 設定の優先順位

設定は以下の優先順位で読み込まれます（高い順）：

1. 環境変数（`export VARIABLE=value`）
2. `.env.{environment}`ファイル（例: `.env.local`）
3. `.env`ファイル（共通設定、オプション）
4. `config.py`のデフォルト値

## 環境ごとの違い

### ローカル開発環境

- **データベース**: PostgreSQL（ローカルインストール）
- **ストレージ**: ローカルファイルシステム
- **LLM**: Anthropic Claude直接接続
- **デバッグ**: 有効
- **ホットリロード**: 有効

### ステージング環境

- **データベース**: ステージング用PostgreSQL
- **ストレージ**: Azure Blob Storage
- **LLM**: Azure OpenAI
- **デバッグ**: 無効
- **監視**: LangSmith有効

### 本番環境

- **データベース**: 本番用PostgreSQL（高可用性構成）
- **ストレージ**: Azure Blob Storage（本番用）
- **LLM**: Azure OpenAI（本番用）
- **デバッグ**: 無効
- **監視**: LangSmith有効（本番用プロジェクト）
- **セキュリティ**: 厳格な設定

## セキュリティのベストプラクティス

### シークレットキーの管理

```powershell
# 安全なシークレットキーを生成
openssl rand -hex 32
```

### 本番環境での注意事項

1. **SECRET_KEYを必ず変更**

   ```powershell
   $SECRET_KEY = openssl rand -hex 32
   ```

2. **ALLOWED_ORIGINSを制限**

   ```ini
   ALLOWED_ORIGINS=["https://example.com","https://www.example.com"]
   ```

3. **DEBUGを無効化**

   ```ini
   DEBUG=false
   ```

4. **環境変数ファイルをGitに含めない**
   - `.gitignore`で除外済み
   - 絶対にコミットしない

5. **機密情報はシークレット管理サービスを使用**
   - Azure Key Vault
   - AWS Secrets Manager
   - HashiCorp Vault

---

## Azure AD設定の詳細手順

### 前提条件

- Azure ADテナント管理者権限
- Azure Portal アクセス権限

### ステップ1: アプリ登録（バックエンドAPI）

1. **Azure Portal** にアクセス: <https://portal.azure.com>
2. **Azure Active Directory** → **アプリの登録** → **新規登録**
3. 以下を入力:
   - **名前**: `camp-backend-api`
   - **サポートされているアカウントの種類**: 組織内のみ（シングルテナント）
   - **リダイレクトURI**: 不要（API専用）
4. **登録** をクリック

### ステップ2: アプリケーションIDとテナントIDの取得

1. 登録したアプリの **概要** ページに移動
2. 以下の情報をコピー:
   - **アプリケーション（クライアント）ID**: `AZURE_CLIENT_ID` として使用
   - **ディレクトリ（テナント）ID**: `AZURE_TENANT_ID` として使用

### ステップ3: APIスコープの設定（オプション）

APIスコープを公開する場合:

1. 登録したアプリの **APIの公開** に移動
2. **スコープの追加** をクリック:
   - **スコープ名**: `API.Access`
   - **同意できるユーザー**: 管理者とユーザー
   - **管理者の同意の表示名**: `Access API`
   - **管理者の同意の説明**: `Access backend API`
   - **ユーザーの同意の表示名**: `API にアクセス`
   - **ユーザーの同意の説明**: `バックエンドAPIにアクセスします`
3. **アプリケーションIDのURI** を確認（例: `api://12345678-1234-1234-1234-123456789abc`）

### ステップ4: Swagger UI用アプリ登録（オプション）

Swagger UIでOAuth2認証をテストする場合:

1. **Azure Active Directory** → **アプリの登録** → **新規登録**
2. 以下を入力:
   - **名前**: `camp-swagger-ui`
   - **サポートされているアカウントの種類**: 組織内のみ
   - **リダイレクトURI**:
     - プラットフォーム: **シングルページアプリケーション（SPA）**
     - URI: `http://localhost:8000/docs/oauth2-redirect`
3. **登録** をクリック
4. **アプリケーション（クライアント）ID** をコピー: `AZURE_OPENAPI_CLIENT_ID` として使用
5. **APIのアクセス許可** → **アクセス許可の追加**:
   - **自分のAPI** タブを選択
   - `camp-backend-api` を選択
   - `API.Access` スコープを選択
   - **アクセス許可の追加** をクリック

### ステップ5: 環境変数の設定

`.env.production` に以下を追加:

```ini
# Azure AD認証設定（本番環境）
AUTH_MODE=production
AZURE_TENANT_ID=<ディレクトリ（テナント）ID>
AZURE_CLIENT_ID=<バックエンドAPIのアプリケーション（クライアント）ID>
AZURE_OPENAPI_CLIENT_ID=<Swagger UIのアプリケーション（クライアント）ID>

# その他の本番設定
ENVIRONMENT=production
SECRET_KEY=<32文字以上のランダム文字列>
ALLOWED_ORIGINS=["https://example.com"]
```

SECRET_KEYの生成:

```powershell
openssl rand -hex 32
```

### ステップ6: トークン検証の確認

アプリケーション起動時に以下のログが表示されることを確認:

```text
INFO: Azure AD authentication enabled
INFO: Tenant ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
INFO: Client ID: yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
```

### ステップ7: トークン取得とテスト

**本番環境でのトークン取得**（例: Python）:

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="<AZURE_CLIENT_ID>",
    client_credential="<CLIENT_SECRET>",  # 必要に応じて
    authority="https://login.microsoftonline.com/<AZURE_TENANT_ID>"
)

result = app.acquire_token_for_client(scopes=["api://<AZURE_CLIENT_ID>/.default"])
access_token = result["access_token"]

# APIリクエスト
import requests
response = requests.get(
    "https://api.example.com/api/v1/users/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
print(response.json())
```

### トラブルシューティング

#### エラー: "Invalid token"

**原因**:

- トークンの有効期限が切れている
- AZURE_CLIENT_IDが正しくない
- テナントIDが一致していない

**対処法**:

1. トークンの有効期限を確認（通常1時間）
2. `.env.production` の `AZURE_CLIENT_ID` を確認
3. Azure Portalで設定を再確認

#### エラー: "Development authentication cannot be enabled in production"

**原因**:

- 本番環境で `AUTH_MODE=development` が設定されている
- 環境変数の優先順位が誤っている

**対処法**:

1. `.env.production` で `AUTH_MODE=production` を設定
2. シェルの環境変数を確認: `$env:AUTH_MODE`
3. 不要な環境変数を削除

#### エラー: "AZURE_TENANT_ID or AZURE_CLIENT_ID not configured"

**原因**:

- 環境変数が設定されていない
- ファイル名が間違っている（`.env.production` でなく `.env.prod` など）

**対処法**:

1. `.env.production` ファイルが存在することを確認
2. 環境変数が正しく設定されていることを確認:

   ```powershell
   Select-String -Path .env.production -Pattern "AZURE_"
   ```

3. アプリケーション起動時のログを確認

#### Swagger UIでOAuth2が動作しない

**原因**:

- リダイレクトURIが正しく設定されていない
- Swagger UI用アプリにAPIのアクセス許可がない

**対処法**:

1. Azure Portalでリダイレクトウリを確認: `http://localhost:8000/docs/oauth2-redirect`
2. Swagger UI用アプリの **APIのアクセス許可** を確認
3. ブラウザの開発者ツールでエラーを確認

---

## 開発モード設定の詳細

### モック認証の有効化

`.env.local` に以下を設定:

```ini
# 開発モード認証
AUTH_MODE=development
DEV_MOCK_TOKEN=mock-access-token-dev-12345
DEV_MOCK_USER_EMAIL=dev.user@example.com
DEV_MOCK_USER_OID=dev-azure-oid-12345
DEV_MOCK_USER_NAME=Development User
```

### モック認証の仕組み

開発モードでは、以下の動作になります:

1. **トークン検証のスキップ**: Azure ADへの検証リクエストなし
2. **固定ユーザー**: `DEV_MOCK_USER_*` で指定されたユーザー情報を使用
3. **自動ユーザー作成**: データベースに存在しない場合は自動作成

**実装場所**: `src/app/api/auth/dependencies.py`

```python
async def get_current_user_azure(
    token: str,
    settings: Annotated[Settings, Depends(get_settings)],
    db: DatabaseDep,
) -> User:
    if settings.AUTH_MODE == "development":
        # モック認証: トークンチェックなし
        user = await user_service.get_or_create_user(
            azure_oid=settings.DEV_MOCK_USER_OID,
            email=settings.DEV_MOCK_USER_EMAIL,
            display_name=settings.DEV_MOCK_USER_NAME,
        )
        return user
    else:
        # 本番認証: Azure ADトークン検証
        user_info = await verify_azure_token(token, settings)
        ...
```

### APIテスト方法

#### curlでのテスト

```powershell
# ユーザー情報取得
curl -H "Authorization: Bearer mock-access-token-dev-12345" http://localhost:8000/api/v1/users/me

# プロジェクト一覧取得
curl -H "Authorization: Bearer mock-access-token-dev-12345" http://localhost:8000/api/v1/projects

# プロジェクト作成
curl -X POST -H "Authorization: Bearer mock-access-token-dev-12345" -H "Content-Type: application/json" -d '{\"name\":\"テストプロジェクト\",\"code\":\"TEST-001\"}' http://localhost:8000/api/v1/projects
```

#### Postmanでのテスト

1. **Authorization** タブを選択
2. **Type**: `Bearer Token` を選択
3. **Token**: `mock-access-token-dev-12345` を入力
4. リクエストを送信

#### Pythonでのテスト

```python
import requests

# ヘッダーを設定
headers = {
    "Authorization": "Bearer mock-access-token-dev-12345",
    "Content-Type": "application/json"
}

# ユーザー情報取得
response = requests.get("http://localhost:8000/api/v1/users/me", headers=headers)
print(response.json())

# プロジェクト作成
data = {
    "name": "テストプロジェクト",
    "code": "TEST-001",
    "description": "開発環境でのテスト"
}
response = requests.post("http://localhost:8000/api/v1/projects", headers=headers, json=data)
print(response.json())
```

### セキュリティ注意事項

**警告**: 開発モード認証は以下の制限があります:

1. **トークンが固定値**: セキュリティなし
2. **ユーザー情報が固定値**: 複数ユーザーのテスト不可
3. **トークン有効期限の検証なし**: 常に有効

#### 本番環境では絶対に使用しないでください

本番環境で誤って有効にした場合、アプリケーション起動時にエラーが発生します:

```python
# src/app/core/config.py
@model_validator(mode='after')
def validate_dev_auth_not_in_production(self) -> 'Settings':
    """本番環境で開発モード認証が有効な場合にエラーを発生させます。"""
    if self.ENVIRONMENT == "production" and self.AUTH_MODE == "development":
        raise ValueError(
            "Development authentication cannot be enabled in production environment. "
            "Set AUTH_MODE=production for production."
        )
    return self
```

**エラーメッセージ**:

```text
ValueError: Development authentication cannot be enabled in production environment. Set AUTH_MODE=production for production.
```

### 複数ユーザーのテスト

開発モードで複数ユーザーをテストする場合:

1. **データベースに直接ユーザーを作成**:

   ```sql
   INSERT INTO users (id, azure_oid, email, display_name, roles, is_active)
   VALUES (
       'user-uuid-1',
       'azure-oid-1',
       'user1@example.com',
       'テストユーザー1',
       ARRAY['User'],
       true
   );
   ```

2. **モックトークンを切り替える**（環境変数を変更して再起動）:

   ```ini
   DEV_MOCK_USER_EMAIL=user1@example.com
   DEV_MOCK_USER_OID=azure-oid-1
   DEV_MOCK_USER_NAME=テストユーザー1
   ```

3. **本番に近いテストには Azure AD テスト環境を使用**

---

## トラブルシューティング

### 環境変数ファイルが読み込まれない

起動ログを確認：

```text
Loaded config from: ...
```

ファイルが存在するか確認：

```powershell
ls .env.local
```

### 環境変数が反映されない

環境変数の優先順位を確認：

1. シェルの環境変数が優先されます
2. `.env.{environment}`ファイル
3. デフォルト値

### データベース接続エラー

環境ごとの`DATABASE_URL`を確認：

```powershell
# ローカル
Select-String -Path .env.local -Pattern "DATABASE_URL"

# ステージング
Select-String -Path .env.staging -Pattern "DATABASE_URL"
```

## 次のステップ

- [クイックスタート](./05-quick-start.md) - アプリケーションの起動
- [データベース基礎](./07-database-basics.md) - データベース管理
- [API仕様概要](../04-development/05-api-design/01-api-overview.md) - APIエンドポイントの詳細
