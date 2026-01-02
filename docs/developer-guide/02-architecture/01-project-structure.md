# プロジェクト構造

このドキュメントでは、camp-backendのディレクトリ構造と各ファイルの役割について説明します。

## システム構成図

以下の図は、camp-backendの全体的なシステム構成を示しています。

::: mermaid
graph TB
    subgraph "クライアント"
        Client[ブラウザ/アプリ]
    end

    subgraph "バックエンドAPI FastAPI"
        API[API層<br/>routes/]
        MW[ミドルウェア<br/>CORS, エラーハンドリング<br/>ロギング, メトリクス]
        Service[サービス層<br/>services/]
        Repo[リポジトリ層<br/>repositories/]
    end

    subgraph "データベース"
        DB[(PostgreSQL<br/>camp_backend_db)]
    end

    subgraph "外部サービス"
        Anthropic[Anthropic API<br/>Claude]
        OpenAI[OpenAI API<br/>GPT-4]
        Azure[Azure Blob Storage<br/>ファイル保存]
    end

    subgraph "ローカルストレージ"
        Local[uploads/<br/>開発環境]
    end

    Client -->|HTTP/HTTPS| MW
    MW --> API
    API --> Service
    Service --> Repo

    Repo -->|SQLAlchemy<br/>asyncpg| DB

    style Client fill:#81d4fa,stroke:#01579b,stroke-width:3px,color:#000
    style API fill:#ffb74d,stroke:#e65100,stroke-width:3px,color:#000
    style Service fill:#ce93d8,stroke:#4a148c,stroke-width:3px,color:#000
    style Repo fill:#81c784,stroke:#1b5e20,stroke-width:3px,color:#000
    style DB fill:#64b5f6,stroke:#01579b,stroke-width:3px,color:#000
:::

**主要コンポーネント**:

1. **クライアント**: ブラウザまたはモバイルアプリからHTTP/HTTPSでアクセス
2. **バックエンドAPI**: FastAPIによる非同期REST API

   - ミドルウェア: CORS、エラーハンドリング、ロギング、メトリクス収集
   - レイヤードアーキテクチャ: API → Service → Repository → Model

3. **データベース**:

   - PostgreSQL: メインデータベース（camp_backend_db）とテストDB（camp_backend_db_test）

## 全体構造

