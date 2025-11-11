# インフラストラクチャ設計書（Infrastructure Design）

## 📋 文書管理情報

| 項目 | 内容 |
|------|------|
| **文書名** | インフラストラクチャ設計書（Infrastructure Design） |
| **バージョン** | 1.0.0 |
| **作成日** | 2025-01-11 |
| **最終更新日** | 2025-01-11 |
| **作成者** | Claude Code |
| **レビュー状態** | 初版 |

---

## 📑 目次

1. [概要](#1-概要)
2. [環境構成](#2-環境構成)
3. [データベースインフラ](#3-データベースインフラ)
4. [キャッシュインフラ](#4-キャッシュインフラ)
5. [ストレージインフラ](#5-ストレージインフラ)
6. [アプリケーションサーバー](#6-アプリケーションサーバー)
7. [監視・メトリクス](#7-監視メトリクス)
8. [ログ管理](#8-ログ管理)
9. [セキュリティインフラ](#9-セキュリティインフラ)
10. [付録](#10-付録)

---

## 1. 概要

### 1.1 目的

本設計書は、genai-app-docs（camp-backend）プロジェクトのインフラストラクチャ構成を文書化し、以下を達成することを目的とします：

- **インフラ構成の明確化**: 環境別のインフラ構成を説明
- **スケーラビリティ設計**: 水平・垂直スケーリングの戦略を記録
- **可用性設計**: 冗長化と障害対策を文書化
- **運用ガイドの提供**: インフラの構築・保守手順を明示

### 1.2 適用範囲

本設計書は以下を対象とします：

- ✅ 環境構成（local / staging / production）
- ✅ データベースインフラ（PostgreSQL）
- ✅ キャッシュインフラ（Redis）
- ✅ ストレージインフラ（Local FS / Azure Blob）
- ✅ アプリケーションサーバー（FastAPI / Uvicorn）
- ✅ 監視・メトリクス（Prometheus）
- ✅ ログ管理（structlog）

以下は**対象外**とし、別の設計書や運用手順書で詳述します：

- ❌ コンテナオーケストレーション（Kubernetes）の詳細
- ❌ CI/CDパイプライン → Operations設計書
- ❌ 障害対応手順 → Operations設計書

### 1.3 前提条件

本設計書を読むには以下の知識が推奨されます：

- **Linux基礎**: ファイルシステム、プロセス管理
- **ネットワーク基礎**: TCP/IP、HTTP/HTTPS
- **PostgreSQL**: データベースの基本的な運用
- **Docker基礎**: コンテナの概念

---

## 2. 環境構成

### 2.1 環境種別

本システムは3つの環境で構成されます：

| 環境 | 用途 | 設定ファイル | データベース | 認証 |
|------|------|------------|-------------|------|
| **local（開発）** | ローカル開発環境 | `.env.local` | localhost PostgreSQL | JWT開発モード |
| **staging** | ステージング環境 | `.env.staging` | Staging PostgreSQL | Azure AD |
| **production** | 本番環境 | `.env.production` | Production PostgreSQL | Azure AD |

### 2.2 環境別インフラ構成図

**開発環境（local）**:

```mermaid
graph TB
    subgraph "開発マシン（Windows/WSL2）"
        Dev[開発者<br/>VS Code]

        subgraph "FastAPI App"
            FastAPI[FastAPI<br/>Uvicorn]
        end

        subgraph "データストア"
            PostgreSQL[(PostgreSQL<br/>localhost:5432)]
            Redis[(Redis<br/>オプション)]
            LocalFS[Local File System<br/>./uploads/]
        end

        Dev -->|HTTP| FastAPI
        FastAPI --> PostgreSQL
        FastAPI -.->|オプション| Redis
        FastAPI --> LocalFS
    end

    subgraph "外部サービス"
        Anthropic[Anthropic API<br/>Claude LLM]
        OpenAI[OpenAI API<br/>GPT LLM]
    end

    FastAPI -.->|API呼び出し| Anthropic
    FastAPI -.->|API呼び出し| OpenAI
```

**本番環境（production）**:

```mermaid
graph TB
    subgraph "クライアント"
        Browser[ブラウザ]
        Mobile[モバイルアプリ]
    end

    subgraph "CDN / Edge"
        CloudFlare[CloudFlare<br/>CDN + WAF]
    end

    subgraph "ロードバランサー"
        LB[Azure Load Balancer]
    end

    subgraph "アプリケーション層"
        App1[FastAPI App 1]
        App2[FastAPI App 2]
        AppN[FastAPI App N]
    end

    subgraph "データストア"
        PostgreSQL[(Azure Database<br/>for PostgreSQL)]
        Redis[(Azure Cache<br/>for Redis)]
        AzureBlob[Azure Blob Storage]
    end

    subgraph "監視・ログ"
        Prometheus[Prometheus]
        Grafana[Grafana]
        AzureMonitor[Azure Monitor]
    end

    subgraph "外部サービス"
        AzureAD[Azure AD]
        Anthropic[Anthropic API]
    end

    Browser --> CloudFlare
    Mobile --> CloudFlare
    CloudFlare --> LB

    LB --> App1
    LB --> App2
    LB --> AppN

    App1 --> PostgreSQL
    App2 --> PostgreSQL
    AppN --> PostgreSQL

    App1 --> Redis
    App2 --> Redis
    AppN --> Redis

    App1 --> AzureBlob
    App2 --> AzureBlob
    AppN --> AzureBlob

    App1 -.->|メトリクス| Prometheus
    App2 -.->|メトリクス| Prometheus
    AppN -.->|メトリクス| Prometheus

    Prometheus --> Grafana
    App1 -.->|ログ| AzureMonitor

    App1 -.->|認証| AzureAD
    App1 -.->|LLM| Anthropic
```

### 2.3 環境設定ファイル

**`.env.local`（開発環境）**:

```bash
# 環境設定
ENVIRONMENT=development
DEBUG=True
AUTH_MODE=development

# アプリケーション設定
APP_NAME=camp-backend
PORT=8000
HOST=127.0.0.1
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# データベース設定
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Redis設定（オプション）
# REDIS_URL=redis://localhost:6379/0

# ストレージ設定
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads

# LLM設定
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# 開発モード認証
DEV_MOCK_TOKEN=mock-access-token-dev-12345
DEV_MOCK_USER_EMAIL=dev.user@example.com
```

**`.env.production`（本番環境）**:

```bash
# 環境設定
ENVIRONMENT=production
DEBUG=False
AUTH_MODE=production

# アプリケーション設定
APP_NAME=camp-backend
PORT=8000
HOST=0.0.0.0
ALLOWED_ORIGINS=["https://app.example.com"]

# セキュリティ設定
SECRET_KEY=<64文字のランダム文字列>
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# データベース設定
DATABASE_URL=postgresql+asyncpg://user:password@prod-db.postgres.database.azure.com:5432/app_db?sslmode=require
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=True

# Redis設定
REDIS_URL=rediss://prod-cache.redis.cache.windows.net:6380?ssl_cert_reqs=required
CACHE_TTL=300

# ストレージ設定
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_NAME=prodstorageaccount
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_STORAGE_CONTAINER_NAME=uploads

# LLM設定
LLM_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://prod-openai.openai.azure.com
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Azure AD設定
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_OPENAPI_CLIENT_ID=your-swagger-ui-client-id

# モニタリング
LANGCHAIN_TRACING_V2=True
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=camp-backend-production
```

---

## 3. データベースインフラ

### 3.1 PostgreSQL構成

**データベースエンジン**: PostgreSQL 16

**接続URL形式**:

```text
postgresql+asyncpg://[user]:[password]@[host]:[port]/[database]?[options]
```

### 3.2 接続プール設定

**接続プール（SQLAlchemy AsyncEngine）**:

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,           # 通常時の接続プールサイズ
    max_overflow=10,       # ピーク時の追加接続数（最大15接続）
    pool_recycle=1800,     # 30分で接続をリサイクル
    pool_pre_ping=True,    # 接続前にPINGチェック（切断検出）
    echo=settings.DEBUG,   # SQL出力（デバッグ時のみ）
)
```

**設定パラメータ説明**:

| パラメータ | 開発環境 | 本番環境 | 説明 |
|-----------|---------|---------|------|
| `pool_size` | 5 | 20 | 通常時の接続プール数 |
| `max_overflow` | 10 | 40 | ピーク時の追加接続数 |
| `pool_recycle` | 1800 | 1800 | 接続リサイクル時間（秒） |
| `pool_pre_ping` | True | True | 接続前のPINGチェック |
| `echo` | True | False | SQL出力（デバッグ用） |

**最大接続数計算**:

```text
最大接続数 = pool_size + max_overflow

開発環境: 5 + 10 = 15接続
本番環境: 20 + 40 = 60接続
```

### 3.3 データベーススキーマ管理

**Alembicマイグレーション**:

```bash
# マイグレーション生成
cd src
uv run alembic revision --autogenerate -m "Add user table"

# マイグレーション適用
uv run alembic upgrade head

# マイグレーション履歴
uv run alembic history

# マイグレーション巻き戻し
uv run alembic downgrade -1
```

**マイグレーションファイル構成**:

```text
src/alembic/
├── versions/
│   ├── 20250101_1234_add_user_table.py
│   ├── 20250102_5678_add_project_table.py
│   └── 20250103_9012_add_rbac_tables.py
├── env.py
└── script.py.mako
```

### 3.4 データベースバックアップ戦略

**開発環境**:

- 手動バックアップ（必要に応じて）
- `pg_dump`コマンド使用

```bash
pg_dump -U postgres -d app_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

**本番環境（Azure Database for PostgreSQL）**:

- ✅ **自動バックアップ**: 7日間保持（Azure標準）
- ✅ **ポイントインタイムリストア**: 5分単位で復元可能
- ✅ **Geo冗長バックアップ**: 地理的冗長化オプション

**バックアップ頻度**:

| 環境 | バックアップタイプ | 頻度 | 保持期間 |
|------|----------------|------|---------|
| 開発 | 手動 | 必要に応じて | 無制限 |
| ステージング | 自動（Azure） | 毎日 | 7日間 |
| 本番 | 自動（Azure） | 毎日 | 35日間 |

---

## 4. キャッシュインフラ

### 4.1 Redis構成

**Redisの用途**:

- ✅ セッション管理（将来の拡張）
- ✅ APIレスポンスキャッシュ
- ✅ レート制限カウンター
- ✅ ユーザープロファイルキャッシュ
- ✅ プロジェクトメンバーロールキャッシュ

### 4.2 Redis接続設定

**開発環境（オプション）**:

```bash
# ローカルRedis（オプション）
REDIS_URL=redis://localhost:6379/0
```

**本番環境（Azure Cache for Redis）**:

```bash
# SSL必須
REDIS_URL=rediss://prod-cache.redis.cache.windows.net:6380?ssl_cert_reqs=required
```

### 4.3 キャッシュ戦略

**キャッシュマネージャー実装（`core/cache.py`）**:

```python
class CacheManager:
    """Redisキャッシュ管理クラス。"""

    def __init__(self):
        self.redis: Redis | None = None

    async def connect(self):
        """Redis接続を確立します。"""
        self.redis = await Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def get(self, key: str) -> Any:
        """キャッシュからデータを取得します。"""
        if not self.redis:
            return None
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = settings.CACHE_TTL):
        """キャッシュにデータを保存します（TTL付き）。"""
        if self.redis:
            await self.redis.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str):
        """キャッシュからデータを削除します。"""
        if self.redis:
            await self.redis.delete(key)
```

**キャッシュキー設計**:

| キーパターン | 用途 | TTL | 例 |
|------------|------|-----|-----|
| `user:{user_id}` | ユーザープロファイル | 300秒 | `user:12345678-...` |
| `project:{project_id}` | プロジェクト情報 | 300秒 | `project:87654321-...` |
| `member_role:{project_id}:{user_id}` | メンバーロール | 300秒 | `member_role:...:...` |
| `rate_limit:{ip}` | レート制限カウンター | 60秒 | `rate_limit:192.168.1.1` |
| `analysis_template:{template_id}` | 分析テンプレート | 600秒 | `analysis_template:template-1` |

### 4.4 キャッシュ無効化戦略

**書き込み時無効化（Write-Through）**:

```python
async def update_user(user_id: uuid.UUID, update_data: dict) -> User:
    """ユーザー情報を更新し、キャッシュを無効化します。"""
    # データベース更新
    user = await user_repository.update(user_id, **update_data)
    await db.commit()

    # キャッシュ無効化
    await cache_manager.delete(f"user:{user_id}")

    return user
```

---

## 5. ストレージインフラ

### 5.1 ストレージバックエンド

本システムは2つのストレージバックエンドをサポートします：

| バックエンド | 用途 | 環境 |
|------------|------|------|
| **Local File System** | 開発環境 | local |
| **Azure Blob Storage** | 本番環境 | staging, production |

### 5.2 ローカルファイルシステム

**設定**:

```bash
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads
```

**ディレクトリ構造**:

```text
uploads/
├── projects/
│   ├── {project_id}/
│   │   ├── {file_id}_original_filename.xlsx
│   │   └── {file_id}_data.csv
├── analysis/
│   ├── {session_id}/
│   │   ├── snapshot_{timestamp}.json
│   │   └── graph_{graph_id}.png
└── temp/
    └── {upload_id}_temp.tmp
```

**実装（`services/storage.py`）**:

```python
class LocalFileStorage:
    """ローカルファイルシステムストレージ。"""

    def __init__(self, base_path: str = settings.LOCAL_STORAGE_PATH):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(self, file: UploadFile, path: str) -> str:
        """ファイルをアップロードします。"""
        file_path = self.base_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        return str(file_path)

    async def download(self, path: str) -> bytes:
        """ファイルをダウンロードします。"""
        file_path = self.base_path / path
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()

    async def delete(self, path: str) -> None:
        """ファイルを削除します。"""
        file_path = self.base_path / path
        file_path.unlink(missing_ok=True)
```

### 5.3 Azure Blob Storage

**設定**:

```bash
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_NAME=prodstorageaccount
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_NAME=uploads
```

**コンテナ構成**:

| コンテナ名 | 用途 | アクセスレベル |
|----------|------|--------------|
| `uploads` | ユーザーアップロードファイル | Private |
| `analysis` | 分析結果・スナップショット | Private |
| `public` | 公開リソース（将来の拡張） | Blob（匿名読み取り可） |

**実装（`services/storage.py`）**:

```python
class AzureBlobStorage:
    """Azure Blob Storageストレージ。"""

    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        self.container_client = self.blob_service_client.get_container_client(
            settings.AZURE_STORAGE_CONTAINER_NAME
        )

    async def upload(self, file: UploadFile, path: str) -> str:
        """ファイルをアップロードします。"""
        blob_client = self.container_client.get_blob_client(path)

        content = await file.read()
        await blob_client.upload_blob(content, overwrite=True)

        return blob_client.url

    async def download(self, path: str) -> bytes:
        """ファイルをダウンロードします。"""
        blob_client = self.container_client.get_blob_client(path)
        stream = await blob_client.download_blob()
        return await stream.readall()

    async def delete(self, path: str) -> None:
        """ファイルを削除します。"""
        blob_client = self.container_client.get_blob_client(path)
        await blob_client.delete_blob()
```

### 5.4 ファイルサイズ制限

**設定**:

```bash
MAX_FILE_SIZE_MB=10
```

**実装（ミドルウェアレベル）**:

```python
# api/routes/v1/project_files.py
@router.post("/files", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(..., description="アップロードファイル（最大10MB）"),
):
    # ファイルサイズチェック
    if file.size > settings.MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"ファイルサイズが制限（{settings.MAX_FILE_SIZE_MB}MB）を超えています")
```

---

## 6. アプリケーションサーバー

### 6.1 Uvicornサーバー設定

**開発環境**:

```bash
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**本番環境**:

```bash
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Uvicornワーカー数計算**:

```text
推奨ワーカー数 = (CPU コア数 × 2) + 1

例: 4コアCPU → (4 × 2) + 1 = 9ワーカー
```

### 6.2 プロセス管理

**本番環境でのプロセス管理（Systemd）**:

```ini
# /etc/systemd/system/camp-backend.service
[Unit]
Description=camp-backend FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=app
Group=app
WorkingDirectory=/opt/camp-backend
Environment="PATH=/opt/camp-backend/.venv/bin"
EnvironmentFile=/opt/camp-backend/.env.production
ExecStart=/opt/camp-backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Systemdコマンド**:

```bash
# サービス起動
sudo systemctl start camp-backend

# サービス停止
sudo systemctl stop camp-backend

# サービス再起動
sudo systemctl restart camp-backend

# ステータス確認
sudo systemctl status camp-backend

# 自動起動有効化
sudo systemctl enable camp-backend

# ログ確認
sudo journalctl -u camp-backend -f
```

### 6.3 リバースプロキシ（Nginx）

**Nginx設定例**:

```nginx
# /etc/nginx/sites-available/camp-backend
upstream camp_backend {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name api.example.com;

    # HTTPSへリダイレクト
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL証明書
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    # セキュリティヘッダー
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # アップロードサイズ制限
    client_max_body_size 10M;

    # プロキシ設定
    location / {
        proxy_pass http://camp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocketサポート
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # タイムアウト
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静的ファイル（将来の拡張）
    location /static/ {
        alias /opt/camp-backend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # ヘルスチェック
    location /health {
        proxy_pass http://camp_backend;
        access_log off;
    }
}
```

---

## 7. 監視・メトリクス

### 7.1 Prometheusメトリクス

**メトリクス収集（`api/middlewares/metrics.py`）**:

```python
from prometheus_client import Counter, Histogram, generate_latest

# メトリクス定義
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Prometheusメトリクス収集ミドルウェア。"""

    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path

        # リクエスト開始時刻
        start_time = time.time()

        # リクエスト処理
        response = await call_next(request)

        # レスポンスタイム計算
        duration = time.time() - start_time

        # メトリクス記録
        http_requests_total.labels(
            method=method,
            endpoint=path,
            status=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=path
        ).observe(duration)

        return response
```

**メトリクスエンドポイント**:

```python
# api/routes/system/metrics.py
@router.get("/metrics")
async def metrics():
    """Prometheusメトリクスを返します。"""
    return Response(content=generate_latest(), media_type="text/plain")
```

### 7.2 収集メトリクス一覧

| メトリクス名 | タイプ | ラベル | 説明 |
|-----------|-------|-------|------|
| `http_requests_total` | Counter | method, endpoint, status | HTTPリクエスト総数 |
| `http_request_duration_seconds` | Histogram | method, endpoint | HTTPリクエスト処理時間 |
| `db_connections_active` | Gauge | - | アクティブDB接続数 |
| `cache_hits_total` | Counter | - | キャッシュヒット数 |
| `cache_misses_total` | Counter | - | キャッシュミス数 |
| `llm_api_calls_total` | Counter | provider, model | LLM API呼び出し数 |
| `llm_api_duration_seconds` | Histogram | provider, model | LLM APIレスポンスタイム |

### 7.3 Prometheus設定

**prometheus.yml**:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'camp-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### 7.4 Grafanaダッシュボード

**ダッシュボードパネル**:

1. **HTTPリクエスト数（QPS）**
   - クエリ: `rate(http_requests_total[5m])`
   - グラフタイプ: Graph

2. **レスポンスタイム（P95）**
   - クエリ: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
   - グラフタイプ: Graph

3. **HTTPステータスコード分布**
   - クエリ: `sum by (status) (rate(http_requests_total[5m]))`
   - グラフタイプ: Pie Chart

4. **DB接続数**
   - クエリ: `db_connections_active`
   - グラフタイプ: Gauge

---

## 8. ログ管理

### 8.1 構造化ログ（structlog）

**ログ設定（`core/logging.py`）**:

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

def get_logger(name: str):
    """構造化ログ取得関数。"""
    return structlog.get_logger(name)
```

**ログ出力例**:

```python
logger = get_logger(__name__)

logger.info(
    "ユーザー認証成功",
    user_id=str(user.id),
    email=user.email,
    auth_mode=settings.AUTH_MODE,
)

logger.warning(
    "認証失敗",
    reason="invalid_token",
    ip_address=request.client.host,
)

logger.error(
    "データベースエラー",
    error_type=type(e).__name__,
    error_message=str(e),
    query=query_str,
)
```

### 8.2 ログレベル

| レベル | 用途 | 出力先 |
|-------|------|-------|
| `DEBUG` | 詳細デバッグ情報 | 開発環境のみ |
| `INFO` | 通常の操作情報 | 全環境 |
| `WARNING` | 警告（処理は継続） | 全環境 |
| `ERROR` | エラー（処理失敗） | 全環境 + アラート |
| `CRITICAL` | 致命的エラー | 全環境 + 緊急アラート |

### 8.3 ログ集約（本番環境）

**Azure Monitor / Application Insights**:

```python
# 環境変数
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# Pythonコード
from opencensus.ext.azure.log_exporter import AzureLogHandler

logger.addHandler(AzureLogHandler(
    connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING
))
```

---

## 9. セキュリティインフラ

### 9.1 HTTPS/TLS設定

**TLS証明書管理**:

- ✅ **Let's Encrypt**: 無料SSL証明書（自動更新）
- ✅ **Certbot**: 証明書自動更新ツール

```bash
# Certbot自動更新
sudo certbot renew --quiet
```

### 9.2 ファイアウォール設定

**開放ポート**:

| ポート | プロトコル | 用途 | アクセス元 |
|-------|----------|------|-----------|
| 22 | TCP | SSH | 管理者IP限定 |
| 80 | TCP | HTTP（→HTTPS転送） | インターネット |
| 443 | TCP | HTTPS | インターネット |
| 5432 | TCP | PostgreSQL | 内部ネットワークのみ |
| 6379 | TCP | Redis | 内部ネットワークのみ |

**ufw設定例**:

```bash
# ファイアウォール有効化
sudo ufw enable

# SSH許可（管理者IPのみ）
sudo ufw allow from 192.168.1.0/24 to any port 22

# HTTP/HTTPS許可
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# PostgreSQL/Redis拒否（外部アクセス）
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp
```

### 9.3 セキュリティヘッダー

**実装（`api/middlewares/security_headers.py`）**:

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダーミドルウェア。"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # セキュリティヘッダー追加
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
```

---

## 10. 付録

### 10.1 関連ファイル一覧

#### インフラ設定ファイル

| ファイル | 説明 |
|---------|------|
| `.env.local` | 開発環境設定 |
| `.env.staging` | ステージング環境設定 |
| `.env.production` | 本番環境設定 |
| `src/app/core/config.py` | 設定管理 |
| `src/app/core/database.py` | データベース接続管理 |
| `src/app/core/cache.py` | Redisキャッシュ管理 |
| `src/app/services/storage.py` | ストレージ管理 |

#### デプロイ関連

| ファイル | 説明 |
|---------|------|
| `pyproject.toml` | プロジェクト設定・依存関係 |
| `uv.lock` | 依存関係ロックファイル |
| `scripts/setup-windows.ps1` | Windows環境セットアップ |
| `scripts/reset-database.ps1` | データベースリセット |

### 10.2 参考リンク

#### 公式ドキュメント

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)
- [Azure Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

### 10.3 クロスリファレンス

本設計書に関連する他の設計書：

| 設計書 | リンク | 関連箇所 |
|-------|--------|---------|
| **System設計書** | [01-system-design.md](../01-architecture/01-system-design.md) | アプリケーションアーキテクチャ |
| **Database設計書** | [01-database-design.md](../02-database/01-database-design.md) | データベース設計 |
| **API設計書** | [01-api-design.md](../04-api/01-api-design.md) | APIエンドポイント |

### 10.4 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-01-11 | 初版作成 | Claude Code |

---

**最終更新**: 2025-01-11
**管理者**: Claude Code
**レビュー状態**: 初版
