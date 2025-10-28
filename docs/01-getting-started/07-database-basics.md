# データベース基礎

このガイドでは、開発に必要な最小限のデータベース操作を説明します。

## データベース構成

### PostgreSQL

- **開発環境**: PostgreSQL 16（WSL2のDockerコンテナ）
- **ORM**: SQLAlchemy 2.0（非同期対応）
- **接続**: Windows → WSL2 localhost forwarding
- **ポート**: 5432

### Redis

- **開発環境**: Redis 7（WSL2のDockerコンテナ）
- **用途**: キャッシュ
- **接続**: Windows → WSL2 localhost forwarding
- **ポート**: 6379

## PostgreSQL管理

### 自動起動（推奨）

**F5でデバッグ起動すると、PostgreSQLとRedisは自動的に起動します。**

通常、手動での操作は不要です。

### 手動起動

必要に応じて手動で起動する場合：

```powershell
# PostgreSQL起動
wsl -d Ubuntu bash /mnt/c/developments/backend/.vscode/start-postgres.sh

# コンテナ状態確認
wsl -d Ubuntu bash -c "docker ps | grep postgres"
```

### コンテナ操作

```powershell
# 停止
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose stop postgres"

# 起動
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose start postgres"

# 再起動
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose restart postgres"

# ログ確認
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose logs postgres"
```

## データベース接続

### 接続設定の確認

`.env.local`ファイル：

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_db
REDIS_URL=redis://localhost:6379/0
```

### データベースへの直接接続

```powershell
# psqlで接続
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose exec postgres psql -U postgres -d app_db"
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

## データベース初期化

### 自動初期化

アプリケーション起動時（F5）に自動的にテーブルが作成されます。

### 手動初期化

必要に応じて手動で初期化：

```bash
uv run python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

## バックアップとリストア

### バックアップ

```powershell
# バックアップ作成
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose exec -T postgres pg_dump -U postgres app_db > backup_$(date +%Y%m%d).sql"
```

### リストア

```powershell
# データベースをリストア
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose exec -T postgres psql -U postgres -d app_db < backup_20251016.sql"
```

## データベースのリセット

開発中にデータベースを初期状態に戻す：

```powershell
# コンテナとボリュームを削除
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose down -v"

# 再起動
wsl -d Ubuntu bash /mnt/c/developments/backend/.vscode/start-postgres.sh
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

## Redis管理

### 接続確認

```powershell
# redis-cliで接続
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose exec redis redis-cli ping"
# 応答: PONG
```

### キャッシュ操作

```powershell
# redis-cli起動
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose exec redis redis-cli"

# キー一覧表示
KEYS *

# キャッシュ取得
GET your_key

# キャッシュ削除
DEL your_key

# 全キャッシュクリア
FLUSHALL

# 終了
EXIT
```

### コンテナ操作

```powershell
# 停止
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose stop redis"

# 起動
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose start redis"

# 再起動
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose restart redis"

# ログ確認
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose logs redis"
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

## マイグレーション（参考）

データベーススキーマの変更は **Alembic** で管理されています。

基本的な操作は起動時に自動実行されるため、通常は手動操作不要です。

詳細は以下を参照してください:

- [Alembicマイグレーション](../04-development/04-database/03-alembic-migrations.md)
- [新しいモデル追加](../06-guides/02-add-model/index.md)

## 次のステップ

- [プロジェクト構造](../02-architecture/01-project-structure.md) - モデルの配置
- [レイヤードアーキテクチャ](../02-architecture/02-layered-architecture.md) - データアクセス層

---

## トラブルシューティング

### PostgreSQL接続エラー

```powershell
# コンテナ確認
wsl -d Ubuntu bash -c "docker ps | grep postgres"

# PostgreSQL再起動
wsl -d Ubuntu bash /mnt/c/developments/backend/.vscode/start-postgres.sh
```

### テーブルが存在しない

```bash
# データベース初期化
uv run python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### ポート5432が使用中

他のPostgreSQLが起動している可能性があります。

```powershell
# Windowsでポート確認
netstat -ano | findstr :5432

# WSL2でポート確認
wsl -d Ubuntu bash -c "sudo lsof -i :5432"
```

### Docker起動エラー

```powershell
# Docker起動確認
wsl -d Ubuntu bash -c "sudo service docker status"

# Docker起動
wsl -d Ubuntu bash -c "sudo service docker start"
```

### データベースが破損した場合

```powershell
# 完全リセット
wsl -d Ubuntu bash -c "cd /mnt/c/developments/backend && docker compose down -v"
wsl -d Ubuntu bash /mnt/c/developments/backend/.vscode/start-postgres.sh

# F5でアプリケーション起動（自動初期化）
```