```text
camp_backend/
├── .venv/                   # 仮想環境（uvが自動生成）
├── docs/                    # ドキュメント
│   ├── developer-guide/    # 開発者ガイド
│   │   ├── 01-getting-started/ # 入門ガイド
│   │   ├── 02-architecture/    # アーキテクチャ説明
│   │   ├── 03-core-concepts/   # コアコンセプト
│   │   ├── 04-development/     # 開発ガイド
│   │   ├── 05-testing/         # テスト戦略
│   │   ├── 06-guides/          # 実装ガイド
│   │   └── 07-reference/       # リファレンス
│   ├── specifications/     # 設計仕様書
│   └── README.md           # ドキュメントインデックス
├── src/                     # アプリケーションソースコード
│   ├── alembic/            # データベースマイグレーション
│   │   ├── versions/       # マイグレーションファイル
│   │   └── env.py          # Alembic環境設定
│   ├── alembic.ini         # Alembic設定ファイル
│   └── app/                # メインアプリケーション
│       ├── main.py         # アプリケーションエントリーポイント
│       ├── api/            # API層（ルーター、エンドポイント、ミドルウェア）
│       │   ├── core/       # APIコア機能
│       │   │   ├── dependencies/ # 依存性注入（機能別に分割）
│       │   │   └── exception_handlers.py
│       │   ├── middlewares/# ミドルウェア（CSRF, レート制限, 監査ログ等）
│       │   └── routes/     # エンドポイント定義
│       │       ├── system/ # システムエンドポイント
│       │       └── v1/     # API v1エンドポイント（機能別サブディレクトリ）
│       ├── core/           # コア機能（設定、DB、例外、ロギング、セキュリティ、キャッシュ）
│       │   ├── app_factory.py  # アプリケーションファクトリ
│       │   ├── cache.py        # キャッシュ管理
│       │   ├── config.py       # アプリケーション設定
│       │   ├── database.py     # データベース設定
│       │   ├── decorators/     # デコレータ（横断的関心事）
│       │   ├── exceptions.py   # 例外定義
│       │   ├── lifespan.py     # ライフサイクル管理
│       │   ├── logging.py      # ログ設定
│       │   └── security/       # セキュリティ機能
│       ├── data/           # データファイル・テンプレート
│       │   └── analysis/   # 分析機能用データ
│       ├── models/         # データベースモデル（機能別サブディレクトリ）
│       │   ├── analysis/       # 個別施策分析モデル
│       │   ├── driver_tree/    # ドライバーツリーモデル
│       │   ├── project/        # プロジェクト管理モデル
│       │   └── user_account/   # ユーザーアカウントモデル（Azure AD対応）
│       ├── repositories/   # データアクセス層（機能別サブディレクトリ）
│       │   ├── analysis/       # 個別施策分析リポジトリ
│       │   ├── driver_tree/    # ドライバーツリーリポジトリ
│       │   ├── project/        # プロジェクト管理リポジトリ
│       │   └── user_account/   # ユーザーアカウントリポジトリ（Azure AD対応）
│       ├── schemas/        # Pydanticスキーマ（機能別サブディレクトリ）
│       │   ├── analysis/       # 個別施策分析スキーマ
│       │   ├── driver_tree/    # ドライバーツリースキーマ
│       │   ├── project/        # プロジェクト管理スキーマ
│       │   └── user_account/   # ユーザーアカウントスキーマ（Azure AD対応）
│       ├── services/       # ビジネスロジック層（機能別サブディレクトリ）
│       │   ├── analysis/       # 個別施策分析サービス
│       │   ├── driver_tree/    # ドライバーツリーサービス
│       │   ├── project/        # プロジェクト管理サービス
│       │   ├── storage.py      # 汎用ストレージサービス
│       │   └── user_account/   # ユーザーアカウントサービス（Azure AD対応）
│       └── utils/          # ユーティリティ関数
├── tests/                   # テストコード（src/app/のミラー構造）
│   ├── __init__.py
│   ├── conftest.py         # 共通フィクスチャとテスト設定
│   ├── api/                # APIレイヤーのテスト
│   │   ├── middlewares/    # ミドルウェアテスト
│   │   └── routes/         # エンドポイントテスト
│   ├── core/               # コア機能のテスト
│   │   └── security/       # セキュリティ関連テスト
│   ├── models/             # モデル層テスト
│   ├── repositories/       # リポジトリ層テスト
│   └── services/           # サービス層テスト
├── scripts/                 # ユーティリティスクリプト
├── uploads/                 # ローカルファイルストレージ（開発環境）
├── .env.local.example       # ローカル環境変数テンプレート
├── .env.staging.example     # ステージング環境変数テンプレート
├── .env.production.example  # 本番環境変数テンプレート
├── .gitignore               # Git無視ファイル
├── .python-version          # Pythonバージョン指定（3.13）
├── pyproject.toml           # プロジェクト設定と依存関係
├── README.md                # プロジェクト概要
└── uv.lock                  # 依存関係ロックファイル
```

## src/app/ ディレクトリ詳細

### ルートファイル

#### `main.py` - アプリケーションエントリーポイント

アプリケーションの起動とロギング設定を行う軽量なエントリーポイント（86行）。
FastAPIアプリの初期化は `core/app_factory.py` に委譲。

```python
# 主な内容
from app.core.config import settings
from app.core.app_factory import create_app
from app.core.logging import setup_logging

# Setup logging
setup_logging()

# Create FastAPI application instance
app = create_app()

def main():
    """CLI起動用エントリーポイント"""
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

if __name__ == "__main__":
    main()
```

**役割**:

- ロギングシステムの初期化
- FastAPIアプリケーションインスタンスの生成（create_appファクトリー経由）
- CLI起動用のmain関数提供
- **注**: アプリの詳細な設定は `core/app_factory.py` で行われる

**注**: `config.py`と`database.py`は`core/`ディレクトリ内にあります。

- `core/config.py` - アプリケーション設定（Pydantic Settings）
- `core/database.py` - データベース接続とセッション管理

```python
# core/config.py の例
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "camp-backend"
    DATABASE_URL: str
    SECRET_KEY: str
    # ... その他の設定

settings = Settings()
```

**役割**:

- 環境変数の読み込み
- 設定値のバリデーション
- 型安全な設定アクセス

#### `database.py` - データベース設定

SQLAlchemyの非同期エンジンとセッション管理。

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

**役割**:

- データベース接続管理
- セッションファクトリー
- 依存性注入用のget_db関数

### api/ - API層

API層は、HTTPリクエストを受け取り、レスポンスを返す責務を持ちます。

