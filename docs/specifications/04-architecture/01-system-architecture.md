# システムアーキテクチャ設計書

## 1. 概要

本文書は、genai-app-docs（GenAI Application Document System）のシステムアーキテクチャを定義します。
このシステムは、FastAPIベースの非同期Webアプリケーションであり、LangChainを活用したAIエージェント機能を提供します。

### 1.1 システム目的

- プロジェクトベースのドキュメント管理
- AIエージェントによるデータ分析機能
- ロールベースアクセス制御（RBAC）によるセキュアな運用
- Azure ADまたはモック認証による柔軟な認証機能

### 1.2 主要機能

- ユーザー管理（Azure AD統合）
- プロジェクト管理（メンバー、ファイル）
- AI分析セッション管理
- ドライバーツリー管理
- PPT生成機能

---

## 2. 全体アーキテクチャ

### 2.1 システム構成図

::: mermaid
graph TB
    subgraph "クライアント層"
        Client[Webクライアント/APIクライアント]
    end

    subgraph "アプリケーション層"
        FastAPI[FastAPI Application]

        subgraph "ミドルウェア"
            CORS[CORSMiddleware]
            RateLimit[RateLimitMiddleware]
            Logging[LoggingMiddleware]
            Metrics[PrometheusMetricsMiddleware]
            SecurityHeaders[SecurityHeadersMiddleware]
        end

        subgraph "APIレイヤー"
            SystemAPI[System Routes<br/>/health, /metrics]
            V1API[API v1 Routes<br/>/api/v1/*]
        end

        subgraph "サービス層"
            UserService[UserService]
            ProjectService[ProjectService]
            AnalysisService[AnalysisService]
            StorageService[StorageService]
            AIAgent[AI Agent Service]
        end

        subgraph "リポジトリ層"
            UserRepo[UserRepository]
            ProjectRepo[ProjectRepository]
            AnalysisRepo[AnalysisRepository]
            BaseRepo[BaseRepository<T>]
        end
    end

    subgraph "データ層"
        PostgreSQL[(PostgreSQL<br/>Database)]
        Redis[(Redis<br/>Cache)]
    end

    subgraph "外部サービス"
        AzureAD[Azure AD<br/>認証]
        AzureBlobStorage[Azure Blob Storage<br/>ファイルストレージ]
        LLM[LLM Services<br/>Anthropic/OpenAI/Azure OpenAI]
        LangSmith[LangSmith<br/>トレーシング]
    end

    Client --> FastAPI
    FastAPI --> CORS
    CORS --> RateLimit
    RateLimit --> Logging
    Logging --> Metrics
    Metrics --> SecurityHeaders
    SecurityHeaders --> SystemAPI
    SecurityHeaders --> V1API

    V1API --> UserService
    V1API --> ProjectService
    V1API --> AnalysisService
    V1API --> StorageService

    UserService --> UserRepo
    ProjectService --> ProjectRepo
    AnalysisService --> AnalysisRepo
    AnalysisService --> AIAgent

    UserRepo --> BaseRepo
    ProjectRepo --> BaseRepo
    AnalysisRepo --> BaseRepo

    BaseRepo --> PostgreSQL
    UserService --> Redis
    StorageService --> AzureBlobStorage

    FastAPI --> AzureAD
    AIAgent --> LLM
    AIAgent --> LangSmith

    style FastAPI fill:#4A90E2
    style PostgreSQL fill:#336791
    style Redis fill:#D82C20
:::

### 2.2 レイヤードアーキテクチャ

システムは以下の5層で構成されます：

::: mermaid
graph LR
    A[API Layer] --> B[Service Layer]
    B --> C[Repository Layer]
    C --> D[Model Layer]
    D --> E[Data Layer]

    style A fill:#E8F5E9
    style B fill:#C8E6C9
    style C fill:#A5D6A7
    style D fill:#81C784
    style E fill:#66BB6A
:::

#### 2.2.1 各層の責務

| 層 | 責務 | 実装場所 |
|---|------|----------|
| **API Layer** | HTTPリクエスト処理、バリデーション、レスポンス生成 | `src/app/api/routes/` |
| **Service Layer** | ビジネスロジック、トランザクション管理、外部サービス連携 | `src/app/services/` |
| **Repository Layer** | データアクセス、クエリ構築、N+1問題対策 | `src/app/repositories/` |
| **Model Layer** | データモデル定義、リレーションシップ、制約 | `src/app/models/` |
| **Data Layer** | データベース、キャッシュ | PostgreSQL, Redis |

---

## 3. 技術スタック

### 3.1 技術スタック全体図

::: mermaid
graph TB
    subgraph "フロントエンド"
        FE[任意のHTTPクライアント]
    end

    subgraph "Webフレームワーク"
        FastAPI[FastAPI 0.115+]
        Pydantic[Pydantic 2.0+]
        Uvicorn[Uvicorn ASGI Server]
    end

    subgraph "AI/LLM"
        LangChain[LangChain 0.3+]
        LangGraph[LangGraph 0.2+]
        LangServe[LangServe 0.3+]
        LangSmith[LangSmith 0.2+]
    end

    subgraph "データベース"
        SQLAlchemy[SQLAlchemy 2.0+<br/>非同期ORM]
        Alembic[Alembic 1.13+<br/>マイグレーション]
        asyncpg[asyncpg 0.30+<br/>PostgreSQLドライバー]
    end

    subgraph "セキュリティ"
        JWT[python-jose<br/>JWT実装]
        Passlib[passlib+bcrypt<br/>パスワードハッシュ]
        AzureAuth[fastapi-azure-auth<br/>Azure AD認証]
    end

    subgraph "監視・ログ"
        Structlog[structlog<br/>構造化ログ]
        Prometheus[prometheus-client<br/>メトリクス]
    end

    subgraph "ストレージ"
        Aiofiles[aiofiles<br/>非同期ファイルI/O]
        AzureBlob[azure-storage-blob<br/>Blob Storage]
    end

    subgraph "開発ツール"
        Ruff[Ruff 0.8+<br/>Linter/Formatter]
        Pytest[pytest 8.3+<br/>テストフレームワーク]
        Mypy[mypy 1.18+<br/>型チェック]
        UV[uv<br/>パッケージマネージャー]
    end

    FE --> FastAPI
    FastAPI --> Pydantic
    FastAPI --> Uvicorn
    FastAPI --> LangChain
    FastAPI --> SQLAlchemy
    FastAPI --> JWT
    FastAPI --> Structlog

    LangChain --> LangGraph
    LangChain --> LangServe
    LangChain --> LangSmith

    SQLAlchemy --> Alembic
    SQLAlchemy --> asyncpg

    JWT --> AzureAuth
    Passlib --> AzureAuth

    FastAPI --> Aiofiles
    Aiofiles --> AzureBlob

    style FastAPI fill:#009688
    style LangChain fill:#FF6F00
    style SQLAlchemy fill:#BA0C2F
:::

### 3.2 主要技術の選定理由

| 技術 | バージョン | 選定理由 |
|------|-----------|----------|
| **FastAPI** | 0.115+ | 高速な非同期処理、自動APIドキュメント生成、Pydantic統合 |
| **SQLAlchemy 2.0** | 2.0+ | 非同期ORM、型安全性、柔軟なクエリ構築 |
| **Pydantic v2** | 2.0+ | 高速なバリデーション、自動型変換、設定管理 |
| **LangChain** | 0.3+ | LLMアプリケーション構築フレームワーク、多様なLLM対応 |
| **PostgreSQL** | - | 信頼性、JSONB型、トランザクション、高度なインデックス |
| **Redis** | 6.4+ | 高速キャッシュ、レート制限、セッション管理 |
| **structlog** | - | 構造化ログ、JSON出力、パフォーマンス |
| **Prometheus** | - | 業界標準メトリクス、Grafana統合、スケーラビリティ |

---

## 4. 非同期アーキテクチャ

### 4.1 非同期処理フロー

::: mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Service
    participant Repository
    participant Database
    participant ExternalAPI

    Client->>+FastAPI: HTTP Request (async)
    FastAPI->>+Service: Business Logic (async)

    par 並列処理可能
        Service->>+Repository: DB Query (async)
        Repository->>+Database: SQL Execution
        Database-->>-Repository: Result Set
        Repository-->>-Service: Domain Objects
    and
        Service->>+ExternalAPI: API Call (async)
        ExternalAPI-->>-Service: Response
    end

    Service-->>-FastAPI: Service Response
    FastAPI-->>-Client: HTTP Response (async)
:::

### 4.2 非同期実装の特徴

::: mermaid
graph LR
    A[async/await<br/>完全非同期] --> B[AsyncSession<br/>SQLAlchemy 2.0]
    B --> C[asyncpg<br/>PostgreSQLドライバー]

    A --> D[aiofiles<br/>ファイルI/O]
    A --> E[httpx<br/>HTTP Client]
    A --> F[AsyncGenerator<br/>依存性注入]

    style A fill:#FFEB3B
    style B fill:#FFC107
    style C fill:#FF9800
:::

**主要な非同期コンポーネント：**

1. **FastAPI**: ASGI（Uvicorn）による非同期リクエスト処理
2. **SQLAlchemy**: AsyncSession、AsyncEngine、asyncpg
3. **aiofiles**: 非同期ファイル読み書き
4. **httpx**: 非同期HTTPクライアント（外部API呼び出し）
5. **AsyncGenerator**: 依存性注入でのセッション管理

**実装例：**

```python
# 依存性注入（AsyncGenerator）
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 非同期エンドポイント
@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    # 非同期サービス呼び出し
    user = await user_service.get(db, user_id)
    return user
```

---

## 5. 認証モード切り替えアーキテクチャ

### 5.1 認証モード設計

システムは環境変数 `AUTH_MODE` により認証方式を切り替えます。

::: mermaid
graph TB
    Start[アプリケーション起動] --> CheckMode{AUTH_MODE}

    CheckMode -->|development| DevMode[開発モード<br/>dev_auth.py]
    CheckMode -->|production| ProdMode[本番モード<br/>azure_ad.py]

    DevMode --> MockToken[モックトークン認証<br/>DEV_MOCK_TOKEN]
    MockToken --> MockUser[固定モックユーザー<br/>DEV_MOCK_USER_EMAIL]

    ProdMode --> AzureAD[Azure AD認証<br/>SingleTenantAzureAuthorizationCodeBearer]
    AzureAD --> JWTValidation[JWT検証<br/>署名・有効期限・発行者]
    JWTValidation --> AzureUser[Azure ADユーザー<br/>azure_oid]

    MockUser --> UserAccount[UserAccount取得/作成]
    AzureUser --> UserAccount

    UserAccount --> Endpoint[エンドポイント処理]

    style DevMode fill:#FFF9C4
    style ProdMode fill:#C5E1A5
    style MockToken fill:#FFE082
    style AzureAD fill:#AED581
:::

### 5.2 認証モード比較表

| 項目 | 開発モード (development) | 本番モード (production) |
|------|-------------------------|------------------------|
| **実装ファイル** | `dev_auth.py` | `azure_ad.py` |
| **認証方式** | モックトークン | Azure AD JWT |
| **トークン検証** | 固定文字列照合 | JWT署名検証（RS256） |
| **設定** | `DEV_MOCK_TOKEN`, `DEV_MOCK_USER_EMAIL` | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |
| **ユーザー識別** | モック email | azure_oid (Azure Object ID) |
| **適用環境** | ローカル開発 | ステージング、本番 |
| **セキュリティ** | ⚠️ 低（開発用のみ） | ✅ 高（エンタープライズ級） |

### 5.3 依存性注入による切り替え

```python
# src/app/api/core/dependencies/auth.py

if settings.AUTH_MODE == "production":
    # 本番モード: Azure AD認証
    from app.core.security.azure_ad import azure_scheme

    async def get_current_user_azure(
        auth_token: Annotated[AzureToken, Depends(azure_scheme)]
    ) -> UserAccount:
        # Azure AD検証済みトークンからユーザー取得
        ...
else:
    # 開発モード: モック認証
    from app.core.security.dev_auth import dev_token_auth

    async def get_current_user_azure(
        token: Annotated[str, Depends(dev_token_auth)]
    ) -> UserAccount:
        # モックトークンからモックユーザー取得
        ...
```

---

## 6. データフローアーキテクチャ

### 6.1 標準的なリクエストフロー

::: mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant MW as Middleware Stack
    participant API as API Route
    participant Svc as Service
    participant Repo as Repository
    participant DB as PostgreSQL
    participant Cache as Redis

    C->>MW: HTTP Request

    Note over MW: 1. CORS<br/>2. Rate Limit (100req/min)<br/>3. Logging<br/>4. Metrics<br/>5. Security Headers

    MW->>API: Validated Request

    API->>API: Pydanticバリデーション
    API->>API: 認証・認可チェック

    API->>Svc: ビジネスロジック呼び出し

    Svc->>Cache: キャッシュチェック

    alt キャッシュヒット
        Cache-->>Svc: キャッシュデータ
    else キャッシュミス
        Svc->>Repo: データアクセス
        Repo->>DB: SQLクエリ実行
        DB-->>Repo: 結果セット
        Repo-->>Svc: ドメインオブジェクト
        Svc->>Cache: キャッシュ保存
    end

    Svc-->>API: サービスレスポンス
    API-->>MW: HTTPレスポンス
    MW-->>C: Final Response
:::

### 6.2 分析機能のデータフロー

::: mermaid
graph TB
    Start[クライアント: 分析リクエスト] --> Upload[ファイルアップロード<br/>ProjectFileService]

    Upload --> CreateSession[AnalysisSession作成<br/>AnalysisService]

    CreateSession --> InitAgent[AIエージェント初期化<br/>LangChain AgentExecutor]

    InitAgent --> LoadData[データ読み込み<br/>Pandas DataFrame]

    LoadData --> Chat[チャット処理<br/>AnalysisChatService]

    Chat --> AgentDecision{エージェント判断}

    AgentDecision -->|ツール実行| ToolExec[ツール実行<br/>13種類のツール]
    ToolExec --> UpdateStep[AnalysisStep作成<br/>履歴保存]
    UpdateStep --> Chat

    AgentDecision -->|完了| SaveSnapshot[スナップショット保存<br/>JSONB]

    SaveSnapshot --> Response[レスポンス返却<br/>分析結果]

    Response --> End[クライアント]

    subgraph "データ永続化"
        DB[(PostgreSQL)]
        UpdateStep --> DB
        SaveSnapshot --> DB
    end

    subgraph "LLM連携"
        LLM[Anthropic/OpenAI/Azure OpenAI]
        Chat -.->|API Call| LLM
        LLM -.->|Response| Chat
    end

    style Start fill:#E3F2FD
    style Response fill:#C8E6C9
    style ToolExec fill:#FFF9C4
:::

---

## 7. 設計パターン

### 7.1 採用している設計パターン

::: mermaid
graph TB
    subgraph "アーキテクチャパターン"
        A1[Layered Architecture<br/>5層アーキテクチャ]
        A2[Repository Pattern<br/>データアクセス抽象化]
        A3[Dependency Injection<br/>FastAPI Depends]
    end

    subgraph "ビジネスロジックパターン"
        B1[Strategy Pattern<br/>ストレージ切り替え]
        B2[Factory Pattern<br/>アプリケーション生成]
        B3[Facade Pattern<br/>State管理統一]
    end

    subgraph "データアクセスパターン"
        C1[Unit of Work<br/>トランザクション管理]
        C2[Identity Map<br/>SQLAlchemyセッション]
        C3[Lazy Loading<br/>リレーションシップ遅延読込]
    end

    subgraph "並行処理パターン"
        D1[Async/Await<br/>非同期処理]
        D2[Connection Pool<br/>接続プール管理]
    end

    style A1 fill:#BBDEFB
    style B1 fill:#C5CAE9
    style C1 fill:#D1C4E9
    style D1 fill:#F8BBD0
:::

### 7.2 主要パターンの実装例

#### 7.2.1 Repository Pattern

```python
# src/app/repositories/base.py

class BaseRepository(Generic[ModelType, IDType]):
    """汎用リポジトリ基底クラス"""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: IDType) -> ModelType | None:
        """ID取得"""
        return await db.get(self.model, id)

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> list[ModelType]:
        """複数取得（フィルタ対応）"""
        ...

    async def create(self, db: AsyncSession, **obj_in) -> ModelType:
        """作成"""
        ...
```

#### 7.2.2 Strategy Pattern（ストレージ）

```python
# src/app/services/storage/__init__.py

from .base import StorageService
from .local import LocalStorageService
from .azure import AzureStorageService

def get_storage_service() -> StorageService:
    """設定に応じてストレージ実装を返す"""
    if settings.STORAGE_TYPE == "azure":
        return AzureStorageService(settings.AZURE_STORAGE_CONNECTION_STRING)
    return LocalStorageService(settings.LOCAL_STORAGE_PATH)

# src/app/services/storage/base.py - StorageService（抽象基底クラス）
# src/app/services/storage/local.py - LocalStorageService
# src/app/services/storage/azure.py - AzureStorageService
```

#### 7.2.3 Dependency Injection

```python
# src/app/api/core/dependencies/ (機能別に分割)
# - auth.py: 認証関連
# - database.py: データベース関連
# - project.py: プロジェクト関連
# - analysis.py: 個別施策分析関連
# - driver_tree.py: ドライバーツリー関連
# - user_account.py: ユーザーアカウント関連

# 型付き依存性
CurrentUserAccountDep = Annotated[UserAccount, Depends(get_current_active_user_azure)]
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]

# エンドポイントでの利用
@router.get("/projects/{project_id}")
async def get_project(
    project_id: UUID,
    db: DatabaseDep,  # DB接続注入
    current_user: CurrentUserAccountDep,  # 認証ユーザー注入
) -> ProjectResponse:
    ...
```

---

## 8. スケーラビリティ設計

### 8.1 スケーラビリティ戦略

::: mermaid
graph TB
    subgraph "水平スケーリング"
        LB[ロードバランサー] --> App1[FastAPI Instance 1]
        LB --> App2[FastAPI Instance 2]
        LB --> App3[FastAPI Instance N]
    end

    subgraph "データ層スケーリング"
        App1 --> Master[PostgreSQL Master]
        App2 --> Master
        App3 --> Master

        Master --> Replica1[Read Replica 1]
        Master --> Replica2[Read Replica N]

        App1 --> RedisCluster[Redis Cluster]
        App2 --> RedisCluster
        App3 --> RedisCluster
    end

    subgraph "ストレージスケーリング"
        App1 --> AzureBlob[Azure Blob Storage<br/>高可用性・無制限]
        App2 --> AzureBlob
        App3 --> AzureBlob
    end

    style LB fill:#4CAF50
    style Master fill:#2196F3
    style RedisCluster fill:#F44336
:::

### 8.2 パフォーマンス最適化

| 項目 | 実装 | 効果 |
|------|------|------|
| **接続プール** | pool_size=5, max_overflow=10 | DB接続再利用 |
| **N+1対策** | selectinload(), joinedload() | クエリ数削減 |
| **キャッシュ** | Redis TTL付きキャッシュ | DB負荷軽減 |
| **非同期I/O** | async/await全面採用 | 並行処理性能向上 |
| **レート制限** | 100req/min | サービス保護 |
| **インデックス** | 主キー、外部キー、検索列 | クエリ高速化 |

---

## 9. 可観測性（Observability）

### 9.1 可観測性の3本柱

::: mermaid
graph LR
    subgraph "Logs"
        A1[structlog<br/>構造化ログ]
        A2[JSON形式出力]
        A3[コンテキスト付与]
    end

    subgraph "Metrics"
        B1[Prometheus<br/>メトリクス収集]
        B2[HTTPメトリクス]
        B3[カスタムメトリクス]
    end

    subgraph "Traces"
        C1[LangSmith<br/>LLMトレーシング]
        C2[エージェント実行履歴]
        C3[パフォーマンス分析]
    end

    A1 --> ELK[ELK Stack<br/>ログ集約]
    B1 --> Grafana[Grafana<br/>ダッシュボード]
    C1 --> LangSmithUI[LangSmith UI<br/>トレース分析]

    style A1 fill:#FFD54F
    style B1 fill:#FF8A65
    style C1 fill:#81C784
:::

### 9.2 実装されている計測

**ログ（src/app/core/logging.py）:**

- リクエスト/レスポンスログ
- エラースタックトレース
- ユーザーコンテキスト（user_id, project_id）
- 実行時間

**メトリクス（src/app/api/middlewares/metrics.py）:**

- `http_requests_total`: リクエスト総数
- `http_request_duration_seconds`: レスポンスタイム
- `http_requests_in_progress`: 実行中リクエスト数
- カスタムメトリクス（ビジネスメトリクス）

**トレーシング:**

- LangSmithによるLLM呼び出しトレース
- ツール実行履歴（ToolTrackingHandler）
- エージェントステート履歴

---

## 10. セキュリティアーキテクチャ

### 10.1 多層防御（Defense in Depth）

::: mermaid
graph TB
    subgraph "Layer 1: ネットワーク"
        L1[HTTPS強制<br/>TLS 1.2+]
    end

    subgraph "Layer 2: アプリケーション境界"
        L2A[CORS制御]
        L2B[レート制限<br/>100req/min]
        L2C[セキュリティヘッダー]
    end

    subgraph "Layer 3: 認証・認可"
        L3A[Azure AD JWT認証]
        L3B[RBAC<br/>システム/プロジェクトロール]
        L3C[プロジェクトメンバーシップ検証]
    end

    subgraph "Layer 4: データ保護"
        L4A[bcryptパスワードハッシュ<br/>12ラウンド]
        L4B[SQLインジェクション対策<br/>パラメータ化クエリ]
        L4C[XSS対策<br/>Pydanticバリデーション]
    end

    subgraph "Layer 5: 監査"
        L5A[監査ログ]
        L5B[アクセスログ]
        L5C[エラートラッキング]
    end

    L1 --> L2A
    L2A --> L2B
    L2B --> L2C
    L2C --> L3A
    L3A --> L3B
    L3B --> L3C
    L3C --> L4A
    L4A --> L4B
    L4B --> L4C
    L4C --> L5A
    L5A --> L5B
    L5B --> L5C

    style L1 fill:#F44336
    style L3A fill:#FF9800
    style L4A fill:#FFC107
    style L5A fill:#4CAF50
:::

---

## 11. 環境構成

### 11.1 環境別設定

::: mermaid
graph LR
    subgraph "開発環境"
        Dev[.env.local]
        DevDB[(PostgreSQL<br/>localhost)]
        DevRedis[(Redis<br/>localhost)]
        DevStorage[Local Storage]
    end

    subgraph "ステージング環境"
        Stg[.env.staging]
        StgDB[(PostgreSQL<br/>Azure Database)]
        StgRedis[(Azure Redis)]
        StgStorage[Azure Blob Storage]
    end

    subgraph "本番環境"
        Prod[.env.production]
        ProdDB[(PostgreSQL<br/>Azure Database<br/>HA構成)]
        ProdRedis[(Azure Redis<br/>Cluster)]
        ProdStorage[Azure Blob Storage<br/>Geo冗長]
    end

    Dev --> DevDB
    Dev --> DevRedis
    Dev --> DevStorage

    Stg --> StgDB
    Stg --> StgRedis
    Stg --> StgStorage

    Prod --> ProdDB
    Prod --> ProdRedis
    Prod --> ProdStorage

    style Dev fill:#FFF9C4
    style Stg fill:#FFE082
    style Prod fill:#FFD54F
:::

### 11.2 環境別の主要差分

| 設定項目 | 開発 | ステージング | 本番 |
|---------|------|------------|------|
| **AUTH_MODE** | development | production | production |
| **DEBUG** | True | False | False |
| **DATABASE_URL** | localhost | Azure Database | Azure Database (HA) |
| **REDIS_URL** | localhost | Azure Redis | Azure Redis Cluster |
| **STORAGE_BACKEND** | local | azure | azure |
| **LOG_LEVEL** | DEBUG | INFO | WARNING |
| **WORKERS** | 1 | 2 | 4+ |

---

## 12. 依存関係管理

### 12.1 パッケージ管理

::: mermaid
graph TB
    UV[uv: 高速パッケージマネージャー]

    UV --> PyProject[pyproject.toml<br/>依存関係定義]
    PyProject --> UVLock[uv.lock<br/>バージョンロック]

    UVLock --> ProdDeps[本番依存関係<br/>47パッケージ]
    UVLock --> DevDeps[開発依存関係<br/>8パッケージ]

    ProdDeps --> FastAPI[FastAPI 0.115+]
    ProdDeps --> SQLAlchemy[SQLAlchemy 2.0+]
    ProdDeps --> LangChain[LangChain 0.3+]

    DevDeps --> Pytest[pytest 8.3+]
    DevDeps --> Ruff[Ruff 0.8+]
    DevDeps --> Mypy[mypy 1.18+]

    style UV fill:#00ACC1
    style PyProject fill:#0097A7
    style UVLock fill:#00838F
:::

**主要な依存関係グループ：**

1. **Webフレームワーク**: FastAPI, Uvicorn, Pydantic
2. **AI/LLM**: LangChain, LangGraph, LangServe, LangSmith
3. **データベース**: SQLAlchemy, asyncpg, Alembic
4. **セキュリティ**: python-jose, passlib, fastapi-azure-auth
5. **監視**: structlog, prometheus-client
6. **ストレージ**: aiofiles, azure-storage-blob
7. **開発**: pytest, pytest-asyncio, pytest-cov, Ruff, mypy

---

## 13. まとめ

### 13.1 アーキテクチャの強み

✅ **モダンな非同期アーキテクチャ**: FastAPI + SQLAlchemy 2.0による高性能
✅ **明確な責務分離**: レイヤードアーキテクチャによる保守性
✅ **柔軟な認証**: 開発/本番モード切り替え
✅ **エンタープライズセキュリティ**: Azure AD、RBAC、多層防御
✅ **AIエージェント統合**: LangChainによる高度な分析機能
✅ **可観測性**: ログ、メトリクス、トレーシング完備
✅ **スケーラビリティ**: 水平スケーリング対応設計
✅ **型安全性**: Pydantic + Type Hints

### 13.2 今後の拡張ポイント

- Docker/Kubernetes対応
- CI/CDパイプライン整備
- Alembicマイグレーション有効化
- GraphQL API追加
- WebSocket対応（リアルタイム通信）
- マイクロサービス分割検討

---

**ドキュメント管理情報:**

- **作成日**: 2025年（リバースエンジニアリング実施）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - データベース設計書: `02-database/01-database-design.md`
  - セキュリティ設計書: `03-security/`
  - API仕様書: `04-api/01-api-specifications.md`
