# デプロイメント

このガイドでは、本番環境へのデプロイ手順と設定方法を説明します。

## 目次

- [概要](#概要)
- [前提条件](#前提条件)
- [ステップバイステップ](#ステップバイステップ)
- [チェックリスト](#チェックリスト)
- [よくある落とし穴](#よくある落とし穴)
- [ベストプラクティス](#ベストプラクティス)
- [参考リンク](#参考リンク)

## 概要

本番環境へのデプロイには以下の要素が含まれます：

```text
デプロイメント構成
├── Docker化
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── 環境設定
│   ├── .env.local              # ローカル開発環境（gitignore）
│   ├── .env.staging            # ステージング環境（gitignore）
│   ├── .env.production         # 本番環境（gitignore）
│   ├── .env.local.example      # ローカル環境テンプレート
│   ├── .env.staging.example    # ステージング環境テンプレート
│   └── .env.production.example # 本番環境テンプレート
├── CI/CD
│   └── GitHub Actions / Azure DevOps
├── インフラ
│   ├── Azure App Service
│   ├── Azure Container Instances
│   └── Kubernetes (オプション)
└── モニタリング
    ├── ログ収集
    ├── メトリクス
    └── アラート
```

## 前提条件

- Dockerの基礎知識
- クラウドプラットフォームの理解（Azure推奨）
- CI/CDの基礎知識
- 環境変数管理の理解

## ステップバイステップ

### 1. Docker化

#### 1.1 Dockerfileの作成

`Dockerfile`を作成：

```dockerfile
# マルチステージビルド
FROM python:3.11-slim as builder

# 作業ディレクトリ
WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry のインストール
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# 依存関係のインストール
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# 本番イメージ
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# システムパッケージ（最小限）
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ビルドステージから依存関係をコピー
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードをコピー
COPY ./src /app/src
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

# 非rootユーザーの作成
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ポート公開
EXPOSE 8000

# 環境変数
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# エントリーポイント
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.2 .dockerignoreの作成

`.dockerignore`を作成：

```text
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
venv/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Tests
.pytest_cache/
.coverage
htmlcov/
.tox/

# Environment
.env.local
.env.staging
.env.production
!.env.local.example
!.env.staging.example
!.env.production.example

# Data
*.db
*.sqlite3
uploads/
logs/

# Git
.git/
.gitignore

# Documentation
docs/
*.md
!README.md

# CI/CD
.github/
.gitlab-ci.yml

# OS
.DS_Store
Thumbs.db
```

#### 1.3 docker-compose.ymlの作成

`docker-compose.yml`を作成（開発・ステージング用）：

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/appdb
      - STORAGE_BACKEND=local
      - LOCAL_STORAGE_PATH=/app/uploads
    volumes:
      - ./src:/app/src  # 開発時のホットリロード
      - uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=appdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  uploads:
```

`docker-compose.prod.yml`を作成（本番用）：

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    volumes:
      - uploads:/app/uploads
      - logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  postgres:
    image: postgres:15-alpine
    restart: always
    env_file:
      - .env.production
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static:/var/www/static:ro
    depends_on:
      - app

volumes:
  postgres_data:
  uploads:
  logs:
  static:
```

### 2. 環境設定

#### 2.1 環境変数ファイル

開発環境用テンプレート `.env.local.example` の例：

```bash
# Application
APP_NAME=camp-backend
VERSION=0.1.0
ENVIRONMENT=development
DEBUG=false
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["http://localhost:3000"]

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/appdb

# Storage
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads

# Azure Storage (for production)
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER_NAME=uploads

# LLM Configuration
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT_NAME=

# LangSmith (optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=ai-agent-app

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
```

`.env.production`を作成（本番環境用）：

```bash
# Application
APP_NAME=camp-backend
VERSION=0.1.0
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Database (Azure Database for PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user@server:password@server.postgres.database.azure.com:5432/appdb?sslmode=require

# Storage (Azure Blob)
STORAGE_BACKEND=azure
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_NAME=uploads

# LLM Configuration
ANTHROPIC_API_KEY=sk-ant-...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=ai-agent-app-prod

# Security (強力なキーを使用)
SECRET_KEY=<generate-strong-key-here>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# File Upload
MAX_UPLOAD_SIZE=52428800  # 50MB
```

#### 2.2 秘密鍵の生成

```python
# generate_secret_key.py
import secrets

def generate_secret_key(length: int = 64) -> str:
    """セキュアな秘密鍵を生成します。"""
    return secrets.token_urlsafe(length)

if __name__ == "__main__":
    print(f"SECRET_KEY={generate_secret_key()}")
```

実行：

```bash
python generate_secret_key.py
```

### 3. Nginxの設定

`nginx.conf`を作成：

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name yourdomain.com;

        # HTTPSへリダイレクト
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL証明書
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # セキュリティヘッダー
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # ファイルアップロードサイズ
        client_max_body_size 50M;

        # タイムアウト
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # API リクエスト
        location /api {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check (rate limitなし)
        location /health {
            proxy_pass http://app;
            access_log off;
        }

        # 静的ファイル
        location /static {
            alias /var/www/static;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # ドキュメント
        location /docs {
            proxy_pass http://app;
        }

        location /redoc {
            proxy_pass http://app;
        }
    }
}
```

### 4. Azure App Serviceへのデプロイ

#### 4.1 Azure CLIの設定

```bash
# Azure CLIのインストール
# https://docs.microsoft.com/cli/azure/install-azure-cli

# ログイン
az login

# リソースグループの作成
az group create \
  --name ai-agent-rg \
  --location japaneast

# Azure Container Registryの作成
az acr create \
  --name aiagentacr \
  --resource-group ai-agent-rg \
  --sku Basic \
  --admin-enabled true

# Azure Database for PostgreSQLの作成
az postgres flexible-server create \
  --name ai-agent-db \
  --resource-group ai-agent-rg \
  --location japaneast \
  --admin-user dbadmin \
  --admin-password <strong-password> \
  --sku-name Standard_B1ms \
  --storage-size 32 \
  --version 15

# データベースの作成
az postgres flexible-server db create \
  --resource-group ai-agent-rg \
  --server-name ai-agent-db \
  --database-name appdb

# ファイアウォールルール（Azureサービスからのアクセスを許可）
az postgres flexible-server firewall-rule create \
  --resource-group ai-agent-rg \
  --name ai-agent-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### 4.2 Dockerイメージのビルドとプッシュ

```bash
# ACRにログイン
az acr login --name aiagentacr

# イメージのビルド
docker build -t ai-agent-app:latest .

# タグ付け
docker tag ai-agent-app:latest aiagentacr.azurecr.io/ai-agent-app:latest

# プッシュ
docker push aiagentacr.azurecr.io/ai-agent-app:latest
```

#### 4.3 App Serviceの作成とデプロイ

```bash
# App Service Planの作成
az appservice plan create \
  --name ai-agent-plan \
  --resource-group ai-agent-rg \
  --is-linux \
  --sku B1

# Web Appの作成
az webapp create \
  --name ai-agent-app \
  --resource-group ai-agent-rg \
  --plan ai-agent-plan \
  --deployment-container-image-name aiagentacr.azurecr.io/ai-agent-app:latest

# ACRの認証情報を設定
az webapp config container set \
  --name ai-agent-app \
  --resource-group ai-agent-rg \
  --docker-registry-server-url https://aiagentacr.azurecr.io \
  --docker-registry-server-user <acr-username> \
  --docker-registry-server-password <acr-password>

# 環境変数の設定
az webapp config appsettings set \
  --name ai-agent-app \
  --resource-group ai-agent-rg \
  --settings \
    ENVIRONMENT=production \
    DATABASE_URL="postgresql+asyncpg://..." \
    SECRET_KEY="..." \
    ANTHROPIC_API_KEY="..."

# ヘルスチェックの設定
az webapp config set \
  --name ai-agent-app \
  --resource-group ai-agent-rg \
  --health-check-path /health

# 継続的デプロイの有効化
az webapp deployment container config \
  --name ai-agent-app \
  --resource-group ai-agent-rg \
  --enable-cd true
```

### 5. CI/CDパイプライン

#### 5.1 GitHub Actionsの設定

`.github/workflows/deploy.yml`を作成：

```yaml
name: Deploy to Azure

on:
  push:
    branches:
      - main
  workflow_dispatch:

env:
  AZURE_WEBAPP_NAME: ai-agent-app
  ACR_NAME: aiagentacr

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests
        run: |
          poetry run pytest

      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Login to ACR
        uses: azure/docker-login@v1
        with:
          login-server: ${{ env.ACR_NAME }}.azurecr.io
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}

      - name: Build and push Docker image
        run: |
          docker build -t ${{ env.ACR_NAME }}.azurecr.io/ai-agent-app:${{ github.sha }} .
          docker tag ${{ env.ACR_NAME }}.azurecr.io/ai-agent-app:${{ github.sha }} \
                     ${{ env.ACR_NAME }}.azurecr.io/ai-agent-app:latest
          docker push ${{ env.ACR_NAME }}.azurecr.io/ai-agent-app:${{ github.sha }}
          docker push ${{ env.ACR_NAME }}.azurecr.io/ai-agent-app:latest

      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ env.AZURE_WEBAPP_NAME }}
          images: ${{ env.ACR_NAME }}.azurecr.io/ai-agent-app:${{ github.sha }}

      - name: Run database migrations
        run: |
          # マイグレーション実行用のジョブまたはスクリプト
          az webapp ssh --name ${{ env.AZURE_WEBAPP_NAME }} \
                        --resource-group ai-agent-rg \
                        --command "alembic upgrade head"
```

#### 5.2 GitHub Secretsの設定

GitHub リポジトリ → Settings → Secrets and variables → Actions で以下を設定：

- `AZURE_CREDENTIALS`: Azure認証情報（JSONフォーマット）
- `ACR_USERNAME`: Azure Container Registry ユーザー名
- `ACR_PASSWORD`: Azure Container Registry パスワード

Azure認証情報の取得：

```bash
az ad sp create-for-rbac \
  --name "ai-agent-github-actions" \
  --role contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/ai-agent-rg \
  --sdk-auth
```

### 6. マイグレーションスクリプト

`scripts/migrate.sh`を作成：

```bash
#!/bin/bash
set -e

echo "Running database migrations..."

# データベース接続テスト
python -c "
import asyncio
from app.database import engine

async def test_connection():
    async with engine.begin() as conn:
        print('Database connection successful')

asyncio.run(test_connection())
"

# マイグレーション実行
alembic upgrade head

echo "Migrations completed successfully"
```

### 7. モニタリングとログ

#### 7.1 Application Insightsの設定

```bash
# Application Insightsの作成
az monitor app-insights component create \
  --app ai-agent-insights \
  --location japaneast \
  --resource-group ai-agent-rg

# Instrumentation Keyの取得
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app ai-agent-insights \
  --resource-group ai-agent-rg \
  --query instrumentationKey -o tsv)

# Web Appに設定
az webapp config appsettings set \
  --name ai-agent-app \
  --resource-group ai-agent-rg \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

#### 7.2 ログ設定の更新

`src/app/core/logging.py`を更新：

```python
"""ロギング設定（Application Insights統合）。"""

import logging
import sys

from app.config import settings

# Application Insights統合（本番環境）
if settings.ENVIRONMENT == "production":
    from opencensus.ext.azure.log_exporter import AzureLogHandler

    logger = logging.getLogger(__name__)
    logger.addHandler(
        AzureLogHandler(
            connection_string=f"InstrumentationKey={settings.APPINSIGHTS_INSTRUMENTATIONKEY}"
        )
    )
```

## チェックリスト

デプロイメントチェックリスト：

### 準備

- [ ] Dockerfileの作成とテスト
- [ ] docker-compose.ymlの作成
- [ ] .dockerignoreの設定
- [ ] 環境変数テンプレートの整理（.env.*.example）
- [ ] 本番環境用設定ファイルの作成（.env.production）
- [ ] 秘密鍵の生成（本番用）

### セキュリティ

- [ ] HTTPSの設定
- [ ] 強力なSECRET_KEYの設定
- [ ] データベース接続のSSL有効化
- [ ] CORS設定の確認
- [ ] レート制限の設定
- [ ] セキュリティヘッダーの設定

### インフラ

- [ ] Azureリソースグループの作成
- [ ] Azure Container Registryの設定
- [ ] Azure Database for PostgreSQLの設定
- [ ] Azure Blob Storageの設定
- [ ] App Serviceの設定

### CI/CD

- [ ] GitHub Actionsワークフローの作成
- [ ] GitHub Secretsの設定
- [ ] 自動テストの設定
- [ ] 自動デプロイの設定

### データベース

- [ ] マイグレーションスクリプトの準備
- [ ] 本番データベースのバックアップ設定
- [ ] マイグレーションの実行

### モニタリング

- [ ] Application Insightsの設定
- [ ] ログ収集の設定
- [ ] アラートの設定
- [ ] ヘルスチェックの設定

### 最終確認

- [ ] 本番環境でのテスト
- [ ] パフォーマンステスト
- [ ] セキュリティスキャン
- [ ] ドキュメントの更新

## よくある落とし穴

### 1. 環境変数の設定漏れ

```bash
# 悪い例
# 環境変数が設定されていない

# 良い例
az webapp config appsettings set \
  --name ai-agent-app \
  --resource-group ai-agent-rg \
  --settings @appsettings.json
```

### 2. データベース接続のSSL

```python
# 悪い例
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# 良い例
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?sslmode=require
```

### 3. Dockerイメージサイズ

```dockerfile
# 悪い例（大きなイメージ）
FROM python:3.11
RUN pip install -r requirements.txt

# 良い例（最適化されたイメージ）
FROM python:3.11-slim
# マルチステージビルドを使用
```

### 4. シークレットのハードコード

```python
# 悪い例
SECRET_KEY = "hardcoded-secret-key"

# 良い例
SECRET_KEY = os.getenv("SECRET_KEY")
```

## ベストプラクティス

### 1. 環境の分離

```text
開発環境 → ステージング環境 → 本番環境
```

### 2. ブルーグリーンデプロイメント

```bash
# スロットを使用したゼロダウンタイムデプロイ
az webapp deployment slot create \
  --name ai-agent-app \
  --resource-group ai-agent-rg \
  --slot staging

# スワップ
az webapp deployment slot swap \
  --name ai-agent-app \
  --resource-group ai-agent-rg \
  --slot staging
```

### 3. 自動スケーリング

```bash
az monitor autoscale create \
  --resource-group ai-agent-rg \
  --resource ai-agent-plan \
  --resource-type Microsoft.Web/serverFarms \
  --name autoscale-rule \
  --min-count 2 \
  --max-count 5 \
  --count 2
```

### 4. バックアップの自動化

```bash
# データベースバックアップ
az postgres flexible-server backup create \
  --name ai-agent-db \
  --resource-group ai-agent-rg \
  --backup-name daily-backup
```

## 参考リンク

### 公式ドキュメント

- [Azure App Service](https://docs.microsoft.com/azure/app-service/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions](https://docs.github.com/actions)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

### プロジェクト内リンク

- [環境設定](../01-getting-started/02-setup.md)
- [Docker使用方法](../01-getting-started/03-docker.md)
- [セキュリティ](../03-core-concepts/05-security.md)

### 関連ガイド

- [トラブルシューティング](./07-troubleshooting.md)
- [バックグラウンドタスク](./05-background-tasks.md)
