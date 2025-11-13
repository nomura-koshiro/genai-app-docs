# データベース設計

このドキュメントでは、camp-backendのデータベース設計について詳しく説明します。

## データベース概要

### 使用技術

- **ORM**: SQLAlchemy 2.0（非同期対応）
- **データベース**: PostgreSQL 16（全環境共通）
- **マイグレーション**: Alembic

### 設計原則

1. **正規化**: 適切な正規化でデータの整合性を保つ
2. **インデックス**: 頻繁に検索されるカラムにインデックスを設定
3. **タイムスタンプ**: すべてのテーブルに作成日時・更新日時を含める
4. **外部キー**: リレーションシップを明示的に定義
5. **論理削除**: 必要に応じて物理削除ではなく論理削除を使用

## SQLAlchemyモデル定義

### Base クラス

すべてのモデルの基底クラスです。

```python
# src/app/core/database.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """全てのデータベースモデル用のベースクラス。"""
    pass
```

### SQLAlchemy 2.0 の型ヒント

SQLAlchemy 2.0では、`Mapped`型を使用して型安全なモデルを定義します。

```python
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

class Example(Base):
    __tablename__ = "examples"

    # 基本的なカラム定義
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    # オプショナルなカラム
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # デフォルト値
    is_active: Mapped[bool] = mapped_column(default=True)
```

## テーブル設計

### ユーザーモデル

このプロジェクトには2つのユーザーモデルが存在します：

1. **users テーブル（UserAccountモデル）**: Azure AD認証用、UUID主キー
2. **sample_users テーブル（SampleUserモデル）**: レガシー JWT認証用、integer主キー

#### users テーブル（Azure AD認証用）

Azure AD認証に対応したユーザー管理モデルです。

```python
# src/app/models/user_account/user_account.py
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class UserAccount(Base, TimestampMixin):
    """Azure AD認証用ユーザーモデル。

    Attributes:
        id: ユーザーID（UUID、主キー）
        azure_oid: Azure AD Object ID（一意識別子）
        email: メールアドレス（ユニーク、インデックス）
        display_name: 表示名
        roles: システムロール（例: ["system_admin", "user"]）
        is_active: アクティブ状態
        created_at: 作成日時（UTC）
        updated_at: 更新日時（UTC）
        last_login: 最終ログイン日時
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    azure_oid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    roles: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**テーブル定義**:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    azure_oid VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    roles JSON NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_azure_oid ON users(azure_oid);
CREATE INDEX idx_users_email ON users(email);
```

#### sample_users テーブル（レガシー JWT認証用）

レガシーなJWT認証用のユーザーモデルです（移行予定）。

```python
# src/app/models/sample/sample_user.py
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SampleUser(Base):
    """ユーザーモデル。

    Attributes:
        id: ユーザーID（主キー）
        email: メールアドレス（ユニーク、インデックス）
        username: ユーザー名（ユニーク、インデックス）
        hashed_password: ハッシュ化されたパスワード
        is_active: アクティブ状態
        is_superuser: スーパーユーザー権限
        created_at: 作成日時（UTC）
        updated_at: 更新日時（UTC）
    """

    __tablename__ = "sample_users"

    # プライマリキー
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 基本情報
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="ユーザーのメールアドレス"
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="ユーザー名"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcryptでハッシュ化されたパスワード"
    )

    # フラグ
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="アカウントのアクティブ状態"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="管理者権限"
    )

    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="作成日時（UTC）"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新日時（UTC）"
    )

    # リレーションシップ
    sessions: Mapped[list["SampleSession"]] = relationship(
        "SampleSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """文字列表現。"""
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
```

**テーブル定義**:

```sql
CREATE TABLE sample_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX ix_sample_users_email ON sample_users(email);
CREATE INDEX ix_sample_users_username ON sample_users(username);
```

### sample_sessions テーブル

AI Agentのチャットセッションを管理します。

```python
# src/app/models/sample/sample_session.py
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SampleSession(Base):
    """チャットセッションモデル。

    Attributes:
        id: セッションID（主キー）
        user_id: ユーザーID（外部キー）
        session_id: セッション識別子（ユニーク）
        title: セッションタイトル
        created_at: 作成日時
        updated_at: 更新日時
    """

    __tablename__ = "sample_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sample_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ユーザーID"
    )
    session_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="セッション識別子（UUID等）"
    )
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="セッションタイトル"
    )

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
    user: Mapped["SampleUser"] = relationship("SampleUser", back_populates="sessions")
    messages: Mapped[list["SampleMessage"]] = relationship(
        "SampleMessage",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SampleSession(id={self.id}, session_id={self.session_id})>"
```

### sample_messages テーブル

チャットメッセージの履歴を管理します。

