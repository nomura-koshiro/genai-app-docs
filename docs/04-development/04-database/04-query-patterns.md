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

## Eager Loading

```python
from sqlalchemy.orm import selectinload, joinedload

# selectinload（別クエリで取得）
query = select(SampleUser).options(selectinload(SampleUser.sessions))

# joinedload（JOINで取得）
query = select(SampleUser).options(joinedload(User.sessions))
```

## 参考リンク

- [SQLAlchemy Core](https://docs.sqlalchemy.org/en/20/core/)
- [SQLAlchemy ORM Querying](https://docs.sqlalchemy.org/en/20/orm/queryguide/)
