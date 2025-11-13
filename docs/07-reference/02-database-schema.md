# データベーススキーマ

バックエンドで使用されるすべてのデータベーステーブル定義とリレーションを記載します。

## 目次

- [概要](#概要)
- [ER図](#er図)
- [テーブル定義](#テーブル定義)
  - [users](#users-ユーザー)
  - [sessions](#sessions-セッション)
  - [messages](#messages-メッセージ)
  - [files](#files-ファイル)
- [リレーション](#リレーション)
- [インデックス](#インデックス)
- [マイグレーション](#マイグレーション)

---

## 概要

### データベースエンジン

- **開発環境**: SQLite（aiosqlite）
- **本番環境**: PostgreSQL推奨

### ORM

- **SQLAlchemy 2.0**（非同期対応）
- 宣言的マッピング（Declarative Base）
- 型安全な`Mapped`型を使用

### 接続情報

環境変数`DATABASE_URL`で設定

```ini
# 開発（SQLite）
DATABASE_URL=sqlite+aiosqlite:///./app.db

# 本番（PostgreSQL）
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
```

---

## ER図

```text
┌─────────────────┐
│     users       │
│─────────────────│
│ id (PK)         │
│ email           │
│ username        │
│ hashed_password │
│ is_active       │
│ is_superuser    │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────┴────┬─────────────────┐
    │         │                 │
    │         │                 │
┌───▼───────────┐       ┌───────▼──────┐
│   sessions    │       │    files     │
│───────────────│       │──────────────│
│ id (PK)       │       │ id (PK)      │
│ session_id    │       │ file_id      │
│ user_id (FK)  │       │ filename     │
│ metadata      │       │ original...  │
│ created_at    │       │ content_type │
│ updated_at    │       │ size         │
└───────┬───────┘       │ storage_path │
        │               │ user_id (FK) │
        │ 1:N           │ created_at   │
        │               └──────────────┘
┌───────▼───────┐
│   messages    │
│───────────────│
│ id (PK)       │
│ session_id(FK)│
│ role          │
│ content       │
│ tokens_used   │
│ model         │
│ created_at    │
└───────────────┘
```

---

## テーブル定義

### users（ユーザー）

ユーザーアカウント情報を管理するテーブル。

#### スキーマ

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|---|------|----------|------|
| id | UUID | NOT NULL | UUID_V4 | 主キー |
| email | VARCHAR(255) | NOT NULL | - | メールアドレス（一意） |
| username | VARCHAR(50) | NOT NULL | - | ユーザー名（一意） |
| hashed_password | VARCHAR(100) | NOT NULL | - | ハッシュ化されたパスワード |
| is_active | BOOLEAN | NOT NULL | TRUE | アカウント有効フラグ |
| is_superuser | BOOLEAN | NOT NULL | FALSE | 管理者フラグ |
| created_at | TIMESTAMP | NOT NULL | NOW() | 作成日時（UTC） |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新日時（UTC） |
| last_login_at | TIMESTAMP | NULL | - | 最終ログイン日時（UTC） |
| last_login_ip | VARCHAR(45) | NULL | - | 最終ログインIPアドレス（IPv6対応） |
| failed_login_attempts | INTEGER | NOT NULL | 0 | ログイン失敗回数 |
| locked_until | TIMESTAMP | NULL | - | アカウントロック解除日時 |
| refresh_token_hash | VARCHAR(100) | NULL | - | リフレッシュトークンハッシュ |
| refresh_token_expires_at | TIMESTAMP | NULL | - | リフレッシュトークン有効期限 |
| api_key_hash | VARCHAR(100) | NULL | - | APIキーハッシュ |
| api_key_created_at | TIMESTAMP | NULL | - | APIキー作成日時 |

#### インデックス

- PRIMARY KEY: `id`
- UNIQUE INDEX: `email`
- UNIQUE INDEX: `username`
- INDEX: `email`, `username`

#### 制約

- `email`: NOT NULL, UNIQUE, MAX_LENGTH=255
- `username`: NOT NULL, UNIQUE, MAX_LENGTH=50
- `hashed_password`: NOT NULL, MAX_LENGTH=100
- `last_login_ip`: IPv4/IPv6対応（最大45文字）
- `failed_login_attempts`: デフォルト0、アカウントロックに使用
- `api_key_hash`: インデックス付き

#### SQLAlchemyモデル

```python
class SampleUser(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sample_users"

    # PrimaryKeyMixinからid（UUID）を継承
    # TimestampMixinからcreated_at, updated_atを継承

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # セキュリティ監査フィールド
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    last_login_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, default=None)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # リフレッシュトークン関連
    refresh_token_hash: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # APIキー認証関連
    api_key_hash: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None, index=True)
    api_key_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    sessions: Mapped[list["SampleSession"]] = relationship("SampleSession", back_populates="user", cascade="all, delete-orphan")
```

#### サンプルデータ

```sql
INSERT INTO users (email, username, hashed_password, is_active, is_superuser)
VALUES ('user@example.com', 'testuser', '$2b$12$...', true, false);
```

---

### sessions（セッション）

AIエージェントとの会話セッションを管理するテーブル。

#### スキーマ

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|---|------|----------|------|
| id | UUID | NOT NULL | UUID_V4 | 主キー |
| session_id | VARCHAR(255) | NOT NULL | - | セッション識別子（一意） |
| user_id | UUID | NULL | - | ユーザーID（外部キー） |
| metadata | JSON | NULL | - | セッションメタデータ |
| created_at | TIMESTAMP | NOT NULL | NOW() | 作成日時（UTC） |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新日時（UTC） |

#### インデックス

- PRIMARY KEY: `id`
- UNIQUE INDEX: `session_id`
- INDEX: `session_id`
- FOREIGN KEY: `user_id` → `users.id` (CASCADE DELETE)

#### 制約

- `session_id`: NOT NULL, UNIQUE, MAX_LENGTH=255
- `user_id`: NULLABLE（ゲストユーザー対応）
- `metadata`: JSON形式

#### SQLAlchemyモデル

```python
class SampleSession(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sample_sessions"

    # PrimaryKeyMixinからid（UUID）を継承
    # TimestampMixinからcreated_at, updated_atを継承

    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sample_users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    session_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    user: Mapped["SampleUser | None"] = relationship("SampleUser", back_populates="sessions")
    messages: Mapped[list["SampleMessage"]] = relationship("SampleMessage", back_populates="session", cascade="all, delete-orphan")
```

#### サンプルデータ

```sql
INSERT INTO sessions (session_id, user_id, metadata)
VALUES ('session_abc123', 1, '{"location": "Tokyo"}');
```

---

### messages（メッセージ）

セッション内の個別の会話メッセージを管理するテーブル。

#### スキーマ

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|---|------|----------|------|
| id | UUID | NOT NULL | UUID_V4 | 主キー |
| session_id | UUID | NOT NULL | - | セッションID（外部キー） |
| role | VARCHAR(50) | NOT NULL | - | メッセージロール（user/assistant/system） |
| content | TEXT | NOT NULL | - | メッセージ内容 |
| tokens_used | INTEGER | NULL | - | 使用トークン数 |
| model | VARCHAR(100) | NULL | - | 使用モデル名 |
| created_at | TIMESTAMP | NOT NULL | NOW() | 作成日時（UTC） |

#### インデックス

- PRIMARY KEY: `id`
- FOREIGN KEY: `session_id` → `sessions.id` (CASCADE DELETE)
- INDEX: `session_id`, `created_at`

#### 制約

- `session_id`: NOT NULL
- `role`: NOT NULL, MAX_LENGTH=50, VALUES=('user', 'assistant', 'system')
- `content`: NOT NULL, TEXT
- `tokens_used`: NULLABLE, INTEGER
- `model`: NULLABLE, MAX_LENGTH=100

#### SQLAlchemyモデル

```python
class SampleMessage(Base, PrimaryKeyMixin):
    __tablename__ = "sample_messages"

    # PrimaryKeyMixinからid（UUID）を継承
    # created_atのみ（updated_atは不要）

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sample_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    session: Mapped["SampleSession"] = relationship("SampleSession", back_populates="messages")
```

#### サンプルデータ

```sql
INSERT INTO messages (session_id, role, content, tokens_used, model)
VALUES (1, 'user', 'こんにちは', NULL, NULL),
       (1, 'assistant', 'こんにちは！何かお手伝いできますか？', 150, 'gpt-4');
```

---

### files（ファイル）

アップロードされたファイルの情報を管理するテーブル。

#### スキーマ

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|---|------|----------|------|
| id | UUID | NOT NULL | UUID_V4 | 主キー |
| file_id | VARCHAR(255) | NOT NULL | - | ファイル識別子（一意） |
| filename | VARCHAR(255) | NOT NULL | - | 保存ファイル名 |
| filepath | VARCHAR(500) | NOT NULL | - | サーバー上のファイルパス |
| content_type | VARCHAR(100) | NOT NULL | - | MIMEタイプ |
| size | INTEGER | NOT NULL | - | ファイルサイズ（バイト） |
| user_id | UUID | NULL | - | ユーザーID（外部キー） |
| created_at | TIMESTAMP | NOT NULL | NOW() | 作成日時（UTC） |

#### インデックス

- PRIMARY KEY: `id`
- UNIQUE INDEX: `file_id`
- INDEX: `file_id`
- FOREIGN KEY: `user_id` → `users.id` (CASCADE DELETE)

#### 制約

- `file_id`: NOT NULL, UNIQUE, MAX_LENGTH=255
- `filename`: NOT NULL, MAX_LENGTH=255
- `filepath`: NOT NULL, MAX_LENGTH=500
- `size`: NOT NULL, INTEGER
- `content_type`: NOT NULL, MAX_LENGTH=100
- `user_id`: NULLABLE（ゲストユーザー対応）

#### SQLAlchemyモデル

```python
class SampleFile(Base, PrimaryKeyMixin):
    __tablename__ = "sample_files"

    # PrimaryKeyMixinからid（UUID）を継承
    # created_atのみ（updated_atは不要）

    file_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sample_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(500), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

#### サンプルデータ

```sql
INSERT INTO files (file_id, filename, original_filename, content_type, size, storage_path, user_id)
VALUES ('file_xyz789', '20251014_document.pdf', 'document.pdf', 'application/pdf', 1048576, 'uploads/20251014_document.pdf', 1);
```

---

## リレーション

### 一覧

| 親テーブル | 子テーブル | 関係 | CASCADE |
|----------|----------|------|---------|
| users | sessions | 1:N | DELETE |
| users | files | 1:N | DELETE |
| sessions | messages | 1:N | DELETE |

### 詳細

#### users → sessions

- **関係**: 1対多（1ユーザーは複数セッションを持つ）
- **外部キー**: `sessions.user_id` → `users.id`
- **CASCADE**: DELETE（ユーザー削除時、関連セッションも削除）
- **NULL許可**: `user_id`はNULL可能（ゲストユーザー対応）

#### users → files

- **関係**: 1対多（1ユーザーは複数ファイルを持つ）
- **外部キー**: `files.user_id` → `users.id`
- **CASCADE**: DELETE（ユーザー削除時、関連ファイルも削除）
- **NULL許可**: `user_id`はNULL可能（ゲストユーザー対応）

#### sessions → messages

- **関係**: 1対多（1セッションは複数メッセージを持つ）
- **外部キー**: `messages.session_id` → `sessions.id`
- **CASCADE**: DELETE（セッション削除時、関連メッセージも削除）
- **NULL許可**: 不可

---

## インデックス

### パフォーマンス最適化のためのインデックス

| テーブル | カラム | 種類 | 目的 |
|---------|-------|------|------|
| users | id | PRIMARY KEY | 主キー検索 |
| users | email | UNIQUE INDEX | メール検索・認証 |
| users | username | UNIQUE INDEX | ユーザー名検索 |
| sessions | id | PRIMARY KEY | 主キー検索 |
| sessions | session_id | UNIQUE INDEX | セッション識別子検索 |
| sessions | user_id | FOREIGN KEY INDEX | ユーザーセッション検索 |
| messages | id | PRIMARY KEY | 主キー検索 |
| messages | session_id | FOREIGN KEY INDEX | セッションメッセージ検索 |
| messages | created_at | INDEX | 時系列ソート |
| files | id | PRIMARY KEY | 主キー検索 |
| files | file_id | UNIQUE INDEX | ファイル識別子検索 |
| files | user_id | FOREIGN KEY INDEX | ユーザーファイル検索 |

### インデックス作成例

```sql
-- メール検索用インデックス
CREATE UNIQUE INDEX idx_users_email ON sample_users(email);

-- セッション識別子検索用インデックス
CREATE UNIQUE INDEX idx_sessions_session_id ON sessions(session_id);

-- メッセージ時系列検索用複合インデックス
CREATE INDEX idx_messages_session_created ON messages(session_id, created_at);
```

---

## マイグレーション

### Alembicの使用

このプロジェクトでは**Alembic**を使用してデータベースマイグレーションを管理します。

#### マイグレーションコマンド

```powershell
# マイグレーション作成
alembic revision --autogenerate -m "マイグレーション名"

# マイグレーション適用
alembic upgrade head

# マイグレーション取り消し
alembic downgrade -1

# 現在のバージョン確認
alembic current

# マイグレーション履歴
alembic history
```

#### 初期マイグレーション

```powershell
# 初回セットアップ
alembic init alembic

# 初期スキーマ作成
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### マイグレーションファイルの場所

```text
src/alembic/
├── versions/         # マイグレーションファイル
│   └── xxxxx_initial_schema.py
├── env.py           # Alembic環境設定
└── alembic.ini      # Alembic設定
```

---

## データベース初期化

### 開発環境

```powershell
# データベース作成
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# または
python -m app.main
```

### 本番環境

```powershell
# PostgreSQL接続文字列設定
$env:DATABASE_URL="postgresql+asyncpg://user:password@localhost/dbname"

# マイグレーション適用
alembic upgrade head
```

---

## クエリ例

### ユーザーの全セッション取得

```python
from sqlalchemy import select
from app.models.sample import SampleUser, SampleSession

# SQLAlchemy 2.0スタイル
stmt = select(SampleSession).where(SampleSession.user_id == user_id)
sessions = await db.execute(stmt)
result = sessions.scalars().all()
```

### セッションの全メッセージ取得

```python
from sqlalchemy import select
from app.models.sample import SampleMessage

stmt = select(SampleMessage).where(SampleMessage.session_id == session_id).order_by(SampleMessage.created_at)
messages = await db.execute(stmt)
result = messages.scalars().all()
```

### ユーザーのファイル一覧取得

```python
from sqlalchemy import select
from app.models.sample import SampleFile

stmt = select(SampleFile).where(SampleFile.user_id == user_id).order_by(SampleFile.created_at.desc())
files = await db.execute(stmt)
result = files.scalars().all()
```

---

## 参考リンク

- [SQLAlchemy 2.0ドキュメント](https://docs.sqlalchemy.org/en/20/)
- [Alembicドキュメント](https://alembic.sqlalchemy.org/)
- [PostgreSQL公式ドキュメント](https://www.postgresql.org/docs/)
- [SQLiteドキュメント](https://www.sqlite.org/docs.html)
