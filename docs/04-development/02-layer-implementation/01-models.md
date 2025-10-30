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

## タイムスタンプフィールドのベストプラクティス（詳細）

### 推奨: datetime.now(UTC)

```python
from datetime import UTC, datetime
from sqlalchemy import DateTime

created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(UTC),  # ✅ 推奨（Python 3.11+）
    nullable=False,
)
```

### 非推奨: datetime.utcnow

```python
# ❌ 非推奨（タイムゾーン情報なし）
default=datetime.utcnow

# ❌ 非推奨（古い書き方）
default=lambda: datetime.now(timezone.utc)
```

**理由**:
- Python 3.11+推奨の書き方
- タイムゾーン情報の明示
- PostgreSQLの`TIMESTAMP WITH TIME ZONE`と連携

---

## リレーションシップとN+1対策

### リレーションシップの定義例

```python
class User(Base):
    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="user",
        lazy="select",  # デフォルト: 遅延ロード
    )
```

### N+1問題対策

リレーションシップにアクセスする際は、必ず`selectinload`を使用してください。

```python
# ✅ 正しい（N+1対策あり）
from sqlalchemy.orm import selectinload

users = await db.execute(
    select(User)
    .options(selectinload(User.project_memberships))
    .limit(10)
)

# ❌ 間違い（N+1問題発生）
users = await db.execute(select(User).limit(10))
for user in users:
    memberships = user.project_memberships  # 追加クエリ発生
```

詳細は [04-database/04-query-patterns.md](../04-database/04-query-patterns.md) を参照。

---

## Azure AD統合用Userモデル

新しいAzure AD統合用のUserモデルの例です。

### User モデル（Azure AD対応）

```python
from datetime import UTC, datetime
import uuid

from sqlalchemy import Boolean, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # プライマリキー（UUID）
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Azure AD統合
    azure_oid: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Azure AD Object ID",
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ロール（JSON配列）
    roles: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="User roles from Azure AD",
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # リレーションシップ
    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        secondary="project_members",
        back_populates="members",
        viewonly=True,
    )
```

**特徴**:
- UUID主キー（従来のint型から変更）
- Azure AD Object ID（azure_oid）で一意識別
- パスワードなし（Azure AD認証のみ）
- ロールをJSON配列で管理
- プロジェクトメンバーシップのリレーション

**User vs SampleUserの使い分け**:
- **User**: 新規開発、Azure AD統合機能
- **SampleUser**: レガシー、段階的移行中のサンプルコード

---
---

## 参考リンク

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy ORM Mapping](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html)

---

次のセクション: [02-schemas.md](./02-schemas.md)
