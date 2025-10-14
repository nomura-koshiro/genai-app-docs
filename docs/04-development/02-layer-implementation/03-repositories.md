# リポジトリ層（Repositories）

データアクセスロジックのカプセル化について説明します。

## 概要

リポジトリ層は、データベース操作を抽象化し、ビジネスロジックからデータアクセスの詳細を隠蔽します。

**責務**:
- CRUD操作の実装
- クエリの構築と実行
- データ取得ロジックの集約

---

## 基底リポジトリ

```python
# src/app/repositories/base.py
from typing import Any, Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """共通のCRUD操作を持つベースリポジトリ。"""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        """IDでレコードを取得。"""
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        """複数のレコードを取得。"""
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **obj_in: Any) -> ModelType:
        """レコードを作成。"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, **update_data: Any) -> ModelType:
        """レコードを更新。"""
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        """レコードを削除。"""
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
            return True
        return False
```

---

## 具体的なリポジトリ

```python
# src/app/repositories/user.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """ユーザーリポジトリ。"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """メールアドレスでユーザーを取得。"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """ユーザー名でユーザーを取得。"""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """アクティブなユーザーを取得。"""
        return await self.get_multi(skip=skip, limit=limit, is_active=True)
```

---

## クエリパターン

### フィルタリング

```python
async def get_by_criteria(
    self,
    email: str | None = None,
    is_active: bool | None = None
) -> list[User]:
    """条件でフィルタリング。"""
    query = select(User)

    if email:
        query = query.where(User.email.like(f"%{email}%"))
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    result = await self.db.execute(query)
    return list(result.scalars().all())
```

### JOIN

```python
async def get_with_sessions(self, user_id: int) -> User | None:
    """セッション情報と一緒にユーザーを取得。"""
    query = (
        select(User)
        .options(selectinload(User.sessions))
        .where(User.id == user_id)
    )
    result = await self.db.execute(query)
    return result.scalar_one_or_none()
```

---

## ベストプラクティス

1. **ビジネスロジックを含めない**
   - リポジトリはデータ取得のみ
   - バリデーションはサービス層

2. **特定のクエリはメソッドとして定義**
   ```python
   async def get_active_users_with_recent_sessions(self) -> list[User]:
       """最近セッションを持つアクティブユーザーを取得。"""
       # 複雑なクエリをメソッド化
   ```

---

次のセクション: [04-services.md](./04-services.md)
