# マイグレーション戦略（Migration Strategy）

## 📋 文書管理情報

| 項目 | 内容 |
|------|------|
| **文書名** | マイグレーション戦略（Migration Strategy） |
| **バージョン** | 1.0.0 |
| **作成日** | 2025-01-11 |
| **最終更新日** | 2025-01-11 |
| **作成者** | Claude Code |
| **レビュー状態** | 初版 |

---

## 📑 目次

1. [概要](#1-概要)
2. [Alembic設定](#2-alembic設定)
3. [マイグレーションファイル管理](#3-マイグレーションファイル管理)
4. [マイグレーション実行](#4-マイグレーション実行)
5. [ロールバック戦略](#5-ロールバック戦略)
6. [環境別マイグレーション](#6-環境別マイグレーション)
7. [データマイグレーション](#7-データマイグレーション)
8. [ベストプラクティス](#8-ベストプラクティス)
9. [トラブルシューティング](#9-トラブルシューティング)
10. [付録](#10-付録)

---

## 1. 概要

### 1.1 目的

本設計書は、genai-app-docs（camp-backend）プロジェクトのデータベーススキーママイグレーション戦略を文書化し、以下を達成することを目的とします：

- **スキーマ変更の管理**: バージョン管理されたマイグレーションファイル
- **安全なデプロイ**: Blue-Green/Rolling Updateに対応したマイグレーション
- **ロールバック対応**: マイグレーション失敗時の復旧手順
- **環境間整合性**: 開発・ステージング・本番環境の一貫性

### 1.2 適用範囲

本設計書は以下を対象とします：

- ✅ Alembic設定とディレクトリ構造
- ✅ マイグレーションファイルの作成・管理
- ✅ マイグレーション実行手順（upgrade/downgrade）
- ✅ データマイグレーション戦略
- ✅ 環境別マイグレーション手順
- ✅ ロールバック戦略

以下は**対象外**とし、別の設計書で詳述します：

- ❌ テーブル設計の詳細 → [Database設計書](./01-database-design.md)
- ❌ ER図 → [ER図詳細](./02-er-diagram.md)
- ❌ デプロイメント手順 → [Deployment設計書](../06-operations/01-deployment-design.md)

### 1.3 使用技術

| 技術 | バージョン | 用途 |
|------|----------|------|
| **Alembic** | 1.13+ | データベースマイグレーションツール |
| **SQLAlchemy** | 2.0+ | ORM、非同期対応 |
| **PostgreSQL** | 14+ | RDBMS |
| **asyncpg** | 0.30+ | PostgreSQL非同期ドライバ |

---

## 2. Alembic設定

### 2.1 ディレクトリ構造

```text
src/
├── alembic/
│   ├── versions/              # マイグレーションファイル
│   │   ├── 001_add_azure_oid_to_sample_users.py
│   │   ├── 002_add_analysis_tables.py
│   │   ├── 003_add_driver_tree_tables.py
│   │   ├── 004_refactor_driver_tree_to_true_tree.py
│   │   └── 856dac83d2e3_add_analysis_template_tables.py
│   ├── env.py                 # Alembic環境設定
│   ├── script.py.mako         # マイグレーションテンプレート
│   └── README                 # Alembicディレクトリ説明
├── alembic.ini                # Alembic設定ファイル
└── app/
    └── models/                # SQLAlchemyモデル
```

### 2.2 alembic.ini設定

**ファイル**: `src/alembic.ini`

```ini
[alembic]
# マイグレーションスクリプトの場所
script_location = %(here)s/alembic

# sys.pathに追加するパス
prepend_sys_path = .

# パス区切り文字（OS依存）
path_separator = os

# データベースURL（env.pyで動的設定）
# sqlalchemy.url はenv.pyでsettings.DATABASE_URLから設定される

[loggers]
keys = root,sqlalchemy,alembic

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

**重要な設定**:

- `script_location`: マイグレーションスクリプトの場所（`src/alembic`）
- `prepend_sys_path = .`: 現在のディレクトリをsys.pathに追加（app.modelsをimport可能に）
- データベースURLは`env.py`で動的に設定（`settings.DATABASE_URL`から取得）

### 2.3 env.py設定

**ファイル**: `src/alembic/env.py`

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# アプリケーション設定とモデルをimport
from app.core.config import settings
from app.models.base import Base

# Alembic設定オブジェクト
config = context.config

# データベースURLを動的に設定
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ロギング設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# メタデータ設定（autogenerate用）
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """オフラインモードでマイグレーション実行（SQL出力のみ）"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """非同期モードでマイグレーション実行"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # マイグレーション時はコネクションプール不要
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection: Connection) -> None:
    """コネクション内でマイグレーション実行"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """オンラインモードでマイグレーション実行（実DBに適用）"""
    asyncio.run(run_async_migrations())


# モード判定
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**特徴**:

- **非同期対応**: `async_engine_from_config`と`asyncio.run`を使用
- **動的URL設定**: `settings.DATABASE_URL`から環境変数を読み込み
- **NullPool**: マイグレーション時はコネクションプールを無効化（リソース節約）
- **オフライン/オンラインモード**: SQL出力のみ or 実DB適用を選択可能

---

## 3. マイグレーションファイル管理

### 3.1 マイグレーションファイルの命名規則

Alembicは以下の命名規則を使用します：

```text
<revision_id>_<slug>.py

例:
001_add_azure_oid_to_sample_users.py        # カスタムrevision_id
002_add_analysis_tables.py
856dac83d2e3_add_analysis_template_tables.py  # 自動生成revision_id
```

**推奨命名規則**:

- **連番を使用**: `001_`, `002_`, `003_` でマイグレーション順序を明示
- **スラッグは動詞_名詞形式**: `add_table`, `modify_column`, `drop_index`
- **説明的な名前**: 何を変更するのかが一目でわかるように

### 3.2 マイグレーションファイルの構造

```python
"""add_analysis_tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """スキーマ変更を適用"""
    # テーブル作成
    op.create_table(
        'analysis_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_name', sa.String(255), nullable=True),
        # ... その他のカラム
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )

    # インデックス作成
    op.create_index(
        'idx_analysis_sessions_project',
        'analysis_sessions',
        ['project_id']
    )


def downgrade() -> None:
    """スキーマ変更をロールバック"""
    # インデックス削除
    op.drop_index('idx_analysis_sessions_project', table_name='analysis_sessions')

    # テーブル削除
    op.drop_table('analysis_sessions')
```

**重要な要素**:

- **revision**: 現在のマイグレーションID
- **down_revision**: 親マイグレーションID（依存関係）
- **upgrade()**: スキーマ変更を適用する関数
- **downgrade()**: スキーマ変更を元に戻す関数

### 3.3 マイグレーションファイルの作成

#### 3.3.1 自動生成（推奨）

```bash
# モデルの変更を自動検出してマイグレーションファイル生成
alembic revision --autogenerate -m "add_user_profile_table"
```

**出力例**:

```text
Generating C:\developments\genai-app-docs\src\alembic\versions\abc123def456_add_user_profile_table.py ... done
```

**autogenerate の検出内容**:

- ✅ テーブルの追加/削除
- ✅ カラムの追加/削除
- ✅ インデックスの追加/削除
- ✅ 外部キーの追加/削除
- ❌ カラム名の変更（削除+追加として検出される）
- ❌ テーブル名の変更（削除+追加として検出される）

#### 3.3.2 手動作成

```bash
# 空のマイグレーションファイルを生成
alembic revision -m "add_custom_constraint"
```

**手動作成が必要なケース**:

- カラム/テーブルのリネーム
- データマイグレーション
- 複雑なSQL操作

#### 3.3.3 連番マイグレーションの作成

**カスタムrevision_id（連番）を使用**:

```bash
# revision_idを指定してマイグレーションファイル生成
alembic revision --rev-id 005 --autogenerate -m "add_notification_system"
```

### 3.4 マイグレーション依存関係

```mermaid
graph LR
    Base[Base<br/>初期状態] --> R001[001<br/>add_azure_oid]
    R001 --> R002[002<br/>add_analysis_tables]
    R002 --> R003[003<br/>add_driver_tree_tables]
    R003 --> R004[004<br/>refactor_driver_tree]
    R004 --> R005[856dac...<br/>add_templates]

    style Base fill:#e3f2fd
    style R005 fill:#c8e6c9
```

**依存関係の定義**:

```python
revision = '002'
down_revision = '001'  # 001を親とする
```

**注意点**:

- すべてのマイグレーションは線形チェーンを形成
- ブランチマージは避ける（複雑性増大のため）
- 複数開発者が同時にマイグレーション作成時は注意

---

## 4. マイグレーション実行

### 4.1 基本コマンド

#### 4.1.1 現在のバージョン確認

```bash
alembic current
```

**出力例**:

```text
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
004 (head)
```

#### 4.1.2 最新バージョンへアップグレード

```bash
alembic upgrade head
```

**出力例**:

```text
INFO  [alembic.runtime.migration] Running upgrade 003 -> 004, refactor_driver_tree_to_true_tree
INFO  [alembic.runtime.migration] Running upgrade 004 -> 856dac83d2e3, add_analysis_template_tables
```

#### 4.1.3 特定バージョンへアップグレード

```bash
alembic upgrade 003
```

#### 4.1.4 1つ先のバージョンへアップグレード

```bash
alembic upgrade +1
```

#### 4.1.5 1つ前のバージョンへダウングレード

```bash
alembic downgrade -1
```

#### 4.1.6 特定バージョンへダウングレード

```bash
alembic downgrade 002
```

#### 4.1.7 初期状態へ完全ロールバック

```bash
alembic downgrade base
```

**警告**: すべてのテーブルが削除されます！

### 4.2 マイグレーション履歴の確認

#### 4.2.1 履歴表示

```bash
alembic history
```

**出力例**:

```text
001 -> 002 (head), add_azure_oid_to_sample_users
002 -> 003, add_analysis_tables
003 -> 004, add_driver_tree_tables
004 -> 856dac83d2e3, refactor_driver_tree_to_true_tree
856dac83d2e3 -> (head), add_analysis_template_tables
```

#### 4.2.2 詳細履歴表示

```bash
alembic history --verbose
```

### 4.3 SQL出力（ドライラン）

```bash
# アップグレードSQLを出力（実行しない）
alembic upgrade head --sql

# ダウングレードSQLを出力（実行しない）
alembic downgrade -1 --sql
```

**用途**:

- マイグレーション内容の事前確認
- DBアクセス権限がない場合の手動実行用SQL取得
- レビュープロセスでの変更内容確認

---

## 5. ロールバック戦略

### 5.1 ロールバックの基本方針

| シナリオ | ロールバック方法 | データ損失 |
|---------|----------------|-----------|
| **マイグレーション失敗** | 自動ロールバック（トランザクション） | なし |
| **アプリケーション不具合** | `alembic downgrade -1` | 場合による |
| **データ不整合** | 手動修正 + downgrade | 場合による |
| **緊急ロールバック** | Blue-Green切り替え | なし |

### 5.2 段階的ロールバック手順

```mermaid
flowchart TD
    Start[マイグレーション適用] --> Check{正常動作？}

    Check -->|Yes| Success[✅ 完了]
    Check -->|No| Severity{重要度}

    Severity -->|Critical| Emergency[緊急ロールバック]
    Severity -->|Major| Planned[計画ロールバック]
    Severity -->|Minor| Fix[修正マイグレーション]

    Emergency --> BlueGreen[Blue-Green切り替え]
    BlueGreen --> Downgrade1[alembic downgrade -1]

    Planned --> Downgrade2[alembic downgrade -1]
    Downgrade2 --> Verify[動作確認]

    Fix --> NewMigration[新マイグレーション作成]
    NewMigration --> Apply[適用]

    Verify --> Deploy[再デプロイ]

    style Success fill:#c8e6c9
    style Emergency fill:#ffccbc
    style BlueGreen fill:#fff9c4
```

### 5.3 ロールバック実行例

#### 5.3.1 1つ前のバージョンへロールバック

```bash
# 現在のバージョン確認
alembic current
# 出力: 004 (head)

# 1つ前のバージョンへダウングレード
alembic downgrade -1

# 確認
alembic current
# 出力: 003
```

#### 5.3.2 特定バージョンへロールバック

```bash
# バージョン002へロールバック
alembic downgrade 002

# 確認
alembic current
# 出力: 002
```

### 5.4 データ損失を伴うロールバック

**注意**: 以下の操作はデータ損失を伴います！

#### カラム削除のロールバック

```python
def upgrade() -> None:
    """新カラム追加"""
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))


def downgrade() -> None:
    """カラム削除（データ損失）"""
    op.drop_column('users', 'phone_number')
    # ⚠️ phone_numberのデータは完全に失われる
```

**対策**: データバックアップ + 段階的削除

```python
# Step 1: カラムをNULLABLE化（マイグレーション001）
def upgrade() -> None:
    op.alter_column('users', 'phone_number', nullable=True)

# Step 2: アプリケーションコードからカラム参照を削除（デプロイ）

# Step 3: カラム削除（マイグレーション002、数日後）
def upgrade() -> None:
    op.drop_column('users', 'phone_number')
```

---

## 6. 環境別マイグレーション

### 6.1 環境一覧

| 環境 | データベース | マイグレーションタイミング |
|------|------------|----------------------|
| **開発環境（local）** | PostgreSQL (Docker) | 開発者が随時実行 |
| **ステージング環境（staging）** | Azure PostgreSQL | CI/CDパイプラインで自動実行 |
| **本番環境（production）** | Azure PostgreSQL | デプロイ前に手動/自動実行 |

### 6.2 開発環境マイグレーション

#### 6.2.1 初回セットアップ

```bash
# PostgreSQLコンテナ起動
docker-compose up -d postgres

# 環境変数設定
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/genai_app"

# マイグレーション実行
alembic upgrade head

# サンプルデータ投入
python scripts/seed_data.py
```

#### 6.2.2 モデル変更後のマイグレーション

```bash
# 1. モデル変更（例: app/models/user.pyにphone_numberカラム追加）

# 2. マイグレーションファイル自動生成
alembic revision --rev-id 006 --autogenerate -m "add_phone_number_to_users"

# 3. 生成されたマイグレーションファイルを確認
# src/alembic/versions/006_add_phone_number_to_users.py

# 4. マイグレーション適用
alembic upgrade head

# 5. 動作確認
python scripts/test_user_phone.py
```

#### 6.2.3 開発データベースのリセット

```bash
# 方法1: Alembicで完全ロールバック + アップグレード
alembic downgrade base
alembic upgrade head

# 方法2: PostgreSQLコンテナ再作成
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

### 6.3 ステージング環境マイグレーション

#### 6.3.1 CI/CDパイプライン統合

**GitHub Actions例**:

```yaml
name: Deploy to Staging

on:
  push:
    branches: [staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run Database Migration
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
        run: |
          cd src
          alembic upgrade head

      - name: Deploy Application
        run: |
          # Azure Web Appへデプロイ
          az webapp deploy ...
```

#### 6.3.2 マイグレーション前チェック

```bash
# ステージング環境のバージョン確認
DATABASE_URL=$STAGING_DATABASE_URL alembic current

# アップグレードSQL確認（ドライラン）
DATABASE_URL=$STAGING_DATABASE_URL alembic upgrade head --sql

# 実際のアップグレード
DATABASE_URL=$STAGING_DATABASE_URL alembic upgrade head
```

### 6.4 本番環境マイグレーション

#### 6.4.1 Blue-Green Deployment対応マイグレーション

**原則**: マイグレーションは**後方互換性**を保つ

```mermaid
sequenceDiagram
    participant Old as Blue Env<br/>(v1.0.0)
    participant DB as Database
    participant New as Green Env<br/>(v1.1.0)

    Note over DB: 現在のスキーマ

    New->>DB: マイグレーション実行<br/>(後方互換)
    Note over DB: 新スキーマ<br/>（v1.0.0も動作可能）

    Old->>DB: 旧バージョンで動作確認<br/>（引き続き正常動作）

    New->>DB: 新バージョンで動作確認<br/>（新機能も動作）

    Note over Old,New: トラフィック切り替え

    Old->>New: トラフィック: Blue → Green

    Note over Old: Blueは待機状態
```

**後方互換性のあるマイグレーション例**:

```python
# Good: カラム追加（NULL可能）
def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))
    # 旧バージョンのアプリケーションはphone_numberを無視して動作可能

# Bad: NOT NULL制約のカラム追加
def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=False))
    # 旧バージョンのアプリケーションはINSERT時にエラー
```

#### 6.4.2 本番マイグレーション手順

```bash
# 1. バックアップ取得
pg_dump -h $PROD_DB_HOST -U $PROD_DB_USER -d genai_app > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. メンテナンスウィンドウ確保（オプション）
# - Blue-Green Deploymentの場合は不要
# - 大規模マイグレーションの場合は確保

# 3. マイグレーション前確認
DATABASE_URL=$PROD_DATABASE_URL alembic current
DATABASE_URL=$PROD_DATABASE_URL alembic history

# 4. ドライラン
DATABASE_URL=$PROD_DATABASE_URL alembic upgrade head --sql > migration.sql

# 5. SQL内容レビュー
cat migration.sql

# 6. マイグレーション実行
DATABASE_URL=$PROD_DATABASE_URL alembic upgrade head

# 7. バージョン確認
DATABASE_URL=$PROD_DATABASE_URL alembic current

# 8. アプリケーション動作確認
curl https://api.example.com/health

# 9. モニタリング確認
# - Grafanaダッシュボード
# - アプリケーションログ
# - エラー率
```

---

## 7. データマイグレーション

### 7.1 データマイグレーションの種類

| 種類 | 説明 | 例 |
|------|------|---|
| **型変換** | カラムのデータ型変更 | String → Integer |
| **デフォルト値設定** | 既存レコードにデフォルト値設定 | NULL → 空文字列 |
| **データ移動** | カラム間/テーブル間のデータ移動 | full_name → first_name + last_name |
| **データ正規化** | 非正規化データの正規化 | JSON → 正規化テーブル |

### 7.2 データマイグレーションパターン

#### 7.2.1 既存データへのデフォルト値設定

```python
def upgrade() -> None:
    # カラム追加（NULL可能）
    op.add_column('users', sa.Column('status', sa.String(20), nullable=True))

    # 既存レコードにデフォルト値を設定
    op.execute("""
        UPDATE users
        SET status = 'active'
        WHERE status IS NULL
    """)

    # NOT NULL制約を追加
    op.alter_column('users', 'status', nullable=False)
```

#### 7.2.2 データ型変換

```python
def upgrade() -> None:
    # 一時カラム作成（新しい型）
    op.add_column('orders', sa.Column('amount_new', sa.Numeric(10, 2), nullable=True))

    # データ変換
    op.execute("""
        UPDATE orders
        SET amount_new = CAST(amount_old AS NUMERIC(10, 2))
    """)

    # 旧カラム削除
    op.drop_column('orders', 'amount_old')

    # 新カラムをリネーム
    op.alter_column('orders', 'amount_new', new_column_name='amount')
```

#### 7.2.3 データ分割（full_name → first_name + last_name）

```python
def upgrade() -> None:
    # 新カラム追加
    op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))

    # データ分割（PostgreSQL string_to_array関数使用）
    op.execute("""
        UPDATE users
        SET
            first_name = SPLIT_PART(full_name, ' ', 1),
            last_name = SPLIT_PART(full_name, ' ', 2)
        WHERE full_name IS NOT NULL
    """)

    # full_nameカラムは保持（後方互換性のため）


def downgrade() -> None:
    # データ結合
    op.execute("""
        UPDATE users
        SET full_name = CONCAT(first_name, ' ', last_name)
        WHERE first_name IS NOT NULL AND last_name IS NOT NULL
    """)

    # 新カラム削除
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
```

### 7.3 大規模データマイグレーション

#### 7.3.1 バッチ処理

```python
def upgrade() -> None:
    connection = op.get_bind()

    # バッチサイズ
    batch_size = 1000
    offset = 0

    while True:
        # バッチ取得
        result = connection.execute(
            sa.text("""
                SELECT id, old_data
                FROM large_table
                ORDER BY id
                LIMIT :limit OFFSET :offset
            """),
            {"limit": batch_size, "offset": offset}
        )

        rows = result.fetchall()
        if not rows:
            break  # データ終了

        # データ変換
        for row in rows:
            new_data = transform_data(row.old_data)
            connection.execute(
                sa.text("""
                    UPDATE large_table
                    SET new_data = :new_data
                    WHERE id = :id
                """),
                {"new_data": new_data, "id": row.id}
            )

        offset += batch_size

        # 進捗ログ
        print(f"Processed {offset} records...")
```

#### 7.3.2 インデックス無効化→再作成

```python
def upgrade() -> None:
    # 1. インデックス削除（更新を高速化）
    op.drop_index('idx_users_email', table_name='users')

    # 2. 大量データ更新
    op.execute("""
        UPDATE users
        SET email = LOWER(email)
    """)

    # 3. インデックス再作成
    op.create_index('idx_users_email', 'users', ['email'])
```

---

## 8. ベストプラクティス

### 8.1 マイグレーション設計の原則

#### 8.1.1 小さく頻繁なマイグレーション

```text
❌ Bad: 1つのマイグレーションで10個のテーブルを作成
✅ Good: 1つのマイグレーションで1~2個のテーブルを作成
```

**理由**:

- レビューが容易
- ロールバックが安全
- コンフリクトが少ない

#### 8.1.2 後方互換性の維持

```text
❌ Bad: カラム削除（アプリケーションが即座にエラー）
✅ Good: カラム追加（NULL可能） → アプリケーション更新 → カラム削除
```

**3段階リリース**:

1. **マイグレーション1**: 新カラム追加（NULL可能）
2. **アプリケーション更新**: 新カラムを使用開始、旧カラムも読み込み
3. **マイグレーション2**: 旧カラム削除（数日後）

#### 8.1.3 downgrade()の実装

```text
❌ Bad: downgrade()が未実装（pass）
✅ Good: downgrade()で完全なロールバックが可能
```

**例外**: データ損失を伴う場合はコメントで明示

```python
def downgrade() -> None:
    # ⚠️ Warning: この操作はphone_numberカラムのデータを完全に失います
    op.drop_column('users', 'phone_number')
```

### 8.2 マイグレーションのテスト

#### 8.2.1 ローカルテスト

```bash
# 1. テスト用DBを作成
createdb genai_app_test

# 2. マイグレーション適用
DATABASE_URL="postgresql+asyncpg://localhost/genai_app_test" alembic upgrade head

# 3. ロールバックテスト
DATABASE_URL="postgresql+asyncpg://localhost/genai_app_test" alembic downgrade base

# 4. 再適用
DATABASE_URL="postgresql+asyncpg://localhost/genai_app_test" alembic upgrade head

# 5. DBクリーンアップ
dropdb genai_app_test
```

#### 8.2.2 CI/CDでの自動テスト

```yaml
# .github/workflows/test-migrations.yml
name: Test Migrations

on: [pull_request]

jobs:
  test-migrations:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

    steps:
      - uses: actions/checkout@v4

      - name: Test upgrade
        run: |
          export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/test"
          cd src
          alembic upgrade head

      - name: Test downgrade
        run: |
          export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/test"
          cd src
          alembic downgrade base

      - name: Test re-upgrade
        run: |
          export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/test"
          cd src
          alembic upgrade head
```

### 8.3 マイグレーションのレビュー

#### 8.3.1 レビューチェックリスト

- [ ] `upgrade()`と`downgrade()`の両方が実装されているか
- [ ] 後方互換性が保たれているか
- [ ] データ損失のリスクが明示されているか
- [ ] インデックスが適切に作成されているか
- [ ] 外部キー制約のカスケード動作が適切か
- [ ] トランザクション境界が適切か
- [ ] 大規模データの場合、バッチ処理が使用されているか

#### 8.3.2 レビュー時の確認SQL

```bash
# マイグレーションのSQL出力
alembic upgrade head --sql > review.sql

# SQL内容を確認
cat review.sql
```

---

## 9. トラブルシューティング

### 9.1 よくある問題と解決策

#### 9.1.1 "Target database is not up to date"

**症状**:

```text
alembic.util.exc.CommandError: Target database is not up to date.
```

**原因**: alembic_versionテーブルのバージョンとマイグレーションファイルが不一致

**解決策**:

```bash
# 現在のDBバージョン確認
alembic current

# 履歴確認
alembic history

# 強制的にバージョンスタンプ
alembic stamp head
```

#### 9.1.2 "Can't locate revision identified by '...'"

**症状**:

```text
alembic.script.revision.ResolutionError: Can't locate revision identified by '003'
```

**原因**: マイグレーションファイルが削除されたか、down_revisionの参照が壊れている

**解決策**:

```bash
# 履歴確認
alembic history

# マイグレーションファイルの整合性確認
ls src/alembic/versions/

# 必要に応じて手動でalembic_versionテーブル修正
psql -h localhost -d genai_app -c "UPDATE alembic_version SET version_num='002'"
```

#### 9.1.3 マイグレーション中のロック

**症状**:

```text
psycopg2.errors.LockNotAvailable: could not obtain lock on relation "users"
```

**原因**: 他のトランザクションがテーブルをロック中

**解決策**:

```bash
# アクティブな接続確認
psql -h localhost -d genai_app -c "SELECT * FROM pg_stat_activity WHERE state='active'"

# ロック確認
psql -h localhost -d genai_app -c "SELECT * FROM pg_locks WHERE NOT granted"

# 必要に応じて接続終了
psql -h localhost -d genai_app -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <PID>"

# マイグレーション再実行
alembic upgrade head
```

### 9.2 緊急時の手動修正

#### 9.2.1 alembic_versionテーブルの手動修正

```sql
-- 現在のバージョン確認
SELECT * FROM alembic_version;

-- バージョン更新
UPDATE alembic_version SET version_num='004';

-- バージョン挿入（テーブルが空の場合）
INSERT INTO alembic_version (version_num) VALUES ('004');
```

#### 9.2.2 部分的マイグレーション適用後の修正

```bash
# マイグレーションが途中で失敗した場合

# 1. 現在の状態確認
alembic current

# 2. 失敗したマイグレーションのSQLを手動確認
alembic upgrade +1 --sql

# 3. 手動でSQLを実行（失敗した箇所から）
psql -h localhost -d genai_app -f fix.sql

# 4. バージョンスタンプ更新
alembic stamp head
```

---

## 10. 付録

### 10.1 Alembicコマンドリファレンス

| コマンド | 説明 | 例 |
|---------|------|---|
| `alembic init` | Alembic初期化 | `alembic init alembic` |
| `alembic revision` | 空のマイグレーション作成 | `alembic revision -m "add_column"` |
| `alembic revision --autogenerate` | 自動マイグレーション生成 | `alembic revision --autogenerate -m "auto"` |
| `alembic upgrade` | アップグレード | `alembic upgrade head` |
| `alembic downgrade` | ダウングレード | `alembic downgrade -1` |
| `alembic current` | 現在のバージョン表示 | `alembic current` |
| `alembic history` | 履歴表示 | `alembic history --verbose` |
| `alembic stamp` | バージョンスタンプ | `alembic stamp head` |
| `alembic show` | マイグレーション内容表示 | `alembic show 003` |

### 10.2 スクリプト例

#### 10.2.1 マイグレーション実行スクリプト

**scripts/migrate.sh**:

```bash
#!/bin/bash
set -e

echo "=== Database Migration ==="

# 環境変数チェック
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL is not set"
    exit 1
fi

# 現在のバージョン確認
echo "Current version:"
alembic current

# マイグレーション実行
echo "Running migrations..."
alembic upgrade head

# 最終バージョン確認
echo "Final version:"
alembic current

echo "=== Migration Complete ==="
```

#### 10.2.2 ロールバックスクリプト

**scripts/rollback.sh**:

```bash
#!/bin/bash
set -e

echo "=== Database Rollback ==="

# 引数チェック
if [ -z "$1" ]; then
    echo "Usage: $0 <target_revision>"
    echo "Example: $0 003"
    exit 1
fi

TARGET=$1

# バックアップ作成
echo "Creating backup..."
pg_dump $DATABASE_URL > "backup_$(date +%Y%m%d_%H%M%S).sql"

# ロールバック実行
echo "Rolling back to $TARGET..."
alembic downgrade $TARGET

# 最終バージョン確認
echo "Current version:"
alembic current

echo "=== Rollback Complete ==="
```

### 10.3 関連設計書

| 設計書 | 関連箇所 |
|-------|---------|
| [Database設計書](./01-database-design.md) | テーブル定義、制約 |
| [ER図詳細](./02-er-diagram.md) | エンティティリレーションシップ |
| [Deployment設計書](../06-operations/01-deployment-design.md) | デプロイメント手順 |
| [Infrastructure設計書](../05-infrastructure/01-infrastructure-design.md) | データベース環境設定 |

### 10.4 参考リンク

#### 公式ドキュメント

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

#### ベストプラクティス

- [Database Migrations Best Practices](https://www.notion.so/Database-Migrations-Best-Practices)
- [Zero-Downtime Deployments](https://www.notion.so/Zero-Downtime-Deployments)

### 10.5 用語集

| 用語 | 説明 |
|------|------|
| **Alembic** | SQLAlchemy用のデータベースマイグレーションツール |
| **Migration** | スキーマ変更の履歴を管理する仕組み |
| **Revision** | マイグレーションの各バージョン |
| **Upgrade** | 新しいバージョンへのマイグレーション適用 |
| **Downgrade** | 古いバージョンへのロールバック |
| **Autogenerate** | モデルとDBの差分から自動マイグレーション生成 |
| **Head** | 最新のマイグレーションバージョン |
| **Base** | 初期状態（マイグレーション適用前） |

### 10.6 変更履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-01-11 | 初版作成 | Claude Code |

---

このマイグレーション戦略設計書は、genai-app-docsプロジェクトのデータベーススキーママイグレーションの完全な運用ガイドを提供します。
Alembicを使用した安全で効率的なマイグレーション管理を実現します。