```text
api/
├── core/                    # APIコア機能
│   ├── __init__.py
│   ├── dependencies/        # 依存性注入の定義（機能別に分割）
│   │   ├── __init__.py      # 統合エクスポート
│   │   ├── analysis.py      # 個別施策分析関連の依存性
│   │   ├── auth.py          # 認証関連の依存性
│   │   ├── database.py      # データベース関連の依存性
│   │   ├── driver_tree.py   # ドライバーツリー関連の依存性
│   │   ├── project.py       # プロジェクト関連の依存性
│   │   └── user_account.py  # ユーザーアカウント関連の依存性
│   └── exception_handlers.py # グローバル例外ハンドラー
├── routes/                  # エンドポイント定義
│   ├── v1/                  # API v1 エンドポイント（ビジネスロジック）
│   │   ├── __init__.py
│   │   ├── analysis/        # 個別施策分析エンドポイント
│   │   │   ├── __init__.py
│   │   │   ├── analysis_sessions.py  # 分析セッション管理
│   │   │   └── analysis_templates.py # テンプレート管理
│   │   ├── driver_tree/     # ドライバーツリーエンドポイント
│   │   │   ├── __init__.py
│   │   │   ├── driver_tree_files.py  # ファイル管理
│   │   │   ├── driver_tree_nodes.py  # ノード管理
│   │   │   └── driver_tree_trees.py  # ツリー管理
│   │   ├── project/         # プロジェクト管理エンドポイント
│   │   │   ├── __init__.py
│   │   │   ├── projects.py       # プロジェクト管理
│   │   │   ├── project_members.py # メンバー管理
│   │   │   └── project_files.py  # ファイル管理
│   │   └── user_accounts/   # ユーザーアカウントエンドポイント
│   │       ├── __init__.py
│   │       └── user_accounts.py # Azure AD対応ユーザー管理
│   └── system/              # システムエンドポイント（インフラ）
│       ├── __init__.py
│       ├── root.py          # / (ルート)
│       ├── health.py        # /health (ヘルスチェック)
│       └── metrics.py       # /metrics (Prometheusメトリクス)
├── decorators/              # デコレーター（横断的関心事）
│   ├── __init__.py
│   ├── basic.py             # 基本デコレータ
│   ├── security.py          # セキュリティデコレータ
│   ├── data_access.py       # データアクセスデコレータ
│   └── reliability.py       # 信頼性デコレータ
├── middlewares/             # カスタムミドルウェア
│   ├── __init__.py
│   ├── logging.py          # リクエストロギング
│   ├── metrics.py          # Prometheusメトリクス収集
│   ├── rate_limit.py       # レート制限
│   └── security_headers.py # セキュリティヘッダー
└── __init__.py
```

#### `api/core/` - APIコア機能

APIレイヤーの基盤となる依存性注入と例外ハンドリング機能を提供します。

**`dependencies/`** - 依存性注入の定義（機能別に分割）:

- `__init__.py` - 統合エクスポート（全ての依存性を一括インポート可能）
- `analysis.py` - 個別施策分析関連の依存性（`AnalysisSessionServiceDep` など）
- `auth.py` - 認証関連の依存性（`CurrentUserAccountDep` など）
- `database.py` - データベース関連の依存性（`DatabaseDep`）
- `driver_tree.py` - ドライバーツリー関連の依存性（`DriverTreeFileServiceDep` など）
- `project.py` - プロジェクト関連の依存性（`ProjectServiceDep`, `ProjectFileServiceDep`, `ProjectMemberServiceDep`）
- `user_account.py` - ユーザーアカウント関連の依存性（`UserAccountServiceDep`）

**`exception_handlers.py`** - グローバル例外ハンドラー:

- カスタム例外を適切なHTTPレスポンスに変換
- 統一的なエラーレスポンス形式を提供

#### `core/decorators/` - デコレータ（横断的関心事）

> **Note**: デコレータはAPI層に依存しないため、`core/`レイヤーに配置されています。

関数やメソッドに追加機能を付与するデコレータを提供します。機能別に4つのモジュールに分割されています。

**`basic.py`** - 基本機能デコレータ:

- `@log_execution`: 関数の実行をログに記録
- `@measure_performance`: 実行時間を測定
- `@async_timeout`: タイムアウト制御

**`error_handling.py`** - エラーハンドリングデコレータ:

- `@handle_service_errors`: サービス層のエラーをHTTP例外に変換

**`data_access.py`** - データアクセスデコレータ:

- `@transactional`: データベーストランザクション管理
- `@cache_result`: 関数の結果をRedisにキャッシュ

**`reliability.py`** - 信頼性向上デコレータ:

- `@retry_on_error`: エラー時の自動リトライ（Exponential Backoff）

**インポート方法**:

```python
# 旧: from app.api.decorators import log_execution
# 新:
from app.core.decorators import log_execution, retry_on_error, transactional
```

