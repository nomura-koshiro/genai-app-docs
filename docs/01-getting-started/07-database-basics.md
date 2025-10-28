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

```bash
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

```bash
cd src
uv run alembic upgrade head
cd ..
```

### マイグレーションファイルの作成

モデルを変更した後、マイグレーションファイルを生成：

```bash
cd src
uv run alembic revision --autogenerate -m "説明メッセージ"
cd ..
```

### マイグレーションの適用

```bash
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

開発中にデータベースを初期状態に戻す：

```powershell
# データベースを削除して再作成
psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db;"
psql -U postgres -c "CREATE DATABASE camp_backend_db;"

# マイグレーション実行
cd src
uv run alembic upgrade head
cd ..
```

## テーブル構成

主要なテーブル：

### sample_users

- `id` - 主キー
- `email` - メールアドレス（ユニーク）
- `username` - ユーザー名（ユニーク）
- `hashed_password` - パスワードハッシュ
- `is_active` - アクティブ状態
- `created_at` / `updated_at` - タイムスタンプ

### sample_sessions

- `id` - 主キー
- `user_id` - ユーザーID（外部キー）
- `session_id` - セッションID
- `title` - タイトル
- `created_at` / `updated_at` - タイムスタンプ

### sample_files

- `id` - 主キー
- `user_id` - ユーザーID（外部キー）
- `filename` - ファイル名
- `content_type` - MIMEタイプ
- `size` - サイズ
- `storage_path` - 保存パス
- `created_at` - タイムスタンプ

詳細は`src/app/models/`を参照してください。

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

```bash
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
# 完全リセット
psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db;"
psql -U postgres -c "CREATE DATABASE camp_backend_db;"

# マイグレーション実行
cd src
uv run alembic upgrade head
cd ..
```
