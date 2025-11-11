# 環境設定設計書（Environment Configuration）

## 📋 文書管理情報

| 項目 | 内容 |
|------|------|
| **文書名** | 環境設定設計書（Environment Configuration） |
| **バージョン** | 1.0.0 |
| **作成日** | 2025-01-11 |
| **最終更新日** | 2025-01-11 |
| **作成者** | Claude Code |
| **対象システム** | genai-app-docs (camp-backend) |
| **関連文書** | [インフラ設計書](./01-infrastructure-design.md), [セキュリティ実装](../03-security/03-security-implementation.md) |

---

## 📑 目次

1. [概要](#1-概要)
2. [環境変数リファレンス](#2-環境変数リファレンス)
3. [環境別設定](#3-環境別設定)
4. [シークレット管理](#4-シークレット管理)
5. [設定バリデーション](#5-設定バリデーション)
6. [設定の優先順位](#6-設定の優先順位)
7. [デプロイ手順](#7-デプロイ手順)
8. [トラブルシューティング](#8-トラブルシューティング)
9. [付録](#9-付録)

---

## 1. 概要

### 1.1 目的

本設計書は、genai-app-docsプロジェクトの環境設定を文書化し、以下を達成することを目的とします：

- **環境変数の完全なリファレンス**: すべての設定項目の説明と使用方法
- **環境別設定の標準化**: development/staging/production環境の設定ガイドライン
- **シークレット管理の明確化**: 機密情報の安全な管理方法
- **設定エラーの防止**: バリデーションルールとトラブルシューティング

### 1.2 適用範囲

本設計書は以下を対象とします：

- ✅ すべての環境変数の定義と説明
- ✅ 環境別（local/staging/production）の設定
- ✅ 機密情報（シークレット）の管理方法
- ✅ 設定バリデーションルール
- ✅ デプロイ時の設定手順

### 1.3 環境設定アーキテクチャ

```mermaid
graph TB
    subgraph "設定の読み込み順序"
        A[1. 環境変数<br/>最優先] --> B[2. .env.{environment}<br/>環境別設定]
        B --> C[3. .env<br/>共通設定]
        C --> D[4. デフォルト値<br/>Settings クラス]
    end

    subgraph "環境別ファイル"
        E[.env.local<br/>開発環境]
        F[.env.staging<br/>ステージング]
        G[.env.production<br/>本番環境]
    end

    subgraph "設定管理"
        H[Pydantic Settings<br/>型安全・バリデーション]
        I[Azure Key Vault<br/>シークレット管理]
    end

    E --> H
    F --> H
    G --> I
    I --> H

    style A fill:#51cf66
    style B fill:#74c0fc
    style C fill:#ffd43b
    style D fill:#ff8787
    style I fill:#ff6b6b
```

### 1.4 設定カテゴリ

本システムの環境変数は以下のカテゴリに分類されます：

| カテゴリ | 設定数 | 主要項目 |
|---------|-------|---------|
| **アプリケーション** | 6 | APP_NAME, VERSION, DEBUG, HOST, PORT, ALLOWED_ORIGINS |
| **環境** | 1 | ENVIRONMENT |
| **セキュリティ** | 7 | SECRET_KEY, ALGORITHM, レート制限、ログイン制限 |
| **データベース** | 8 | DATABASE_URL, 接続プール設定 |
| **Redis** | 3 | REDIS_URL, CACHE_TTL |
| **ストレージ** | 5 | STORAGE_BACKEND, Azure Blob設定 |
| **LLM** | 12 | LLM_PROVIDER, APIキー、モデル設定 |
| **認証** | 8 | AUTH_MODE, Azure AD設定 |

---

## 2. 環境変数リファレンス

### 2.1 アプリケーション設定

#### APP_NAME

- **型**: `string`
- **デフォルト**: `"camp-backend"`
- **説明**: アプリケーション名（ログ、メトリクスで使用）
- **設定例**:

  ```bash
  # 開発環境
  APP_NAME=camp-backend

  # ステージング環境
  APP_NAME="camp-backend (Staging)"

  # 本番環境
  APP_NAME=camp-backend
  ```

#### VERSION

- **型**: `string`
- **デフォルト**: `"0.1.0"`
- **説明**: アプリケーションバージョン（Semantic Versioning）
- **設定例**:

  ```bash
  VERSION=0.1.0
  VERSION=1.2.3
  ```

#### DEBUG

- **型**: `boolean`
- **デフォルト**: `false`
- **説明**: デバッグモードの有効化
- **影響**:
  - `true`: SQLクエリログ、詳細エラー、開発用機能を有効化
  - `false`: 本番モード、エラーの詳細を非表示
- **設定例**:

  ```bash
  # 開発環境
  DEBUG=true

  # 本番環境（必須）
  DEBUG=false
  ```

- **⚠️ 警告**: 本番環境で`DEBUG=true`は**禁止**（情報漏洩リスク）

#### HOST

- **型**: `string`
- **デフォルト**: `"0.0.0.0"`
- **説明**: サーバーのバインドアドレス
- **設定例**:

  ```bash
  # すべてのインターフェースでリッスン
  HOST=0.0.0.0

  # ローカルホストのみ
  HOST=127.0.0.1
  ```

#### PORT

- **型**: `int`
- **デフォルト**: `8000`
- **説明**: サーバーのリッスンポート
- **設定例**:

  ```bash
  PORT=8000
  PORT=8080
  ```

#### ALLOWED_ORIGINS

- **型**: `list[string]` (JSON形式)
- **デフォルト**: 環境依存
  - development: `["http://localhost:3000", "http://localhost:5173"]`
  - staging: `["https://staging.example.com"]`
  - production: **必須設定（デフォルトなし）**
- **説明**: CORS許可オリジンリスト
- **設定例**:

  ```bash
  # 開発環境（複数のローカルホスト）
  ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]

  # ステージング環境
  ALLOWED_ORIGINS=["https://staging.example.com"]

  # 本番環境（複数ドメイン）
  ALLOWED_ORIGINS=["https://example.com","https://www.example.com"]
  ```

- **⚠️ 警告**: 本番環境で`["*"]`（ワイルドカード）は**禁止**

### 2.2 環境設定

#### ENVIRONMENT

- **型**: `Literal["development", "staging", "production"]`
- **デフォルト**: `"development"`
- **説明**: 実行環境の識別子
- **影響**:
  - `.env.{environment}`ファイルの選択
  - セキュリティバリデーションの厳格さ
  - デフォルト設定の適用
- **設定例**:

  ```bash
  ENVIRONMENT=development
  ENVIRONMENT=staging
  ENVIRONMENT=production
  ```

### 2.3 セキュリティ設定

#### SECRET_KEY

- **型**: `string`
- **デフォルト**: `"dev-secret-key-change-in-production-must-be-32-chars-minimum"` (開発用)
- **最小長**: 32文字
- **説明**: JWT署名、暗号化に使用するシークレットキー
- **生成方法**:

  ```bash
  # OpenSSLを使用
  openssl rand -hex 32

  # Pythonを使用
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- **設定例**:

  ```bash
  # ✅ 正しい例（32文字以上）
  SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

  # ❌ 間違った例（短すぎる）
  SECRET_KEY=secret123
  ```

- **⚠️ 重要**:
  - 本番環境では**必須変更**
  - デフォルト値を使用すると`ValueError`が発生
  - 漏洩した場合は即座に再生成が必要

#### ALGORITHM

- **型**: `string`
- **デフォルト**: `"HS256"`
- **説明**: JWT署名アルゴリズム
- **推奨値**: `HS256` (HMAC-SHA256)
- **設定例**:

  ```bash
  ALGORITHM=HS256
  ```

#### ACCESS_TOKEN_EXPIRE_MINUTES

- **型**: `int`
- **デフォルト**: `30`
- **説明**: JWTアクセストークンの有効期限（分）
- **推奨範囲**: 15-60分
- **設定例**:

  ```bash
  # 短い有効期限（高セキュリティ）
  ACCESS_TOKEN_EXPIRE_MINUTES=15

  # 標準（推奨）
  ACCESS_TOKEN_EXPIRE_MINUTES=30

  # 長い有効期限（開発環境のみ）
  ACCESS_TOKEN_EXPIRE_MINUTES=60
  ```

#### RATE_LIMIT_CALLS

- **型**: `int`
- **デフォルト**: `100`
- **説明**: レート制限のリクエスト数
- **設定例**:

  ```bash
  # 厳しい制限
  RATE_LIMIT_CALLS=50

  # 標準（推奨）
  RATE_LIMIT_CALLS=100

  # 緩い制限（開発環境）
  RATE_LIMIT_CALLS=1000
  ```

#### RATE_LIMIT_PERIOD

- **型**: `int`
- **デフォルト**: `60`
- **説明**: レート制限の期間（秒）
- **設定例**:

  ```bash
  # 1分間
  RATE_LIMIT_PERIOD=60

  # 5分間
  RATE_LIMIT_PERIOD=300
  ```

#### MAX_LOGIN_ATTEMPTS

- **型**: `int`
- **デフォルト**: `5`
- **説明**: アカウントロックまでのログイン失敗回数
- **設定例**:

  ```bash
  MAX_LOGIN_ATTEMPTS=5
  MAX_LOGIN_ATTEMPTS=3  # より厳格
  ```

#### ACCOUNT_LOCK_DURATION_HOURS

- **型**: `int`
- **デフォルト**: `1`
- **説明**: アカウントロック期間（時間）
- **設定例**:

  ```bash
  ACCOUNT_LOCK_DURATION_HOURS=1
  ACCOUNT_LOCK_DURATION_HOURS=24  # 1日間ロック
  ```

### 2.4 データベース設定

#### DATABASE_URL

- **型**: `string`
- **デフォルト**: `"postgresql+asyncpg://postgres:postgres@localhost:5432/app_db"`
- **説明**: PostgreSQLデータベース接続URL（asyncpg使用）
- **形式**: `postgresql+asyncpg://username:password@host:port/database`
- **設定例**:

  ```bash
  # 開発環境（ローカル）
  DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db

  # ステージング環境
  DATABASE_URL=postgresql+asyncpg://staging_user:staging_pass@staging-db.example.com:5432/camp_backend_db_staging

  # 本番環境（SSL必須）
  DATABASE_URL=postgresql+asyncpg://prod_user:secure_password@production-db.example.com:5432/camp_backend_db?ssl=require
  ```

- **⚠️ 警告**:
  - 本番環境でパスワードは**強力なもの**を使用
  - SSL接続を推奨（`?ssl=require`）

#### TEST_DATABASE_URL

- **型**: `string`
- **デフォルト**: `"postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"`
- **説明**: テストデータベース接続URL（pytest用）
- **設定例**:

  ```bash
  TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db_test
  ```

#### TEST_DATABASE_ADMIN_URL

- **型**: `string`
- **デフォルト**: `"postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"`
- **説明**: テストDB作成・削除用の管理者接続URL
- **設定例**:

  ```bash
  TEST_DATABASE_ADMIN_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
  ```

#### TEST_DATABASE_NAME

- **型**: `string`
- **デフォルト**: `"test_db"`
- **説明**: テストデータベース名
- **設定例**:

  ```bash
  TEST_DATABASE_NAME=camp_backend_db_test
  ```

#### DB_POOL_SIZE

- **型**: `int`
- **デフォルト**: `5`
- **説明**: データベース接続プールの通常サイズ
- **推奨値**:
  - 開発: 5
  - ステージング: 5-10
  - 本番: 10-20
- **設定例**:

  ```bash
  # 開発環境
  DB_POOL_SIZE=5

  # 本番環境（高トラフィック）
  DB_POOL_SIZE=20
  ```

#### DB_MAX_OVERFLOW

- **型**: `int`
- **デフォルト**: `10`
- **説明**: ピーク時の追加接続数（プールサイズを超えた場合）
- **計算式**: 最大接続数 = `DB_POOL_SIZE + DB_MAX_OVERFLOW`
- **設定例**:

  ```bash
  DB_MAX_OVERFLOW=10
  DB_MAX_OVERFLOW=20  # 本番環境
  ```

#### DB_POOL_RECYCLE

- **型**: `int`
- **デフォルト**: `1800` (30分)
- **説明**: 接続の再利用期限（秒）
- **説明**: この時間が経過すると接続が自動的にリサイクルされる
- **設定例**:

  ```bash
  DB_POOL_RECYCLE=1800  # 30分
  DB_POOL_RECYCLE=3600  # 1時間
  ```

#### DB_POOL_PRE_PING

- **型**: `boolean`
- **デフォルト**: `true`
- **説明**: 接続使用前のPINGチェック（切断検出）
- **推奨**: `true`（常に有効化）
- **設定例**:

  ```bash
  DB_POOL_PRE_PING=true
  ```

### 2.5 Redis設定

#### REDIS_URL

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Redis接続URL（キャッシュ、レート制限用）
- **形式**: `redis://host:port/database`
- **設定例**:

  ```bash
  # 開発環境（ローカル）
  REDIS_URL=redis://localhost:6379/0

  # ステージング環境
  REDIS_URL=redis://staging-redis.example.com:6379/0

  # 本番環境（パスワード付き）
  REDIS_URL=redis://:password@production-redis.example.com:6379/0

  # Azure Redis Cache（SSL）
  REDIS_URL=rediss://:password@myredis.redis.cache.windows.net:6380/0
  ```

- **⚠️ 注意**: `None`の場合、インメモリキャッシュにフォールバック

#### CACHE_TTL

- **型**: `int`
- **デフォルト**: `300` (5分)
- **説明**: デフォルトキャッシュTTL（秒）
- **設定例**:

  ```bash
  CACHE_TTL=300   # 5分
  CACHE_TTL=600   # 10分
  CACHE_TTL=3600  # 1時間
  ```

### 2.6 ストレージ設定

#### STORAGE_BACKEND

- **型**: `Literal["local", "azure"]`
- **デフォルト**: `"local"`
- **説明**: ファイルストレージバックエンド
- **設定例**:

  ```bash
  # 開発環境
  STORAGE_BACKEND=local

  # 本番環境
  STORAGE_BACKEND=azure
  ```

#### LOCAL_STORAGE_PATH

- **型**: `string`
- **デフォルト**: `"./uploads"`
- **説明**: ローカルストレージのパス
- **設定例**:

  ```bash
  LOCAL_STORAGE_PATH=./uploads
  LOCAL_STORAGE_PATH=/var/app/uploads
  ```

#### AZURE_STORAGE_ACCOUNT_NAME

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Azure Storageアカウント名
- **必須条件**: `STORAGE_BACKEND=azure`の場合に必須
- **設定例**:

  ```bash
  AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount
  ```

#### AZURE_STORAGE_CONNECTION_STRING

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Azure Storage接続文字列
- **必須条件**: `STORAGE_BACKEND=azure`の場合に必須
- **設定例**:

  ```bash
  AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=mykey;EndpointSuffix=core.windows.net"
  ```

- **⚠️ 警告**: 機密情報のため、Azure Key Vaultで管理推奨

#### AZURE_STORAGE_CONTAINER_NAME

- **型**: `string`
- **デフォルト**: `"uploads"`
- **説明**: Azure Blob Storageコンテナ名
- **設定例**:

  ```bash
  AZURE_STORAGE_CONTAINER_NAME=uploads
  AZURE_STORAGE_CONTAINER_NAME=production-uploads
  ```

### 2.7 LLM設定

#### LLM_PROVIDER

- **型**: `Literal["anthropic", "openai", "azure_openai"]`
- **デフォルト**: `"anthropic"`
- **説明**: LLMプロバイダーの選択
- **設定例**:

  ```bash
  # Claude（Anthropic）
  LLM_PROVIDER=anthropic

  # OpenAI
  LLM_PROVIDER=openai

  # Azure OpenAI
  LLM_PROVIDER=azure_openai
  ```

#### LLM_MODEL

- **型**: `string`
- **デフォルト**: `"claude-3-5-sonnet-20241022"`
- **説明**: 使用するLLMモデル名
- **設定例**:

  ```bash
  # Anthropic Claude
  LLM_MODEL=claude-3-5-sonnet-20241022
  LLM_MODEL=claude-3-opus-20240229

  # OpenAI
  LLM_MODEL=gpt-4
  LLM_MODEL=gpt-3.5-turbo

  # Azure OpenAI
  LLM_MODEL=gpt-4  # デプロイメント名と一致させる
  ```

#### LLM_TEMPERATURE

- **型**: `float`
- **デフォルト**: `0.0`
- **説明**: モデルの温度パラメータ（ランダム性）
- **範囲**: 0.0-1.0
  - `0.0`: 決定的（一貫性重視）
  - `1.0`: ランダム（創造性重視）
- **設定例**:

  ```bash
  LLM_TEMPERATURE=0.0   # 決定的
  LLM_TEMPERATURE=0.7   # バランス
  LLM_TEMPERATURE=1.0   # 創造的
  ```

#### LLM_MAX_TOKENS

- **型**: `int`
- **デフォルト**: `4096`
- **説明**: 最大トークン数（レスポンス長）
- **設定例**:

  ```bash
  LLM_MAX_TOKENS=4096
  LLM_MAX_TOKENS=8192
  ```

#### ANTHROPIC_API_KEY

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Anthropic APIキー
- **必須条件**: `LLM_PROVIDER=anthropic`の場合に必須（本番環境）
- **設定例**:

  ```bash
  ANTHROPIC_API_KEY=sk-ant-api03-...
  ```

#### OPENAI_API_KEY

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: OpenAI APIキー
- **必須条件**: `LLM_PROVIDER=openai`の場合に必須（本番環境）
- **設定例**:

  ```bash
  OPENAI_API_KEY=sk-...
  ```

#### AZURE_OPENAI_ENDPOINT

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Azure OpenAIエンドポイント
- **必須条件**: `LLM_PROVIDER=azure_openai`の場合に必須（本番環境）
- **設定例**:

  ```bash
  AZURE_OPENAI_ENDPOINT=https://myresource.openai.azure.com/
  ```

#### AZURE_OPENAI_API_KEY

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Azure OpenAI APIキー
- **必須条件**: `LLM_PROVIDER=azure_openai`の場合に必須（本番環境）
- **設定例**:

  ```bash
  AZURE_OPENAI_API_KEY=1234567890abcdef...
  ```

#### AZURE_OPENAI_API_VERSION

- **型**: `string`
- **デフォルト**: `"2024-02-15-preview"`
- **説明**: Azure OpenAI APIバージョン
- **設定例**:

  ```bash
  AZURE_OPENAI_API_VERSION=2024-02-15-preview
  ```

#### AZURE_OPENAI_DEPLOYMENT_NAME

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Azure OpenAIデプロイメント名
- **必須条件**: `LLM_PROVIDER=azure_openai`の場合に必須（本番環境）
- **設定例**:

  ```bash
  AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-deployment
  ```

#### LANGCHAIN_TRACING_V2

- **型**: `boolean`
- **デフォルト**: `false`
- **説明**: LangSmithトレーシングの有効化
- **設定例**:

  ```bash
  LANGCHAIN_TRACING_V2=true
  LANGCHAIN_TRACING_V2=false
  ```

#### LANGCHAIN_API_KEY

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: LangSmith APIキー
- **必須条件**: `LANGCHAIN_TRACING_V2=true`の場合に必須
- **設定例**:

  ```bash
  LANGCHAIN_API_KEY=ls__...
  ```

#### LANGCHAIN_PROJECT

- **型**: `string`
- **デフォルト**: `"camp-backend"`
- **説明**: LangSmithプロジェクト名
- **設定例**:

  ```bash
  LANGCHAIN_PROJECT=camp-backend-dev
  LANGCHAIN_PROJECT=camp-backend-production
  ```

### 2.8 認証設定

#### AUTH_MODE

- **型**: `Literal["development", "production"]`
- **デフォルト**: `"development"`
- **説明**: 認証モードの選択
  - `development`: モック認証（固定トークン）
  - `production`: Azure AD認証
- **設定例**:

  ```bash
  # 開発環境
  AUTH_MODE=development

  # 本番環境（必須）
  AUTH_MODE=production
  ```

- **⚠️ 警告**: `ENVIRONMENT=production`かつ`AUTH_MODE=development`は**禁止**

#### AZURE_TENANT_ID

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Azure ADテナントID
- **必須条件**: `AUTH_MODE=production`の場合に必須
- **設定例**:

  ```bash
  AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
  ```

#### AZURE_CLIENT_ID

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Azure ADアプリケーション（クライアント）ID（バックエンド用）
- **必須条件**: `AUTH_MODE=production`の場合に必須
- **設定例**:

  ```bash
  AZURE_CLIENT_ID=87654321-4321-4321-4321-210987654321
  ```

#### AZURE_CLIENT_SECRET

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Azure ADクライアントシークレット（オプション）
- **設定例**:

  ```bash
  AZURE_CLIENT_SECRET=my-client-secret-value
  ```

#### AZURE_OPENAPI_CLIENT_ID

- **型**: `string | None`
- **デフォルト**: `None`
- **説明**: Azure ADアプリケーションID（Swagger UI用）
- **設定例**:

  ```bash
  AZURE_OPENAPI_CLIENT_ID=abcdefgh-abcd-abcd-abcd-abcdefghijkl
  ```

#### DEV_MOCK_TOKEN

- **型**: `string`
- **デフォルト**: `"mock-access-token-dev-12345"`
- **説明**: 開発モード用モックトークン
- **設定例**:

  ```bash
  DEV_MOCK_TOKEN=mock-access-token-dev-12345
  ```

#### DEV_MOCK_USER_EMAIL

- **型**: `string`
- **デフォルト**: `"dev.user@example.com"`
- **説明**: 開発モード用モックユーザーメール
- **設定例**:

  ```bash
  DEV_MOCK_USER_EMAIL=dev.user@example.com
  ```

#### DEV_MOCK_USER_OID

- **型**: `string`
- **デフォルト**: `"dev-azure-oid-12345"`
- **説明**: 開発モード用モックAzure Object ID
- **設定例**:

  ```bash
  DEV_MOCK_USER_OID=dev-azure-oid-12345
  ```

#### DEV_MOCK_USER_NAME

- **型**: `string`
- **デフォルト**: `"Development User"`
- **説明**: 開発モード用モックユーザー表示名
- **設定例**:

  ```bash
  DEV_MOCK_USER_NAME="Development User"
  ```

### 2.9 ファイルアップロード設定

#### MAX_UPLOAD_SIZE

- **型**: `int`
- **デフォルト**: `10485760` (10MB)
- **説明**: ファイルアップロードの最大サイズ（バイト）
- **設定例**:

  ```bash
  # 10MB
  MAX_UPLOAD_SIZE=10485760

  # 50MB
  MAX_UPLOAD_SIZE=52428800

  # 100MB
  MAX_UPLOAD_SIZE=104857600
  ```

---

## 3. 環境別設定

### 3.1 開発環境（Local）

**ファイル**: `.env.local`

**特徴**:

- デバッグモード有効
- ローカルサービス（PostgreSQL、Redis）使用
- 緩いレート制限
- モック認証可能

**最小設定例**:

```bash
# ==============================================================================
# 開発環境用設定
# ==============================================================================

# 環境識別
ENVIRONMENT=development
DEBUG=true

# アプリケーション
APP_NAME=camp-backend
PORT=8000
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# セキュリティ（開発用）
SECRET_KEY=dev-secret-key-change-in-production-must-be-32-chars-minimum
RATE_LIMIT_CALLS=1000  # 開発環境では緩い制限

# データベース（ローカル）
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db_test

# Redis（ローカル）
REDIS_URL=redis://localhost:6379/0

# ストレージ（ローカル）
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads

# LLM（Anthropic）
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-api03-...  # 開発用APIキー

# 認証（モック）
AUTH_MODE=development
DEV_MOCK_TOKEN=mock-access-token-dev-12345
```

**Docker Compose統合**:

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: camp_backend_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 3.2 ステージング環境（Staging）

**ファイル**: `.env.staging`

**特徴**:

- 本番に近い設定
- Azure AD認証使用
- Azure Storage使用
- 本番同等のレート制限

**設定例**:

```bash
# ==============================================================================
# ステージング環境用設定
# ==============================================================================

# 環境識別
ENVIRONMENT=staging
DEBUG=false

# アプリケーション
APP_NAME="camp-backend (Staging)"
PORT=8000
ALLOWED_ORIGINS=["https://staging.example.com"]

# セキュリティ（ステージング用シークレット）
# ⚠️ 必ず変更: openssl rand -hex 32
SECRET_KEY=<ステージング環境用の32文字以上のランダム文字列>
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# データベース（Azure PostgreSQL）
DATABASE_URL=postgresql+asyncpg://staging_user:staging_password@staging-postgresql.postgres.database.azure.com:5432/camp_backend_db_staging?ssl=require
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis（Azure Redis Cache）
REDIS_URL=rediss://:staging_redis_password@staging-redis.redis.cache.windows.net:6380/0
CACHE_TTL=300

# ストレージ（Azure Blob Storage）
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_NAME=stagingstorage123
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=stagingstorage123;AccountKey=...;EndpointSuffix=core.windows.net"
AZURE_STORAGE_CONTAINER_NAME=staging-uploads

# LLM（Azure OpenAI）
LLM_PROVIDER=azure_openai
LLM_MODEL=gpt-4
AZURE_OPENAI_ENDPOINT=https://staging-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=<staging_azure_openai_key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-deployment

# LangSmith（トレーシング）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<langsmith_staging_key>
LANGCHAIN_PROJECT=camp-backend-staging

# 認証（Azure AD）
AUTH_MODE=production
AZURE_TENANT_ID=<staging_tenant_id>
AZURE_CLIENT_ID=<staging_backend_client_id>
AZURE_CLIENT_SECRET=<staging_client_secret>
AZURE_OPENAPI_CLIENT_ID=<staging_frontend_client_id>
```

### 3.3 本番環境（Production）

**ファイル**: `.env.production`

**特徴**:

- 最高レベルのセキュリティ
- すべてのバリデーション有効
- Azure Key Vault推奨
- 厳格な設定要件

**設定例**:

```bash
# ==============================================================================
# 本番環境用設定
# ==============================================================================

# 環境識別
ENVIRONMENT=production
DEBUG=false  # 必須: false

# アプリケーション
APP_NAME=camp-backend
PORT=8000
ALLOWED_ORIGINS=["https://example.com","https://www.example.com"]  # 必須設定

# セキュリティ（本番用シークレット）
# ⚠️ 必須: 32文字以上のランダム文字列
SECRET_KEY=<本番環境用の強力なシークレットキー>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_DURATION_HOURS=1

# データベース（Azure PostgreSQL）
DATABASE_URL=postgresql+asyncpg://prod_user:prod_secure_password@production-postgresql.postgres.database.azure.com:5432/camp_backend_db?ssl=require
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=true

# Redis（Azure Redis Cache）
REDIS_URL=rediss://:prod_redis_password@production-redis.redis.cache.windows.net:6380/0
CACHE_TTL=300

# ストレージ（Azure Blob Storage）
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_NAME=prodstorage123
AZURE_STORAGE_CONNECTION_STRING="<Azure Key Vaultから取得>"
AZURE_STORAGE_CONTAINER_NAME=production-uploads

# LLM（Azure OpenAI）
LLM_PROVIDER=azure_openai
LLM_MODEL=gpt-4
AZURE_OPENAI_ENDPOINT=https://production-openai.openai.azure.com/
AZURE_OPENAI_API_KEY="<Azure Key Vaultから取得>"
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-production

# LangSmith（トレーシング）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY="<Azure Key Vaultから取得>"
LANGCHAIN_PROJECT=camp-backend-production

# 認証（Azure AD）必須
AUTH_MODE=production  # 必須: production
AZURE_TENANT_ID=<production_tenant_id>
AZURE_CLIENT_ID=<production_backend_client_id>
AZURE_CLIENT_SECRET="<Azure Key Vaultから取得>"
AZURE_OPENAPI_CLIENT_ID=<production_frontend_client_id>

# ファイルアップロード
MAX_UPLOAD_SIZE=10485760
```

**⚠️ 本番環境チェックリスト**:

- [ ] `DEBUG=false`
- [ ] `SECRET_KEY`が32文字以上でランダム
- [ ] `ALLOWED_ORIGINS`が明示的に設定され、ワイルドカードなし
- [ ] `AUTH_MODE=production`
- [ ] Azure AD設定が正しく設定されている
- [ ] データベースURLがSSL使用（`?ssl=require`）
- [ ] すべてのAPIキーがAzure Key Vaultで管理されている

---

## 4. シークレット管理

### 4.1 Azure Key Vault統合

**概要**:

Azure Key Vaultは機密情報（パスワード、APIキー、接続文字列）を安全に保存・管理するサービスです。

```mermaid
graph LR
    A[アプリケーション] --> B[Azure Key Vault]
    B --> C[SECRET_KEY]
    B --> D[DATABASE_URL]
    B --> E[ANTHROPIC_API_KEY]
    B --> F[AZURE_STORAGE_CONNECTION_STRING]

    style B fill:#51cf66
    style C fill:#ff6b6b
    style D fill:#ff6b6b
    style E fill:#ff6b6b
    style F fill:#ff6b6b
```

### 4.2 Key Vault設定手順

#### ステップ1: Key Vaultの作成

```bash
# Azure CLIでKey Vaultを作成
az keyvault create \
  --name "camp-backend-keyvault" \
  --resource-group "camp-backend-rg" \
  --location "japaneast"
```

#### ステップ2: シークレットの追加

```bash
# SECRET_KEYを追加
az keyvault secret set \
  --vault-name "camp-backend-keyvault" \
  --name "SECRET-KEY" \
  --value "$(openssl rand -hex 32)"

# DATABASE_URLを追加
az keyvault secret set \
  --vault-name "camp-backend-keyvault" \
  --name "DATABASE-URL" \
  --value "postgresql+asyncpg://prod_user:secure_password@prod-db.postgres.database.azure.com:5432/camp_backend_db?ssl=require"

# ANTHROPIC_API_KEYを追加
az keyvault secret set \
  --vault-name "camp-backend-keyvault" \
  --name "ANTHROPIC-API-KEY" \
  --value "sk-ant-api03-..."
```

#### ステップ3: アクセス権限の付与

```bash
# Managed IdentityにKey Vaultアクセス権を付与
az keyvault set-policy \
  --name "camp-backend-keyvault" \
  --object-id <managed-identity-object-id> \
  --secret-permissions get list
```

### 4.3 アプリケーションでの使用

**Python実装例**（将来実装）:

```python
# src/app/core/secrets.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class SecretManager:
    """Azure Key Vaultからシークレットを取得"""

    def __init__(self, vault_url: str):
        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)

    def get_secret(self, name: str) -> str:
        """シークレットを取得"""
        secret = self.client.get_secret(name)
        return secret.value

# 使用例
if settings.ENVIRONMENT == "production":
    secret_manager = SecretManager("https://camp-backend-keyvault.vault.azure.net/")
    settings.SECRET_KEY = secret_manager.get_secret("SECRET-KEY")
    settings.DATABASE_URL = secret_manager.get_secret("DATABASE-URL")
```

### 4.4 GitHub Secrets統合

**CI/CDでのシークレット管理**:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Azure
        env:
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # デプロイスクリプト実行
          ./deploy.sh
```

**GitHub Secretsの設定方法**:

1. GitHubリポジトリ → Settings → Secrets and variables → Actions
2. "New repository secret"をクリック
3. シークレット名と値を入力
4. "Add secret"で保存

---

## 5. 設定バリデーション

### 5.1 起動時バリデーション

**Pydantic Settingsによる自動バリデーション**:

```python
# src/app/core/config.py
class Settings(BaseSettings):
    """設定クラス（自動バリデーション付き）"""

    @model_validator(mode="before")
    @classmethod
    def validate_dev_auth_not_in_production(cls, values: dict[str, Any]) -> dict[str, Any]:
        """本番環境で開発モード認証を禁止"""
        if values.get("ENVIRONMENT") == "production" and values.get("AUTH_MODE") == "development":
            raise ValueError(
                "Development authentication cannot be enabled in production environment. "
                "Set AUTH_MODE=production for production."
            )
        return values

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # カスタムバリデーション
        self._validate_cors_settings()
        self._validate_security_settings()
        self._validate_llm_config()
        self._validate_database_config()
        self._validate_storage_config()
        self._validate_azure_ad_config()
```

### 5.2 バリデーションルール

#### 本番環境の必須チェック

| 項目 | チェック内容 | エラーメッセージ |
|------|-------------|-----------------|
| **DEBUG** | `DEBUG=false`必須 | "DEBUG must be False in production" |
| **SECRET_KEY** | 32文字以上、デフォルト値以外 | "SECRET_KEY must be set in production. Generate one with: openssl rand -hex 32" |
| **ALLOWED_ORIGINS** | 明示的に設定、ワイルドカード禁止 | "ALLOWED_ORIGINS must be set in production" |
| **AUTH_MODE** | `AUTH_MODE=production`必須 | "AUTH_MODE must be 'production' in production environment" |
| **DATABASE_URL** | `asyncpg`ドライバー使用 | "DATABASE_URL must use asyncpg driver (postgresql+asyncpg://)" |
| **Azure AD** | TENANT_ID, CLIENT_ID設定 | "AUTH_MODE=production requires AZURE_TENANT_ID and AZURE_CLIENT_ID" |

### 5.3 設定検証スクリプト

**手動検証スクリプト**:

```bash
#!/bin/bash
# scripts/validate-config.sh

# 環境変数を読み込み
source .env.production

# 検証関数
check_required() {
  local var_name=$1
  local var_value="${!var_name}"

  if [ -z "$var_value" ]; then
    echo "❌ ERROR: $var_name is not set"
    return 1
  else
    echo "✅ OK: $var_name is set"
    return 0
  fi
}

check_length() {
  local var_name=$1
  local var_value="${!var_name}"
  local min_length=$2

  if [ ${#var_value} -lt $min_length ]; then
    echo "❌ ERROR: $var_name must be at least $min_length characters"
    return 1
  else
    echo "✅ OK: $var_name length is sufficient"
    return 0
  fi
}

echo "=== Configuration Validation ==="

# 必須項目チェック
check_required "SECRET_KEY" || exit 1
check_required "DATABASE_URL" || exit 1
check_required "ALLOWED_ORIGINS" || exit 1
check_required "AZURE_TENANT_ID" || exit 1
check_required "AZURE_CLIENT_ID" || exit 1

# 長さチェック
check_length "SECRET_KEY" 32 || exit 1

# DEBUGモードチェック
if [ "$DEBUG" = "true" ]; then
  echo "❌ ERROR: DEBUG must be 'false' in production"
  exit 1
else
  echo "✅ OK: DEBUG is disabled"
fi

# 開発認証チェック
if [ "$ENVIRONMENT" = "production" ] && [ "$AUTH_MODE" = "development" ]; then
  echo "❌ ERROR: Development authentication cannot be enabled in production"
  exit 1
else
  echo "✅ OK: Authentication mode is valid"
fi

echo "=== All checks passed ✅ ==="
```

**実行方法**:

```bash
# 設定検証
bash scripts/validate-config.sh

# 出力例
=== Configuration Validation ===
✅ OK: SECRET_KEY is set
✅ OK: DATABASE_URL is set
✅ OK: ALLOWED_ORIGINS is set
✅ OK: AZURE_TENANT_ID is set
✅ OK: AZURE_CLIENT_ID is set
✅ OK: SECRET_KEY length is sufficient
✅ OK: DEBUG is disabled
✅ OK: Authentication mode is valid
=== All checks passed ✅ ===
```

---

## 6. 設定の優先順位

### 6.1 読み込み順序

Pydantic Settingsは以下の順序で設定を読み込みます（後のものが優先）：

```text
1. Settingsクラスのデフォルト値（最低優先度）
   ↓
2. .env（共通設定ファイル）
   ↓
3. .env.{environment}（環境別設定ファイル）
   ↓
4. 環境変数（最高優先度）
```

### 6.2 優先順位の例

**設定ファイル**:

```bash
# .env（共通設定）
SECRET_KEY=common-secret-key
DATABASE_URL=postgresql://localhost/common_db
PORT=8000

# .env.production（本番環境設定）
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://prod-db/production_db
# PORTは指定なし

# 環境変数
export PORT=9000
```

**最終的な設定**:

```python
settings.SECRET_KEY  # → "production-secret-key" (.env.productionから)
settings.DATABASE_URL  # → "postgresql://prod-db/production_db" (.env.productionから)
settings.PORT  # → 9000 (環境変数から)
```

### 6.3 環境変数によるオーバーライド

**ユースケース**: CI/CDパイプラインで一時的に設定を変更

```bash
# GitHub Actions
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  SECRET_KEY: ${{ secrets.SECRET_KEY }}

# Docker Compose
environment:
  - DATABASE_URL=${DATABASE_URL}
  - SECRET_KEY=${SECRET_KEY}

# Kubernetes
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: database-url
```

---

## 7. デプロイ手順

### 7.1 ローカル開発環境

#### ステップ1: リポジトリのクローン

```bash
git clone https://github.com/yourorg/camp-backend.git
cd camp-backend
```

#### ステップ2: 環境ファイルの作成

```bash
# サンプルファイルをコピー
cp .env.local.example .env.local

# エディタで編集
vim .env.local
```

#### ステップ3: 依存関係のインストール

```bash
# uvを使用
uv sync

# または pipenv
pipenv install
```

#### ステップ4: データベースのセットアップ

```bash
# Docker ComposeでPostgreSQL起動
docker-compose up -d postgres redis

# マイグレーション実行
uv run alembic upgrade head
```

#### ステップ5: アプリケーションの起動

```bash
# 開発サーバー起動
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7.2 ステージング環境

#### ステップ1: Azure リソースの作成

```bash
# リソースグループ作成
az group create --name camp-backend-staging-rg --location japaneast

# PostgreSQL作成
az postgres flexible-server create \
  --name camp-backend-staging-db \
  --resource-group camp-backend-staging-rg \
  --location japaneast \
  --admin-user dbadmin \
  --admin-password <secure-password> \
  --sku-name Standard_B2s \
  --tier Burstable \
  --version 16

# Redis Cache作成
az redis create \
  --name camp-backend-staging-redis \
  --resource-group camp-backend-staging-rg \
  --location japaneast \
  --sku Basic \
  --vm-size c0

# Storage Account作成
az storage account create \
  --name campbackendstagingst \
  --resource-group camp-backend-staging-rg \
  --location japaneast \
  --sku Standard_LRS
```

#### ステップ2: 環境設定ファイルの準備

```bash
# .env.stagingを作成
cp .env.staging.example .env.staging

# Azure リソースの接続情報を設定
vim .env.staging
```

#### ステップ3: GitHub Secretsの設定

```bash
# GitHub CLIを使用
gh secret set SECRET_KEY < secret_key.txt
gh secret set DATABASE_URL < database_url.txt
gh secret set AZURE_STORAGE_CONNECTION_STRING < storage_connection.txt
```

#### ステップ4: CI/CDパイプラインのトリガー

```bash
git push origin staging
```

### 7.3 本番環境

#### ステップ1: Azure Key Vaultの設定

```bash
# Key Vault作成
az keyvault create \
  --name camp-backend-prod-kv \
  --resource-group camp-backend-prod-rg \
  --location japaneast

# シークレット追加
az keyvault secret set --vault-name camp-backend-prod-kv \
  --name SECRET-KEY --value "$(openssl rand -hex 32)"

az keyvault secret set --vault-name camp-backend-prod-kv \
  --name DATABASE-URL --value "<production-database-url>"
```

#### ステップ2: Managed Identityの設定

```bash
# App ServiceにManaged Identityを有効化
az webapp identity assign \
  --name camp-backend-prod-app \
  --resource-group camp-backend-prod-rg

# Managed IdentityにKey Vaultアクセス権を付与
az keyvault set-policy \
  --name camp-backend-prod-kv \
  --object-id <managed-identity-object-id> \
  --secret-permissions get list
```

#### ステップ3: デプロイ

```bash
# メインブランチへのマージでCI/CDトリガー
git checkout main
git merge staging
git push origin main
```

---

## 8. トラブルシューティング

### 8.1 よくある問題と解決方法

#### 問題1: SECRET_KEY長さエラー

**エラーメッセージ**:

```text
ValueError: String should have at least 32 characters
```

**原因**: `SECRET_KEY`が32文字未満

**解決方法**:

```bash
# 新しいシークレットキーを生成
openssl rand -hex 32

# .envファイルに設定
SECRET_KEY=<生成された64文字の文字列>
```

#### 問題2: ALLOWED_ORIGINS未設定

**エラーメッセージ**:

```text
ValueError: 本番環境ではALLOWED_ORIGINSを明示的に設定する必要があります
```

**原因**: 本番環境で`ALLOWED_ORIGINS`が未設定

**解決方法**:

```bash
# .env.productionに追加
ALLOWED_ORIGINS=["https://example.com","https://www.example.com"]
```

#### 問題3: 開発認証が本番環境で有効

**エラーメッセージ**:

```text
ValueError: Development authentication cannot be enabled in production environment. Set AUTH_MODE=production for production.
```

**原因**: `ENVIRONMENT=production`かつ`AUTH_MODE=development`

**解決方法**:

```bash
# .env.productionで修正
AUTH_MODE=production
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
```

#### 問題4: データベース接続エラー

**エラーメッセージ**:

```text
asyncpg.exceptions.InvalidPasswordError: password authentication failed
```

**原因**: データベースURLのパスワードが間違っている

**解決方法**:

```bash
# 正しい接続URLを確認
DATABASE_URL=postgresql+asyncpg://username:correct_password@host:5432/database

# Azure PostgreSQLの場合、ユーザー名の形式を確認
# 形式: username@servername
DATABASE_URL=postgresql+asyncpg://dbadmin@camp-backend-db:password@camp-backend-db.postgres.database.azure.com:5432/camp_backend_db
```

#### 問題5: Redis接続エラー

**エラーメッセージ**:

```text
redis.exceptions.ConnectionError: Error connecting to Redis
```

**原因**: Redisが起動していない、または接続情報が間違っている

**解決方法**:

```bash
# ローカルRedisの起動確認
docker ps | grep redis

# Redis接続URLの確認
REDIS_URL=redis://localhost:6379/0

# Azure Redis Cacheの場合、SSL使用
REDIS_URL=rediss://:password@myredis.redis.cache.windows.net:6380/0
```

#### 問題6: LLM APIキー未設定

**エラーメッセージ**:

```text
ValueError: LLM_PROVIDER=anthropicの場合、ANTHROPIC_API_KEYが必要です
```

**原因**: 本番環境でLLM APIキーが未設定

**解決方法**:

```bash
# Anthropicの場合
ANTHROPIC_API_KEY=sk-ant-api03-...

# Azure OpenAIの場合
AZURE_OPENAI_ENDPOINT=https://myresource.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-deployment
```

### 8.2 設定デバッグ方法

#### 現在の設定値を確認

```python
# Pythonインタラクティブシェル
from app.core.config import settings

# すべての設定を表示
print(settings.model_dump())

# 特定の設定を確認
print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"DEBUG: {settings.DEBUG}")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"AUTH_MODE: {settings.AUTH_MODE}")
```

#### 環境変数の読み込み確認

```bash
# 環境変数が正しく設定されているか確認
env | grep -E "SECRET_KEY|DATABASE_URL|ENVIRONMENT"

# .envファイルの内容を確認
cat .env.local | grep -v "^#"
```

#### ログで設定を確認

```python
# src/app/core/config.py
import structlog

logger = structlog.get_logger(__name__)

# 設定初期化時にログ出力
logger.info(
    "Configuration loaded",
    environment=settings.ENVIRONMENT,
    debug=settings.DEBUG,
    auth_mode=settings.AUTH_MODE,
    llm_provider=settings.LLM_PROVIDER,
    storage_backend=settings.STORAGE_BACKEND,
)
```

---

## 9. 付録

### 9.1 完全な環境変数チェックリスト

**本番環境デプロイ前チェックリスト**:

```markdown
## 必須設定

- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `SECRET_KEY`（32文字以上、ランダム）
- [ ] `ALLOWED_ORIGINS`（ワイルドカードなし）
- [ ] `DATABASE_URL`（SSL使用）
- [ ] `AUTH_MODE=production`
- [ ] `AZURE_TENANT_ID`
- [ ] `AZURE_CLIENT_ID`

## データベース

- [ ] `DATABASE_URL`（本番DB接続情報）
- [ ] `DB_POOL_SIZE`（適切な値）
- [ ] `DB_MAX_OVERFLOW`（適切な値）
- [ ] SSL証明書の検証

## キャッシュ

- [ ] `REDIS_URL`（本番Redis接続情報）
- [ ] Redis接続テスト完了

## ストレージ

- [ ] `STORAGE_BACKEND=azure`（推奨）
- [ ] `AZURE_STORAGE_ACCOUNT_NAME`
- [ ] `AZURE_STORAGE_CONNECTION_STRING`

## LLM

- [ ] LLMプロバイダー選択
- [ ] APIキー設定（Key Vault推奨）
- [ ] デプロイメント名確認（Azure OpenAI）

## セキュリティ

- [ ] レート制限設定
- [ ] ログイン試行制限
- [ ] Azure Key Vault統合
- [ ] すべてのシークレットをKey Vaultで管理

## モニタリング

- [ ] LangSmithトレーシング設定（オプション）
- [ ] ログ集約設定
- [ ] アラート設定
```

### 9.2 環境変数テンプレート生成スクリプト

```bash
#!/bin/bash
# scripts/generate-env-template.sh

ENV_FILE="${1:-.env.production}"

cat > "$ENV_FILE" << 'EOF'
# ==============================================================================
# 本番環境用設定テンプレート
# ==============================================================================

# アプリケーション設定
ENVIRONMENT=production
DEBUG=false
APP_NAME=camp-backend
PORT=8000
ALLOWED_ORIGINS=["https://example.com"]

# セキュリティ設定
# ⚠️ 必ず変更: openssl rand -hex 32
SECRET_KEY=REPLACE_WITH_RANDOM_32_CHAR_STRING
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# データベース設定
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database?ssl=require
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Redis設定
REDIS_URL=rediss://:password@host:6380/0
CACHE_TTL=300

# ストレージ設定
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_NAME=REPLACE_WITH_STORAGE_ACCOUNT
AZURE_STORAGE_CONNECTION_STRING=REPLACE_WITH_CONNECTION_STRING
AZURE_STORAGE_CONTAINER_NAME=production-uploads

# LLM設定
LLM_PROVIDER=azure_openai
LLM_MODEL=gpt-4
AZURE_OPENAI_ENDPOINT=REPLACE_WITH_ENDPOINT
AZURE_OPENAI_API_KEY=REPLACE_WITH_API_KEY
AZURE_OPENAI_DEPLOYMENT_NAME=REPLACE_WITH_DEPLOYMENT

# 認証設定
AUTH_MODE=production
AZURE_TENANT_ID=REPLACE_WITH_TENANT_ID
AZURE_CLIENT_ID=REPLACE_WITH_CLIENT_ID
AZURE_CLIENT_SECRET=REPLACE_WITH_CLIENT_SECRET
AZURE_OPENAPI_CLIENT_ID=REPLACE_WITH_OPENAPI_CLIENT_ID
EOF

echo "✅ Environment template created: $ENV_FILE"
echo "⚠️  Please replace all REPLACE_WITH_* placeholders with actual values"
```

### 9.3 参考資料

**公式ドキュメント**:

- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI Configuration](https://fastapi.tiangolo.com/advanced/settings/)
- [Azure Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/)
- [12 Factor App - Config](https://12factor.net/config)

**ベストプラクティス**:

- [OWASP Configuration Management](https://owasp.org/www-project-proactive-controls/v3/en/c10-errors-exceptions)
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|----------|--------|
| 1.0.0 | 2025-01-11 | 初版作成 | Claude Code |

---
