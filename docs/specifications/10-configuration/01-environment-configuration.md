# 環境設定書

## 1. 概要

本文書は、genai-app-docsシステムの環境設定を定義します。
Pydantic Settingsによる型安全な設定管理を実現しています。

### 1.1 環境設定方針

- **環境別設定**: 開発/ステージング/本番で設定を分離
- **型安全**: Pydanticによるバリデーション
- **セキュアバイデフォルト**: 安全なデフォルト値
- **検証**: 本番環境での必須設定チェック

---

## 2. 環境構成

### 2.1 環境別設定ファイル

```mermaid
graph TB
    App[Application] --> Env{ENVIRONMENT}

    Env -->|development| Local[.env.local]
    Env -->|staging| Staging[.env.staging]
    Env -->|production| Production[.env.production]

    Local --> Config[config.py<br/>Settings]
    Staging --> Config
    Production --> Config

    Config --> Valid{バリデーション}

    Valid -->|OK| Start[アプリケーション起動]
    Valid -->|NG| Error[ValidationError<br/>起動失敗]

    subgraph "開発環境"
        Local
        LocalDB[(PostgreSQL<br/>localhost)]
        LocalRedis[(Redis<br/>localhost)]
        LocalStorage[Local Storage]
    end

    subgraph "ステージング環境"
        Staging
        StagingDB[(Azure PostgreSQL)]
        StagingRedis[(Azure Redis)]
        StagingStorage[Azure Blob Storage]
    end

    subgraph "本番環境"
        Production
        ProdDB[(Azure PostgreSQL<br/>HA構成)]
        ProdRedis[(Azure Redis<br/>Cluster)]
        ProdStorage[Azure Blob Storage<br/>Geo冗長]
    end

    style Local fill:#FFF9C4
    style Staging fill:#FFE082
    style Production fill:#FFD54F
```

### 2.2 環境変数読み込み順序

```mermaid
flowchart LR
    Start[起動] --> EnvVar[1. 環境変数]

    EnvVar --> DotEnv[2. .env.{ENVIRONMENT}ファイル]

    DotEnv --> Default[3. デフォルト値<br/>config.py]

    Default --> Validation[4. Pydanticバリデーション]

    Validation --> OK{バリデーションOK?}

    OK -->|Yes| App[アプリケーション起動]
    OK -->|No| Error[ValidationError<br/>エラーメッセージ出力]

    style App fill:#4CAF50
    style Error fill:#F44336
```

---

## 3. 設定カテゴリ

### 3.1 設定カテゴリ全体図

```mermaid
mindmap
  root((Settings))
    アプリケーション
      APP_NAME
      VERSION
      DEBUG
      ENVIRONMENT
    サーバー
      HOST
      PORT
      WORKERS
      RELOAD
    セキュリティ
      SECRET_KEY
      ALGORITHM
      ACCESS_TOKEN_EXPIRE_MINUTES
    認証
      AUTH_MODE
      Azure AD設定
      開発モック設定
    データベース
      DATABASE_URL
      接続プール設定
    Redis
      REDIS_URL
      CACHE_TTL
    ストレージ
      STORAGE_BACKEND
      Azure Blob設定
    LLM
      LLM_PROVIDER
      API Keys
      モデル設定
    ロギング
      LOG_LEVEL
      LOG_FORMAT
    CORS
      ALLOWED_ORIGINS
```

---

## 4. 設定詳細

### 4.1 アプリケーション設定

**実装**: `src/app/core/config.py` (582行)

| 設定項目 | 型 | デフォルト | 説明 |
|---------|-----|----------|------|
| **APP_NAME** | str | "genai-app-docs" | アプリケーション名 |
| **VERSION** | str | "1.0.0" | バージョン |
| **DEBUG** | bool | False | デバッグモード |
| **ENVIRONMENT** | str | "development" | 環境（development/staging/production） |
| **HOST** | str | "0.0.0.0" | バインドホスト |
| **PORT** | int | 8000 | ポート番号 |
| **WORKERS** | int | 1 | ワーカー数（本番: 4+） |
| **RELOAD** | bool | True（開発のみ） | ホットリロード |

**環境別設定:**

```python
# .env.local
DEBUG=true
ENVIRONMENT=development
RELOAD=true
WORKERS=1

# .env.production
DEBUG=false
ENVIRONMENT=production
RELOAD=false
WORKERS=4
```

### 4.2 セキュリティ設定