```python
# src/app/models/sample/sample_session.py (SampleMessage)
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SampleMessage(Base):
    """チャットメッセージモデル。

    Attributes:
        id: メッセージID（主キー）
        session_id: セッションID（外部キー）
        role: メッセージの役割（user/assistant/system）
        content: メッセージ内容
        created_at: 作成日時
    """

    __tablename__ = "sample_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sample_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="セッションID"
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="メッセージの役割（user/assistant/system）"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="メッセージ内容"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # リレーションシップ
    session: Mapped["SampleSession"] = relationship("SampleSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<SampleMessage(id={self.id}, role={self.role})>"
```

### sample_files テーブル（非推奨）

アップロードされたファイルを管理します（現在は使用していません）。

```python
# src/app/models/sample/sample_file.py
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SampleFile(Base):
    """ファイルモデル。

    Attributes:
        id: ファイルID（主キー）
        user_id: ユーザーID（外部キー）
        filename: ファイル名
        content_type: MIMEタイプ
        size: ファイルサイズ（バイト）
        storage_path: ストレージパス
        created_at: アップロード日時
    """

    __tablename__ = "sample_files"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sample_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ユーザーID"
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="オリジナルファイル名"
    )
    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="MIMEタイプ（例: image/png）"
    )
    size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="ファイルサイズ（バイト）"
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="ストレージ上のパス"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # リレーションシップ
    user: Mapped["SampleUser"] = relationship("SampleUser")

    def __repr__(self) -> str:
        return f"<File(id={self.id}, filename={self.filename})>"
```

## リレーションシップ

### 1対多リレーション

```python
# SampleUser → SampleSessions（1対多）
class SampleUser(Base):
    sessions: Mapped[list["SampleSession"]] = relationship(
        "SampleSession",
        back_populates="user",
        cascade="all, delete-orphan"  # ユーザー削除時にセッションも削除
    )

class SampleSession(Base):
    user: Mapped["SampleUser"] = relationship("SampleUser", back_populates="sessions")
```

### カスケード設定

- **cascade="all, delete-orphan"**: 親が削除されたら子も削除
- **ondelete="CASCADE"**: データベースレベルでのカスケード削除

```python
# ForeignKey with cascade
user_id: Mapped[int] = mapped_column(
    ForeignKey("sample_users.id", ondelete="CASCADE"),
    nullable=False
)
```

### Lazy Loading

リレーションシップの読み込みタイミングを制御します。

```python
# Lazy Loading の種類
sessions: Mapped[list["SampleSession"]] = relationship(
    "SampleSession",
    lazy="select",      # デフォルト: 必要時に別クエリで取得
    # lazy="selectin",  # IN句で一括取得（N+1問題を回避）
    # lazy="joined",    # JOINで同時取得
    # lazy="subquery",  # サブクエリで取得
    # lazy="noload",    # 自動読み込みしない
)
```

## 非同期SQLAlchemy

### セッション管理

```python
# src/app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# エンジンの作成
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,        # SQLログの出力
    pool_pre_ping=True,         # 接続の健全性チェック
    future=True,                # SQLAlchemy 2.0スタイル
)

# セッションファクトリー
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,     # コミット後もオブジェクトを使用可能
    autocommit=False,           # 自動コミット無効
    autoflush=False,            # 自動フラッシュ無効
)
```

