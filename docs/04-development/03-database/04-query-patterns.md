# クエリパターン

SQLAlchemyでのよく使うクエリパターンについて説明します。

## フィルタリング

```python
# 等価
query = select(User).where(User.email == "test@example.com")

# LIKE
query = select(User).where(User.username.like("%john%"))

# IN
query = select(User).where(User.id.in_([1, 2, 3]))

# AND条件
query = select(User).where(
    User.is_active == True,
    User.created_at > datetime.now() - timedelta(days=30)
)

# OR条件
from sqlalchemy import or_
query = select(User).where(
    or_(User.email == "a@example.com", User.email == "b@example.com")
)
```

## ソートとページネーション

```python
# ソート
query = select(User).order_by(User.created_at.desc())

# ページネーション
query = select(User).offset(20).limit(10)  # 20件スキップして10件取得
```

## JOIN

```python
# 明示的JOIN
query = (
    select(User, Session)
    .join(Session, User.id == Session.user_id)
    .where(Session.created_at > datetime.now() - timedelta(days=7))
)

# リレーションシップを使用したJOIN
query = select(User).join(User.sessions)
```

## 集計

```python
from sqlalchemy import func

# COUNT
query = select(func.count(User.id))
result = await db.execute(query)
count = result.scalar()

# GROUP BY
query = (
    select(User.is_active, func.count(User.id))
    .group_by(User.is_active)
)
```

## サブクエリ

```python
# サブクエリ
subq = select(Session.user_id).where(
    Session.created_at > datetime.now() - timedelta(days=7)
).subquery()

query = select(User).where(User.id.in_(select(subq)))
```

## Eager Loading

```python
from sqlalchemy.orm import selectinload, joinedload

# selectinload（別クエリで取得）
query = select(User).options(selectinload(User.sessions))

# joinedload（JOINで取得）
query = select(User).options(joinedload(User.sessions))
```

## 参考リンク

- [SQLAlchemy Core](https://docs.sqlalchemy.org/en/20/core/)
- [SQLAlchemy ORM Querying](https://docs.sqlalchemy.org/en/20/orm/queryguide/)