| 設定項目 | 型 | デフォルト | 説明 | バリデーション |
|---------|-----|----------|------|-------------|
| **SECRET_KEY** | str | - | JWT署名キー | 本番: 必須（32文字以上） |
| **ALGORITHM** | str | "HS256" | JWT署名アルゴリズム | - |
| **ACCESS_TOKEN_EXPIRE_MINUTES** | int | 60 | アクセストークン有効期限（分） | - |
| **REFRESH_TOKEN_EXPIRE_DAYS** | int | 7 | リフレッシュトークン有効期限（日） | - |

**バリデーション:**

```python
@validator("SECRET_KEY")
def validate_secret_key(cls, v, values):
    """SECRET_KEYバリデーション"""
    if values.get("ENVIRONMENT") == "production":
        if not v or v == "default-secret-key-change-this":
            raise ValueError(
                "SECRET_KEY must be set for production environment"
            )
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters"
            )
    return v
```

### 4.3 認証設定

#### 4.3.1 認証モード

```mermaid
graph LR
    AUTH_MODE{AUTH_MODE} -->|development| Dev[開発モード<br/>モックトークン認証]
    AUTH_MODE -->|production| Prod[本番モード<br/>Azure AD認証]

    Dev --> DevSettings[DEV_MOCK_TOKEN<br/>DEV_MOCK_USER_EMAIL]
    Prod --> AzureSettings[AZURE_TENANT_ID<br/>AZURE_CLIENT_ID<br/>AZURE_CLIENT_SECRET]

    style Dev fill:#FFF9C4
    style Prod fill:#C5E1A5
```

#### 4.3.2 認証設定項目

| 設定項目 | 型 | 必須 | 説明 |
|---------|-----|------|------|
| **AUTH_MODE** | str | Yes | 認証モード（development/production） |
| **DEV_MOCK_TOKEN** | str | 開発時 | モックトークン |
| **DEV_MOCK_USER_EMAIL** | str | 開発時 | モックユーザーメール |
| **AZURE_TENANT_ID** | str | 本番時 | Azure AD テナントID |
| **AZURE_CLIENT_ID** | str | 本番時 | Azure AD クライアントID |
| **AZURE_CLIENT_SECRET** | str | 本番時 | Azure AD クライアントシークレット |

**設定例:**

```bash
# .env.local (開発)
AUTH_MODE=development
DEV_MOCK_TOKEN=mock-access-token-dev-12345
DEV_MOCK_USER_EMAIL=dev.user@example.com

# .env.production (本番)
AUTH_MODE=production
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789abc
AZURE_CLIENT_ID=87654321-4321-4321-4321-cba987654321
AZURE_CLIENT_SECRET=your-client-secret-here
```

### 4.4 データベース設定

| 設定項目 | 型 | デフォルト | 説明 |
|---------|-----|----------|------|
| **DATABASE_URL** | str | - | PostgreSQL接続URL |
| **DB_POOL_SIZE** | int | 5 | 接続プールサイズ |
| **DB_MAX_OVERFLOW** | int | 10 | 最大追加接続数 |
| **DB_POOL_RECYCLE** | int | 1800 | 接続再生成時間（秒） |
| **DB_POOL_PRE_PING** | bool | True | 接続前PING |
| **DB_POOL_TIMEOUT** | int | 30 | 接続タイムアウト（秒） |
| **DB_ECHO** | bool | False | SQLログ出力 |

**設定例:**

```bash
# .env.local
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/genai_app

# .env.production
DATABASE_URL=postgresql+asyncpg://user:password@azure-postgres.postgres.database.azure.com:5432/genai_app?sslmode=require
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### 4.5 Redis設定

| 設定項目 | 型 | デフォルト | 説明 |
|---------|-----|----------|------|
| **REDIS_URL** | str | "redis://localhost:6379/0" | Redis接続URL |
| **CACHE_TTL** | int | 300 | デフォルトキャッシュTTL（秒） |

**設定例:**

```bash
# .env.local
REDIS_URL=redis://localhost:6379/0

# .env.production
REDIS_URL=redis://:password@azure-redis.redis.cache.windows.net:6380?ssl=true
CACHE_TTL=600
```

### 4.6 ストレージ設定

```mermaid
graph LR
    STORAGE_BACKEND{STORAGE_BACKEND}

    STORAGE_BACKEND -->|local| Local[LocalStorageService]
    STORAGE_BACKEND -->|azure| Azure[AzureStorageService]

    Local --> LocalConfig[UPLOAD_DIR<br/>デフォルト: uploads/]
    Azure --> AzureConfig[AZURE_STORAGE_CONNECTION_STRING<br/>AZURE_STORAGE_CONTAINER]

    style Local fill:#4CAF50
    style Azure fill:#2196F3
