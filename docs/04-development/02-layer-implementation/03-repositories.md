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
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseRepository[ModelType: Base, IDType: (int, uuid.UUID)]:
    """SQLAlchemyモデルの共通CRUD操作を提供するベースリポジトリクラス。

    Python 3.12+ のジェネリック構文を使用:
    - ModelType: SQLAlchemyモデルの型
    - IDType: プライマリキーの型（intまたはUUID）

    トランザクション管理:
        - create(), update(), delete() は flush() のみ実行
        - commit() は呼び出し側（サービス層）の責任
    """

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: IDType) -> ModelType | None:
        """IDでレコードを取得。

        Args:
            id: レコードのプライマリキー（intまたはUUID）

        Returns:
            ModelType | None: 該当するモデルインスタンス、見つからない場合はNone
        """
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        load_relations: list[str] | None = None,
        **filters: Any,
    ) -> list[ModelType]:
        """複数のレコードを取得（N+1クエリ対策付き）。

        Args:
            skip: スキップするレコード数（オフセット）
            limit: 返す最大レコード数
            order_by: ソート対象のカラム名
            load_relations: Eager loadするリレーションシップ名のリスト（N+1対策）
            **filters: フィルタ条件

        Returns:
            list[ModelType]: モデルインスタンスのリスト

        Example:
            # N+1クエリ問題を回避
            users = await user_repo.get_multi(
                limit=10,
                load_relations=["sessions", "files"]
            )
            # リレーションシップが事前ロード済み（追加クエリなし）
            for user in users:
                print(f"{user.username}: {len(user.sessions)} sessions")
        """
        from sqlalchemy.orm import selectinload

        query = select(self.model)

        # Eager loading（N+1クエリ対策）
        if load_relations:
            for relation in load_relations:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))
                else:
                    logger.warning(
                        "無効なリレーション指定",
                        model=self.model.__name__,
                        relation=relation,
                        action="skip",
                    )

        # フィルタを適用（モデル属性のみ）
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
            else:
                logger.warning(
                    "無効なフィルタキー指定",
                    model=self.model.__name__,
                    filter_key=key,
                    action="skip",
                )

        # ソート順を適用
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))

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

    async def delete(self, id: IDType) -> bool:
        """レコードを削除。IDTypeはintまたはUUID。"""
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
# src/app/repositories/sample_user.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sample_user import SampleUser
from app.repositories.base import BaseRepository


