# クイックスタートガイド

最速でアプリケーションを起動し、動作を確認する方法を説明します。

## 前提条件

[Windows環境セットアップ](./02-windows-setup.md)と[環境設定](./04-environment-config.md)が完了していることを確認してください。

## 起動方法

### VS Codeで起動（推奨）

1. VS Codeでプロジェクトを開く
2. **F5キー**を押す

これだけです！PostgreSQLが自動的に起動し、FastAPIサーバーが起動します。

**仕組み:**

- `.vscode/launch.json`の`preLaunchTask`でPostgreSQL起動タスクを実行
- `scripts/dev.ps1 start-postgres`がPostgreSQLの状態を確認して起動
- FastAPIアプリケーションが起動

### 起動確認

ブラウザで以下にアクセス：

- **APIドキュメント**: <http://localhost:8000/docs>
- **ヘルスチェック**: <http://localhost:8000/health>

起動成功！

## 開発管理者ユーザーのセットアップ

初回起動後、管理者権限が必要なエンドポイント（SystemAdmin限定）をテストするために、開発ユーザーにSystemAdminロールを付与します。

### セットアップスクリプトの実行

```powershell
uv run python scripts/setup_dev_admin.py
```

**実行結果の例:**

```text
============================================================
開発管理者セットアップ
============================================================

対象ユーザー:
  Azure OID: dev-azure-oid-12345
  Email: dev.user@example.com
  Display Name: Development User

SystemAdminロールを追加中...
[SUCCESS] SystemAdminロールを追加しました！

最終状態:
  Roles: ['SystemAdmin', 'User']
============================================================
```

**このスクリプトの役割:**

- 開発ユーザーが存在しない場合: 新規作成 + SystemAdminロール付与
- 開発ユーザーが既に存在する場合: SystemAdminロールを追加（必要な場合のみ）

**環境変数でカスタマイズ可能:**

`.env.local`で開発ユーザー情報を変更できます：

```ini
DEV_MOCK_USER_OID=custom-azure-oid-67890
DEV_MOCK_USER_EMAIL=admin@example.com
DEV_MOCK_USER_NAME=Custom Admin User
```

## Swagger UIでのテスト

### 1. エンドポイントの確認

<http://localhost:8000/docs> にアクセスすると、すべてのAPIエンドポイントが表示されます。

### 2. 認証が必要なエンドポイントのテスト

開発環境では、認証が必要なエンドポイント（🔒マークがついているもの）をテストする際に、モック認証トークンを使用します。

**手順:**

1. Swagger UI右上の **「Authorize」** ボタンをクリック
2. **HTTPBearer (http, Bearer)** セクションに以下のトークンを入力：

   ```text
   mock-access-token-dev-12345
   ```

3. **「Authorize」** ボタンをクリック
4. **「Close」** で閉じる

これで、認証が必要なすべてのエンドポイント（例: `/api/v1/user-accounts/me`）がテスト可能になります。

**認証エンドポイントのテスト例:**

1. `GET /api/v1/user-accounts/me` エンドポイントをクリック
2. 「Try it out」ボタンをクリック
3. 「Execute」ボタンをクリック

レスポンス例：

```json
{
  "id": "12345678-1234-1234-1234-123456789abc",
  "azure_oid": "dev-azure-oid-12345",
  "email": "dev.user@example.com",
  "display_name": "Development User",
  "roles": ["SystemAdmin", "User"],
  "is_active": true,
  "created_at": "2025-01-20T12:34:56.789012+00:00",
  "updated_at": "2025-01-20T12:34:56.789012+00:00",
  "last_login": null
}
```

> **注意:** 管理者専用エンドポイント（SystemAdmin権限が必要）をテストする場合は、事前に[開発管理者ユーザーのセットアップ](#開発管理者ユーザーのセットアップ)を実行してください。

### 3. ヘルスチェックのテスト

1. `GET /health` エンドポイントをクリック
2. 「Try it out」ボタンをクリック
3. 「Execute」ボタンをクリック

レスポンス例：

```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T08:00:00.000000",
  "version": "0.1.0",
  "environment": "development"
}
```

### 4. その他のエンドポイントをテスト

同様に、他のエンドポイントも「Try it out」→「Execute」で簡単にテストできます。

## curlでのテスト

コマンドラインからもテストできます：

```powershell
# ヘルスチェック（認証不要）
curl http://localhost:8000/health

# JSON整形して表示
curl http://localhost:8000/health | python -m json.tool

# 認証が必要なエンドポイント
curl -H "Authorization: Bearer mock-access-token-dev-12345" http://localhost:8000/api/v1/user-accounts/me
```

## Pythonコードでのテスト

```python
import requests

# ヘルスチェック（認証不要）
response = requests.get("http://localhost:8000/health")
print(response.json())

# 認証が必要なエンドポイント
headers = {"Authorization": "Bearer mock-access-token-dev-12345"}
response = requests.get("http://localhost:8000/api/v1/user-accounts/me", headers=headers)
print(response.json())
```

## 停止方法

VS Codeで **Shift+F5** を押すか、ターミナルで **Ctrl+C** を押してください。

## 次のステップ

- [データベース基礎](./07-database-basics.md) - データベース管理
- [環境設定](./04-environment-config.md) - ステージング・本番環境の設定
- [プロジェクト構造](../02-architecture/01-project-structure.md) - コードベースの理解

---

## 詳細情報

### 手動起動（コマンドライン）

```powershell
# PostgreSQLを起動（未起動の場合）
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 start-postgres

# アプリケーション起動
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ログレベルの変更

`.env.local`ファイルで設定：

```ini
DEBUG=true
```

### ホットリロード

F5で起動すると、コード変更時に自動的にサーバーが再起動します。

---

## トラブルシューティング

### ポート8000が使用中

別のアプリケーションがポート8000を使用しています。

`.env.local`ファイルで変更：

```ini
PORT=8001
```

### データベース接続エラー

PostgreSQLが起動していない可能性があります。

```powershell
# PostgreSQL起動スクリプトを実行
.\scripts\start-postgres.ps1
```

または、手動で起動：

Scoop版の場合：

```powershell
# PostgreSQL起動
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data start
```

公式インストーラー版の場合：

```powershell
# サービス確認
Get-Service postgresql*
# サービス起動
Start-Service postgresql-x64-16
```

### Swagger UIが表示されない

アプリケーションが起動していることを確認：

```powershell
curl http://localhost:8000/health
```

起動していない場合はF5を押してください。

### 環境が壊れた・依存関係を更新したい

**完全リセット（環境＋データベース）:**

```powershell
# 1. 環境を完全リセット
.\scripts\reset-environment.ps1

# 2. データベースをリセット
.\scripts\reset-database.ps1
```

**依存関係のみ再インストール:**

```powershell
# 環境リセットスクリプトを使用（推奨）
.\scripts\reset-environment.ps1

# または手動で
uv sync --reinstall
```

**データベースのみリセット:**

```powershell
# 1. データベースリセットスクリプトを実行
.\scripts\reset-database.ps1

# 2. 開発管理者ユーザーを再セットアップ（必須）
uv run python scripts/setup_dev_admin.py
```

> **注意:** データベースリセット後は、必ず`setup_dev_admin.py`を実行して開発管理者ユーザーを再作成してください。
