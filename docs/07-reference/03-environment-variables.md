# 環境変数リファレンス

バックエンドアプリケーションで使用される全ての環境変数の詳細を記載します。

## 目次

- [概要](#概要)
- [設定ファイル](#設定ファイル)
- [環境変数一覧](#環境変数一覧)
  - [アプリケーション設定](#アプリケーション設定)
  - [環境設定](#環境設定)
  - [データベース設定](#データベース設定)
  - [Redis Cache設定](#redis-cache設定)
  - [ストレージ設定](#ストレージ設定)
  - [LLM設定](#llm設定)
  - [ファイルアップロード設定](#ファイルアップロード設定)
  - [セキュリティ設定](#セキュリティ設定)
- [環境別設定例](#環境別設定例)
- [設定の優先順位](#設定の優先順位)

---

## 概要

### 設定管理

このプロジェクトでは**Pydantic Settings**を使用して環境変数を管理しています。

- 型安全な設定管理
- `.env`ファイルからの自動読み込み
- バリデーション機能
- デフォルト値の提供

### 設定クラス

`src/app/config.py`で定義されています。

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
```

---

## 設定ファイル

### .envファイルの場所

```
backend/
├── .env                    # 環境変数ファイル（gitignore対象）
├── .env.example            # 環境変数テンプレート
└── src/
    └── app/
        └── config.py       # 設定クラス
```

### .env.exampleからのコピー

```bash
# 初回セットアップ
cp .env.example .env

# 必要な値を編集
nano .env
```

---

## 環境変数一覧

### アプリケーション設定

FastAPIアプリケーションの基本設定。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| APP_NAME | string | "AI Agent App" | × | アプリケーション名 |
| VERSION | string | "0.1.0" | × | アプリケーションバージョン |
| DEBUG | boolean | false | × | デバッグモード（開発時はtrue） |
| HOST | string | "0.0.0.0" | × | サーバーホスト |
| PORT | integer | 8000 | × | サーバーポート |
| ALLOWED_ORIGINS | list[string] | ["*"] | × | CORS許可オリジン |

#### 設定例

```bash
APP_NAME="AI Agent App"
VERSION="0.1.0"
DEBUG=true
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

#### 使用例

```python
from app.config import settings

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
from app.config import settings

if settings.ENVIRONMENT == "production":
    # 本番環境用の設定
    setup_production_logging()
```

---

### データベース設定

データベース接続の設定。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| DATABASE_URL | string | "sqlite+aiosqlite:///./app.db" | × | データベース接続URL |

#### 設定例

```bash
# SQLite（開発環境）
DATABASE_URL=sqlite+aiosqlite:///./app.db

# PostgreSQL（本番環境）
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# PostgreSQL（SSL接続）
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname?ssl=require
```

#### 接続URL形式

```
# SQLite
sqlite+aiosqlite:///<path>

# PostgreSQL
postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>

# MySQL
mysql+aiomysql://<user>:<password>@<host>:<port>/<database>
```

#### 使用例

```python
from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(settings.DATABASE_URL)
```

---

### Redis Cache設定

Redisキャッシュの設定（オプション）。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| REDIS_URL | string | null | × | Redis接続URL |
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

```
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
from app.config import settings
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
| AZURE_STORAGE_CONNECTION_STRING | string | null | △ | Azure Storage接続文字列 |
| AZURE_STORAGE_CONTAINER_NAME | string | "uploads" | × | Azureコンテナ名 |

#### 設定例

**ローカルストレージ（開発環境）**

```bash
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads
```

**Azure Blob Storage（本番環境）**

```bash
STORAGE_BACKEND=azure
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=xxx;EndpointSuffix=core.windows.net"
AZURE_STORAGE_CONTAINER_NAME=uploads
```

#### 使用例

```python
from app.config import settings
from app.storage import get_storage_backend

storage = get_storage_backend()
await storage.upload(file_path, content)
```

---

### LLM設定

言語モデルAPIの設定。

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
from app.config import settings
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
from app.config import settings

if file.size > settings.MAX_UPLOAD_SIZE:
    raise ValueError(f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE} bytes")
```

---

### セキュリティ設定

認証・認可のためのセキュリティ設定。

| 変数名 | 型 | デフォルト値 | 必須 | 説明 |
|-------|---|------------|------|------|
| SECRET_KEY | string | "your-secret-key-here-change-in-production" | ○ | JWT署名用の秘密鍵 |
| ALGORITHM | string | "HS256" | × | JWT署名アルゴリズム |
| ACCESS_TOKEN_EXPIRE_MINUTES | integer | 30 | × | アクセストークンの有効期限（分） |

#### 設定例

```bash
# ランダムな秘密鍵を生成
SECRET_KEY=your-random-secret-key-here-at-least-32-characters-long

# JWTアルゴリズム
ALGORITHM=HS256

# トークン有効期限（分）
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 秘密鍵の生成

```bash
# Pythonで生成
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSLで生成
openssl rand -base64 32
```

#### 使用例

```python
from app.config import settings
from app.core.security import create_access_token

token = create_access_token(
    data={"sub": user.email},
    expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
)
```

---

## 環境別設定例

### 開発環境（.env.development）

```bash
# Application
APP_NAME="AI Agent App"
VERSION="0.1.0"
DEBUG=true
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["http://localhost:3000"]

# Environment
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Redis Cache (Optional)
# REDIS_URL=redis://localhost:6379/0
# CACHE_TTL=300

# Storage
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads

# LLM
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Security
SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LangSmith (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__xxxxxxxxxxxxx
LANGCHAIN_PROJECT=ai-agent-app-dev
```

---

### ステージング環境（.env.staging）

```bash
# Application
APP_NAME="AI Agent App"
VERSION="0.1.0"
DEBUG=false
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["https://staging.example.com"]

# Environment
ENVIRONMENT=staging

# Database
DATABASE_URL=postgresql+asyncpg://user:password@db-staging.example.com:5432/aiagent_staging

# Redis Cache
REDIS_URL=redis://redis-staging.example.com:6379/0
CACHE_TTL=300

# Storage
STORAGE_BACKEND=azure
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=mystaging;AccountKey=xxx;EndpointSuffix=core.windows.net"
AZURE_STORAGE_CONTAINER_NAME=uploads-staging

# LLM
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Security
SECRET_KEY=staging-secret-key-32-characters-min
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__xxxxxxxxxxxxx
LANGCHAIN_PROJECT=ai-agent-app-staging
```

---

### 本番環境（.env.production）

```bash
# Application
APP_NAME="AI Agent App"
VERSION="0.1.0"
DEBUG=false
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["https://example.com", "https://www.example.com"]

# Environment
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+asyncpg://user:password@db-prod.example.com:5432/aiagent_production?ssl=require

# Redis Cache
REDIS_URL=redis://redis-prod.example.com:6379/0
CACHE_TTL=600  # 10分

# Storage
STORAGE_BACKEND=azure
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=myprod;AccountKey=xxx;EndpointSuffix=core.windows.net"
AZURE_STORAGE_CONTAINER_NAME=uploads

# LLM
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# File Upload
MAX_UPLOAD_SIZE=52428800  # 50MB

# Security
SECRET_KEY=production-secret-key-use-strong-random-value
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__xxxxxxxxxxxxx
LANGCHAIN_PROJECT=ai-agent-app-production
```

---

## 設定の優先順位

環境変数の読み込み優先順位（高い順）:

1. **環境変数**（システムまたはシェルで設定）
2. **.envファイル**（プロジェクトルート）
3. **デフォルト値**（`config.py`で定義）

### 例

```bash
# 1. デフォルト値（config.py）
DEBUG = False

# 2. .envファイル
DEBUG=true

# 3. 環境変数（最優先）
export DEBUG=false
```

結果: `DEBUG=false`（環境変数が優先）

---

## 環境変数の検証

### 必須チェック

本番環境で必須の環境変数:

```bash
# 必須項目チェックスクリプト
python -c "
from app.config import settings

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
ls -la .env

# 環境変数の値を確認
python -c "from app.config import settings; print(settings.DEBUG)"

# .envファイルの文字エンコーディング確認（UTF-8であること）
file -i .env
```

### DATABASE_URLが無効

```bash
# 接続テスト
python -c "
from app.database import engine
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
from app.config import settings
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