#### `api/routes/v1/sample_agents.py` - AI Agentエンドポイント（API v1）

```python
from fastapi import APIRouter

from app.api.core import AgentServiceDep, CurrentUserDep

router = APIRouter()

@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: AgentServiceDep,
    current_user: CurrentUserDep,
):
    """AI Agentとチャット"""
    return await service.process_message(request)
```

#### `api/routes/v1/sample_files.py` - ファイル管理エンドポイント（API v1）

```python
from fastapi import APIRouter, UploadFile

from app.api.core import CurrentUserDep, FileServiceDep

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile,
    service: FileServiceDep,
    current_user: CurrentUserDep,
):
    """ファイルをアップロード"""
    return await service.upload(file)
```

#### `api/routes/system/` - システムエンドポイント（インフラ）

APIバージョンに依存しないインフラストラクチャ関連のエンドポイント。

```python
# root.py - ルートエンドポイント
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    """アプリケーション基本情報を返す"""
    return {"message": f"Welcome to {settings.APP_NAME}", "version": settings.VERSION}

# health.py - ヘルスチェック
@router.get("/health")
async def health():
    """データベースとRedisの接続状態を確認"""
    return {"status": "healthy", "services": {"database": "healthy", "redis": "healthy"}}

# metrics.py - Prometheusメトリクス
@router.get("/metrics")
async def metrics():
    """Prometheusメトリクスを出力"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

#### `api/exception_handlers.py` - グローバル例外ハンドラー

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException

async def app_exception_handler(request: Request, exc: AppException):
    """カスタムアプリケーション例外のハンドラー"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )

def register_exception_handlers(app: FastAPI):
    """FastAPIアプリに例外ハンドラーを登録"""
    app.add_exception_handler(AppException, app_exception_handler)
```

#### `api/core/dependencies.py` - 依存性注入

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]

# JWT認証用（非推奨）
def get_sample_user_service(db: DatabaseDep) -> SampleUserService:
    return SampleUserService(db)

SampleUserServiceDep = Annotated[SampleUserService, Depends(get_sample_user_service)]

# Azure AD認証用（推奨）
def get_azure_user_service(db: DatabaseDep) -> UserService:
    return UserService(db)

AzureUserServiceDep = Annotated[UserService, Depends(get_azure_user_service)]

# 認証依存性
CurrentUserDep = Annotated[SampleUser, Depends(get_current_active_user)]  # JWT認証（非推奨）
CurrentUserAzureDep = Annotated[UserAccount, Depends(get_current_active_user_azure)]  # Azure AD認証（推奨）
```

### models/ - データベースモデル

SQLAlchemyのORMモデルを定義します。機能別にサブディレクトリ化されています。

```text
models/
├── __init__.py              # モデル統合エクスポート
├── base.py                  # ベースモデル
├── analysis/                # 個別施策分析モデル
│   ├── __init__.py
│   ├── analysis_chat.py             # 分析チャットモデル
│   ├── analysis_dummy_chart_master.py    # ダミーチャートマスタ
│   ├── analysis_dummy_formula_master.py  # ダミー数式マスタ
│   ├── analysis_file.py             # 分析ファイルモデル
│   ├── analysis_graph_axis_master.py     # グラフ軸マスタ
│   ├── analysis_issue_master.py     # 課題マスタ
│   ├── analysis_session.py          # 分析セッションモデル
│   ├── analysis_snapshot.py         # スナップショットモデル
│   ├── analysis_step.py             # 分析ステップモデル
│   └── analysis_validation_master.py # バリデーションマスタ
├── driver_tree/             # ドライバーツリーモデル
│   ├── __init__.py
│   ├── driver_tree.py               # ドライバーツリー
│   ├── driver_tree_data_frame.py    # データフレーム
│   ├── driver_tree_file.py          # ファイル
│   ├── driver_tree_formula.py       # 数式
│   ├── driver_tree_node.py          # ノード
│   ├── driver_tree_policy.py        # ポリシー
│   ├── driver_tree_relationship.py      # リレーションシップ
│   └── driver_tree_relationship_child.py # リレーションシップ子
├── project/                 # プロジェクト管理モデル
│   ├── __init__.py
│   ├── project.py           # プロジェクト
│   ├── project_file.py      # プロジェクトファイル
│   └── project_member.py    # プロジェクトメンバー
└── user_account/            # ユーザーアカウントモデル（Azure AD対応）
    ├── __init__.py
    └── user_account.py      # Azure AD対応ユーザーアカウントモデル
