# テックスタック

このドキュメントでは、AI Agent Appで使用している主要な技術スタックとライブラリについて説明します。

## 技術スタック概要

```
┌─────────────────────────────────────────────┐
│  Webフレームワーク: FastAPI                 │
├─────────────────────────────────────────────┤
│  ORM: SQLAlchemy 2.0 (非同期)                │
│  バリデーション: Pydantic 2.0                │
│  マイグレーション: Alembic                   │
├─────────────────────────────────────────────┤
│  キャッシュ: Redis                           │
│  モニタリング: Prometheus                    │
├─────────────────────────────────────────────┤
│  AI/Agent: LangChain + LangGraph             │
│  LLM: Anthropic Claude / OpenAI              │
├─────────────────────────────────────────────┤
│  パッケージ管理: uv                          │
│  コード品質: Ruff                            │
│  テスト: pytest + pytest-asyncio             │
└─────────────────────────────────────────────┘
```

## 1. FastAPI - Webフレームワーク

**バージョン**: 0.115.0+

FastAPIは、現代的で高速なPython Webフレームワークです。

### 主な特徴

- **高速**: NodeJS並みの高いパフォーマンス
- **自動ドキュメント生成**: Swagger UI / ReDoc
- **型ヒントベース**: Pydanticによる自動バリデーション
- **非同期サポート**: async/awaitのネイティブサポート
- **依存性注入**: 組み込みのDIシステム

### 基本的な使い方

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="AI Agent App",
    version="0.1.0",
    description="AI Agent application with file management",
)

class Item(BaseModel):
    name: str
    price: float

@app.get("/")
async def root():
    """ルートエンドポイント。"""
    return {"message": "Hello World"}

@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    """アイテムを作成する。"""
    return item

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    """アイテムを取得する。"""
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}
```

### ミドルウェア

```python
from fastapi.middleware.cors import CORSMiddleware

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# カスタムミドルウェア
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # リクエスト前の処理
        print(f"Request: {request.method} {request.url}")

        response = await call_next(request)

        # レスポンス後の処理
        print(f"Response: {response.status_code}")
        return response

app.add_middleware(CustomMiddleware)
```

### 公式ドキュメント

- https://fastapi.tiangolo.com/

## 2. SQLAlchemy - ORM

**バージョン**: 2.0.0+

SQLAlchemyは、Pythonで最も人気のあるORMライブラリです。
このプロジェクトでは非同期版（asyncio）を使用しています。

### 主な特徴

- **完全な非同期サポート**: async/await
- **型安全**: Python 3.10+の型ヒント対応
- **強力なクエリAPI**: 柔軟なクエリ構築
- **リレーションシップ**: 複雑な関連を簡単に定義

### モデル定義

```python
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    """ユーザーモデル。"""

    __tablename__ = "users"

    # 主キー
    id: Mapped[int] = mapped_column(primary_key=True)

    # カラム定義
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # リレーションシップ
    posts: Mapped[list["Post"]] = relationship(back_populates="user")

class Post(Base):
    """投稿モデル。"""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # リレーションシップ
    user: Mapped["User"] = relationship(back_populates="posts")
```

### 非同期クエリ

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_with_posts(db: AsyncSession, user_id: int):
    """ユーザーと投稿を取得する。"""
    # 基本的なクエリ
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # JOINクエリ
    query = (
        select(User)
        .join(User.posts)
        .where(User.id == user_id)
    )
    result = await db.execute(query)
    user = result.unique().scalar_one_or_none()

    return user

async def create_user(db: AsyncSession, email: str, username: str):
    """ユーザーを作成する。"""
    user = User(email=email, username=username)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
```

### 公式ドキュメント

- https://docs.sqlalchemy.org/en/20/

## 3. Pydantic - データバリデーション

**バージョン**: 2.6.0+

Pydanticは、Pythonの型ヒントを使用したデータバリデーションライブラリです。

### 主な特徴

- **型安全**: 自動的な型変換とバリデーション
- **高速**: Rustで実装されたコア
- **エラーメッセージ**: わかりやすいバリデーションエラー
- **JSON Schema**: 自動生成

### スキーマ定義

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

class UserCreate(BaseModel):
    """ユーザー作成リクエスト。"""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """ユーザー名は英数字のみ許可。"""
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v

class UserResponse(BaseModel):
    """ユーザーレスポンス。"""

    id: int
    email: str
    username: str
    created_at: datetime

    # ORMモデルから変換を許可
    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    """ユーザー更新リクエスト。"""

    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)

    # すべてのフィールドがオプショナル
```

### バリデーションの使用

```python
from pydantic import ValidationError

# 正常なケース
user_data = UserCreate(
    email="user@example.com",
    username="testuser",
    password="password123"
)
print(user_data.email)  # user@example.com

# エラーケース
try:
    invalid_user = UserCreate(
        email="invalid-email",  # 無効なメールアドレス
        username="ab",  # 短すぎる
        password="123"  # 短すぎる
    )