### 基本的なクエリ

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_email(db: AsyncSession, email: str) -> SampleUser | None:
    """メールアドレスでユーザーを取得。"""
    query = select(SampleUser).where(SampleUser.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_active_users(db: AsyncSession) -> list[SampleUser]:
    """アクティブなユーザーの一覧を取得。"""
    query = select(SampleUser).where(SampleUser.is_active == True).order_by(SampleUser.created_at)
    result = await db.execute(query)
    return list(result.scalars().all())
```

### JOINクエリ

```python
from sqlalchemy.orm import selectinload

async def get_user_with_sessions(db: AsyncSession, user_id: int) -> SampleUser | None:
    """ユーザーとセッションを一緒に取得。"""
    query = (
        select(SampleUser)
        .options(selectinload(SampleUser.sessions))  # セッションを一緒に読み込み
        .where(SampleUser.id == user_id)
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()

async def get_sessions_with_messages(
    db: AsyncSession,
    user_id: int
) -> list[SampleSession]:
    """セッションとメッセージを一緒に取得。"""
    query = (
        select(SampleSession)
        .options(
            selectinload(SampleSession.messages),  # メッセージを読み込み
            selectinload(SampleSession.user)       # ユーザーも読み込み
        )
        .where(SampleSession.user_id == user_id)
        .order_by(SampleSession.updated_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
```

### 集計クエリ

```python
from sqlalchemy import func

async def count_user_sessions(db: AsyncSession, user_id: int) -> int:
    """ユーザーのセッション数を取得。"""
    query = select(func.count(SampleSession.id)).where(SampleSession.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one()

async def count_user_messages(db: AsyncSession, user_id: int) -> int:
    """ユーザーの総メッセージ数を取得。"""
    query = (
        select(func.count(SampleMessage.id))
        .join(SampleSession)
        .where(SampleSession.user_id == user_id)
    )
    result = await db.execute(query)
    return result.scalar_one() or 0
```

### トランザクション

```python
async def transfer_sessions(
    db: AsyncSession,
    from_user_id: int,
    to_user_id: int,
) -> None:
    """セッションを別のユーザーに移動（トランザクション）。"""
    try:
        # 複数の操作を1つのトランザクションで実行
        sessions = await get_user_sessions(db, from_user_id)

        for session in sessions:
            session.user_id = to_user_id

        await db.flush()  # 変更をフラッシュ

        # 成功すればコミット（get_db()が自動的に行う）
    except Exception:
        # エラー時はロールバック（get_db()が自動的に行う）
        raise
```

## インデックス戦略

### 基本的なインデックス

```python
# 単一カラムインデックス
email: Mapped[str] = mapped_column(String(255), index=True)

# ユニークインデックス
email: Mapped[str] = mapped_column(String(255), unique=True)

# 主キー（自動的にインデックスが作成される）
id: Mapped[int] = mapped_column(primary_key=True)
```

### 複合インデックス

```python
from sqlalchemy import Index

class SampleMessage(Base):
    __tablename__ = "sample_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sample_sessions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # 複合インデックスの定義
    __table_args__ = (
        Index("ix_messages_session_created", "session_id", "created_at"),
    )
```

## データベースパフォーマンス最適化

### 1. N+1問題の回避

```python
# 悪い例: N+1問題
users = await get_all_users(db)
for user in users:
    sessions = await get_user_sessions(db, user.id)  # N回クエリ実行

# 良い例: selectinloadで一括取得
query = select(SampleUser).options(selectinload(SampleUser.sessions))
result = await db.execute(query)
users = result.scalars().all()
for user in users:
    sessions = user.sessions  # 追加クエリなし
```

### 2. ページネーション

```python
async def get_users_paginated(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> list[SampleUser]:
    """ページネーション付きでユーザーを取得。"""
    query = (
        select(SampleUser)
        .order_by(SampleUser.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
```

### 3. 部分的な読み込み

```python
from sqlalchemy.orm import load_only

async def get_user_basic_info(db: AsyncSession, user_id: int):
    """必要なカラムのみ取得。"""
    query = (
        select(SampleUser)
        .options(load_only(SampleUser.id, SampleUser.email, SampleUser.username))
        .where(SampleUser.id == user_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

## ベストプラクティス

### 1. 型ヒントを使用する

```python
# 良い例
async def get_user(db: AsyncSession, user_id: int) -> SampleUser | None:
    return await db.get(SampleUser, user_id)

# 悪い例
async def get_user(db, user_id):  # 型ヒントなし
    return await db.get(SampleUser, user_id)
```

### 2. ドキュメント文字列を書く

```python
class SampleUser(Base):
    """ユーザーモデル。

    このモデルは、アプリケーションのユーザーアカウントを表します。
    認証、認可、プロファイル情報を管理します。

    Attributes:
        id: ユーザーの一意識別子
        email: ログイン用のメールアドレス
        username: 表示名
    """
```

### 3. デフォルト値を設定する

```python
is_active: Mapped[bool] = mapped_column(default=True)
created_at: Mapped[datetime] = mapped_column(
    default=lambda: datetime.now(timezone.utc)
)
```

### 4. カスケード削除を適切に設定する

```python
# 親レコード削除時に子レコードも削除
sessions: Mapped[list["SampleSession"]] = relationship(
    "SampleSession",
    cascade="all, delete-orphan"
)
```

## まとめ

### データベース設計の要点

- **正規化**: データの整合性を保つ
- **インデックス**: パフォーマンス向上
- **リレーションシップ**: 明示的な関連定義
- **非同期**: async/awaitで効率的な処理
- **型安全**: Mapped型で型チェック

### SQLAlchemy 2.0の利点

- 型安全性の向上
- より直感的なAPI
- パフォーマンスの改善
- 非同期サポート

## 次のステップ

- [テックスタック](./01-tech-stack.md) - SQLAlchemyの詳細
- [レイヤードアーキテクチャ](../02-architecture/02-layered-architecture.md) - リポジトリ層での使用
- [データベースセットアップ](../01-getting-started/03-database-setup.md) - 実際のセットアップ手順
