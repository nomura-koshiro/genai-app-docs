# SQLAlchemy基礎

SQLAlchemy 2.0の基本的な使い方について説明します。

## データベース設定

```python
# src/app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# 非同期エンジン作成
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/dbname",
    echo=True,  # SQLログ出力
    pool_pre_ping=True,  # 接続チェック
)

# セッションファクトリ作成
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """すべてのモデルの基底クラス。"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """データベースセッション取得。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## 基本的なクエリ

```python
from sqlalchemy import select

# 単一取得
async def get_user(db: AsyncSession, user_id: int) -> SampleUser | None:
    return await db.get(SampleUser, user_id)

# 複数取得
async def get_users(db: AsyncSession) -> list[SampleUser]:
    query = select(SampleUser)
    result = await db.execute(query)
    return list(result.scalars().all())

# フィルタ
async def get_active_users(db: AsyncSession) -> list[SampleUser]:
    query = select(SampleUser).where(SampleUser.is_active == True)
    result = await db.execute(query)
    return list(result.scalars().all())

# 作成
async def create_user(db: AsyncSession, email: str, username: str) -> SampleUser:
    user = User(email=email, username=username)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

# 更新
async def update_user(db: AsyncSession, user: SampleUser, username: str) -> SampleUser:
    user.username = username
    await db.flush()
    await db.refresh(user)
    return user

# 削除
async def delete_user(db: AsyncSession, user: SampleUser) -> None:
    await db.delete(user)
    await db.flush()
```

## タイムゾーン対応のタイムスタンプ

SQLAlchemyモデルでタイムスタンプを扱う際は、**UTCタイムゾーン付き**のdatetimeを使用してください。

### 正しい実装（推奨）

```python
from datetime import UTC, datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

class ProjectFile(Base):
    __tablename__ = "project_files"

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),  # ✅ 正しい: UTCタイムゾーン付き
        nullable=False,
        comment="Upload timestamp",
    )
```

### 避けるべき実装

```python
from datetime import datetime, timezone

# ❌ 古い書き方（非推奨）
uploaded_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc),  # timezone.utc は古い
    nullable=False,
)

# ❌ さらに古い書き方（非推奨）
uploaded_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=datetime.utcnow,  # タイムゾーン情報なし
    nullable=False,
)
```

### なぜdatetime.now(UTC)を使うべきか

1. **Python 3.11+推奨の書き方**: `UTC`は`datetime.timezone.utc`の推奨エイリアス
2. **タイムゾーン情報の明示**: `timezone=True`と組み合わせて使用
3. **SQLAlchemyとの親和性**: PostgreSQLの`TIMESTAMP WITH TIME ZONE`と正しく連携

### データベース側の設定

```python
DateTime(timezone=True)  # PostgreSQL: TIMESTAMP WITH TIME ZONE
DateTime(timezone=False)  # PostgreSQL: TIMESTAMP WITHOUT TIME ZONE（非推奨）
```

**推奨**: 必ず`timezone=True`を使用してタイムゾーン情報を保持してください。
```

## 参考リンク

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