except ValidationError as e:
    print(e.json())  # 詳細なエラー情報
```

### 設定管理

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """アプリケーション設定。"""

    APP_NAME: str = "AI Agent App"
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

# 環境変数から自動読み込み
settings = Settings()
```

### 公式ドキュメント

- https://docs.pydantic.dev/

## 4. Alembic - データベースマイグレーション

**バージョン**: 1.13.0+

Alembicは、SQLAlchemyのためのデータベースマイグレーションツールです。

### 主な特徴

- **バージョン管理**: データベーススキーマの履歴管理
- **自動生成**: モデルから自動的にマイグレーション生成
- **ロールバック**: 以前のバージョンに戻すことが可能
- **ブランチ**: 複数の開発ブランチをサポート

### 基本的な使い方

```bash
# 初期化
alembic init alembic

# マイグレーションの自動生成
alembic revision --autogenerate -m "Add users table"

# マイグレーションの適用
alembic upgrade head

# ロールバック
alembic downgrade -1

# 現在のバージョンを確認
alembic current

# 履歴を表示
alembic history
```

### マイグレーションファイル

```python
# alembic/versions/xxxx_add_users_table.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    """アップグレード処理。"""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

def downgrade():
    """ダウングレード処理。"""
    op.drop_index('ix_users_email', 'users')
    op.drop_table('users')
```

### 公式ドキュメント

- https://alembic.sqlalchemy.org/

## 5. LangChain / LangGraph - AI Agent

**バージョン**:
- LangChain: 0.3.0+
- LangGraph: 0.2.0+

LangChainは、LLMアプリケーションを構築するためのフレームワークです。
LangGraphは、ステートフルなマルチアクターアプリケーションを構築するためのライブラリです。

### 主な特徴

- **チェーン構築**: 複数のLLM呼び出しを連鎖
- **エージェント**: ツールを使用する自律的なAI
- **メモリ**: 会話履歴の管理
- **ツール**: 外部システムとの統合

### LangGraphの使用

```python
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from typing import TypedDict

class AgentState(TypedDict):
    """エージェントの状態。"""
    messages: list[dict]
    next_action: str

# LLMの初期化
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

def process_message(state: AgentState) -> AgentState:
    """メッセージを処理する。"""
    messages = state["messages"]
    response = llm.invoke(messages)
    messages.append({"role": "assistant", "content": response.content})
    return {"messages": messages, "next_action": "end"}

# グラフの構築
workflow = StateGraph(AgentState)
workflow.add_node("process", process_message)
workflow.set_entry_point("process")
workflow.add_edge("process", END)

# コンパイル
app = workflow.compile()

# 実行
result = app.invoke({
    "messages": [{"role": "user", "content": "Hello!"}],
    "next_action": ""
})
```

### 公式ドキュメント

- LangChain: https://python.langchain.com/
- LangGraph: https://langchain-ai.github.io/langgraph/

## 6. uv - パッケージマネージャー

**公式サイト**: https://github.com/astral-sh/uv

uvは、Rustで実装された超高速Pythonパッケージマネージャーです。

### 主な特徴

- **高速**: pipの10-100倍速い
- **信頼性**: ロックファイルによる再現可能なインストール
- **互換性**: pip、pip-tools、poetryと互換
- **簡単**: 設定なしで使用可能

### 基本コマンド

```bash
# 依存関係のインストール
uv sync

# パッケージの追加
uv add fastapi

# 開発依存関係の追加
uv add --dev pytest

# パッケージの削除
uv remove fastapi

# コマンドの実行
uv run python script.py
uv run pytest

# 仮想環境の作成
uv venv

# ロックファイルの更新
uv lock
```

## 7. Ruff - リンターとフォーマッター

**公式サイト**: https://github.com/astral-sh/ruff

Ruffは、Rustで実装された超高速Pythonリンターとフォーマッターです。

### 主な特徴

- **高速**: Flake8やBlackの10-100倍速い
- **統合**: リントとフォーマットを1つのツールで
- **互換性**: Flake8、Black、isortと互換
- **設定簡単**: pyproject.tomlで設定

### 設定

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 使用方法

```bash
# コードのフォーマット
uv run ruff format .

# リント
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# 特定のファイルのみ
uv run ruff check src/app/main.py
```

## 8. Redis - キャッシュ

**バージョン**: 6.4.0+ (redis-py)

Redisは、高速なインメモリデータストアで、キャッシュとして使用しています。

### 主な特徴

- **高速**: メモリベースで非常に高速
- **多様なデータ型**: String、Hash、List、Set等
- **永続化**: オプションでディスクに保存可能
- **非同期対応**: redis-pyで非同期サポート

### 基本的な使い方

