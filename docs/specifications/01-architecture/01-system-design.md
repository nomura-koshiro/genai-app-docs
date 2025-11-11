# システム設計書（System Design）

## 📋 文書管理情報

| 項目 | 内容 |
|------|------|
| **文書名** | システム設計書（System Design） |
| **バージョン** | 1.0.0 |
| **作成日** | 2025-01-11 |
| **最終更新日** | 2025-01-11 |
| **作成者** | Claude Code |
| **レビュー状態** | 初版 |

---

## 📑 目次

1. [概要](#1-概要)
2. [システム全体像](#2-システム全体像)
3. [技術スタック](#3-技術スタック)
4. [アーキテクチャ設計](#4-アーキテクチャ設計)
5. [レイヤードアーキテクチャ](#5-レイヤードアーキテクチャ)
6. [依存性注入（DI）](#6-依存性注入di)
7. [アプリケーションファクトリパターン](#7-アプリケーションファクトリパターン)
8. [設定管理](#8-設定管理)
9. [ライフサイクル管理](#9-ライフサイクル管理)
10. [デザインパターン](#10-デザインパターン)
11. [パフォーマンス最適化](#11-パフォーマンス最適化)
12. [付録](#12-付録)

---

## 1. 概要

### 1.1 目的

本設計書は、genai-app-docs（camp-backend）プロジェクトのシステム全体のアーキテクチャと設計判断を文書化し、以下を達成することを目的とします：

- **システム全体の理解促進**: 新規参画者が迅速にシステムを理解できる
- **設計判断の記録**: なぜこのアーキテクチャを選択したのかを説明
- **保守性の向上**: 一貫した設計原則に基づく開発を支援
- **技術的負債の削減**: 設計意図を明確にし、誤った実装を防止

### 1.2 適用範囲

本設計書は以下を対象とします：

- ✅ システム全体のアーキテクチャ構成
- ✅ 技術スタックと選定理由
- ✅ レイヤー設計とコンポーネント構成
- ✅ 依存性注入とライフサイクル管理
- ✅ 設計パターンとベストプラクティス

以下は**対象外**とし、別の設計書で詳述します：

- ❌ データベース設計の詳細 → [Database設計書](../02-database/01-database-design.md)
- ❌ セキュリティ・認証の詳細 → [RBAC設計書](../03-security/01-rbac-design.md)
- ❌ API仕様の詳細 → [API設計書](../04-api/01-api-design.md)

### 1.3 前提条件

本設計書を読むには以下の知識が推奨されます：

- **Python 3.13+**: 非同期プログラミング（async/await）
- **FastAPI**: 基本的なAPIエンドポイント定義
- **SQLAlchemy 2.0**: ORM基礎
- **PostgreSQL**: リレーショナルデータベース基礎
- **REST API**: 基本的なHTTPメソッドとステータスコード

---

## 2. システム全体像

### 2.1 システム概要

**genai-app-docs（camp-backend）** は、FastAPI + LangChain + LangGraphをベースにした、AIエージェント機能とデータ分析機能を持つバックエンドAPIシステムです。

**主要機能**:

- 🤖 **AIエージェント**: LangGraphによる高度な会話エンジン
- 📊 **データ分析**: pandas連携によるデータ集計・グラフ生成
- 📁 **ファイル管理**: アップロード・ダウンロード機能
- 🔐 **認証・認可**: Azure AD / JWT認証、RBAC（2階層ロール）
- 🚀 **プロジェクト管理**: マルチテナント対応のプロジェクトワークスペース

### 2.2 システムコンテキスト図

```mermaid
graph TB
    subgraph "External Users"
        WebUI[フロントエンドUI<br/>React/Next.js]
        SwaggerUI[Swagger UI<br/>API開発者]
    end

    subgraph "genai-app-docs Backend"
        API[FastAPI<br/>Application]

        subgraph "Core Services"
            AuthSvc[認証サービス]
            ProjectSvc[プロジェクトサービス]
            AnalysisSvc[分析サービス]
            FileSvc[ファイルサービス]
        end

        subgraph "AI/Agent Layer"
            LangGraph[LangGraph<br/>Agent Executor]
            LangChain[LangChain<br/>Tools & Chains]
        end
    end

    subgraph "External Systems"
        AzureAD[Azure AD<br/>認証プロバイダー]
        AnthropicAPI[Anthropic API<br/>Claude LLM]
        OpenAIAPI[OpenAI API<br/>GPT LLM]
    end

    subgraph "Data Storage"
        PostgreSQL[(PostgreSQL<br/>メインDB)]
        Redis[(Redis<br/>キャッシュ)]
        AzureBlob[Azure Blob Storage<br/>ファイル]
        LocalFS[Local File System<br/>開発用)]
    end

    WebUI -->|REST API| API
    SwaggerUI -->|REST API| API

    API --> AuthSvc
    API --> ProjectSvc
    API --> AnalysisSvc
    API --> FileSvc

    AnalysisSvc --> LangGraph
    LangGraph --> LangChain

    AuthSvc -.->|Azure AD<br/>Token検証| AzureAD
    LangChain -.->|LLM API| AnthropicAPI
    LangChain -.->|LLM API| OpenAIAPI

    API --> PostgreSQL
    API --> Redis
    FileSvc --> AzureBlob
    FileSvc --> LocalFS
```

### 2.3 システム特性

| 特性 | 現状の設計 | 目標 |
|------|-----------|------|
| **可用性** | 単一サーバー | 99.9% (ロードバランサー + 冗長化) |
| **パフォーマンス** | 100req/min制限 | レスポンスタイム < 200ms (95パーセンタイル) |
| **スケーラビリティ** | 垂直スケーリング | 水平スケーリング対応（ステートレス設計） |
| **セキュリティ** | Azure AD認証, RBAC | OWASP Top 10対策、監査ログ |
| **保守性** | 4層アーキテクチャ | コードカバレッジ > 80% |

---

## 3. 技術スタック

### 3.1 技術スタック全体図

```mermaid
graph TB
    subgraph "Application Layer"
        FastAPI[FastAPI 0.115+<br/>Web Framework]
        Uvicorn[Uvicorn<br/>ASGI Server]
        Pydantic[Pydantic 2.0+<br/>Validation]
    end

    subgraph "AI/Agent Layer"
        LangChain[LangChain 0.3+<br/>LLM Framework]
        LangGraph[LangGraph 0.2+<br/>Agent Orchestration]
        LangServe[LangServe 0.3+<br/>Deployment]
        LangSmith[LangSmith<br/>Observability]
    end

    subgraph "Data Layer"
        SQLAlchemy[SQLAlchemy 2.0+<br/>ORM]
        Alembic[Alembic<br/>Migration]
        AsyncPG[asyncpg<br/>PostgreSQL Driver]
        Psycopg2[psycopg2-binary<br/>Sync Driver]
    end

    subgraph "Storage Layer"
        AzureStorage[azure-storage-blob<br/>Blob Storage]
        AzureIdentity[azure-identity<br/>Auth]
        AIOFiles[aiofiles<br/>Async File IO]
    end

    subgraph "Processing Layer"
        Pandas[pandas<br/>Data Analysis]
        PythonPPTX[python-pptx<br/>PowerPoint]
    end

    subgraph "Security Layer"
        Passlib[passlib[bcrypt]<br/>Password Hashing]
        PythonJose[python-jose<br/>JWT]
        FastAPIAzure[fastapi-azure-auth<br/>Azure AD]
    end

    subgraph "Infrastructure Layer"
        Redis[redis[hiredis]<br/>Cache]
        Prometheus[prometheus-client<br/>Metrics]
        Structlog[structlog<br/>Logging]
        HTTPX[httpx<br/>HTTP Client]
    end

    FastAPI --> Pydantic
    FastAPI --> SQLAlchemy
    FastAPI --> LangChain
    LangChain --> LangGraph
    LangGraph --> LangSmith
    SQLAlchemy --> AsyncPG
    SQLAlchemy --> Alembic
```

### 3.2 主要技術の選定理由

#### 3.2.1 Web Framework: FastAPI

**選定理由**:

- ✅ **高速**: Uvicorn（ASGI）ベースで非同期処理に最適
- ✅ **自動ドキュメント生成**: OpenAPI/Swagger UI自動生成
- ✅ **型安全性**: Pydanticによる自動バリデーション
- ✅ **依存性注入**: 組み込みDIシステム（Depends）
- ✅ **非同期対応**: async/awaitネイティブサポート

**代替案との比較**:

| フレームワーク | FastAPI | Flask | Django REST |
|--------------|---------|-------|-------------|
| 非同期サポート | ◎ Native | △ 外部ライブラリ | △ Django 3.1+ |
| 自動ドキュメント | ◎ 組み込み | ✕ 手動 | △ drf-spectacular |
| パフォーマンス | ◎ 高速 | ○ 中速 | △ 低速 |
| 学習曲線 | ○ 中 | ◎ 易 | △ 難 |

#### 3.2.2 ORM: SQLAlchemy 2.0

**選定理由**:

- ✅ **非同期対応**: asyncpgドライバーで完全非同期
- ✅ **型安全性**: SQLAlchemy 2.0のMapped型アノテーション
- ✅ **強力なクエリビルダ**: 複雑なJOIN、サブクエリ対応
- ✅ **マイグレーション**: Alembicとの統合
- ✅ **成熟度**: 15年以上の実績

#### 3.2.3 AI/Agent: LangChain + LangGraph

**選定理由**:

- ✅ **エージェント構築**: LangGraphによる状態管理型エージェント
- ✅ **マルチLLM対応**: Anthropic, OpenAI, Azure OpenAIを統一API
- ✅ **ツール統合**: pandas, ファイル処理などのツール連携
- ✅ **可観測性**: LangSmithによるトレーシング
- ✅ **コミュニティ**: 活発な開発とエコシステム

#### 3.2.4 Database: PostgreSQL

**選定理由**:

- ✅ **JSONB型**: 柔軟なスキーマ（analysis_session.config）
- ✅ **UUID型**: ネイティブUUID v4サポート
- ✅ **ACID保証**: トランザクション整合性
- ✅ **パフォーマンス**: インデックス、パーティショニング
- ✅ **エンタープライズ対応**: 監査ログ、レプリケーション

### 3.3 依存関係（pyproject.toml）

```toml
[project]
name = "camp-backend"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    # Web Framework
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",

    # AI/LangChain
    "langchain>=0.3.0",
    "langgraph>=0.2.0",
    "langserve>=0.3.0",
    "langsmith>=0.2.0",
    "langchain-anthropic>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-community>=0.3.0",

    # Database
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
    "psycopg2-binary>=2.9.0",
    "asyncpg>=0.30.0",

    # File Processing
    "python-multipart>=0.0.17",
    "aiofiles>=24.1.0",
    "azure-storage-blob>=12.23.0",
    "azure-identity>=1.19.0",

    # Data Processing
    "pandas>=2.2.0",
    "python-pptx>=1.0.0",

    # Configuration & Utilities
    "pydantic-settings>=2.6.0",
    "pydantic[email]>=2.0.0",
    "python-dotenv>=1.0.0",

    # Logging
    "structlog>=24.4.0",

    # HTTP Client
    "httpx>=0.28.1",

    # Security
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",

    # Cache
    "redis[hiredis]>=6.4.0",

    # Monitoring
    "prometheus-client>=0.23.1",
    "prometheus-fastapi-instrumentator>=7.1.0",
]
```

---

## 4. アーキテクチャ設計

### 4.1 設計原則

本システムは以下の設計原則に基づいて構築されています：

#### 4.1.1 SOLID原則

1. **単一責任の原則（SRP: Single Responsibility Principle）**
   - 各クラスは1つの責任のみを持つ
   - 例: `ProjectMemberAuthorizationChecker` は権限チェックのみを担当

2. **オープン・クローズドの原則（OCP: Open/Closed Principle）**
   - 拡張に対して開いている、修正に対して閉じている
   - 例: `BaseRepository[ModelType, IDType]` ジェネリック型で拡張可能

3. **リスコフの置換原則（LSP: Liskov Substitution Principle）**
   - 派生クラスは基底クラスと置換可能
   - 例: すべてのRepositoryは `BaseRepository` と互換性あり

4. **インターフェース分離の原則（ISP: Interface Segregation Principle）**
   - クライアントは使用しないメソッドに依存しない
   - 例: Facadeパターンで必要な操作のみ公開

5. **依存性逆転の原則（DIP: Dependency Inversion Principle）**
   - 上位モジュールは下位モジュールに依存しない、抽象に依存する
   - 例: サービス層はRepositoryインターフェース（抽象）に依存

#### 4.1.2 Clean Architecture原則

```mermaid
graph TB
    subgraph "Outer Layer"
        API[API Layer<br/>routes/]
    end

    subgraph "Application Layer"
        Service[Service Layer<br/>services/]
    end

    subgraph "Domain Layer"
        Repository[Repository Layer<br/>repositories/]
    end

    subgraph "Infrastructure Layer"
        Model[Data Layer<br/>models/]
        DB[(Database)]
    end

    API -->|"依存"| Service
    Service -->|"依存"| Repository
    Repository -->|"依存"| Model
    Model --> DB

    style API fill:#e3f2fd
    style Service fill:#fff9c4
    style Repository fill:#c8e6c9
    style Model fill:#ffccbc
```

**依存性の方向**: 外側の層が内側の層に依存する（単一方向のデータフロー）

#### 4.1.3 DRY原則（Don't Repeat Yourself）

- **BaseRepository**: すべてのリポジトリで共通のCRUD操作を一元化
- **TimestampMixin**: created_at, updated_atフィールドを共通化
- **PrimaryKeyMixin**: UUID主キーを共通化

### 4.2 コンポーネント図

```mermaid
graph TB
    subgraph "API Layer (routes/)"
        SystemRoutes[System Routes<br/>health, metrics, root]
        V1Routes[V1 Routes<br/>users, projects, analysis]
        Middlewares[Middlewares<br/>CORS, Rate Limit, Logging]
        ExceptionHandlers[Exception Handlers<br/>カスタム例外処理]
        Dependencies[Dependencies<br/>DI定義]
    end

    subgraph "Service Layer (services/)"
        UserService[UserService<br/>ユーザー管理]
        ProjectService[ProjectService<br/>プロジェクト管理]
        MemberFacade[ProjectMemberFacade<br/>メンバー管理]
        AnalysisService[AnalysisService<br/>データ分析]
        FileService[FileService<br/>ファイル管理]
        AuthChecker[AuthorizationChecker<br/>権限チェック]
    end

    subgraph "Repository Layer (repositories/)"
        BaseRepo[BaseRepository<br/>共通CRUD]
        UserRepo[UserRepository]
        ProjectRepo[ProjectRepository]
        MemberRepo[MemberRepository]
        FileRepo[FileRepository]
    end

    subgraph "Data Layer (models/)"
        BaseModel[Base<br/>DeclarativeBase]
        Mixins[Mixins<br/>Timestamp, PrimaryKey]
        UserModel[User Model]
        ProjectModel[Project Model]
        MemberModel[ProjectMember Model]
    end

    subgraph "Core (core/)"
        Config[Config<br/>settings管理]
        Database[Database<br/>接続管理]
        Security[Security<br/>認証・認可]
        Logging[Logging<br/>structlog]
        Cache[Cache<br/>Redis管理]
    end

    V1Routes --> Dependencies
    Dependencies --> UserService
    Dependencies --> ProjectService
    Dependencies --> AnalysisService

    UserService --> UserRepo
    ProjectService --> ProjectRepo
    MemberFacade --> MemberRepo
    MemberFacade --> AuthChecker

    UserRepo --> BaseRepo
    ProjectRepo --> BaseRepo
    MemberRepo --> BaseRepo

    BaseRepo --> Database
    UserModel --> BaseModel
    UserModel --> Mixins

    style API Layer fill:#e3f2fd
    style Service Layer fill:#fff9c4
    style Repository Layer fill:#c8e6c9
    style Data Layer fill:#ffccbc
    style Core fill:#f3e5f5
```

---

## 5. レイヤードアーキテクチャ

### 5.1 4層アーキテクチャ

本システムは以下の4層に分離されています：

```text
┌─────────────────────────────────────────────────────────┐
│ API Layer (routes/)                                      │
│ - HTTPリクエスト受信                                      │
│ - Pydanticによるバリデーション                            │
│ - レスポンス整形                                          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ Service Layer (services/)                                │
│ - ビジネスロジック                                        │
│ - トランザクション管理                                    │
│ - 複数リポジトリの調整                                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ Repository Layer (repositories/)                         │
│ - データアクセスロジック                                  │
│ - クエリ構築                                              │
│ - CRUD操作                                                │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ Data Layer (models/)                                     │
│ - SQLAlchemyモデル定義                                    │
│ - リレーションシップ定義                                  │
│ - 制約定義                                                │
└─────────────────────────────────────────────────────────┘
```

### 5.2 API Layer（routes/）

**責任**:

- HTTPリクエストの受信とレスポンスの返却
- Pydanticスキーマによる入力バリデーション
- 依存性注入（DI）によるサービス取得
- 認証・認可の適用

**ディレクトリ構造**:

```text
api/
├── core/
│   ├── dependencies.py      # DI定義
│   └── exception_handlers.py # 例外ハンドラー
├── decorators/              # デコレータ（認可、再試行など）
├── middlewares/             # ミドルウェア（CORS, Rate Limit, Logging）
└── routes/
    ├── system/              # システムエンドポイント（health, metrics）
    │   ├── health.py
    │   ├── metrics.py
    │   └── root.py
    └── v1/                  # API v1エンドポイント
        ├── users.py
        ├── projects.py
        ├── project_members.py
        ├── project_files.py
        ├── analysis.py
        ├── analysis_templates.py
        ├── ppt_generator.py
        └── driver_tree.py
```

**実装例（`routes/v1/users.py`）**:

```python
from fastapi import APIRouter, Depends
from app.api.core.dependencies import AzureUserServiceDep, CurrentUserAzureDep
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: CurrentUserAzureDep,
) -> UserResponse:
    """現在の認証ユーザー情報を取得します。"""
    return UserResponse.model_validate(current_user)
```

**設計指針**:

- ✅ エンドポイントは薄く保つ（ビジネスロジックを含まない）
- ✅ サービス層への委譲のみ
- ✅ Pydanticスキーマで入出力を明示
- ✅ 依存性注入を活用

### 5.3 Service Layer（services/）

**責任**:

- ビジネスロジックの実装
- トランザクション管理（commit/rollback）
- 複数リポジトリの調整
- ドメインルールの実施

**主要サービス**:

| サービス | 責任 | 依存リポジトリ |
|---------|------|---------------|
| `UserService` | ユーザー管理、Azure AD連携 | `UserRepository` |
| `ProjectService` | プロジェクトCRUD、権限チェック | `ProjectRepository`, `ProjectMemberRepository` |
| `ProjectMemberFacade` | メンバー管理の統一インターフェース | `ProjectMemberRepository`, `UserRepository`, `ProjectRepository` |
| `AnalysisService` | データ分析セッション管理 | `AnalysisSessionRepository`, `ProjectRepository` |
| `FileService` | ファイルアップロード/ダウンロード | `FileRepository`, `StorageService` |

**実装例（`services/user.py`）**:

```python
from app.repositories.user import UserRepository

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.db = db

    async def get_or_create_by_azure_oid(
        self,
        azure_oid: str,
        email: str,
        display_name: str | None = None,
        roles: list[str] | None = None,
    ) -> User:
        """Azure OIDでユーザーを検索、存在しない場合は作成します。"""
        # ビジネスロジック
        user = await self.repository.get_by_azure_oid(azure_oid)
        if not user:
            user = await self.repository.create(
                azure_oid=azure_oid,
                email=email,
                display_name=display_name,
                roles=roles or ["user"],
            )
            await self.db.commit()
        return user
```

**設計指針**:

- ✅ 1サービス = 1ドメインエンティティ（SRP）
- ✅ トランザクションはサービス層で管理
- ✅ Facadeパターンで複雑な操作を単純化
- ✅ 再利用可能な小さなメソッドに分割

### 5.4 Repository Layer（repositories/）

**責任**:

- データアクセスロジックのカプセル化
- SQLクエリの構築と実行
- CRUD操作の提供

**BaseRepository（共通CRUD）**:

```python
class BaseRepository[ModelType: Base, IDType: (int, uuid.UUID)]:
    """SQLAlchemyモデルの共通CRUD操作を提供するベースリポジトリクラス。"""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: IDType) -> ModelType | None:
        """IDによってレコードを取得します。"""
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        load_relations: list[str] | None = None,
        **filters: Any,
    ) -> list[ModelType]:
        """オプションのフィルタリングで複数のレコードを取得します。"""
        # 実装省略（N+1クエリ対策、フィルタリング、ソート）

    async def create(self, **obj_in: Any) -> ModelType:
        """新しいレコードを作成します（flush()のみ、commit()は呼び出し側）。"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, **update_data: Any) -> ModelType:
        """既存レコードを更新します。"""
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: IDType) -> bool:
        """レコードを削除します。"""
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
            return True
        return False

    async def count(self, **filters: Any) -> int:
        """オプションのフィルタリングでレコードの総数を取得します。"""
        # 実装省略
```

**カスタムリポジトリ（`repositories/user.py`）**:

```python
class UserRepository(BaseRepository[User, uuid.UUID]):
    """ユーザー専用のリポジトリクラス。"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """メールアドレスでユーザーを取得します。"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_azure_oid(self, azure_oid: str) -> User | None:
        """Azure OIDでユーザーを取得します。"""
        result = await self.db.execute(
            select(User).where(User.azure_oid == azure_oid)
        )
        return result.scalar_one_or_none()
```

**設計指針**:

- ✅ BaseRepositoryを継承してDRY原則を実現
- ✅ ジェネリック型`[ModelType, IDType]`で型安全性確保
- ✅ `flush()`のみ実行、`commit()`はサービス層の責任
- ✅ N+1クエリ対策（`load_relations`パラメータ）

### 5.5 Data Layer（models/）

**責任**:

- SQLAlchemyモデル定義
- テーブル構造の定義
- リレーションシップの定義

**Base & Mixins**:

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """すべてのデータベースモデル（ORMクラス）の基底クラス。"""
    pass

class PrimaryKeyMixin:
    """主キー（id）を提供するミックスイン。"""
    @declared_attr
    def id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            index=True,
        )

class TimestampMixin:
    """タイムスタンプフィールドを提供するミックスイン。"""
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            onupdate=lambda: datetime.now(UTC),
            nullable=False,
        )
```

**モデル例（`models/user.py`）**:

```python
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

class User(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    # フィールド定義
    azure_oid: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # リレーションシップ
    projects: Mapped[list["Project"]] = relationship(
        "Project", secondary="project_members", back_populates="members"
    )
```

**設計指針**:

- ✅ Mixinで共通フィールドを一元化
- ✅ SQLAlchemy 2.0のMapped型アノテーションを使用
- ✅ UUID v4主キーで分散システム対応
- ✅ JSONB型で柔軟なスキーマ対応

---

## 6. 依存性注入（DI）

### 6.1 FastAPI Dependsシステム

本システムはFastAPIの`Depends`機能を活用した依存性注入を実装しています。

**DI定義（`api/core/dependencies.py`）**:

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# データベースセッション依存性
from app.core.database import get_db
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]

# サービス依存性
def get_azure_user_service(db: DatabaseDep) -> UserService:
    return UserService(db)

AzureUserServiceDep = Annotated[UserService, Depends(get_azure_user_service)]

# 認証依存性
async def get_authenticated_user_from_azure(
    user_service: AzureUserServiceDep,
    azure_user: Any = Depends(get_current_azure_user),
) -> User:
    user = await user_service.get_or_create_by_azure_oid(
        azure_oid=azure_user.oid,
        email=azure_user.email,
        display_name=getattr(azure_user, "name", None),
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

CurrentUserAzureDep = Annotated[User, Depends(get_authenticated_user_from_azure)]
```

### 6.2 依存性グラフ

```mermaid
graph TB
    Endpoint[エンドポイント関数]

    Endpoint -->|Depends| CurrentUser[CurrentUserAzureDep<br/>認証ユーザー]
    Endpoint -->|Depends| ProjectService[ProjectServiceDep<br/>プロジェクトサービス]

    CurrentUser -->|Depends| UserService[AzureUserServiceDep<br/>ユーザーサービス]
    CurrentUser -->|Depends| AzureUser[AzureUser<br/>Azure AD検証]

    UserService -->|Depends| DB1[DatabaseDep<br/>DBセッション]
    ProjectService -->|Depends| DB2[DatabaseDep<br/>DBセッション]

    DB1 -->|生成| Session1[AsyncSession]
    DB2 -->|生成| Session2[AsyncSession]

    style Endpoint fill:#e3f2fd
    style CurrentUser fill:#fff9c4
    style UserService fill:#c8e6c9
    style DB1 fill:#ffccbc
```

**利点**:

- ✅ **テスタビリティ**: モックに差し替え可能
- ✅ **コードの再利用**: DI定義を複数エンドポイントで共有
- ✅ **明示的な依存関係**: 型アノテーションで依存関係が明確
- ✅ **自動クリーンアップ**: セッションの自動クローズ

---

## 7. アプリケーションファクトリパターン

### 7.1 create_app()関数

アプリケーションの初期化は`core/app_factory.py`の`create_app()`関数で集中管理されています。

**実装（`core/app_factory.py`）**:

```python
from fastapi import FastAPI
from app.core.config import settings

def create_app() -> FastAPI:
    """FastAPIアプリケーションインスタンスを作成します。"""

    # FastAPIインスタンス作成
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="LangChain/LangGraphを使用したAIエージェントAPI",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 例外ハンドラーを登録
    register_exception_handlers(app)

    # ミドルウェアを登録（実行順序は登録の逆順）
    app.add_middleware(PrometheusMetricsMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.RATE_LIMIT_CALLS,
        period=settings.RATE_LIMIT_PERIOD,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS or [],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Accept", "Content-Type", "Authorization", "X-API-Key"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    # ルーターを登録
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
    app.include_router(health.router, tags=["health"])
    app.include_router(metrics.router, tags=["metrics"])

    return app
```

### 7.2 ミドルウェアスタック

リクエストは以下の順序でミドルウェアを通過します：

```text
 リクエスト
    ↓
[CORS Middleware] ← クロスオリジン制御
    ↓
[RateLimitMiddleware] ← 100req/min制限
    ↓
[LoggingMiddleware] ← 構造化ログ記録
    ↓
[ErrorHandlerMiddleware] ← エラーハンドリング
    ↓
[PrometheusMetricsMiddleware] ← メトリクス収集
    ↓
[Router] ← エンドポイント処理
    ↓
レスポンス
```

**各ミドルウェアの責任**:

| ミドルウェア | 責任 | 実装ファイル |
|------------|------|-------------|
| `SecurityHeadersMiddleware` | X-Content-Type-Options, X-Frame-Options, HSTS追加 | `api/middlewares/security_headers.py` |
| `CORSMiddleware` | CORS制御（本番環境では厳格化） | FastAPI組み込み |
| `RateLimitMiddleware` | 100req/min制限、IPベース | `api/middlewares/rate_limit.py` |
| `LoggingMiddleware` | 構造化ログ（structlog） | `api/middlewares/logging.py` |
| `ErrorHandlerMiddleware` | 例外キャッチと整形 | `api/middlewares/error_handler.py` |
| `PrometheusMetricsMiddleware` | メトリクス収集（レスポンスタイム、ステータスコード） | `api/middlewares/metrics.py` |

---

## 8. 設定管理

### 8.1 環境別設定ファイル

設定は環境変数と`.env`ファイルで管理され、`core/config.py`で集約されます。

**設定ファイルの優先順位**:

```text
1. 環境変数（最優先）
2. .env.{environment}（環境別設定）
   - .env.local (development)
   - .env.staging (staging)
   - .env.production (production)
3. .env（共通設定）
4. Settingsクラスのデフォルト値
```

### 8.2 Settings クラス（Pydantic Settings）

**実装（`core/config.py`）**:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """アプリケーション設定クラス。"""

    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # アプリケーション設定
    APP_NAME: str = "camp-backend"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # セキュリティ設定
    SECRET_KEY: str = Field(min_length=32)
    ALLOWED_ORIGINS: list[str] | None = None

    # データベース設定
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app_db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True

    # LLM設定
    LLM_PROVIDER: Literal["anthropic", "openai", "azure_openai"] = "anthropic"
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_API_KEY: str | None = None

    # Azure AD設定
    AUTH_MODE: Literal["development", "production"] = "development"
    AZURE_TENANT_ID: str | None = None
    AZURE_CLIENT_ID: str | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_cors_settings()
        self._validate_security_settings()
        self._validate_llm_config()
        self._validate_azure_ad_config()

settings = Settings()
```

### 8.3 環境別バリデーション

**本番環境での必須チェック**:

- ✅ SECRET_KEYが設定されているか（32文字以上）
- ✅ ALLOWED_ORIGINSが明示的に設定されているか
- ✅ LLM_PROVIDERに対応するAPIキーが設定されているか
- ✅ AUTH_MODE=productionの場合、Azure AD設定が存在するか

**開発環境での警告**:

- ⚠️ デフォルトSECRET_KEY使用時は警告ログを出力

---

## 9. ライフサイクル管理

### 9.1 lifespan コンテキストマネージャー

アプリケーションの起動・終了処理は`core/lifespan.py`で管理されます。

**実装（`core/lifespan.py`）**:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル（起動・終了）を管理します。"""

    # 起動時処理
    logger.info("アプリケーション起動", app_name=settings.APP_NAME, version=settings.VERSION)
    logger.info("環境情報", environment=settings.ENVIRONMENT)

    # データベーステーブルを確認・作成
    await init_db()
    logger.info("データベーステーブルの確認が完了しました")

    # Redisキャッシュを初期化
    if settings.REDIS_URL:
        await cache_manager.connect()
        logger.info("Redisキャッシュに接続しました")

    # Azure AD認証の初期化（本番モードのみ）
    if settings.AUTH_MODE == "production":
        try:
            from app.core.security.azure_ad import initialize_azure_scheme
            await initialize_azure_scheme()
            logger.info("Azure AD認証スキームを初期化しました")
        except Exception as e:
            logger.error("Azure AD初期化エラー", error=str(e))

    yield

    # 終了時処理
    logger.info("シャットダウン中...")

    # Redis接続を切断
    if settings.REDIS_URL:
        await cache_manager.disconnect()
        logger.info("Redisキャッシュから切断しました")

    # データベース接続をクローズ
    await close_db()
    logger.info("データベース接続をクローズしました")
```

### 9.2 起動時処理

1. **ログ出力**: アプリ名、バージョン、環境を記録
2. **データベース初期化**: `init_db()`でテーブル確認（開発環境のみ作成）
3. **Redis接続**: `REDIS_URL`が設定されていれば接続
4. **Azure AD初期化**: 本番モードの場合、トークン検証スキームを初期化

### 9.3 終了時処理

1. **Redis切断**: gracefulに接続を切断
2. **データベースクローズ**: すべてのコネクションプールを解放

---

## 10. デザインパターン

### 10.1 Facadeパターン

**適用場所**: プロジェクトメンバー管理（`services/project_member/member_facade.py`）

**目的**: 複雑なサブシステム（メンバー追加・更新・削除・権限チェック）を単一のインターフェースで統一

**実装**:

```python
class ProjectMemberFacade:
    """プロジェクトメンバー管理のFacadeクラス。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_checker = ProjectMemberAuthorizationChecker(db)
        self.adder = ProjectMemberAdder(db)
        self.updater = ProjectMemberUpdater(db)
        self.remover = ProjectMemberRemover(db)

    async def add_member(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        role: ProjectRole,
        requester_id: uuid.UUID,
    ) -> ProjectMember:
        """プロジェクトメンバーを追加します（権限チェック付き）。"""
        # 権限チェック → 実行 → commit を一括で管理
        return await self.adder.add_member(project_id, user_id, role, requester_id)

    async def update_member_role(
        self,
        project_id: uuid.UUID,
        member_id: uuid.UUID,
        new_role: ProjectRole,
        requester_id: uuid.UUID,
    ) -> ProjectMember:
        """メンバーのロールを更新します（権限チェック付き）。"""
        return await self.updater.update_member_role(project_id, member_id, new_role, requester_id)

    async def remove_member(
        self,
        project_id: uuid.UUID,
        member_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> None:
        """メンバーを削除します（権限チェック付き）。"""
        await self.remover.remove_member(project_id, member_id, requester_id)
```

**利点**:

- ✅ 複雑な操作を単純なメソッド呼び出しに隠蔽
- ✅ 各専門サービス（Adder, Updater, Remover）の調整
- ✅ APIレイヤーからの呼び出しが簡潔

### 10.2 Repositoryパターン

**適用場所**: すべてのデータアクセス（`repositories/base.py`）

**目的**: データアクセスロジックをカプセル化し、ビジネスロジックから分離

**実装**: 前述の「5.4 Repository Layer」を参照

**利点**:

- ✅ テスタビリティ向上（モックに差し替え可能）
- ✅ データソース変更時の影響を局所化
- ✅ CRUD操作の一元化（DRY原則）

### 10.3 Dependency Injection（DI）パターン

**適用場所**: FastAPIのDependsシステム

**目的**: 依存関係を外部から注入し、テスタビリティと保守性を向上

**実装**: 前述の「6. 依存性注入（DI）」を参照

**利点**:

- ✅ テスタビリティ向上
- ✅ 疎結合
- ✅ 明示的な依存関係

### 10.4 Strategyパターン

**適用場所**: ストレージバックエンド（`services/storage.py`）

**目的**: ストレージ実装（Local / Azure Blob）を切り替え可能にする

**実装**:

```python
class StorageService:
    def __init__(self):
        if settings.STORAGE_BACKEND == "azure":
            self.backend = AzureBlobStorage()
        else:
            self.backend = LocalFileStorage()

    async def upload(self, file: UploadFile, path: str) -> str:
        return await self.backend.upload(file, path)

    async def download(self, path: str) -> bytes:
        return await self.backend.download(path)
```

**利点**:

- ✅ 実行時にストレージバックエンドを切り替え
- ✅ 新しいストレージ追加が容易（Open/Closed原則）

---

## 11. パフォーマンス最適化

### 11.1 データベース接続プール

**設定（`core/database.py`）**:

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

**最適化ポイント**:

- ✅ `pool_pre_ping=True`: 切断された接続を自動検出・再接続
- ✅ `pool_recycle=1800`: 長時間接続を定期的にリサイクル
- ✅ `pool_size + max_overflow`: 通常5接続、ピーク時15接続

### 11.2 N+1クエリ対策

**問題**: リレーションシップの遅延ロード（Lazy Loading）によるN+1クエリ

**解決策**: `selectinload`によるEager Loading

**実装（`repositories/base.py`）**:

```python
async def get_multi(
    self,
    skip: int = 0,
    limit: int = 100,
    load_relations: list[str] | None = None,
    **filters: Any,
) -> list[ModelType]:
    """N+1クエリ対策付きで複数レコードを取得します。"""
    from sqlalchemy.orm import selectinload

    query = select(self.model)

    # Eager loading（N+1クエリ対策）
    if load_relations:
        for relation in load_relations:
            if hasattr(self.model, relation):
                query = query.options(selectinload(getattr(self.model, relation)))

    # フィルタ、ソート、ページネーション適用
    # ...（省略）
```

**使用例**:

```python
# ❌ N+1クエリが発生（悪い例）
users = await user_repo.get_multi(limit=10)
for user in users:
    print(user.projects)  # 各ユーザーごとにクエリ発行（10回 + 1回 = 11クエリ）

# ✅ Eager Loadingで1クエリ（良い例）
users = await user_repo.get_multi(limit=10, load_relations=["projects"])
for user in users:
    print(user.projects)  # すでにロード済み（1クエリのみ）
```

### 11.3 Redisキャッシュ

**実装（`core/cache.py`）**:

```python
class CacheManager:
    def __init__(self):
        self.redis: Redis | None = None

    async def connect(self):
        self.redis = await Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def get(self, key: str) -> Any:
        if not self.redis:
            return None
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = settings.CACHE_TTL):
        if self.redis:
            await self.redis.set(key, json.dumps(value), ex=ttl)
```

**キャッシュ戦略**:

- ✅ プロジェクトメンバーロール（TTL: 5分）
- ✅ ユーザープロファイル（TTL: 5分）
- ✅ 分析テンプレート一覧（TTL: 10分）

### 11.4 非同期I/O

**FastAPI + SQLAlchemy 2.0 + asyncpg**:

- ✅ すべてのI/O操作が非同期（`async/await`）
- ✅ 同時リクエスト処理能力の向上
- ✅ データベース、ファイルI/O、外部API呼び出しがノンブロッキング

**実装例**:

```python
async def get_user_with_projects(user_id: uuid.UUID) -> User:
    """非同期でユーザーとプロジェクトを並行取得します。"""
    async with get_db() as db:
        user_repo = UserRepository(db)
        project_repo = ProjectRepository(db)

        # 並行実行（asyncio.gather）
        user, projects = await asyncio.gather(
            user_repo.get(user_id),
            project_repo.get_by_user(user_id),
        )

        return user
```

---

## 12. 付録

### 12.1 関連ファイル一覧

#### コアファイル

| ファイル | 説明 |
|---------|------|
| `src/app/main.py` | アプリケーションエントリーポイント |
| `src/app/core/app_factory.py` | アプリケーションファクトリ（create_app関数） |
| `src/app/core/config.py` | 設定管理（Pydantic Settings） |
| `src/app/core/database.py` | データベース接続・セッション管理 |
| `src/app/core/lifespan.py` | ライフサイクル管理（起動・終了処理） |
| `src/app/core/logging.py` | ログ設定（structlog） |
| `src/app/core/cache.py` | Redisキャッシュ管理 |
| `src/app/core/exceptions.py` | カスタム例外定義 |
| `src/app/core/security/` | セキュリティ機能（認証・認可） |

#### レイヤーファイル

| レイヤー | ディレクトリ | 説明 |
|---------|-------------|------|
| API Layer | `src/app/api/routes/` | エンドポイント定義 |
| | `src/app/api/core/` | DI定義、例外ハンドラー |
| | `src/app/api/middlewares/` | ミドルウェア |
| Service Layer | `src/app/services/` | ビジネスロジック |
| Repository Layer | `src/app/repositories/` | データアクセスロジック |
| Data Layer | `src/app/models/` | SQLAlchemyモデル |

#### 設定ファイル

| ファイル | 説明 |
|---------|------|
| `pyproject.toml` | プロジェクト設定・依存関係 |
| `uv.lock` | 依存関係ロックファイル |
| `.env.local.example` | 開発環境設定テンプレート |
| `src/alembic.ini` | Alembic設定ファイル |

### 12.2 参考リンク

#### 公式ドキュメント

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

#### 設計パターン

- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Facade Pattern](https://refactoring.guru/design-patterns/facade)
- [Dependency Injection](https://martinfowler.com/articles/injection.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

### 12.3 用語集

| 用語 | 説明 |
|------|------|
| **ASGI** | Asynchronous Server Gateway Interface（非同期Webサーバーインターフェース） |
| **ORM** | Object-Relational Mapping（オブジェクト関係マッピング） |
| **DI** | Dependency Injection（依存性注入） |
| **CRUD** | Create, Read, Update, Delete（基本データ操作） |
| **RBAC** | Role-Based Access Control（ロールベースアクセス制御） |
| **UUID** | Universally Unique Identifier（汎用一意識別子） |
| **JSONB** | PostgreSQLのバイナリJSON型 |
| **N+1クエリ** | リレーションシップの遅延ロードによる複数クエリ発行問題 |
| **Eager Loading** | リレーションシップの事前ロード（N+1対策） |
| **Middleware** | リクエスト/レスポンス処理の中間層 |

### 12.4 クロスリファレンス

本設計書に関連する他の設計書：

| 設計書 | リンク | 関連箇所 |
|-------|--------|---------|
| **Database設計書** | [01-database-design.md](../02-database/01-database-design.md) | データモデル、リレーションシップ、インデックス |
| **RBAC設計書** | [01-rbac-design.md](../03-security/01-rbac-design.md) | 認証・認可、ロール定義、権限チェック |
| **API設計書** | [01-api-design.md](../04-api/01-api-design.md) | エンドポイント仕様、リクエスト/レスポンス |

### 12.5 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-01-11 | 初版作成 | Claude Code |

---

**最終更新**: 2025-01-11
**管理者**: Claude Code
**レビュー状態**: 初版
