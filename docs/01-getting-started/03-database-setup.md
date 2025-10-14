# データベースセットアップガイド

このガイドでは、データベースの初期化、マイグレーション、管理方法について説明します。

## データベース概要

このプロジェクトでは以下のデータベース構成を使用します：

- **開発環境**: SQLite（ファイルベース、設定不要）
- **本番環境**: PostgreSQL（推奨）
- **ORM**: SQLAlchemy 2.0（非同期対応）
- **マイグレーション**: Alembic（将来実装予定）

## データベース初期化

### 自動初期化（推奨）

アプリケーション起動時に自動的にデータベースが初期化されます。

```bash
uv run ai-agent-app
```

起動時に以下の処理が実行されます：

1. データベース接続の確立
2. テーブルが存在しない場合は自動作成
3. 初期データの投入（設定されている場合）

**ログ出力例**:
```
Starting AI Agent App v0.1.0
Environment: development
Database: sqlite+aiosqlite:///./app.db
Database initialized
```

### 手動初期化

データベースを手動で初期化する場合：

```python
# Pythonインタラクティブシェルで実行
uv run python

>>> from app.database import init_db
>>> import asyncio
>>> asyncio.run(init_db())
>>> print("Database initialized")
```

または、スクリプトを作成：

```python
# scripts/init_db.py
import asyncio
from app.database import init_db

async def main():
    await init_db()
    print("Database initialized successfully")

if __name__ == "__main__":
    asyncio.run(main())
```

実行：
```bash
uv run python scripts/init_db.py
```

## データベーステーブル構成

現在のデータベーススキーマには以下のテーブルが含まれます：

### users テーブル

ユーザー情報を管理します。

| カラム名 | 型 | 説明 |
|----------|-----|------|
| id | INTEGER | 主キー（自動生成） |
| email | VARCHAR(255) | メールアドレス（ユニーク） |
| username | VARCHAR(50) | ユーザー名（ユニーク） |
| hashed_password | VARCHAR(255) | ハッシュ化されたパスワード |
| is_active | BOOLEAN | アクティブ状態 |
| is_superuser | BOOLEAN | 管理者権限 |
| created_at | DATETIME | 作成日時 |
| updated_at | DATETIME | 更新日時 |

```python
# モデル定義の例
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

### sessions テーブル

AI Agentのチャットセッションを管理します。

| カラム名 | 型 | 説明 |
|----------|-----|------|
| id | INTEGER | 主キー |
| user_id | INTEGER | ユーザーID（外部キー） |
| session_id | VARCHAR(255) | セッションID（ユニーク） |
| title | VARCHAR(255) | セッションタイトル |
| created_at | DATETIME | 作成日時 |
| updated_at | DATETIME | 更新日時 |

### files テーブル

アップロードされたファイルを管理します。

| カラム名 | 型 | 説明 |
|----------|-----|------|
| id | INTEGER | 主キー |
| user_id | INTEGER | ユーザーID（外部キー） |
| filename | VARCHAR(255) | ファイル名 |
| content_type | VARCHAR(100) | MIMEタイプ |
| size | INTEGER | ファイルサイズ（バイト） |
| storage_path | VARCHAR(500) | ストレージパス |
| created_at | DATETIME | 作成日時 |

### messages テーブル

チャットメッセージの履歴を管理します。

| カラム名 | 型 | 説明 |
|----------|-----|------|
| id | INTEGER | 主キー |
| session_id | INTEGER | セッションID（外部キー） |
| role | VARCHAR(50) | メッセージの役割（user/assistant） |
| content | TEXT | メッセージ内容 |
| created_at | DATETIME | 作成日時 |

## Alembic マイグレーション（準備中）

現在、このプロジェクトではSQLAlchemyの`create_all()`を使用していますが、
本番環境ではAlembicを使用したマイグレーション管理を推奨します。

### Alembicのセットアップ（将来実装予定）

#### 1. Alembicの初期化

```bash
# Alembicディレクトリの作成
uv run alembic init alembic
```

これにより以下のファイルが作成されます：
```
backend/
├── alembic/
│   ├── versions/          # マイグレーションファイル
│   ├── env.py            # Alembic環境設定
│   └── script.py.mako    # マイグレーションテンプレート
└── alembic.ini            # Alembic設定ファイル
```

#### 2. 設定ファイルの編集

`alembic/env.py`を編集して、アプリケーションの設定を使用するようにします：

```python
# alembic/env.py
from app.database import Base
from app.config import settings
from app.models import *  # すべてのモデルをインポート

# データベースURL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# メタデータの設定
target_metadata = Base.metadata
```

#### 3. 初回マイグレーションの作成

既存のモデルから初回マイグレーションを作成：

```bash
uv run alembic revision --autogenerate -m "Initial migration"
```

#### 4. マイグレーションの適用

```bash
# 最新バージョンまでマイグレーション
uv run alembic upgrade head