```

| 設定項目 | 型 | デフォルト | 説明 |
|---------|-----|----------|------|
| **STORAGE_BACKEND** | str | "local" | ストレージバックエンド（local/azure） |
| **UPLOAD_DIR** | str | "uploads" | ローカルアップロードディレクトリ |
| **AZURE_STORAGE_CONNECTION_STRING** | str | - | Azure Storage接続文字列 |
| **AZURE_STORAGE_CONTAINER** | str | "uploads" | Azure Blobコンテナ名 |

**設定例:**

```bash
# .env.local
STORAGE_BACKEND=local
UPLOAD_DIR=uploads

# .env.production
STORAGE_BACKEND=azure
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER=genai-app-uploads
```

### 4.7 LLM設定

```mermaid
graph TB
    LLM_PROVIDER{LLM_PROVIDER}

    LLM_PROVIDER -->|anthropic| Anthropic[Claude]
    LLM_PROVIDER -->|openai| OpenAI[GPT-4]
    LLM_PROVIDER -->|azure_openai| Azure[Azure OpenAI]

    Anthropic --> AnthropicConfig[ANTHROPIC_API_KEY<br/>ANTHROPIC_MODEL]
    OpenAI --> OpenAIConfig[OPENAI_API_KEY<br/>OPENAI_MODEL]
    Azure --> AzureConfig[AZURE_OPENAI_ENDPOINT<br/>AZURE_OPENAI_API_KEY<br/>AZURE_OPENAI_DEPLOYMENT]

    style Anthropic fill:#FF9800
    style OpenAI fill:#4CAF50
    style Azure fill:#2196F3
```

| 設定項目 | 型 | デフォルト | 説明 |
|---------|-----|----------|------|
| **LLM_PROVIDER** | str | "anthropic" | LLMプロバイダー |
| **ANTHROPIC_API_KEY** | str | - | Anthropic APIキー |
| **ANTHROPIC_MODEL** | str | "claude-3-5-sonnet-20241022" | Claudeモデル |
| **OPENAI_API_KEY** | str | - | OpenAI APIキー |
| **OPENAI_MODEL** | str | "gpt-4" | OpenAIモデル |
| **AZURE_OPENAI_ENDPOINT** | str | - | Azure OpenAIエンドポイント |
| **AZURE_OPENAI_API_KEY** | str | - | Azure OpenAI APIキー |
| **AZURE_OPENAI_DEPLOYMENT** | str | - | Azure OpenAIデプロイメント名 |
| **AZURE_OPENAI_API_VERSION** | str | "2024-02-01" | Azure OpenAI APIバージョン |

**設定例:**

```bash
# Anthropic使用
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Azure OpenAI使用
LLM_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01
```

### 4.8 ロギング設定

| 設定項目 | 型 | デフォルト | 説明 |
|---------|-----|----------|------|
| **LOG_LEVEL** | str | "INFO" | ログレベル（DEBUG/INFO/WARNING/ERROR） |
| **LOG_FORMAT** | str | "json" | ログ形式（json/text） |
| **LOG_FILE** | str | None | ログファイルパス（Noneで標準出力） |

**設定例:**

```bash
# .env.local
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# .env.production
LOG_LEVEL=WARNING
LOG_FORMAT=json
LOG_FILE=/var/log/genai-app/app.log
```

### 4.9 CORS設定

| 設定項目 | 型 | デフォルト | 説明 |
|---------|-----|----------|------|
| **ALLOWED_ORIGINS** | list[str] | ["*"] | 許可するオリジン |

**設定例:**

```bash
# .env.local
ALLOWED_ORIGINS=["http://localhost:3000"]

# .env.production
ALLOWED_ORIGINS=["https://app.example.com", "https://www.example.com"]
```

**バリデーション:**

```python
@validator("ALLOWED_ORIGINS")
def validate_allowed_origins(cls, v, values):
    """CORSバリデーション"""
    if values.get("ENVIRONMENT") == "production":
        if "*" in v:
            logger.warning(
                "ALLOWED_ORIGINS contains '*' in production. "
                "This is not recommended for security."
            )
    return v
