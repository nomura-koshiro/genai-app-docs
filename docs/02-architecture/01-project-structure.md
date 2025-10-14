# プロジェクト構造

このドキュメントでは、AI Agent Appのディレクトリ構造と各ファイルの役割について説明します。

## 全体構造

```
backend/
├── .venv/                   # 仮想環境（uvが自動生成）
├── docs/                    # ドキュメント
│   ├── 01-getting-started/ # 入門ガイド
│   ├── 02-architecture/    # アーキテクチャ説明
│   ├── 03-core-concepts/   # コアコンセプト
│   ├── 04-development/     # 開発ガイド
│   ├── 05-testing/         # テスト戦略
│   ├── 06-guides/          # 実装ガイド
│   ├── 07-reference/       # リファレンス
│   └── README.md           # ドキュメントインデックス
├── src/                     # アプリケーションソースコード
│   ├── alembic/            # データベースマイグレーション
│   │   ├── versions/       # マイグレーションファイル
│   │   └── env.py          # Alembic環境設定
│   └── app/                # メインアプリケーション
│       ├── agents/         # AI Agent関連
│       ├── api/            # API層（ルーターとミドルウェア）
│       ├── core/           # コア機能（例外、ロギング、セキュリティ、キャッシュ）
│       ├── models/         # データベースモデル
│       ├── repositories/   # データアクセス層
│       ├── schemas/        # Pydanticスキーマ
│       ├── services/       # ビジネスロジック層
│       ├── storage/        # ファイルストレージ
│       ├── config.py       # アプリケーション設定
│       ├── database.py     # データベース設定
│       └── main.py         # アプリケーションエントリーポイント
├── tests/                   # テストコード
│   ├── __init__.py
│   ├── conftest.py         # 共通フィクスチャとテスト設定
│   ├── test_models.py      # モデル層テスト
│   ├── test_repositories.py # リポジトリ層テスト
│   ├── test_services.py    # サービス層テスト
│   └── test_api.py         # APIエンドポイントテスト
├── uploads/                 # ローカルファイルストレージ（開発環境）
├── .env                     # 環境変数（gitignore）
├── .env.example             # 環境変数テンプレート
├── .gitignore               # Git無視ファイル
├── .python-version          # Pythonバージョン指定
├── alembic.ini              # Alembic設定ファイル
├── pyproject.toml           # プロジェクト設定と依存関係
├── README.md                # プロジェクト概要
└── uv.lock                  # 依存関係ロックファイル
```

## src/app/ ディレクトリ詳細

### ルートファイル

#### `main.py` - アプリケーションエントリーポイント

FastAPIアプリケーションの起動とミドルウェアの設定を行います。

```python
# 主な内容
from fastapi import FastAPI
from app.api.routes import agents, files

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# ミドルウェアの設定
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)

# ルーターの登録
app.include_router(agents.router, prefix="/api/agents")
app.include_router(files.router, prefix="/api/files")
```

**役割**:
- FastAPIアプリケーションの初期化
- CORS設定
- ミドルウェアの登録
- ルーターの統合
- ライフサイクルイベント（起動・シャットダウン）

#### `config.py` - アプリケーション設定

Pydantic Settingsを使用した設定管理。

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Agent App"
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

```
api/
├── routes/                  # APIエンドポイント
│   ├── __init__.py
│   ├── agents.py           # AI Agent関連エンドポイント
│   └── files.py            # ファイル管理エンドポイント
├── middlewares/             # カスタムミドルウェア
│   ├── __init__.py
│   ├── error_handler.py    # エラーハンドリング
│   ├── logging.py          # リクエストロギング
│   ├── metrics.py          # Prometheusメトリクス収集
│   └── rate_limit.py       # レート制限
├── dependencies.py          # 依存性注入の定義
└── __init__.py
```

#### `api/routes/agents.py` - AI Agentエンドポイント

```python
from fastapi import APIRouter, Depends
from app.api.dependencies import SessionServiceDep

router = APIRouter()

@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: SessionServiceDep,
):
    """AI Agentとチャット"""
    return await service.process_message(request)
```

#### `api/routes/files.py` - ファイル管理エンドポイント

```python
from fastapi import APIRouter, UploadFile
from app.api.dependencies import FileServiceDep

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile,
    service: FileServiceDep,
):
    """ファイルをアップロード"""
    return await service.upload(file)
```

#### `api/dependencies.py` - 依存性注入

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]

def get_user_service(db: DatabaseDep) -> UserService:
    return UserService(db)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
```

### models/ - データベースモデル

SQLAlchemyのORMモデルを定義します。

```
models/
├── __init__.py
├── user.py                  # ユーザーモデル
├── session.py               # セッションモデル
├── file.py                  # ファイルモデル
└── message.py               # メッセージモデル
```

#### 例: `models/user.py`

```python
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # リレーションシップ
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    files: Mapped[list["File"]] = relationship(back_populates="user")
```

### schemas/ - Pydanticスキーマ

APIリクエスト/レスポンスのバリデーションスキーマ。

```
schemas/
├── __init__.py
├── user.py                  # ユーザースキーマ
├── agent.py                 # Agent関連スキーマ
├── file.py                  # ファイルスキーマ
└── common.py                # 共通スキーマ
```

#### 例: `schemas/user.py`

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool

    model_config = {"from_attributes": True}
```

### repositories/ - データアクセス層

データベース操作を抽象化します。

```
repositories/
├── __init__.py
├── base.py                  # ベースリポジトリ（共通CRUD）
├── user.py                  # ユーザーリポジトリ
├── session.py               # セッションリポジトリ
└── file.py                  # ファイルリポジトリ
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

#### `repositories/user.py` - ユーザーリポジトリ

```python
from app.repositories.base import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

### services/ - ビジネスロジック層

ビジネスルールと複雑なロジックを実装します。

```
services/
├── __init__.py
├── user.py                  # ユーザーサービス
├── session.py               # セッションサービス
└── file.py                  # ファイルサービス
```

#### 例: `services/user.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.core.security import hash_password

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, user_data: UserCreate) -> User:
        # バリデーション
        existing = await self.repository.get_by_email(user_data.email)
        if existing:
            raise ValidationError("User already exists")

        # パスワードのハッシュ化
        hashed_password = hash_password(user_data.password)

        # ユーザー作成
        return await self.repository.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
```

### core/ - コア機能

アプリケーション全体で使用される共通機能。

```
core/
├── __init__.py
├── cache.py                 # Redisキャッシュマネージャー
├── exceptions.py            # カスタム例外
├── logging.py               # ロギング設定（構造化ログ対応）
└── security.py              # セキュリティ機能
```

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

#### `core/security.py`

```python
from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    return jwt.encode(data, settings.SECRET_KEY)
```

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

### agents/ - AI Agent機能

LangGraphベースのAI Agent実装。

```
agents/
├── __init__.py
├── graph.py                 # LangGraphの定義
└── tools.py                 # カスタムツール
```

### storage/ - ファイルストレージ

ファイルストレージの抽象化レイヤー。

```
storage/
├── __init__.py
├── base.py                  # ストレージインターフェース
├── local.py                 # ローカルストレージ
└── azure_blob.py            # Azure Blobストレージ
```

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
