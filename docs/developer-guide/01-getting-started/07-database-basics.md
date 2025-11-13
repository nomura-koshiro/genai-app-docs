# データベース基礎

このガイドでは、開発に必要な最小限のデータベース操作を説明します。

## データベース構成

### PostgreSQL

- **開発環境**: PostgreSQL（Windowsにローカルインストール）
- **ORM**: SQLAlchemy 2.0（非同期対応）
- **接続**: localhost:5432
- **ポート**: 5432
- **データベース名**: camp_backend_db

### Redis（オプション）

- **用途**: キャッシュ（開発環境では必須ではない）
- **ポート**: 6379

## PostgreSQL管理

### PostgreSQLの起動確認

#### 推奨: スクリプトを使用

```powershell
# PostgreSQL起動（自動で状態確認）
.\scripts\start-postgres.ps1
```

このスクリプトは以下を実行します：

- PostgreSQLが起動しているか確認（接続テスト）
- 未起動の場合のみ起動
- 起動確認（リトライあり）

**手動操作:**

Scoop版の場合：

```powershell
# プロセス確認
Get-Process postgres -ErrorAction SilentlyContinue

# 起動
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data start

# 停止
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data stop

# 再起動
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data restart

# 状態確認
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data status
```

公式インストーラー版の場合：

```powershell
# サービス確認
Get-Service postgresql*

# サービス起動
Start-Service postgresql-x64-16

# サービス停止
Stop-Service postgresql-x64-16

# サービス再起動
Restart-Service postgresql-x64-16
```

## データベース接続

### 接続設定の確認

`.env.local`ファイル：

```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db
```

### データベースへの直接接続

```powershell
# psqlで接続
psql -U postgres -d camp_backend_db
```

psqlコマンド：

```sql
-- テーブル一覧
\dt

-- テーブル構造確認
\d sample_users

-- データ確認
SELECT * FROM sample_users;

-- 終了
\q
```

## データベースマイグレーション

### 初回セットアップ

プロジェクトをクローンした後、最初にマイグレーションを実行：

```powershell
cd src
uv run alembic upgrade head
cd ..
```

#### 分析テンプレートデータのシード（オプション）

分析機能を使用する場合、テンプレートデータ（validation.ymlとダミーチャート）をデータベースにインポートします：

```powershell
# テンプレートデータをシード
uv run python scripts/seed_templates.py
```

このコマンドは以下を実行します：

- `src/app/data/analysis/validation.yml` からテンプレートデータを読み込み
- `src/app/data/analysis/dummy/chart/*.json` からチャートデータを読み込み
- データベースにインポート（既存データは削除）

**注意**: テストでは自動的にシードされるため、通常は手動実行不要です。

### マイグレーションファイルの作成

モデルを変更した後、マイグレーションファイルを生成：

```powershell
cd src
uv run alembic revision --autogenerate -m "説明メッセージ"
cd ..
```

### マイグレーションの適用

```powershell
cd src
uv run alembic upgrade head
cd ..
```

## バックアップとリストア

### バックアップ

```powershell
# バックアップ作成
pg_dump -U postgres -d camp_backend_db > backup_$(Get-Date -Format "yyyyMMdd").sql
```

### リストア

```powershell
# データベースをリストア
psql -U postgres -d camp_backend_db < backup_20250128.sql
```

## データベースのリセット

### 推奨: スクリプトを使用

開発中にデータベースを初期状態に戻す：

```powershell
# データベースリセットスクリプトを実行
.\scripts\reset-database.ps1
```

このスクリプトは以下を自動実行します：

1. `camp_backend_db`を削除・再作成
2. `camp_backend_db_test`を削除・再作成
3. マイグレーション実行（`alembic upgrade head`）
4. **分析テンプレートデータをシード**（自動）

### 手動でリセット

