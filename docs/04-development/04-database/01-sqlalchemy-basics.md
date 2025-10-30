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


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI依存性注入用のデータベースセッションジェネレータ。

    トランザクション管理:
        - このジェネレータは commit() を実行しません
        - commit() はサービス層の @transactional デコレータが責任を持ちます
        - これによりトランザクション境界をサービス層で明確に定義できます
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # 注意: ここでは commit() しない（サービス層で@transactionalデコレータが実行）
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

## トランザクション管理の設計思想

camp-backendでは、トランザクション管理を**サービス層の責任**としています。

### 設計パターン

```
┌─────────────────────────────────────┐
│  エンドポイント層                    │
│  - リクエスト受付                    │
│  - レスポンス返却                    │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  サービス層                          │
│  - ビジネスロジック                  │
│  - @transactional デコレータ         │  ← トランザクション境界
│  - commit() / rollback() の責任      │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  リポジトリ層                        │
│  - flush() のみ実行                  │
│  - commit() は実行しない             │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  データベース層 (get_db())           │
│  - セッション提供                    │
│  - commit() は実行しない             │
│  - エラー時の自動 rollback()         │
└─────────────────────────────────────┘
```

### なぜget_db()でcommitしないのか

1. **トランザクション境界の明確化**
   - サービス層が「どこからどこまでが1つのトランザクションか」を定義
   - 複数のリポジトリ操作を1つのトランザクションにまとめられる

2. **柔軟性の確保**
   - 途中でエラーが発生した場合、サービス層で適切にロールバック
   - 複雑なビジネスロジックでも対応可能

3. **AOPパターンの活用**
   - `@transactional`デコレータで横断的関心事を分離
   - ビジネスロジックとトランザクション管理を分離

### @transactionalデコレータ

**注意**: 現在の実装では明示的な`@transactional`デコレータはありませんが、サービス層で明示的に`commit()`を呼び出すパターンを使用しています。

**将来的な実装例**:

```python
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession

def transactional(func):
    """サービス層メソッドにトランザクション管理を追加するデコレータ。"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 引数からAsyncSessionを探す
        db_session = None
        for arg in args:
            if isinstance(arg, AsyncSession):
                db_session = arg
                break

        if not db_session:
            # self.dbの場合
            self = args[0]
            if hasattr(self, 'db'):
                db_session = self.db

        try:
            result = await func(*args, **kwargs)
            await db_session.commit()  # ← ここでcommit
            return result
        except Exception:
            await db_session.rollback()
            raise

    return wrapper
```

**使用例**:

```python
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(User, db)

    @transactional
    async def create_user_with_profile(
        self,
        email: str,
        username: str,
        profile_data: dict,
    ) -> User:
        """ユーザーとプロフィールを同時に作成（1つのトランザクション）。"""
        # ユーザー作成
        user = await self.repository.create(
            email=email,
            username=username,
        )

        # プロフィール作成
        profile = await self.profile_repository.create(
            user_id=user.id,
            **profile_data,
        )

        # @transactionalデコレータが自動的にcommit()
        return user
```

### 現在のパターン（明示的commit）

現在の実装では、サービス層で明示的に`commit()`を呼び出します：

```python
async def create_user(
    self,
    email: str,
    username: str,
) -> User:
    """ユーザーを作成します。"""
    user = await self.repository.create(
        email=email,
        username=username,
    )

    # サービス層で明示的にcommit
    await self.db.commit()

    return user
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
