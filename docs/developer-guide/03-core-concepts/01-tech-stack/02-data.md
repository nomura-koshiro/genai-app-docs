# テックスタック - データレイヤー

このドキュメントでは、camp-backendのデータレイヤーで使用している技術について説明します。

## 目次

- [PostgreSQL + Docker](#postgresql--docker)
- [SQLAlchemy](#sqlalchemy)
- [Redis](#redis)

---

## PostgreSQL

**バージョン**: PostgreSQL 16

このプロジェクトでは、PostgreSQLをローカルにインストールして使用します。

### 主な特徴

- **ローカルインストール**: Windows上に直接インストール
- **テスト専用DB**: 自動作成・削除される独立したテストデータベース
- **開発・テスト・本番同一**: すべての環境で同じPostgreSQLバージョンを使用

### セットアップ

詳細は [Windows環境セットアップ](../../01-getting-started/02-windows-setup.md) を参照してください。

```powershell
# PostgreSQL起動確認（Scoop版）
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data status

# 接続確認
psql -U postgres -d camp_backend_db
```

### 環境変数

```ini
# 開発用データベース
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db

# テスト用データベース
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db_test
TEST_DATABASE_ADMIN_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
TEST_DATABASE_NAME=camp_backend_db_test
```

### テストデータベースの自動管理

テスト実行時に以下の処理が自動的に行われます：

1. **テストセッション開始時**: `camp_backend_db_test`データベースを作成
2. **各テスト関数の前**: 全テーブルを作成
3. **各テスト関数の後**: 全テーブルを削除
4. **テストセッション終了時**: `camp_backend_db_test`データベースを削除

### 公式ドキュメント

- PostgreSQL: <https://www.postgresql.org/>
- Docker: <https://www.docker.com/>
- asyncpg (PostgreSQLドライバ): <https://magicstack.github.io/asyncpg/>

---

## SQLAlchemy

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
from app.core.database import Base

class SampleUser(Base):
    """ユーザーモデル。"""

    __tablename__ = "sample_users"

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
    user_id: Mapped[int] = mapped_column(ForeignKey("sample_users.id"))

    # リレーションシップ
    user: Mapped["SampleUser"] = relationship(back_populates="posts")
```

### 非同期クエリ

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_with_posts(db: AsyncSession, user_id: int):
    """ユーザーと投稿を取得する。"""
    # 基本的なクエリ
    query = select(SampleUser).where(SampleUser.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # JOINクエリ
    query = (
        select(SampleUser)
        .join(User.posts)
        .where(SampleUser.id == user_id)
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

- <https://docs.sqlalchemy.org/en/20/>

---

## Redis

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
from app.core.config import settings

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
async def get_user_with_cache(user_id: int) -> SampleUser:
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

- <https://redis.io/>
- <https://redis-py.readthedocs.io/>

---

## 関連ドキュメント

- [テックスタック概要](./01-tech-stack.md) - 技術スタック全体像
- [Webフレームワーク](./01-tech-stack-web.md) - FastAPI、Pydantic、Alembic
- [AI・開発ツール](./01-tech-stack-ai-tools.md) - LangChain/LangGraph、uv、Ruff、pytest、Prometheus

---