```powershell
# データベースを削除して再作成
psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db;"
psql -U postgres -c "CREATE DATABASE camp_backend_db;"

# テストデータベースも同様に
psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db_test;"
psql -U postgres -c "CREATE DATABASE camp_backend_db_test;"

# マイグレーション実行
cd src
uv run alembic upgrade head
cd ..
```

## テーブル構成

このプロジェクトのデータベースは、**本番テーブル**と**レガシーサンプルテーブル**に分かれています。

### 本番テーブル（Azure AD認証対応）

#### users（ユーザーアカウント）

- `id` (UUID) - 主キー
- `azure_oid` - Azure AD Object ID（ユニーク）
- `email` - メールアドレス（ユニーク）
- `display_name` - 表示名
- `roles` (JSON) - システムロール（例: ["system_admin", "user"]）
- `is_active` - アクティブ状態
- `last_login` - 最終ログイン日時
- `created_at` / `updated_at` - タイムスタンプ

**用途**: Azure AD認証によるユーザー管理

#### projects（プロジェクト）

- `id` (UUID) - 主キー
- `name` - プロジェクト名
- `code` - プロジェクトコード（ユニーク）
- `description` - 説明
- `is_active` - アクティブ状態
- `created_by` (UUID) - 作成者ID
- `created_at` / `updated_at` - タイムスタンプ

#### project_members（プロジェクトメンバーシップ）

- `id` (UUID) - 主キー
- `project_id` (UUID) - プロジェクトID（外部キー）
- `user_id` (UUID) - ユーザーID（外部キー）
- `role` (Enum) - プロジェクトロール（project_manager/project_moderator/member/viewer）
- `joined_at` - 参加日時
- `added_by` (UUID) - 追加者ID
- **ユニーク制約**: (project_id, user_id)

#### analysis_sessions（分析セッション）

- `id` (UUID) - 主キー
- `project_id` (UUID) - プロジェクトID（外部キー）
- `created_by` (UUID) - 作成者ID（外部キー）
- `session_name` - セッション名
- `validation_config` (JSONB) - 分析設定
- `chat_history` (JSONB) - チャット履歴
- `snapshot_history` (JSONB) - スナップショット履歴
- `original_file_id` (UUID) - 選択中ファイルID
- `is_active` - アクティブ状態
- `created_at` / `updated_at` - タイムスタンプ

#### analysis_steps（分析ステップ）

- `id` (UUID) - 主キー
- `session_id` (UUID) - セッションID（外部キー）
- `step_order` (Integer) - ステップ順序
- `chart_id` - チャートID
- `chart_config` (JSONB) - チャート設定
- `insight` (Text) - インサイト
- `created_at` / `updated_at` - タイムスタンプ

#### driver_trees（ドライバーツリー）

- `id` (UUID) - 主キー
- `name` - ツリー名
- `root_node_id` (UUID) - ルートノードID（外部キー）
- `created_at` / `updated_at` - タイムスタンプ

#### driver_tree_nodes（ツリーノード）

- `id` (UUID) - 主キー
- `tree_id` (UUID) - ツリーID（外部キー）
- `parent_id` (UUID) - 親ノードID（外部キー、NULL=ルート）
- `label` - ノードラベル
- `operator` - 演算子（+, -, *, /, %）
- `order` (Integer) - 兄弟ノード間の順序
- `created_at` / `updated_at` - タイムスタンプ

### レガシーテーブル（JWT認証サンプル）

#### sample_users（サンプルユーザー）

- `id` (Integer) - 主キー（自動インクリメント）
- `email` - メールアドレス（ユニーク）
- `username` - ユーザー名（ユニーク）
- `hashed_password` - パスワードハッシュ
- `is_active` - アクティブ状態
- `is_superuser` - スーパーユーザーフラグ
- `last_login_at` - 最終ログイン日時
- `failed_login_attempts` - ログイン失敗回数
- `created_at` / `updated_at` - タイムスタンプ

**用途**: JWT認証のサンプル実装（開発・学習用）

#### sample_sessions（サンプルセッション）

