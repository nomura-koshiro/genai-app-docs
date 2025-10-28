# 環境変数リファレンス

バックエンドアプリケーションで使用される全ての環境変数の詳細を記載します。

## 目次

- [概要](#概要)
- [設定ファイル](#設定ファイル)
- [環境変数一覧](#環境変数一覧)
  - [アプリケーション設定](#アプリケーション設定)
  - [環境設定](#環境設定)
  - [セキュリティ設定](#セキュリティ設定)
  - [データベース設定](#データベース設定)
  - [Redis Cache設定](#redis-cache設定)
  - [ストレージ設定](#ストレージ設定)
  - [LLM設定](#llm設定)
  - [ファイルアップロード設定](#ファイルアップロード設定)
- [環境別設定例](#環境別設定例)
- [設定の優先順位](#設定の優先順位)

---

## 概要

### 設定管理

このプロジェクトでは**Pydantic Settings**を使用して環境変数を管理しています。

- 型安全な設定管理
- 環境別の`.env`ファイルからの自動読み込み
- バリデーション機能
- デフォルト値の提供

### 環境別設定ファイル

環境変数`ENVIRONMENT`に基づいて、適切な設定ファイルが自動的に読み込まれます：

- **development** → `.env.local`
- **staging** → `.env.staging`
- **production** → `.env.production`

### 設定クラス

`src/app/core/config.py`で定義されています。

```python
from pydantic_settings import BaseSettings

def get_env_file() -> tuple[str, ...]:
    """環境に応じた.envファイルのパスを取得"""
    environment = os.getenv("ENVIRONMENT", "development")

    env_mapping = {
        "development": "local",
        "staging": "staging",
        "production": "production",
    }

    env_name = env_mapping.get(environment, "local")
    env_specific = project_root / f".env.{env_name}"

    return (str(env_specific),) if env_specific.exists() else (".env",)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_env_file(),  # 環境別ファイルを動的に読み込み
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
```

---

## 設定ファイル

### .envファイルの場所

```text
backend/
├── .env.local              # ローカル開発環境（gitignore対象）
├── .env.staging            # ステージング環境（gitignore対象）
├── .env.production         # 本番環境（gitignore対象）
├── .env.local.example      # ローカル開発環境のテンプレート
├── .env.staging.example    # ステージング環境のテンプレート
├── .env.production.example # 本番環境のテンプレート
└── src/
    └── app/
        └── config.py       # 設定クラス
```

### 初回セットアップ

ローカル開発環境用の設定ファイルを作成：

```bash
# テンプレートからコピー
cp .env.local.example .env.local

# 必要な値を編集
nano .env.local
```

ステージング環境・本番環境用の設定ファイルも同様に作成：

```bash
# ステージング環境
cp .env.staging.example .env.staging

# 本番環境
cp .env.production.example .env.production
```

---

## 環境変数一覧

### アプリケーション設定

FastAPIアプリケーションの基本設定。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| APP_NAME | string | "camp-backend" | × | アプリケーション名 |
| VERSION | string | "0.1.0" | × | アプリケーションバージョン |
| DEBUG | boolean | false | × | デバッグモード（開発時はtrue） |
| HOST | string | "0.0.0.0" | × | サーバーホスト |
| PORT | integer | 8000 | × | サーバーポート |
| ALLOWED_ORIGINS | list[string] | 環境依存 | × | CORS許可オリジン（開発: localhost、本番: 明示的指定必須） |

#### 設定例

```bash
APP_NAME="camp-backend"
VERSION="0.1.0"
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 開発環境
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# 本番環境（必ず明示的に指定）
ALLOWED_ORIGINS=["https://example.com", "https://www.example.com"]
```

#### 使用例

```python
from app.core.config import settings

print(f"Starting {settings.APP_NAME} v{settings.VERSION}")
print(f"Debug mode: {settings.DEBUG}")
```

---

### 環境設定

実行環境の指定。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| ENVIRONMENT | string | "development" | × | 実行環境（development/staging/production） |

#### 設定例

```bash
# 開発環境
ENVIRONMENT=development

# ステージング環境
ENVIRONMENT=staging

# 本番環境
ENVIRONMENT=production
```

#### 使用例

```python
from app.core.config import settings

if settings.ENVIRONMENT == "production":
    # 本番環境用の設定
    setup_production_logging()
```

---

### セキュリティ設定

認証・認可のためのセキュリティ設定。

#### JWT設定

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| SECRET_KEY | string | (開発用デフォルト) | ○ | JWT署名用の秘密鍵（本番環境では必須、32文字以上） |
| ALGORITHM | string | "HS256" | × | JWT署名アルゴリズム |
| ACCESS_TOKEN_EXPIRE_MINUTES | integer | 30 | × | アクセストークンの有効期限（分） |

#### レート制限設定

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| RATE_LIMIT_CALLS | integer | 100 | × | レート制限の呼び出し回数 |
| RATE_LIMIT_PERIOD | integer | 60 | × | レート制限の期間（秒） |

#### セキュリティポリシー設定

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| MAX_LOGIN_ATTEMPTS | integer | 5 | × | アカウントロックまでのログイン失敗回数 |
| ACCOUNT_LOCK_DURATION_HOURS | integer | 1 | × | アカウントロック時間（時間） |

#### 設定例

```bash
# JWT設定
SECRET_KEY=your-random-secret-key-here-at-least-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# レート制限設定
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# セキュリティポリシー設定
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_DURATION_HOURS=1
```

#### 秘密鍵の生成

```bash
# Pythonで生成
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSLで生成
openssl rand -hex 32
```

#### 使用例

```python
from app.core.config import settings
from app.core.security import create_access_token

token = create_access_token(
    data={"sub": user.email},
    expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
)
```

---

### データベース設定

データベース接続の設定。

#### メインデータベース

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| DATABASE_URL | string | "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db" | × | データベース接続URL |

#### テストデータベース

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| TEST_DATABASE_URL | string | "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db" | × | テストデータベース接続URL |
| TEST_DATABASE_ADMIN_URL | string | "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres" | × | テストDB管理者接続URL |
| TEST_DATABASE_NAME | string | "test_db" | × | テストデータベース名 |

#### データベース接続プール設定

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| DB_POOL_SIZE | integer | 5 | × | 通常時の接続プールサイズ |
| DB_MAX_OVERFLOW | integer | 10 | × | ピーク時の追加接続数 |
| DB_POOL_RECYCLE | integer | 1800 | × | 接続リサイクル時間（秒） |
| DB_POOL_PRE_PING | boolean | true | × | 接続前のPINGチェック |

#### 設定例

```bash
# メインデータベース
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_db

# テストデータベース設定
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
TEST_DATABASE_ADMIN_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
TEST_DATABASE_NAME=test_db

# 接続プール設定（開発環境）
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=true

# 接続プール設定（本番環境）
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

#### 接続URL形式

```text
# PostgreSQL（推奨）
postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>

# PostgreSQL（SSL接続）
postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>?ssl=require
```

#### 使用例

```python
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(settings.DATABASE_URL)
```

---

### Docker Compose設定

Docker Compose（`docker-compose.yml`）で使用される環境変数。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| POSTGRES_USER | string | "postgres" | × | PostgreSQLユーザー名 |
| POSTGRES_PASSWORD | string | "postgres" | × | PostgreSQLパスワード |
| POSTGRES_DB | string | "app_db" | × | PostgreSQLデータベース名 |
| POSTGRES_PORT | integer | 5432 | × | PostgreSQLポート |
| PGADMIN_EMAIL | string | "<admin@example.com>" | × | PgAdmin管理者メール |
| PGADMIN_PASSWORD | string | "admin" | × | PgAdmin管理者パスワード |
| PGADMIN_PORT | integer | 5050 | × | PgAdminポート |

#### 設定例

```bash
# PostgreSQL設定
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=app_db
POSTGRES_PORT=5432

# Redis設定
REDIS_PORT=6379

# PgAdmin設定（オプション）
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050
```

#### 使用方法

これらの変数は`docker-compose.yml`でコンテナの設定に使用されます。
アプリケーションコード（`src/app/`）では直接使用されません。

```yaml
# docker-compose.yml の例
services:
  postgres:
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-app_db}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
```

**Note**:

- これらの変数は`.env.local`ファイルに記載できます
- Docker Composeが自動的に読み込みます
- 本番環境では異なる認証情報を使用してください

---

### Redis Cache設定

Redisキャッシュの設定（オプション）。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| REDIS_URL | string | null | × | Redis接続URL |
| REDIS_PORT | integer | 6379 | × | Redisポート（Docker Compose用） |
| CACHE_TTL | integer | 300 | × | デフォルトキャッシュTTL（秒） |

#### 設定例

```bash
# Redis接続（ローカル）
REDIS_URL=redis://localhost:6379/0

# Redis接続（認証あり）
REDIS_URL=redis://:password@localhost:6379/0

# Redis接続（リモート）
REDIS_URL=redis://redis.example.com:6379/0

# キャッシュTTL（秒）
CACHE_TTL=300  # 5分
```

#### 接続URL形式

```text
# 基本形式
redis://<host>:<port>/<db>

# 認証あり
redis://:<password>@<host>:<port>/<db>

# ユーザー名とパスワード
redis://<username>:<password>@<host>:<port>/<db>

# TLS接続
rediss://<host>:<port>/<db>
```

#### 使用例

```python
from app.core.config import settings
from app.core.cache import cache_manager

# Redisが設定されている場合のみ接続
if settings.REDIS_URL:
    await cache_manager.connect()

    # キャッシュの使用
    await cache_manager.set("key", "value", expire=settings.CACHE_TTL)
    value = await cache_manager.get("key")
```

**注意**: REDIS_URLが設定されていない場合、キャッシュ機能は無効化されます。

---

### ストレージ設定

ファイルストレージの設定。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| STORAGE_BACKEND | string | "local" | × | ストレージバックエンド（local/azure） |
| LOCAL_STORAGE_PATH | string | "./uploads" | × | ローカルストレージのパス |
| AZURE_STORAGE_ACCOUNT_NAME | string | null | △ | Azure Storageアカウント名 |
| AZURE_STORAGE_CONNECTION_STRING | string | null | △ | Azure Storage接続文字列 |
| AZURE_STORAGE_CONTAINER_NAME | string | "uploads" | × | Azureコンテナ名 |

#### 設定例

ローカルストレージ（開発環境）:

```bash
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads
```

Azure Blob Storage（本番環境）:

```bash
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_NAME=myaccount
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=xxx;EndpointSuffix=core.windows.net"
AZURE_STORAGE_CONTAINER_NAME=uploads
```

#### 使用例

```python
from app.core.config import settings
from app.storage import get_storage_backend

storage = get_storage_backend()
await storage.upload(file_path, content)
```

---

### LLM設定

言語モデルAPIの設定。

#### LLMモデル設定

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| LLM_PROVIDER | string | "anthropic" | × | LLMプロバイダー（anthropic/openai/azure_openai） |
| LLM_MODEL | string | "claude-3-5-sonnet-20241022" | × | 使用するモデル名 |
| LLM_TEMPERATURE | float | 0.0 | × | モデルのtemperature（0.0-1.0） |
| LLM_MAX_TOKENS | integer | 4096 | × | 最大トークン数 |

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=4096
```

#### Anthropic Claude

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| ANTHROPIC_API_KEY | string | null | △ | Anthropic APIキー |

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

#### OpenAI

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| OPENAI_API_KEY | string | null | △ | OpenAI APIキー |

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
```

#### Azure OpenAI

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| AZURE_OPENAI_ENDPOINT | string | null | △ | Azure OpenAIエンドポイント |
| AZURE_OPENAI_API_KEY | string | null | △ | Azure OpenAI APIキー |
| AZURE_OPENAI_API_VERSION | string | "2024-02-15-preview" | × | Azure OpenAI APIバージョン |
| AZURE_OPENAI_DEPLOYMENT_NAME | string | null | △ | デプロイメント名 |

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=xxxxxxxxxxxxx
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

#### LangSmith（トレーシング）

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| LANGCHAIN_TRACING_V2 | boolean | false | × | LangSmithトレーシング有効化 |
| LANGCHAIN_API_KEY | string | null | × | LangSmith APIキー |
| LANGCHAIN_PROJECT | string | "ai-agent-app" | × | LangSmithプロジェクト名 |

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__xxxxxxxxxxxxx
LANGCHAIN_PROJECT=ai-agent-app
```

#### 使用例

```python
from app.core.config import settings
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    model="claude-3-sonnet-20240229"
)
```

---

### ファイルアップロード設定

ファイルアップロードの制限設定。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| MAX_UPLOAD_SIZE | integer | 10485760 | × | 最大アップロードサイズ（バイト） |

#### 設定例

```bash
# 10MB
MAX_UPLOAD_SIZE=10485760

# 50MB
MAX_UPLOAD_SIZE=52428800

# 100MB
MAX_UPLOAD_SIZE=104857600
```

#### サイズ計算

```python
# バイト単位
1KB = 1024
1MB = 1024 * 1024 = 1048576
10MB = 10 * 1024 * 1024 = 10485760
```

#### 使用例

```python
from app.core.config import settings

if file.size > settings.MAX_UPLOAD_SIZE:
    raise ValueError(f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE} bytes")
```

---

## 環境別設定例

### 開発環境（.env.local）

```bash
# Application
APP_NAME="camp-backend"
VERSION="0.1.0"
DEBUG=true
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# Environment
ENVIRONMENT=development

# Security
SECRET_KEY=dev-secret-key-change-in-production-must-be-32-chars-minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_DURATION_HOURS=1

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_db
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
TEST_DATABASE_ADMIN_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
TEST_DATABASE_NAME=test_db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=true

# Redis Cache
REDIS_URL=redis://localhost:6379/0
REDIS_PORT=6379
CACHE_TTL=300

# Storage
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads

# LLM
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=4096
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# File Upload
MAX_UPLOAD_SIZE=10485760

# LangSmith (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__xxxxxxxxxxxxx
LANGCHAIN_PROJECT=ai-agent-app-dev
```

---

### ステージング環境（.env.staging）

```bash
# Application
APP_NAME="camp-backend (Staging)"
VERSION="0.1.0"
DEBUG=false
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["https://staging.example.com"]

# Environment
ENVIRONMENT=staging

# Security
SECRET_KEY=your-staging-secret-key-here-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_DURATION_HOURS=1

# Database
DATABASE_URL=postgresql+asyncpg://username:password@staging-db-host:5432/staging_db
TEST_DATABASE_URL=postgresql+asyncpg://username:password@staging-db-host:5432/staging_test_db
TEST_DATABASE_ADMIN_URL=postgresql+asyncpg://username:password@staging-db-host:5432/postgres
TEST_DATABASE_NAME=staging_test_db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=true

# Redis Cache
REDIS_URL=redis://staging-redis-host:6379/0
CACHE_TTL=300

# Storage
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_NAME=your_staging_storage_account_name
AZURE_STORAGE_CONNECTION_STRING=your_staging_azure_connection_string
AZURE_STORAGE_CONTAINER_NAME=staging-uploads

# LLM
LLM_PROVIDER=azure_openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=4096
AZURE_OPENAI_ENDPOINT=https://your-staging-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_staging_azure_openai_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# File Upload
MAX_UPLOAD_SIZE=10485760

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_staging_langsmith_api_key
LANGCHAIN_PROJECT=ai-agent-app-staging
```

---

### 本番環境（.env.production）

```bash
# Application
APP_NAME="camp-backend"
VERSION="0.1.0"
DEBUG=false
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["https://example.com","https://www.example.com"]

# Environment
ENVIRONMENT=production

# Security
SECRET_KEY=your-production-secret-key-here-must-be-changed
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_DURATION_HOURS=1

# Database
DATABASE_URL=postgresql+asyncpg://prod_user:secure_password@production-db-host:5432/production_db
TEST_DATABASE_URL=postgresql+asyncpg://prod_user:secure_password@production-db-host:5432/test_db
TEST_DATABASE_ADMIN_URL=postgresql+asyncpg://prod_user:secure_password@production-db-host:5432/postgres
TEST_DATABASE_NAME=test_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=true

# Redis Cache
REDIS_URL=redis://production-redis-host:6379/0
CACHE_TTL=300

# Storage
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_NAME=your_production_storage_account_name
AZURE_STORAGE_CONNECTION_STRING=your_production_azure_connection_string
AZURE_STORAGE_CONTAINER_NAME=production-uploads

# LLM
LLM_PROVIDER=azure_openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=4096
AZURE_OPENAI_ENDPOINT=https://your-production-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_production_azure_openai_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# File Upload
MAX_UPLOAD_SIZE=10485760

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_production_langsmith_api_key
LANGCHAIN_PROJECT=ai-agent-app-production
```

---

## 設定の優先順位

環境変数の読み込み優先順位（高い順）:

1. **環境変数**（システムまたはシェルで設定）
2. **環境別.envファイル**（`.env.{environment}`）
3. **デフォルト値**（`config.py`で定義）

### 環境ファイルの選択

`ENVIRONMENT`環境変数に基づいて読み込まれるファイルが決定されます：

```bash
# ENVIRONMENT=development（デフォルト）
.env.local が読み込まれる

# ENVIRONMENT=staging
.env.staging が読み込まれる

# ENVIRONMENT=production
.env.production が読み込まれる
```

### 優先順位の例

```bash
# 1. デフォルト値（config.py）
DEBUG = False

# 2. .env.local ファイル
DEBUG=true

# 3. 環境変数（最優先）
export DEBUG=false
```

結果: `DEBUG=false`（環境変数が優先）

### 環境切り替えの例

```bash
# ローカル開発環境で起動（.env.localを使用）
uv run uvicorn app.main:app --reload

# ステージング環境で起動（.env.stagingを使用）
ENVIRONMENT=staging uv run uvicorn app.main:app

# 本番環境で起動（.env.productionを使用）
ENVIRONMENT=production uv run uvicorn app.main:app
```

---

## 環境変数の検証

### 必須チェック

本番環境で必須の環境変数:

```bash
# 必須項目チェックスクリプト
python -c "
from app.core.config import settings

required = [
    'SECRET_KEY',
    'DATABASE_URL',
]

for var in required:
    value = getattr(settings, var)
    if not value or value == 'your-secret-key-here-change-in-production':
        print(f'ERROR: {var} must be set')
        exit(1)

print('All required environment variables are set')
"
```

---

## トラブルシューティング

### 環境変数が読み込まれない

```bash
# .envファイルの場所を確認
ls -la .env.local

# どのファイルが読み込まれているか確認
python -c "from app.core.config import get_env_file; print(get_env_file())"

# 環境変数の値を確認
python -c "from app.core.config import settings; print(settings.DEBUG)"

# .envファイルの文字エンコーディング確認（UTF-8であること）
file -i .env.local
```

### DATABASE_URLが無効

```bash
# 接続テスト
python -c "
from app.core.database import engine
import asyncio

async def test():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('Connection successful:', result.scalar())

asyncio.run(test())
"
```

### APIキーが無効

```bash
# APIキーの確認（先頭と末尾のみ表示）
python -c "
from app.core.config import settings
key = settings.ANTHROPIC_API_KEY
if key:
    print(f'Key: {key[:10]}...{key[-5:]}')
else:
    print('API key not set')
"
```

---

## 参考リンク

- [Pydantic Settings公式ドキュメント](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI設定と環境変数](https://fastapi.tiangolo.com/advanced/settings/)
- [12 Factor App - Config](https://12factor.net/ja/config)
- [環境変数のベストプラクティス](https://docs.docker.com/compose/environment-variables/)