```python
from app.core.cache import cache_manager
from app.config import settings

# 接続
if settings.REDIS_URL:
    await cache_manager.connect()

# キャッシュの設定
await cache_manager.set("user:123", user_data, expire=300)

# キャッシュの取得
cached_data = await cache_manager.get("user:123")

# キャッシュの削除
await cache_manager.delete("user:123")

# パターンマッチングで一括削除
await cache_manager.clear("user:*")
```

### キャッシュ戦略

```python
async def get_user_with_cache(user_id: int) -> User:
    """キャッシュを使用したユーザー取得."""
    # キャッシュキーの生成
    cache_key = f"user:{user_id}"

    # キャッシュチェック
    cached = await cache_manager.get(cache_key)
    if cached:
        return User(**cached)

    # データベースから取得
    user = await user_repository.get(user_id)

    # キャッシュに保存
    await cache_manager.set(
        cache_key,
        user.dict(),
        expire=settings.CACHE_TTL
    )

    return user
```

### 公式ドキュメント

- https://redis.io/
- https://redis-py.readthedocs.io/

## 9. Prometheus - メトリクス収集

**バージョン**: 0.23.1+ (prometheus-client)

Prometheusは、オープンソースのモニタリングシステムです。

### 主な特徴

- **時系列データ**: メトリクスの時系列管理
- **柔軟なクエリ**: PromQL
- **アラート**: Alertmanagerと連携
- **可視化**: Grafanaと連携

### メトリクスの定義

```python
from prometheus_client import Counter, Histogram

# HTTPリクエスト総数
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

# リクエスト処理時間
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# チャットメッセージ総数
chat_messages_total = Counter(
    "chat_messages_total",
    "Total chat messages processed",
    ["role"],
)
```

### ミドルウェアでの使用

```python
from app.api.middlewares.metrics import PrometheusMetricsMiddleware

app.add_middleware(PrometheusMetricsMiddleware)

# メトリクスエンドポイント
@app.get("/metrics")
async def metrics():
    """Prometheusメトリクスエンドポイント."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 公式ドキュメント

- https://prometheus.io/
- https://prometheus.github.io/client_python/

## 10. pytest - テストフレームワーク

**バージョン**: 8.3.0+

pytestは、Pythonの標準的なテストフレームワークです。

### 主な特徴

- **シンプル**: アサーションが簡単
- **フィクスチャ**: テストデータの管理
- **プラグイン**: 豊富なプラグインエコシステム
- **非同期**: pytest-asyncioで非同期テスト

### テストの作成

```python
# tests/test_user_service.py
import pytest
from app.services.user import UserService
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_create_user(db_session):
    """ユーザー作成のテスト。"""
    service = UserService(db_session)

    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    user = await service.create_user(user_data)

    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.id is not None

@pytest.mark.asyncio
async def test_duplicate_email(db_session):
    """重複メールアドレスのテスト。"""
    service = UserService(db_session)

    user_data = UserCreate(
        email="test@example.com",
        username="testuser1",
        password="password123"
    )

    await service.create_user(user_data)

    # 同じメールアドレスで2回目の作成
    with pytest.raises(ValidationError):
        await service.create_user(user_data)
```

### フィクスチャ

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.database import Base

@pytest.fixture
async def db_session():
    """テスト用データベースセッション。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()
```

### 実行

```bash
# すべてのテストを実行
uv run pytest

# 特定のファイルを実行
uv run pytest tests/test_services.py

# 詳細出力
uv run pytest -v

# カバレッジ（HTML形式）
uv run pytest --cov=app --cov-report=html

# カバレッジ（ターミナル出力）
uv run pytest --cov=app --cov-report=term
```

### 追加プラグイン

このプロジェクトでは以下のpytestプラグインを使用しています：

- **pytest-asyncio**: 非同期テストのサポート
- **pytest-cov**: テストカバレッジの測定
- **httpx**: APIテスト用の非同期HTTPクライアント

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_endpoint(client: AsyncClient):
    """チャットエンドポイントのテスト."""
    response = await client.post(
        "/api/agents/chat",
        json={"message": "こんにちは"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
```

### 公式ドキュメント

- https://docs.pytest.org/
- https://pytest-asyncio.readthedocs.io/
- https://www.python-httpx.org/

## まとめ

### 技術選定の理由

| 技術 | 選定理由 |
|------|----------|
| FastAPI | 高速、型安全、自動ドキュメント |
| SQLAlchemy | 成熟したORM、非同期対応 |
| Pydantic | 強力なバリデーション、型安全 |
| Redis | 高速なキャッシュ、非同期対応 |
| Prometheus | メトリクス収集、モニタリング |
| LangChain | LLMアプリ開発の標準 |
| uv | 高速なパッケージ管理 |
| Ruff | 高速なリント・フォーマット |
| pytest | シンプルで強力なテスト |

## 次のステップ

- [データベース設計](./02-database-design.md) - SQLAlchemyモデルの詳細
- [プロジェクト構造](../02-architecture/01-project-structure.md) - ファイル構成
- [レイヤードアーキテクチャ](../02-architecture/02-layered-architecture.md) - 各層での技術使用