```

---

## 5. 環境別設定比較

### 5.1 設定比較表

| 設定カテゴリ | 開発環境 | ステージング | 本番環境 |
|------------|---------|------------|---------|
| **DEBUG** | True | False | False |
| **LOG_LEVEL** | DEBUG | INFO | WARNING |
| **AUTH_MODE** | development | production | production |
| **DATABASE_URL** | localhost | Azure PostgreSQL | Azure PostgreSQL (HA) |
| **REDIS_URL** | localhost | Azure Redis | Azure Redis Cluster |
| **STORAGE_BACKEND** | local | azure | azure |
| **LLM_PROVIDER** | anthropic | anthropic | anthropic |
| **WORKERS** | 1 | 2 | 4+ |
| **ALLOWED_ORIGINS** | ["*"] | [ステージングURL] | [本番URL] |

---

## 6. 設定バリデーション

### 6.1 バリデーションフロー

```mermaid
flowchart TB
    Start[アプリケーション起動] --> Load[設定ファイル読み込み]

    Load --> V1{必須項目チェック}

    V1 -->|NG| E1[ValidationError:<br/>Required field missing]

    V1 -->|OK| V2{型チェック}

    V2 -->|NG| E2[ValidationError:<br/>Invalid type]

    V2 -->|OK| V3{フォーマットチェック}

    V3 -->|NG| E3[ValidationError:<br/>Invalid format]

    V3 -->|OK| V4{環境別バリデーション}

    V4 -->|本番環境| ProdCheck[本番環境チェック<br/>SECRET_KEY必須<br/>ALLOWED_ORIGINS必須<br/>Azure AD設定必須]

    ProdCheck -->|NG| E4[ValidationError:<br/>Production settings invalid]

    ProdCheck -->|OK| Success[✅ バリデーション成功]

    V4 -->|開発環境| Success

    Success --> App[アプリケーション起動]

    style Success fill:#4CAF50
    style E1 fill:#F44336
    style E2 fill:#F44336
    style E3 fill:#F44336
    style E4 fill:#F44336
```

### 6.2 バリデーション実装

```python
# src/app/core/config.py

class Settings(BaseSettings):
    """アプリケーション設定"""

    # アプリケーション設定
    APP_NAME: str = "genai-app-docs"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # セキュリティ設定
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # データベース設定
    DATABASE_URL: str

    # CORS設定
    ALLOWED_ORIGINS: list[str] = ["*"]

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        """本番環境でSECRET_KEY必須"""
        if values.get("ENVIRONMENT") == "production":
            if not v or v == "default-secret-key-change-this":
                raise ValueError(
                    "SECRET_KEY must be set and changed for production"
                )
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @validator("ALLOWED_ORIGINS")
    def validate_allowed_origins(cls, v, values):
        """本番環境でワイルドカード警告"""
        if values.get("ENVIRONMENT") == "production" and "*" in v:
            logger.warning(
                "ALLOWED_ORIGINS contains '*' in production. "
                "This is not recommended."
            )
        return v

    @validator("AZURE_TENANT_ID", "AZURE_CLIENT_ID")
    def validate_azure_ad_settings(cls, v, values):
        """本番モードでAzure AD設定必須"""
        if values.get("AUTH_MODE") == "production" and not v:
            raise ValueError(
                "Azure AD settings are required for production auth mode"
            )
        return v

    class Config:
        env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}"
        env_file_encoding = "utf-8"
        case_sensitive = True


# グローバルインスタンス
settings = Settings()
```

---

## 7. 設定の使用

### 7.1 設定へのアクセス

```python
from app.core.config import settings

# アプリケーション設定
app_name = settings.APP_NAME
debug_mode = settings.DEBUG

# データベース設定
database_url = settings.DATABASE_URL

# LLM設定
llm_provider = settings.LLM_PROVIDER
anthropic_api_key = settings.ANTHROPIC_API_KEY
```

### 7.2 環境別設定の切り替え

```bash
# 開発環境で起動
ENVIRONMENT=development uvicorn app.main:app --reload

# ステージング環境で起動
ENVIRONMENT=staging uvicorn app.main:app

# 本番環境で起動
ENVIRONMENT=production uvicorn app.main:app --workers 4
```

---

## 8. まとめ

### 8.1 環境設定の特徴

✅ **型安全**: Pydanticによるバリデーション
✅ **環境別設定**: 開発/ステージング/本番の分離
✅ **セキュアバイデフォルト**: 安全なデフォルト値
✅ **本番検証**: 本番環境での必須設定チェック
✅ **明確なドキュメント**: 全設定項目の説明

### 8.2 セキュリティ推奨事項

❌ **避けるべき:**

- SECRET_KEYを平文でGitにコミット
- 本番環境でDEBUG=True
- ALLOWED_ORIGINS="*"（本番環境）
- デフォルトパスワードの使用

✅ **推奨:**

- 環境変数または秘密管理サービス（Azure Key Vault等）を使用
- 本番環境でDEBUG=False、強力なSECRET_KEY
- 明示的なALLOWED_ORIGINS指定
- APIキーのローテーション

---

**ドキュメント管理情報:**

- **作成日**: 2025年（リバースエンジニアリング実施）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - 認証・認可設計書: `03-security/02-authentication-design.md`
  - セキュリティ実装詳細書: `03-security/03-security-implementation.md`