class SampleUserRepository(BaseRepository[SampleUser]):
    """ユーザーリポジトリ。"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> SampleUser | None:
        """メールアドレスでユーザーを取得。"""
        query = select(SampleUser).where(SampleUser.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> SampleUser | None:
        """ユーザー名でユーザーを取得。"""
        query = select(SampleUser).where(SampleUser.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[SampleUser]:
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
) -> list[SampleUser]:
    """条件でフィルタリング。"""
    query = select(SampleUser)

    if email:
        query = query.where(SampleUser.email.like(f"%{email}%"))
    if is_active is not None:
        query = query.where(SampleUser.is_active == is_active)

    result = await self.db.execute(query)
    return list(result.scalars().all())
```

### JOIN

```python
async def get_with_sessions(self, user_id: int) -> SampleUser | None:
    """セッション情報と一緒にユーザーを取得。"""
    query = (
        select(SampleUser)
        .options(selectinload(SampleUser.sessions))
        .where(SampleUser.id == user_id)
    )
    result = await self.db.execute(query)
    return result.scalar_one_or_none()
```

---

## N+1クエリ問題と対策

### N+1クエリ問題とは

リレーションシップを持つデータを取得する際、親データを取得するクエリ(1回) + 各親に対する子データ取得クエリ(N回) = N+1回のクエリが実行される問題です。

**悪い例（N+1クエリ問題）**:

```python
# 10ユーザーを取得（1回のクエリ）
users = await user_repo.get_multi(limit=10)

# 各ユーザーのセッション数を取得
for user in users:
    # ここで各ユーザーごとにクエリが実行される（10回のクエリ）
    session_count = len(user.sessions)  # 遅延ロード
    print(f"{user.username}: {session_count} sessions")

# 合計: 1 + 10 = 11クエリ
```

### 対策: load_relationsパラメータ

BaseRepositoryの`get_multi()`メソッドは、`load_relations`パラメータでN+1問題を解決します：

**良い例（Eager Loading）**:

```python
# リレーションシップを事前ロード（2回のクエリのみ）
users = await user_repo.get_multi(
    limit=10,
    load_relations=["sessions"]  # ← N+1対策
)

# リレーションシップは既にロード済み
for user in users:
    session_count = len(user.sessions)  # 追加クエリなし
    print(f"{user.username}: {session_count} sessions")

# 合計: 2クエリ（1: users取得、2: 全sessionsを一括取得）
```

### 複数リレーションの指定

```python
users = await user_repo.get_multi(
    limit=10,
    load_relations=["sessions", "files", "memberships"]
)

# 全リレーションシップがロード済み
for user in users:
    print(f"{user.username}:")
    print(f"  Sessions: {len(user.sessions)}")
    print(f"  Files: {len(user.files)}")
    print(f"  Memberships: {len(user.memberships)}")

# 合計: 4クエリ（1: users、2: sessions、3: files、4: memberships）
```

### パフォーマンス比較

| 方法 | ユーザー数 | クエリ数 | 実行時間（目安） |
|------|-----------|---------|-----------------|
| 遅延ロード（N+1問題） | 10 | 11 | 110ms |
| Eager Loading | 10 | 2 | 20ms |
| 遅延ロード（N+1問題） | 100 | 101 | 1010ms |
| Eager Loading | 100 | 2 | 22ms |

### selectinloadの動作

`load_relations`は内部で`selectinload()`を使用します：

```python
# BaseRepository内部の実装
from sqlalchemy.orm import selectinload

if load_relations:
    for relation in load_relations:
        if hasattr(self.model, relation):
            query = query.options(selectinload(getattr(self.model, relation)))
```

**selectinloadの特徴**:

1. **親データを先に取得**: 最初に親エンティティ（User）を全て取得
2. **子データを一括取得**: 親のIDリストを使って子エンティティ（Session）を1回のクエリで取得
3. **メモリ効率**: joinedloadと比べてメモリ使用量が少ない

### 無効なリレーション指定への対処

存在しないリレーション名を指定した場合は警告ログを出力してスキップします：

```python
users = await user_repo.get_multi(
    limit=10,
    load_relations=["sessions", "invalid_relation"]
)

# ログ出力:
# WARNING - 無効なリレーション指定 model=User relation=invalid_relation action=skip
```

### selectinload vs joinedload

| 特徴 | selectinload | joinedload |
|------|-------------|------------|
| クエリ数 | 2回（親 + 子） | 1回（JOIN） |
| メモリ使用量 | 少ない | 多い（重複データ） |
| 推奨ケース | 1対多、多対多 | 1対1、少数の関連 |
| 実装 | `load_relations` | カスタムメソッド |

### テスト方法

リレーションシップが正しくロードされているか確認する方法：

```python
from sqlalchemy import inspect

# リレーションシップのロード状態を確認
users = await user_repo.get_multi(limit=10, load_relations=["sessions"])

for user in users:
    insp = inspect(user)

    # セッションがロード済みか確認
    assert "sessions" in insp.loaded_value
    print(f"Sessions loaded: {insp.attrs.sessions.loaded_value}")
```

---

## ベストプラクティス

1. **ビジネスロジックを含めない**
   - リポジトリはデータ取得のみ
   - バリデーションはサービス層

2. **特定のクエリはメソッドとして定義**

   ```python
   async def get_active_users_with_recent_sessions(self) -> list[SampleUser]:
       """最近セッションを持つアクティブユーザーを取得。"""
       # 複雑なクエリをメソッド化
   ```

---

次のセクション: [04-services.md](./04-services.md)
