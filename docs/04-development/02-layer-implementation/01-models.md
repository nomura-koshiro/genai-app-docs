# モデル層（Models）

SQLAlchemyを使用したデータベースモデルの定義方法について説明します。

## 概要

モデル層は、データベーステーブルの構造とリレーションシップを定義します。

**責務**:

- テーブル構造の定義
- カラムの型と制約
- エンティティ間のリレーションシップ
- デフォルト値の設定

---

## 基本的なモデル定義

### シンプルなモデル

```python
# src/app/models/sample_user.py
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SampleUser(Base):
    """ユーザーデータベースモデル。"""

    __tablename__ = "sample_users"

    # プライマリキー
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 基本カラム
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ブール値
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # リレーションシップ
    sessions: Mapped[list["SampleSession"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    files: Mapped[list["SampleFile"]] = relationship(
        "File",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
```

---

## リレーションシップ

### One-to-Many

```python
# 親モデル（User）
class SampleUser(Base):
    __tablename__ = "sample_users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # One-to-Many: 1人のユーザーが複数のセッションを持つ
    sessions: Mapped[list["SampleSession"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan"  # ユーザー削除時にセッションも削除
    )


# 子モデル（Session）
class SampleSession(Base):
    __tablename__ = "sample_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 外部キー
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sample_users.id", ondelete="CASCADE"),
        nullable=True
    )

    # リレーションシップ
    user: Mapped["SampleUser"] = relationship("SampleUser", back_populates="sessions")
```

### Many-to-Many（中間テーブル使用）

```python
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

    # Many-to-Many
    groups: Mapped[list["Group"]] = relationship(
        "Group",
        secondary=user_groups,
        back_populates="users"
    )


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_groups,
        back_populates="groups"
    )
```

---

## ベストプラクティス

### 1. Mapped型アノテーションの使用

```python
# ✅ 推奨：Mapped型を使用
id: Mapped[int] = mapped_column(primary_key=True)
email: Mapped[str] = mapped_column(String(255))
is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

### 非推奨の書き方

```python
# ❌ 非推奨：古い書き方
id = Column(Integer, primary_key=True)
email = Column(String(255))
```

### 2. タイムゾーン付きDateTimeの使用

```python
# ✅ 推奨
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),  # タイムゾーン付き
    default=lambda: datetime.now(timezone.utc),
    nullable=False
)

# ❌ 非推奨
created_at = Column(DateTime, default=datetime.now)  # タイムゾーンなし
```

### 3. 外部キー削除時の動作を明示

```python
# ✅ 推奨：削除時の動作を明示
user_id: Mapped[int] = mapped_column(
    Integer,
    ForeignKey("sample_users.id", ondelete="CASCADE"),  # ユーザー削除時にセッションも削除
    nullable=False
)

# オプション：
# - CASCADE: 親削除時に子も削除
# - SET NULL: 親削除時にNULLに設定
# - RESTRICT: 子が存在する場合、親の削除を拒否
```

---

## 参考リンク

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy ORM Mapping](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html)

---

次のセクション: [02-schemas.md](./02-schemas.md)
