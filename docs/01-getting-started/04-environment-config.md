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