```

#### 例: `models/sample/sample_user.py`

```python
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class SampleUser(Base):
    __tablename__ = "sample_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # リレーションシップ
    sessions: Mapped[list["SampleSession"]] = relationship(back_populates="user")
    files: Mapped[list["SampleFile"]] = relationship(back_populates="user")
```

### schemas/ - Pydanticスキーマ

APIリクエスト/レスポンスのバリデーションスキーマ。機能別にサブディレクトリ化されています。

```text
schemas/
├── __init__.py              # スキーマ統合エクスポート
├── common.py                # 共通スキーマ
├── analysis/                # 個別施策分析スキーマ
│   ├── __init__.py
│   ├── analysis_file.py     # 分析ファイルスキーマ
│   ├── analysis_session.py  # 分析セッションスキーマ
│   └── analysis_template.py # テンプレートスキーマ
├── driver_tree/             # ドライバーツリースキーマ
│   ├── __init__.py
│   ├── node.py              # ノードスキーマ
│   └── tree.py              # ツリースキーマ
├── project/                 # プロジェクト管理スキーマ
│   ├── __init__.py
│   ├── project.py           # プロジェクトスキーマ
│   ├── project_file.py      # プロジェクトファイルスキーマ
│   └── project_member.py    # メンバースキーマ
└── user_account/            # ユーザーアカウントスキーマ（Azure AD対応）
    ├── __init__.py
    └── user_account.py      # Azure AD対応ユーザーアカウントスキーマ
```

**注**: Pydantic v2対応済み（`ConfigDict`使用）

#### 例: `schemas/sample/sample_user.py`

```python
from pydantic import BaseModel, EmailStr

class SampleUserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class SampleUserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool

    model_config = {"from_attributes": True}
```

### repositories/ - データアクセス層

データベース操作を抽象化します。機能別にサブディレクトリ化されています。

```text
repositories/
├── __init__.py              # リポジトリ統合エクスポート
├── base.py                  # ベースリポジトリ（共通CRUD）
├── analysis/                # 個別施策分析リポジトリ
│   ├── __init__.py
│   ├── analysis_file.py     # 分析ファイルリポジトリ
│   ├── analysis_session.py  # 分析セッションリポジトリ
│   ├── analysis_snapshot.py # スナップショットリポジトリ
│   ├── analysis_step.py     # 分析ステップリポジトリ
│   └── analysis_template.py # テンプレートリポジトリ
├── driver_tree/             # ドライバーツリーリポジトリ
│   ├── __init__.py
│   ├── driver_tree.py       # ドライバーツリーリポジトリ
│   ├── driver_tree_file.py  # ファイルリポジトリ
│   ├── driver_tree_formula.py # 数式リポジトリ
│   ├── driver_tree_node.py  # ノードリポジトリ
│   └── driver_tree_policy.py # ポリシーリポジトリ
├── project/                 # プロジェクト管理リポジトリ
│   ├── __init__.py
│   ├── project.py           # プロジェクトリポジトリ
│   ├── project_file.py      # プロジェクトファイルリポジトリ
│   └── project_member.py    # メンバーリポジトリ
└── user_account/            # ユーザーアカウントリポジトリ（Azure AD対応）
    ├── __init__.py
    └── user_account.py      # Azure AD対応ユーザーアカウントリポジトリ
```

#### `repositories/base.py` - ベースリポジトリ

```python
from typing import Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        return await self.db.get(self.model, id)

    async def get_multi(self, skip: int = 0, limit: int = 100):
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **obj_in) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
```

#### `repositories/sample/sample_user.py` - サンプルユーザーリポジトリ

```python
from app.repositories.base import BaseRepository
from app.models.sample.sample_user import SampleUser

