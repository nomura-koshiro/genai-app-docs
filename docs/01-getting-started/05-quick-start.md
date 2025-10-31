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

## Swagger UIでのテスト

### 1. エンドポイントの確認

<http://localhost:8000/docs> にアクセスすると、すべてのAPIエンドポイントが表示されます。

### 2. ヘルスチェックのテスト

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

### 3. その他のエンドポイントをテスト

同様に、他のエンドポイントも「Try it out」→「Execute」で簡単にテストできます。

## curlでのテスト

コマンドラインからもテストできます：

```powershell
# ヘルスチェック
curl http://localhost:8000/health

# JSON整形して表示
curl http://localhost:8000/health | python -m json.tool
```

## Pythonコードでのテスト

```python
import requests

# ヘルスチェック
response = requests.get("http://localhost:8000/health")
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
# データベースリセットスクリプトを実行
.\scripts\reset-database.ps1
```