- `id` (Integer) - 主キー
- `user_id` (Integer) - ユーザーID（外部キー）
- `session_id` - セッションID
- `title` - タイトル
- `created_at` / `updated_at` - タイムスタンプ

#### sample_files（サンプルファイル）

- `id` (Integer) - 主キー
- `user_id` (Integer) - ユーザーID（外部キー）
- `filename` - ファイル名
- `content_type` - MIMEタイプ
- `size` - サイズ
- `storage_path` - 保存パス
- `created_at` - タイムスタンプ

### テーブル使い分けガイドライン

| 認証方式 | ユーザーテーブル | 主キー | 用途 |
|---------|----------------|--------|------|
| **Azure AD** | `users` | UUID | 本番環境、エンタープライズ認証 |
| **JWT** | `sample_users` | Integer | 開発・学習・テスト用 |

**重要**: 本番環境では`users`テーブル（UserAccountモデル）とAzure AD認証を使用してください。`sample_*`テーブルは学習目的のレガシーコードです。

詳細なモデル定義は`src/app/models/`を参照してください。

## Redis管理（オプション）

Redis は開発環境では必須ではありませんが、キャッシュ機能を使用する場合に必要です。

### Redisのインストール（オプション）

Scoop経由でインストール：

```powershell
scoop install redis
```

### 起動・停止

```powershell
# 起動
redis-server

# 別のターミナルで接続
redis-cli ping
# 応答: PONG
```

### キャッシュ使用例

アプリケーションコード内でキャッシュを使用：

```python
from app.core.cache import cache_manager

# キャッシュに保存
await cache_manager.set("user:123", {"name": "John"}, expire=300)

# キャッシュから取得
user_data = await cache_manager.get("user:123")

# キャッシュ削除
await cache_manager.delete("user:123")

# パターンマッチでクリア
await cache_manager.clear("user:*")
```

## 利用可能なスクリプト

開発に便利なスクリプトが用意されています：

### PostgreSQL起動

PostgreSQLを起動します（既に起動している場合はスキップ）。

```powershell
.\scripts\start-postgres.ps1
```

### データベースリセット

データベースをリセットします（削除・再作成・マイグレーション）。

```powershell
.\scripts\reset-database.ps1
```

### 環境セットアップ

初回の開発環境をセットアップします。

```powershell
# 通常のセットアップ
.\scripts\setup-windows.ps1

# 環境クリーン後に再セットアップ
.\scripts\setup-windows.ps1 -Clean
```

### 環境リセット

開発環境（仮想環境・依存関係）をリセットします。

```powershell
.\scripts\reset-environment.ps1
```

## 次のステップ

- [プロジェクト構造](../02-architecture/01-project-structure.md) - モデルの配置
- [レイヤードアーキテクチャ](../02-architecture/02-layered-architecture.md) - データアクセス層
- [Alembicマイグレーション](../04-development/04-database/03-alembic-migrations.md) - マイグレーションの詳細
- [新しいモデル追加](../06-guides/02-add-model/index.md) - モデル追加方法

---

## トラブルシューティング

### PostgreSQL接続エラー

```powershell
# PostgreSQLが起動しているか確認
Get-Process postgres -ErrorAction SilentlyContinue

# Scoop版：起動
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data start

# 公式インストーラー版：起動
Start-Service postgresql-x64-16
```

### テーブルが存在しない

```powershell
# マイグレーション実行
cd src
uv run alembic upgrade head
cd ..
```

### ポート5432が使用中

他のPostgreSQLインスタンスが起動している可能性があります。

```powershell
# ポート確認
netstat -ano | findstr :5432

# プロセスを特定して停止
```

### データベースが破損した場合

```powershell
# データベースリセットスクリプトを実行
.\scripts\reset-database.ps1
```

または手動で：

```powershell
# 完全リセット
psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db;"
psql -U postgres -c "CREATE DATABASE camp_backend_db;"

# マイグレーション実行
cd src
uv run alembic upgrade head
cd ..
```