# 特定のバージョンまでマイグレーション
uv run alembic upgrade <revision_id>

# 1つ前のバージョンにロールバック
uv run alembic downgrade -1
```

### マイグレーション作成の流れ

#### ステップ1: モデルの変更

```python
# src/app/models/user.py
class User(Base):
    __tablename__ = "users"

    # 新しいカラムを追加
    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )
```

#### ステップ2: マイグレーションの自動生成

```bash
uv run alembic revision --autogenerate -m "Add phone_number to users"
```

これにより`alembic/versions/`に新しいマイグレーションファイルが作成されます：

```python
# alembic/versions/xxxx_add_phone_number_to_users.py
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')
```

#### ステップ3: マイグレーションの確認と編集

自動生成されたマイグレーションを確認し、必要に応じて手動で編集します。

#### ステップ4: マイグレーションの適用

```bash
# 本番適用前にテスト環境で確認
uv run alembic upgrade head
```

### マイグレーションのベストプラクティス

#### 1. 常にバックアップを取る

```bash
# SQLiteの場合
cp app.db app.db.backup

# PostgreSQLの場合
pg_dump -U username database_name > backup.sql
```

#### 2. マイグレーションは小さく保つ

```bash
# 悪い例: 複数の変更を1つのマイグレーションに
alembic revision -m "Add columns, create indexes, update constraints"

# 良い例: 1つの変更ごとにマイグレーション
alembic revision -m "Add phone_number column to users"
alembic revision -m "Add index on email column"
```

#### 3. マイグレーションのテスト

```bash
# アップグレード
alembic upgrade head

# ダウングレード（ロールバック）
alembic downgrade -1

# 再度アップグレード
alembic upgrade head
```

#### 4. 本番環境での適用

```bash
# ステージング環境でテスト
ENVIRONMENT=staging alembic upgrade head

# 問題なければ本番環境へ
ENVIRONMENT=production alembic upgrade head
```

## データベース接続設定

### SQLite（開発環境）

`.env`ファイル:
```bash
DATABASE_URL=sqlite+aiosqlite:///./app.db
```

特徴：
- ファイルベース、設定不要
- 単一ファイル（`app.db`）
- 開発・テストに最適
- 並行接続数に制限あり

### PostgreSQL（本番環境）

`.env`ファイル:
```bash
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/dbname
```

PostgreSQLのインストールと設定:

```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# データベースとユーザーの作成
sudo -u postgres psql
CREATE DATABASE ai_agent_app;
CREATE USER aiagent WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ai_agent_app TO aiagent;
```

## データベース管理コマンド

### データベースのリセット

```python
# scripts/reset_db.py
import asyncio
from app.database import engine, Base

async def reset_database():
    # すべてのテーブルを削除
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # テーブルを再作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database reset completed")

if __name__ == "__main__":
    asyncio.run(reset_database())
```

実行：
```bash
uv run python scripts/reset_db.py
```

### データベースのバックアップ

```bash
# SQLite
cp app.db backups/app.db.$(date +%Y%m%d_%H%M%S)

# PostgreSQL
pg_dump -U username database_name > backup_$(date +%Y%m%d_%H%M%S).sql
```

### データベースのリストア

```bash
# SQLite
cp backups/app.db.20250101_120000 app.db

# PostgreSQL
psql -U username database_name < backup_20250101_120000.sql
```

## トラブルシューティング

### データベースファイルが見つからない

```
Error: unable to open database file
```

**解決方法**:
- カレントディレクトリを確認
- `DATABASE_URL`のパスが正しいか確認
- ディレクトリの書き込み権限を確認

### マイグレーションの競合

```
Error: Multiple heads detected
```

**解決方法**:
```bash
# 現在の状態を確認
alembic heads

# マージマイグレーションを作成
alembic merge heads -m "Merge multiple heads"
```

### データベース接続エラー

```
Error: Could not connect to database
```

**解決方法**:
1. データベースサーバーが起動しているか確認
2. 接続情報（ホスト、ポート、ユーザー名、パスワード）が正しいか確認
3. ファイアウォール設定を確認

### テーブルが存在しない

```
Error: no such table: users
```

**解決方法**:
```bash
# データベースを初期化
uv run python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

## 次のステップ

データベースのセットアップが完了したら、以下のドキュメントを参照してください：

- [プロジェクト構造](../02-architecture/01-project-structure.md) - モデルとリポジトリの配置
- [データベース設計](../03-core-concepts/02-database-design.md) - モデル定義の詳細
- [レイヤードアーキテクチャ](../02-architecture/02-layered-architecture.md) - データアクセス層の理解
