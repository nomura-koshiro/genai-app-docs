# デプロイ設計書（Deployment Design）

## 📋 文書管理情報

| 項目 | 内容 |
|------|------|
| **文書名** | デプロイ設計書（Deployment Design） |
| **バージョン** | 1.0.0 |
| **作成日** | 2025-01-11 |
| **最終更新日** | 2025-01-11 |
| **作成者** | Claude Code |
| **レビュー状態** | 初版 |

---

## 📑 目次

1. [概要](#1-概要)
2. [デプロイ戦略](#2-デプロイ戦略)
3. [環境セットアップ](#3-環境セットアップ)
4. [CI/CDパイプライン](#4-cicdパイプライン)
5. [コンテナデプロイ](#5-コンテナデプロイ)
6. [データベースマイグレーション](#6-データベースマイグレーション)
7. [ロールバック戦略](#7-ロールバック戦略)
8. [リリースチェックリスト](#8-リリースチェックリスト)
9. [トラブルシューティング](#9-トラブルシューティング)
10. [付録](#10-付録)

---

## 1. 概要

### 1.1 目的

本設計書は、genai-app-docs（camp-backend）プロジェクトのデプロイメントプロセスを文書化し、以下を達成することを目的とします：

- **デプロイフローの標準化**: 一貫したデプロイ手順の確立
- **リスク低減**: ロールバック戦略とチェックリストによる安全なリリース
- **自動化**: CI/CDパイプラインによる効率的なデプロイ
- **運用ガイド**: デプロイ担当者への明確な手順提供

### 1.2 適用範囲

本設計書は以下を対象とします：

- ✅ 開発環境セットアップ
- ✅ CI/CDパイプライン設計
- ✅ コンテナデプロイ（Docker）
- ✅ データベースマイグレーション
- ✅ ロールバック戦略
- ✅ リリースチェックリスト

以下は**対象外**とし、別の設計書で詳述します：

- ❌ インフラストラクチャの詳細 → [Infrastructure設計書](../05-infrastructure/01-infrastructure-design.md)
- ❌ 監視・メトリクス → Monitoring設計書
- ❌ 障害対応手順 → Maintenance設計書

### 1.3 デプロイフロー全体図

```mermaid
graph TB
    Dev[開発者<br/>コード変更]

    Dev --> Commit[Git Commit]
    Commit --> Push[Git Push]

    Push --> CI{CI Pipeline}

    CI --> Lint[Linter/Formatter<br/>ruff]
    CI --> TypeCheck[Type Check<br/>mypy]
    CI --> Test[Unit Tests<br/>pytest]

    Lint --> CIResult{CI Success?}
    TypeCheck --> CIResult
    Test --> CIResult

    CIResult -->|No| Fail[❌ Build Failed]
    CIResult -->|Yes| Build[Docker Build]

    Build --> Push2Registry[Push to Registry<br/>Docker Hub/ACR]

    Push2Registry --> Deploy{Deploy Target}

    Deploy -->|staging| DeployStaging[Staging Deploy]
    Deploy -->|production| DeployProd[Production Deploy]

    DeployStaging --> StagingTest[Staging Tests<br/>E2E Tests]
    StagingTest --> ManualApproval{Manual Approval?}

    ManualApproval -->|Yes| DeployProd
    ManualApproval -->|No| Rollback1[Rollback]

    DeployProd --> HealthCheck[Health Check]
    HealthCheck --> Success{Healthy?}

    Success -->|Yes| Complete[✅ Deploy Complete]
    Success -->|No| Rollback2[Rollback]

    style Dev fill:#e3f2fd
    style Complete fill:#c8e6c9
    style Fail fill:#ffccbc
    style Rollback1 fill:#ffccbc
    style Rollback2 fill:#ffccbc
```

---

## 2. デプロイ戦略

### 2.1 デプロイ方式

本プロジェクトは以下のデプロイ方式をサポートします：

| 方式 | 環境 | 説明 | ダウンタイム |
|------|------|------|------------|
| **Blue-Green Deployment** | Production | 新旧バージョンを切り替え | ✅ ゼロ |
| **Rolling Update** | Production | 段階的にインスタンス更新 | ✅ ゼロ |
| **Recreate** | Staging | 全インスタンス停止→再作成 | ⚠️ あり（数秒） |
| **Manual** | Local | 手動デプロイ | ⚠️ あり |

### 2.2 Blue-Green Deployment

**概要**:
新バージョン（Green）を既存バージョン（Blue）と並行稼働させ、検証後に切り替えます。

```mermaid
sequenceDiagram
    participant LB as Load Balancer
    participant Blue as Blue Environment<br/>(v1.0.0)
    participant Green as Green Environment<br/>(v1.1.0)
    participant DB as Database

    Note over LB,Blue: 現在の本番環境（Blue）

    LB->>Blue: トラフィック 100%

    Note over Green: Green環境デプロイ開始

    Green->>DB: マイグレーション実行
    DB->>Green: OK

    Note over Green: ヘルスチェック & 検証

    alt 検証成功
        LB->>Green: トラフィック切り替え 100%
        Note over Blue: Blueは待機状態
    else 検証失敗
        LB->>Blue: トラフィック維持 100%
        Note over Green: Green削除
    end
```

**利点**:

- ✅ ダウンタイムゼロ
- ✅ 即座にロールバック可能
- ✅ 本番環境で検証可能

**欠点**:

- ⚠️ リソース2倍必要（コスト増）
- ⚠️ データベースマイグレーションの互換性必要

### 2.3 Rolling Update

**概要**:
インスタンスを段階的に更新し、常に一部のインスタンスがリクエストを処理します。

```mermaid
sequenceDiagram
    participant LB as Load Balancer
    participant App1 as App Instance 1<br/>(v1.0.0)
    participant App2 as App Instance 2<br/>(v1.0.0)
    participant App3 as App Instance 3<br/>(v1.0.0)

    Note over LB,App3: Rolling Update開始

    LB->>App2: トラフィック停止
    LB->>App3: トラフィック停止

    App1->>App1: v1.1.0 デプロイ
    App1->>LB: ヘルスチェック OK

    LB->>App1: トラフィック再開

    App2->>App2: v1.1.0 デプロイ
    App2->>LB: ヘルスチェック OK

    LB->>App2: トラフィック再開

    App3->>App3: v1.1.0 デプロイ
    App3->>LB: ヘルスチェック OK

    LB->>App3: トラフィック再開

    Note over LB,App3: Rolling Update完了
```

**利点**:

- ✅ ダウンタイムゼロ
- ✅ リソース効率的
- ✅ 段階的ロールアウト

**欠点**:

- ⚠️ ロールバックに時間がかかる
- ⚠️ 新旧バージョン混在期間あり

---

## 3. 環境セットアップ

### 3.1 Windows開発環境セットアップ

**自動セットアップスクリプト**: `scripts/setup-windows.ps1`

**実行手順**:

```powershell
# 1. プロジェクトディレクトリに移動
cd C:\path\to\camp_backend

# 2. セットアップスクリプト実行
.\scripts\setup-windows.ps1

# 3. データベースセットアップ
.\scripts\reset-database.ps1

# 4. 開発サーバー起動
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**セットアップスクリプトの内容**:

```powershell
# scripts/setup-windows.ps1

# 1. 依存関係インストール
Write-Host "依存関係をインストールしています..." -ForegroundColor Green
uv sync

# 2. 環境変数ファイル作成
if (-not (Test-Path ".env.local")) {
    Write-Host ".env.localを作成しています..." -ForegroundColor Green
    Copy-Item ".env.local.example" ".env.local"
}

# 3. uploadsディレクトリ作成
if (-not (Test-Path "uploads")) {
    Write-Host "uploadsディレクトリを作成しています..." -ForegroundColor Green
    New-Item -ItemType Directory -Path "uploads"
}

# 4. PostgreSQL起動確認
Write-Host "PostgreSQLの起動を確認しています..." -ForegroundColor Green
.\scripts\start-postgres.ps1

Write-Host "セットアップ完了！" -ForegroundColor Green
```

### 3.2 データベースセットアップ

**データベースリセットスクリプト**: `scripts/reset-database.ps1`

```powershell
# scripts/reset-database.ps1

param(
    [switch]$SkipConfirmation
)

if (-not $SkipConfirmation) {
    $confirmation = Read-Host "データベースを削除して再作成しますか？ (y/n)"
    if ($confirmation -ne 'y') {
        Write-Host "キャンセルしました。" -ForegroundColor Yellow
        exit
    }
}

# 1. データベース削除
Write-Host "データベースを削除しています..." -ForegroundColor Yellow
psql -U postgres -c "DROP DATABASE IF EXISTS app_db;"

# 2. データベース作成
Write-Host "データベースを作成しています..." -ForegroundColor Green
psql -U postgres -c "CREATE DATABASE app_db;"

# 3. マイグレーション実行
Write-Host "マイグレーションを実行しています..." -ForegroundColor Green
cd src
uv run alembic upgrade head
cd ..

Write-Host "データベースのリセットが完了しました！" -ForegroundColor Green
```

### 3.3 環境変数設定

**開発環境（.env.local）**:

```bash
# 環境設定
ENVIRONMENT=development
DEBUG=True
AUTH_MODE=development

# データベース設定
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_db

# LLM設定
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# 開発モード認証
DEV_MOCK_TOKEN=mock-access-token-dev-12345
```

**本番環境（.env.production）**:

```bash
# 環境設定
ENVIRONMENT=production
DEBUG=False
AUTH_MODE=production

# セキュリティ設定
SECRET_KEY=<64文字のランダム文字列>

# データベース設定
DATABASE_URL=postgresql+asyncpg://user:password@prod-db.postgres.database.azure.com:5432/app_db?sslmode=require

# Azure AD設定
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

---

## 4. CI/CDパイプライン

### 4.1 GitHub Actions ワークフロー

**ファイル配置**: `.github/workflows/ci-cd.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main
      - develop

env:
  PYTHON_VERSION: '3.13'

jobs:
  # ============================================
  # CI: Lint, Type Check, Test
  # ============================================
  ci:
    name: CI Pipeline
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v2

      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync

      - name: Run Ruff (Linter)
        run: uv run ruff check src tests

      - name: Run Ruff (Formatter)
        run: uv run ruff format --check src tests

      - name: Run mypy (Type Check)
        run: uv run mypy src

      - name: Run pytest (Unit Tests)
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
          SECRET_KEY: test-secret-key-32-chars-minimum
        run: uv run pytest tests/ -v --cov=src --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage.xml

  # ============================================
  # Build: Docker Image
  # ============================================
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: ci
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract version
        id: version
        run: |
          VERSION=$(grep 'version = ' pyproject.toml | cut -d'"' -f2)
          echo "version=$VERSION" >> $GITHUB_OUTPUT

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/camp-backend:latest
            ${{ secrets.DOCKER_USERNAME }}/camp-backend:${{ steps.version.outputs.version }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ============================================
  # Deploy: Staging Environment
  # ============================================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging

    steps:
      - name: Deploy to Azure Web App (Staging)
        uses: azure/webapps-deploy@v3
        with:
          app-name: camp-backend-staging
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_STAGING }}
          images: ${{ secrets.DOCKER_USERNAME }}/camp-backend:latest

      - name: Run Database Migrations (Staging)
        run: |
          # SSH or Azure CLI to run migrations
          az webapp ssh --name camp-backend-staging --resource-group rg-camp-backend \
            --command "cd /home/site/wwwroot && alembic upgrade head"

  # ============================================
  # Deploy: Production Environment
  # ============================================
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Deploy to Azure Web App (Production)
        uses: azure/webapps-deploy@v3
        with:
          app-name: camp-backend-production
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_PRODUCTION }}
          images: ${{ secrets.DOCKER_USERNAME }}/camp-backend:latest

      - name: Run Database Migrations (Production)
        run: |
          az webapp ssh --name camp-backend-production --resource-group rg-camp-backend \
            --command "cd /home/site/wwwroot && alembic upgrade head"

      - name: Health Check
        run: |
          for i in {1..10}; do
            if curl -f https://api.example.com/health; then
              echo "Health check passed"
              exit 0
            fi
            echo "Waiting for app to be ready..."
            sleep 10
          done
          echo "Health check failed"
          exit 1
```

### 4.2 CI/CDパイプライン フロー

```mermaid
graph TB
    Push[Git Push]

    Push --> CI{CI Pipeline}

    CI --> Lint[Ruff Lint]
    CI --> Format[Ruff Format]
    CI --> Type[mypy Type Check]
    CI --> Test[pytest Tests]

    Lint --> CIResult{CI Success?}
    Format --> CIResult
    Type --> CIResult
    Test --> CIResult

    CIResult -->|No| Fail[❌ CI Failed<br/>PR Block]
    CIResult -->|Yes| Build[Docker Build]

    Build --> Push2Registry[Push to Registry]

    Push2Registry --> Branch{Branch?}

    Branch -->|develop| DeployStaging[Deploy to Staging]
    Branch -->|main| DeployProd[Deploy to Production]

    DeployStaging --> MigrationStaging[DB Migration<br/>Staging]
    DeployProd --> MigrationProd[DB Migration<br/>Production]

    MigrationStaging --> HealthStaging[Health Check<br/>Staging]
    MigrationProd --> HealthProd[Health Check<br/>Production]

    HealthStaging --> CompleteStaging[✅ Staging Complete]
    HealthProd --> CompleteProd[✅ Production Complete]

    style Push fill:#e3f2fd
    style CompleteStaging fill:#c8e6c9
    style CompleteProd fill:#c8e6c9
    style Fail fill:#ffccbc
```

---

## 5. コンテナデプロイ

### 5.1 Dockerfile

**配置**: `Dockerfile`

```dockerfile
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY .env.production ./.env

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 5.2 docker-compose.yml

**開発環境用**:

```yaml
version: '3.8'

services:
  # FastAPI Application
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads

  # PostgreSQL Database
  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

**起動コマンド**:

```bash
# コンテナビルド & 起動
docker-compose up -d

# ログ確認
docker-compose logs -f app

# コンテナ停止
docker-compose down

# ボリューム削除（データベースリセット）
docker-compose down -v
```

---

## 6. データベースマイグレーション

### 6.1 Alembic マイグレーション

**マイグレーション生成**:

```bash
# 1. モデル変更後、マイグレーションファイル生成
cd src
uv run alembic revision --autogenerate -m "Add user table"

# 2. 生成されたマイグレーションファイルを確認
# src/alembic/versions/XXXXXX_add_user_table.py

# 3. マイグレーション適用
uv run alembic upgrade head

# 4. マイグレーション履歴確認
uv run alembic history

# 5. ロールバック（1つ前に戻す）
uv run alembic downgrade -1
```

### 6.2 マイグレーション戦略

**Blue-Green Deployment でのマイグレーション**:

1. **後方互換マイグレーション**（推奨）

   ```sql
   -- ✅ 良い例: カラム追加（NULL許可）
   ALTER TABLE users ADD COLUMN new_field VARCHAR(255) NULL;

   -- ✅ 良い例: インデックス追加
   CREATE INDEX idx_users_email ON users(email);
   ```

2. **非互換マイグレーション**（段階的実施）

   ```sql
   -- ⚠️ 注意: カラム削除は段階的に
   -- Phase 1: カラムをNULL許可に変更（旧バージョンで実行）
   ALTER TABLE users ALTER COLUMN old_field DROP NOT NULL;

   -- Phase 2: アプリケーション更新（旧カラム未使用）

   -- Phase 3: カラム削除（新バージョンで実行）
   ALTER TABLE users DROP COLUMN old_field;
   ```

### 6.3 本番環境マイグレーション手順

```bash
# 1. バックアップ取得
pg_dump -U postgres -d app_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. マイグレーション dry-run（確認）
alembic upgrade head --sql > migration.sql
cat migration.sql

# 3. マイグレーション実行
alembic upgrade head

# 4. ヘルスチェック
curl http://localhost:8000/health

# 5. ロールバック（必要な場合）
alembic downgrade -1
```

---

## 7. ロールバック戦略

### 7.1 アプリケーションロールバック

**Blue-Green Deployment のロールバック**:

```bash
# 1. ロードバランサーをBlue環境に切り替え
az network lb rule update \
  --resource-group rg-camp-backend \
  --lb-name lb-camp-backend \
  --name http-rule \
  --backend-pool-name blue-pool

# 2. ヘルスチェック
curl http://api.example.com/health

# 3. Green環境削除（オプション）
az webapp delete --name camp-backend-green --resource-group rg-camp-backend
```

**Rolling Update のロールバック**:

```bash
# Kubernetes の場合
kubectl rollout undo deployment/camp-backend

# Docker Swarm の場合
docker service update --rollback camp-backend
```

### 7.2 データベースロールバック

**マイグレーションロールバック**:

```bash
# 1. 現在のバージョン確認
alembic current

# 2. マイグレーション履歴確認
alembic history

# 3. 1つ前のバージョンに戻す
alembic downgrade -1

# 4. 特定バージョンに戻す
alembic downgrade <revision_id>
```

**バックアップからの復元**:

```bash
# 1. データベース削除
dropdb app_db

# 2. データベース作成
createdb app_db

# 3. バックアップ復元
psql -U postgres -d app_db < backup_20250111_120000.sql

# 4. ヘルスチェック
curl http://localhost:8000/health
```

---

## 8. リリースチェックリスト

### 8.1 リリース前チェックリスト

#### コード品質

- [ ] すべてのテストがパス（pytest）
- [ ] Linterチェックがパス（ruff check）
- [ ] Formatterチェックがパス（ruff format）
- [ ] Type Checkがパス（mypy）
- [ ] コードカバレッジ >= 80%

#### セキュリティ

- [ ] SECRET_KEYが本番用に設定されている
- [ ] ALLOWED_ORIGINSが適切に設定されている
- [ ] AUTH_MODE=production（本番環境）
- [ ] デバッグモードが無効（DEBUG=False）
- [ ] 環境変数ファイル（.env.production）が.gitignoreに含まれている

#### データベース

- [ ] マイグレーションファイルが生成されている
- [ ] マイグレーションがステージング環境でテスト済み
- [ ] データベースバックアップが取得されている
- [ ] ロールバック手順が準備されている

#### インフラ

- [ ] Azure/AWS リソースが準備されている
- [ ] ロードバランサーが設定されている
- [ ] SSL証明書が有効
- [ ] ヘルスチェックエンドポイントが正常に動作

#### ドキュメント

- [ ] CHANGELOG.mdが更新されている
- [ ] リリースノートが準備されている
- [ ] APIドキュメントが更新されている

### 8.2 リリース後チェックリスト

#### 動作確認

- [ ] ヘルスチェックが正常（/health）
- [ ] メトリクスが取得できる（/metrics）
- [ ] APIドキュメントが表示される（/docs）
- [ ] 主要エンドポイントが動作する

#### 監視

- [ ] Prometheusメトリクスが収集されている
- [ ] ログが正常に出力されている
- [ ] アラートが設定されている
- [ ] ダッシュボードが更新されている

#### パフォーマンス

- [ ] レスポンスタイムが正常範囲内
- [ ] データベース接続プールが正常
- [ ] Redisキャッシュが動作している
- [ ] メモリ使用量が正常範囲内

---

## 9. トラブルシューティング

### 9.1 よくある問題と解決策

#### 問題: デプロイ後にアプリケーションが起動しない

**症状**:

```text
Health check failed: Connection refused
```

**原因と解決策**:

1. **データベース接続エラー**

   ```bash
   # ログ確認
   docker logs camp-backend

   # DATABASE_URL確認
   echo $DATABASE_URL

   # データベース接続テスト
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **マイグレーション未実行**

   ```bash
   # マイグレーション状態確認
   alembic current

   # マイグレーション実行
   alembic upgrade head
   ```

3. **環境変数未設定**

   ```bash
   # 環境変数確認
   env | grep DATABASE_URL
   env | grep SECRET_KEY

   # .env.productionファイル確認
   cat .env.production
   ```

#### 問題: マイグレーションが失敗する

**症状**:

```text
alembic.util.exc.CommandError: Target database is not up to date.
```

**解決策**:

```bash
# 1. 現在のマイグレーション状態確認
alembic current

# 2. マイグレーション履歴確認
alembic history

# 3. マイグレーション整合性チェック
alembic check

# 4. スタンプ修正（最終手段）
alembic stamp head
```

#### 問題: ロールバックが必要

**手順**:

```bash
# 1. トラフィック停止（ロードバランサー）
az network lb rule update --backend-pool-name maintenance-pool

# 2. アプリケーションロールバック
kubectl rollout undo deployment/camp-backend

# 3. データベースロールバック
alembic downgrade -1

# 4. ヘルスチェック
curl http://localhost:8000/health

# 5. トラフィック再開
az network lb rule update --backend-pool-name blue-pool
```

### 9.2 緊急連絡先

| 役割 | 担当者 | 連絡先 |
|------|-------|-------|
| リリースマネージャー | - | - |
| DevOpsエンジニア | - | - |
| データベース管理者 | - | - |
| オンコール担当者 | - | - |

---

## 10. 付録

### 10.1 関連スクリプト一覧

| スクリプト | 説明 |
|-----------|------|
| `scripts/setup-windows.ps1` | Windows環境セットアップ |
| `scripts/reset-database.ps1` | データベースリセット |
| `scripts/reset-environment.ps1` | 環境リセット |
| `scripts/start-postgres.ps1` | PostgreSQL起動 |

### 10.2 参考リンク

#### 公式ドキュメント

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Azure Web Apps Documentation](https://learn.microsoft.com/en-us/azure/app-service/)

#### デプロイ戦略

- [Blue-Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)
- [Rolling Deployment](https://www.redhat.com/en/topics/devops/what-is-rolling-deployment)
- [Canary Deployment](https://martinfowler.com/bliki/CanaryRelease.html)

### 10.3 クロスリファレンス

本設計書に関連する他の設計書：

| 設計書 | リンク | 関連箇所 |
|-------|--------|---------|
| **Infrastructure設計書** | [01-infrastructure-design.md](../05-infrastructure/01-infrastructure-design.md) | 環境構成、サーバー設定 |
| **Database設計書** | [01-database-design.md](../02-database/01-database-design.md) | マイグレーション、バックアップ |
| **System設計書** | [01-system-design.md](../01-architecture/01-system-design.md) | アプリケーション構成 |

### 10.4 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-01-11 | 初版作成 | Claude Code |

---

**最終更新**: 2025-01-11
**管理者**: Claude Code
**レビュー状態**: 初版