class SampleUserRepository(BaseRepository[SampleUser]):
    def __init__(self, db: AsyncSession):
        super().__init__(SampleUser, db)

    async def get_by_email(self, email: str) -> SampleUser | None:
        query = select(SampleUser).where(SampleUser.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

### services/ - ビジネスロジック層

ビジネスルールと複雑なロジックを実装します。機能別にサブディレクトリ化され、Facadeパターンで実装されています。

```text
services/
├── __init__.py                      # サービス統合エクスポート
├── storage/                         # ストレージサービス（Strategyパターン）
│   ├── __init__.py                  # get_storage_service()
│   ├── base.py                      # StorageService（抽象基底クラス）
│   ├── local.py                     # LocalStorageService
│   ├── azure.py                     # AzureStorageService
│   ├── excel.py                     # Excel操作ユーティリティ
│   └── validation.py                # ファイル検証
├── analysis/                        # 個別施策分析サービス
│   ├── __init__.py                  # AnalysisSessionService, AnalysisTemplateService
│   ├── analysis_template.py         # テンプレートサービス
│   ├── analysis_session/            # 分析セッションサービス（機能別分割）
│   │   ├── __init__.py              # AnalysisSessionService（Facade）
│   │   ├── service.py               # メインサービス
│   │   ├── session_crud.py          # セッションCRUD
│   │   ├── file_operations.py       # ファイル操作
│   │   ├── analysis_operations.py   # 分析操作
│   │   ├── step_operations.py       # ステップ操作
│   │   └── excel_parser.py          # Excel解析
│   └── agent/                       # AIエージェント
│       ├── agent.py
│       ├── state.py
│       └── utils/
├── driver_tree/                     # ドライバーツリーサービス
│   ├── __init__.py                  # DriverTreeService, DriverTreeFileService, DriverTreeNodeService
│   ├── driver_tree/                 # ツリー管理（機能別分割）
│   │   ├── __init__.py              # DriverTreeService（Facade）
│   │   ├── base.py                  # 共通ヘルパー
│   │   ├── crud.py                  # DriverTreeCrudService
│   │   ├── master.py                # DriverTreeMasterService
│   │   └── calculation.py           # DriverTreeCalculationService
│   ├── driver_tree_file/            # ファイル管理（機能別分割）
│   │   ├── __init__.py              # DriverTreeFileService
│   │   ├── service.py               # メインサービス
│   │   ├── file_operations.py       # ファイル操作
│   │   ├── sheet_operations.py      # シート操作
│   │   ├── column_config.py         # カラム設定
│   │   └── excel_parser.py          # Excel解析
│   └── driver_tree_node/            # ノード管理（機能別分割）
│       ├── __init__.py              # DriverTreeNodeService（Facade）
│       ├── base.py                  # 共通ヘルパー
│       ├── crud.py                  # DriverTreeNodeCrudService
│       └── policy.py                # DriverTreeNodePolicyService
├── project/                         # プロジェクト管理サービス
│   ├── __init__.py                  # ProjectService, ProjectFileService
│   ├── project/                     # プロジェクト管理（機能別分割）
│   │   ├── __init__.py              # ProjectService（Facade）
│   │   ├── base.py                  # 共通ヘルパー
│   │   └── crud.py                  # ProjectCrudService
│   ├── project_file/                # ファイル管理（機能別分割）
│   │   ├── __init__.py              # ProjectFileService（Facade）
│   │   ├── base.py                  # 共通ヘルパー
│   │   ├── crud.py                  # ProjectFileCrudService
│   │   ├── upload.py                # ProjectFileUploadService
│   │   └── download.py              # ProjectFileDownloadService
│   └── project_member/              # メンバー管理（機能別分割）
│       ├── __init__.py              # ProjectMemberService（Facade）
│       ├── base.py                  # 共通ヘルパー
│       ├── crud.py                  # ProjectMemberCrudService
│       └── leave.py                 # ProjectMemberLeaveService
└── user_account/                    # ユーザーアカウントサービス
    ├── __init__.py                  # UserAccountService
    └── user_account/                # ユーザー管理（機能別分割）
        ├── __init__.py              # UserAccountService（Facade）
        ├── base.py                  # 共通ヘルパー
        ├── auth.py                  # UserAccountAuthService
        └── crud.py                  # UserAccountCrudService
```

**設計パターン**:

- **Facadeパターン**: 各サービスディレクトリの`__init__.py`でFacadeクラスを提供し、サブサービスに委譲
- **機能別分割**: crud.py, auth.py, upload.py など責務ごとにファイルを分離
- **Strategyパターン**: storageサービスで環境に応じた実装を切り替え

#### 例: `services/project/project/__init__.py`（Facadeパターン）

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.project.project.crud import ProjectCrudService

class ProjectService:
    """プロジェクト管理のビジネスロジックを提供するサービスクラス。

    各機能は専用のサービスクラスに委譲されます。
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._crud_service = ProjectCrudService(db)

    async def create_project(self, project_data: ProjectCreate, creator_id: uuid.UUID) -> Project:
        """新しいプロジェクトを作成します。"""
        return await self._crud_service.create_project(project_data, creator_id)

    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        """プロジェクトIDでプロジェクト情報を取得します。"""
        return await self._crud_service.get_project(project_id)
```

#### 例: `services/storage/__init__.py`（Strategyパターン）

```python
from app.core.config import settings
from .azure import AzureStorageService
from .base import StorageService
from .local import LocalStorageService

def get_storage_service() -> StorageService:
    """環境に応じたストレージサービスを取得します。"""
    storage_type = getattr(settings, "STORAGE_TYPE", "local")

    if storage_type == "azure":
        return AzureStorageService(settings.AZURE_STORAGE_CONNECTION_STRING)

    return LocalStorageService(settings.LOCAL_STORAGE_PATH)
```

### core/ - コア機能

アプリケーション全体で使用される共通機能。

```text
core/
├── __init__.py
├── app_factory.py           # FastAPIアプリ生成ファクトリー
├── lifespan.py              # アプリケーションライフサイクル管理
├── cache.py                 # Redisキャッシュマネージャー
├── config.py                # アプリケーション設定
├── database.py              # データベース設定
├── exceptions.py            # カスタム例外
├── logging.py               # ロギング設定（構造化ログ対応）
└── security/                # セキュリティ機能（パッケージ化）
    ├── __init__.py          # 統一インターフェース
    ├── password.py          # パスワードハッシュ化と検証
    ├── jwt.py               # JWT認証
    ├── api_key.py           # APIキー生成
    ├── azure_ad.py          # Azure AD認証（本番モード）
    └── dev_auth.py          # 開発モック認証
```

#### `core/app_factory.py` - アプリファクトリー

FastAPIアプリケーションインスタンスの生成と設定を一元管理。

```python
from fastapi import FastAPI
from app.core.lifespan import lifespan

def create_app() -> FastAPI:
    """FastAPIアプリケーションを生成します。

    Returns:
        FastAPI: 完全に設定されたFastAPIアプリケーション
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    # Exception handlers
    register_exception_handlers(app)

    # Middlewares
    app.add_middleware(PrometheusMetricsMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(CORSMiddleware, ...)

    # Routers
    # API v1 endpoints (versioned business logic)
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(files.router, prefix="/api/v1/files", tags=["files"])

    # System endpoints (infrastructure, no versioning)
    app.include_router(root.router, tags=["root"])
    app.include_router(health.router, tags=["health"])
    app.include_router(metrics.router, tags=["metrics"])

    return app
```

**役割**:

- FastAPIアプリケーションの初期化
- ミドルウェアの登録（実行順序管理）
- ルーターの統合（v1エンドポイントとsystemエンドポイントの分離）
- 例外ハンドラーの登録
- 設定の一元管理

**エンドポイント構成**:

- `/api/v1/*`: バージョン管理されたビジネスロジックAPI
- `/`, `/health`, `/metrics`: バージョン非依存のシステムエンドポイント

#### `core/lifespan.py` - ライフサイクル管理

アプリケーションの起動時・終了時の処理を管理。

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理。

    起動時:
        - データベース初期化
        - Redis接続
        - ログ出力

    終了時:
        - Redis切断
        - データベース接続クローズ
    """
    # Startup
    await init_db()
    if settings.REDIS_URL:
        await cache_manager.connect()

    yield

    # Shutdown
    if settings.REDIS_URL:
        await cache_manager.disconnect()
    await close_db()
```

**役割**:

- データベース接続の初期化とクローズ
- Redis接続の確立と切断
- gracefulシャットダウンの保証

#### `core/exceptions.py`

```python
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

class NotFoundError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)
```

#### `core/security/` - セキュリティパッケージ

セキュリティ機能を責任ごとに分割したパッケージ。認証モード（開発/本番）に応じて適切な認証方式を使用します。

```python
# core/security/__init__.py - 統一インターフェース
from app.core.security.password import hash_password, verify_password, validate_password_strength
from app.core.security.jwt import create_access_token, decode_access_token
from app.core.security.api_key import generate_api_key
from app.core.security.azure_ad import get_azure_ad_user, verify_azure_token
from app.core.security.dev_auth import get_dev_mock_user, create_dev_mock_token

# core/security/password.py - パスワード管理
def hash_password(password: str) -> str:
    """bcryptでパスワードをハッシュ化"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """パスワードを検証"""
    return pwd_context.verify(plain, hashed)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """パスワード強度をチェック"""
    # 8文字以上、大文字、小文字、数字を含むか検証
    ...

# core/security/jwt.py - JWT認証
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """JWTアクセストークンを生成"""
    return jwt.encode(data, settings.SECRET_KEY)

def decode_access_token(token: str) -> dict[str, Any] | None:
    """JWTトークンを検証・デコード"""
    return jwt.decode(token, settings.SECRET_KEY)

# core/security/api_key.py - APIキー生成
def generate_api_key() -> str:
    """暗号学的に安全なAPIキーを生成"""
    return secrets.token_urlsafe(32)

# core/security/azure_ad.py - Azure AD認証（本番モード）
async def verify_azure_token(token: str) -> dict[str, Any]:
    """Azure ADトークンを検証"""
    # Azure AD JWKSを使用してトークンを検証
    ...

async def get_azure_ad_user(token: str) -> dict[str, Any]:
    """Azure ADトークンからユーザー情報を取得"""
    # トークンからユーザー情報（email, oid, name）を抽出
    ...

# core/security/dev_auth.py - 開発モック認証
def create_dev_mock_token() -> str:
    """開発モック用トークンを生成"""
    return settings.DEV_MOCK_TOKEN

def get_dev_mock_user() -> dict[str, Any]:
    """開発モック用ユーザー情報を返す"""
    return {
        "email": settings.DEV_MOCK_USER_EMAIL,
        "oid": settings.DEV_MOCK_USER_OID,
        "name": settings.DEV_MOCK_USER_NAME,
    }
```

**役割**:

- `password.py`: bcryptによるパスワードハッシュ化、検証、強度チェック
- `jwt.py`: JWTトークンの生成、検証、リフレッシュトークン管理
- `api_key.py`: セキュアなAPIキー生成
- `azure_ad.py`: Azure AD認証（本番モード）- トークン検証、ユーザー情報取得
- `dev_auth.py`: 開発モック認証 - ローカル開発時の簡易認証

**認証モード切り替え**:

- `AUTH_MODE=development`: dev_auth.py による簡易認証（ローカル開発用）
- `AUTH_MODE=production`: azure_ad.py による Azure AD 認証（本番環境用）

### data/ - データファイル・テンプレート

アプリケーションで使用する静的データファイルやテンプレートを格納します。

```text
data/
└── analysis/                # 分析機能用データ
    └── (テンプレートファイルなど)
```

**役割**:

- 分析テンプレートの保存
- 静的データファイルの管理
- 初期シードデータの格納

### utils/ - ユーティリティ関数

アプリケーション全体で使用される汎用ユーティリティ関数を格納します。

```text
utils/
├── __init__.py
└── (各種ユーティリティファイル)
```

**役割**:

- 共通ヘルパー関数
- データ変換ユーティリティ
- 日付・時刻処理
- ファイル操作ヘルパー

#### `core/cache.py`

Redisを使用したキャッシュマネージャー。

```python
from redis.asyncio import Redis

class CacheManager:
    """Redisキャッシュマネージャー。"""

    async def connect(self) -> None:
        """Redis接続を確立."""

    async def get(self, key: str) -> Any | None:
        """キャッシュからデータを取得."""

    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        """データをキャッシュに保存."""

    async def delete(self, key: str) -> None:
        """キャッシュからデータを削除."""
```

**役割**:

- Redisへの接続管理
- JSON形式でのデータのシリアライズ/デシリアライズ
- TTLベースのキャッシュ管理
- パターンマッチングによる一括削除

## ファイル命名規則

### モジュール名

- 小文字のスネークケース: `user_service.py`
- 複数形は避ける（例外: `routes/`, `models/`）
- 明確で説明的な名前を使用

### クラス名

- パスカルケース: `UserService`, `BaseRepository`
- 役割を表す接尾辞: `Service`, `Repository`, `Model`

### 関数名

- 小文字のスネークケース: `get_user`, `create_token`
- 動詞で始める: `get_`, `create_`, `update_`, `delete_`

### 変数名

- 小文字のスネークケース: `user_id`, `session_data`
- 略語は避ける（例外: `db`, `id`）

### 定数名

- 大文字のスネークケース: `MAX_UPLOAD_SIZE`, `DEFAULT_LIMIT`

## 各レイヤーの責務

### API層（api/）

- HTTPリクエストの受け取り
- リクエストデータのバリデーション
- サービス層の呼び出し
- HTTPレスポンスの返却
- **禁止**: データベース直接アクセス、ビジネスロジック

### サービス層（services/）

- ビジネスロジックの実装
- トランザクション管理
- 複数リポジトリの調整
- ドメインルールの適用
- **禁止**: HTTPレスポンスの直接作成

### リポジトリ層（repositories/）

- データベースクエリ
- CRUD操作
- データアクセスの抽象化
- **禁止**: ビジネスロジック、他のリポジトリへの依存

### モデル層（models/）

- データベーステーブル定義
- リレーションシップ定義
- **禁止**: ビジネスロジック、外部依存

## 次のステップ

プロジェクト構造を理解したら、以下のドキュメントを参照してください：

- [レイヤードアーキテクチャ](./02-layered-architecture.md) - 各層の相互作用
- [依存性注入](./03-dependency-injection.md) - FastAPIのDIパターン
- [データベース設計](../03-core-concepts/02-database-design.md) - モデル定義の詳細
