# クエリパターン

SQLAlchemyでのよく使うクエリパターンについて説明します。

## フィルタリング

```python
# 等価
query = select(SampleUser).where(SampleUser.email == "test@example.com")

# LIKE
query = select(SampleUser).where(SampleUser.username.like("%john%"))

# IN
query = select(SampleUser).where(SampleUser.id.in_([1, 2, 3]))

# AND条件
query = select(SampleUser).where(
    SampleUser.is_active == True,
    SampleUser.created_at > datetime.now() - timedelta(days=30)
)

# OR条件
from sqlalchemy import or_
query = select(SampleUser).where(
    or_(SampleUser.email == "a@example.com", SampleUser.email == "b@example.com")
)
```

## ソートとページネーション

```python
# ソート
query = select(SampleUser).order_by(SampleUser.created_at.desc())

# ページネーション
query = select(SampleUser).offset(20).limit(10)  # 20件スキップして10件取得
```

## JOIN

```python
# 明示的JOIN
query = (
    select(User, Session)
    .join(Session, SampleUser.id == SampleSession.user_id)
    .where(SampleSession.created_at > datetime.now() - timedelta(days=7))
)

# リレーションシップを使用したJOIN
query = select(SampleUser).join(User.sessions)
```

## 集計

```python
from sqlalchemy import func

# COUNT
query = select(func.count(SampleUser.id))
result = await db.execute(query)
count = result.scalar()

# GROUP BY
query = (
    select(SampleUser.is_active, func.count(SampleUser.id))
    .group_by(SampleUser.is_active)
)
```

## サブクエリ

```python
# サブクエリ
subq = select(SampleSession.user_id).where(
    SampleSession.created_at > datetime.now() - timedelta(days=7)
).subquery()

query = select(SampleUser).where(SampleUser.id.in_(select(subq)))
```

## Eager Loading（N+1問題対策）

N+1問題は、リレーションシップをロードする際に発生する深刻なパフォーマンス問題です。
リストの各アイテムに対して追加のクエリが発行され、全体で1+N回のクエリが実行されます。

### N+1問題の例

```python
# ❌ N+1問題が発生（悪い例）
users = await db.execute(select(User).limit(10))
users = users.scalars().all()

for user in users:  # 10ユーザー
    # project_membershipsアクセスごとに追加クエリが発行される
    print(len(user.project_memberships))  # 1クエリ × 10 = 10クエリ

# 合計11クエリ: 1回（ユーザーリスト） + 10回（各ユーザーのメンバーシップ）
```

### selectinload による解決

```python
from sqlalchemy.orm import selectinload

# ✅ N+1問題を解決（良い例）
query = select(User).options(selectinload(User.project_memberships)).limit(10)
result = await db.execute(query)
users = result.scalars().all()

for user in users:  # 10ユーザー
    # 追加クエリなしでアクセス可能
    print(len(user.project_memberships))

# 合計2クエリのみ: 1回（ユーザーリスト） + 1回（全メンバーシップを一括取得）
```

### selectinload vs joinedload

| 方式 | クエリ数 | 使用ケース | 特徴 |
|-----|---------|-----------|------|
| `selectinload` | 2回 | 1対多の関係 | 別クエリで取得、重複データなし |
| `joinedload` | 1回 | 1対1の関係 | JOINで取得、重複データあり |

### 実装例（UserRepositoryの実装）

```python
# src/app/repositories/user.py
from sqlalchemy.orm import selectinload

class UserRepository(BaseRepository[User, uuid.UUID]):
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """アクティブユーザーの一覧を取得（N+1問題対策付き）。"""
        return await self.get_multi(
            skip=skip,
            limit=limit,
            is_active=True,
            load_relations=["project_memberships"],  # N+1問題対策
        )
```

### BaseRepositoryでの汎用実装

```python
# src/app/repositories/base.py
class BaseRepository(Generic[ModelType, IDType]):
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        load_relations: list[str] | None = None,
        **filters: Any,
    ) -> list[ModelType]:
        """複数レコードを取得（N+1問題対策付き）。

        Args:
            load_relations: 事前ロードするリレーションシップ名のリスト
                例: ["project_memberships", "files"]
        """
        query = select(self.model)

        # N+1問題対策: selectinloadでリレーションを事前ロード
        if load_relations:
            for relation_name in load_relations:
                if hasattr(self.model, relation_name):
                    relation_attr = getattr(self.model, relation_name)
                    query = query.options(selectinload(relation_attr))

        # フィルタ適用
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

### パフォーマンス比較

**N+1問題あり（悪い例）**:

- 10ユーザー × 各5プロジェクト = 51クエリ（1 + 10×5）
- 実行時間: 約500ms

**selectinload使用（良い例）**:

- 2クエリのみ（ユーザーリスト + メンバーシップ一括取得）
- 実行時間: 約20ms

**パフォーマンス改善**: 約25倍高速化

### ベストプラクティス

1. **リスト取得時は必ずselectinloadを検討**
   - 特にリレーションシップにアクセスする場合

2. **load_relationsパラメータを活用**
   - BaseRepositoryの`get_multi()`で統一的に対応

3. **SQLログで確認**
   - 開発時は`echo=True`でクエリ数を確認

4. **N+1検出ツール**
   - `nplusone`ライブラリでN+1問題を自動検出

```

## 参考リンク

- [SQLAlchemy Core](https://docs.sqlalchemy.org/en/20/core/)
- [SQLAlchemy ORM Querying](https://docs.sqlalchemy.org/en/20/orm/queryguide/)
