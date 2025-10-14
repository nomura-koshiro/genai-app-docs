# SQLAlchemy基礎

SQLAlchemy 2.0の基本的な使い方について説明します。

## データベース設定

```python
# src/app/database.py
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
async def get_user(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)

# 複数取得
async def get_users(db: AsyncSession) -> list[User]:
    query = select(User)
    result = await db.execute(query)
    return list(result.scalars().all())

# フィルタ
async def get_active_users(db: AsyncSession) -> list[User]:
    query = select(User).where(User.is_active == True)
    result = await db.execute(query)
    return list(result.scalars().all())

# 作成
async def create_user(db: AsyncSession, email: str, username: str) -> User:
    user = User(email=email, username=username)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

# 更新
async def update_user(db: AsyncSession, user: User, username: str) -> User:
    user.username = username
    await db.flush()
    await db.refresh(user)
    return user

# 削除
async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.flush()
```

## 参考リンク

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
