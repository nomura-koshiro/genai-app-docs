# モデル関係

SQLAlchemyでのリレーションシップ定義について説明します。

## One-to-Many

```python
class SampleUser(Base):
    __tablename__ = "sample_users"
    id: Mapped[int] = mapped_column(primary_key=True)

    # One-to-Many
    sessions: Mapped[list["SampleSession"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class SampleSession(Base):
    __tablename__ = "sample_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sample_users.id", ondelete="CASCADE"))

    # Many-to-One
    user: Mapped["SampleUser"] = relationship("SampleUser", back_populates="sessions")
```

## Many-to-Many

```python
from sqlalchemy import Table, Column, Integer, ForeignKey

# 中間テーブル
user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("sample_users.id")),
    Column("group_id", Integer, ForeignKey("groups.id")),
)


class SampleUser(Base):
    __tablename__ = "sample_users"
    id: Mapped[int] = mapped_column(primary_key=True)

    groups: Mapped[list["Group"]] = relationship(
        "Group",
        secondary=user_groups,
        back_populates="users"
    )


class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(primary_key=True)

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_groups,
        back_populates="groups"
    )
```

## リレーションシップのロード

```python
from sqlalchemy.orm import selectinload, joinedload

# Eager Loading
query = select(SampleUser).options(selectinload(SampleUser.sessions))
result = await db.execute(query)
user = result.scalar_one()
# user.sessions は既にロード済み
```
