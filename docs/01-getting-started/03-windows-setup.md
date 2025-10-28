# Windows環境セットアップガイド

WSL2を使用せず、Windows上で直接開発環境を構築する手順です。

## 前提条件

- Windows 10/11
- 管理者権限

## ステップ1: PostgreSQLのインストール

### 方法A: Scoopを使用（推奨）

Scoopは軽量なWindows用パッケージマネージャーです。

1. **PowerShellを管理者として起動**

2. **Scoopをインストール：**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

3. **PostgreSQLをインストール：**

```powershell
scoop install postgresql
```

4. **PostgreSQLを起動：**

```powershell
# データディレクトリのパスを確認
$PGDATA = "$env:USERPROFILE\scoop\apps\postgresql\current\data"

# データディレクトリが既に存在する場合はそのまま起動
# 存在しない場合のみ初期化
if (-not (Test-Path "$PGDATA\PG_VERSION")) {
    initdb -D $PGDATA -U postgres -W -E UTF8 --locale=C
}

# PostgreSQLをバックグラウンドで起動
pg_ctl -D $PGDATA -l "$env:USERPROFILE\scoop\apps\postgresql\current\logfile" start
```

**注意**: PostgreSQLを停止するには：
```powershell
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data stop
```

### 方法B: 公式インストーラー

1. [PostgreSQL公式サイト](https://www.postgresql.org/download/windows/)からインストーラーをダウンロード

2. インストーラーを実行：
   - インストール先：デフォルト（`C:\Program Files\PostgreSQL\16`）
   - パスワード：開発用の簡単なパスワードを設定（例：`postgres`）
   - ポート：`5432`（デフォルト）
   - ロケール：`Japanese, Japan`または`C`

3. インストール完了後、環境変数PATHに追加：

   ```
   C:\Program Files\PostgreSQL\16\bin
   ```

4. PostgreSQLサービスが自動起動するように設定されています

## ステップ2: データベースの作成と確認

PowerShellで実行：

```powershell
# データベースを作成（存在しない場合）
psql -U postgres -c "CREATE DATABASE genai_app;"

# データベース一覧を確認
psql -U postgres -l
```

**注意**: データベースが既に存在する場合は、エラーが表示されますが問題ありません。`psql -U postgres -l`でgenai_appが表示されていればOKです。

## ステップ3: Pythonのインストール

1. [Python公式サイト](https://www.python.org/downloads/)から最新版（3.11以上）をダウンロード

2. インストール時に **"Add Python to PATH"** にチェックを入れる

3. インストール完了後、確認：

```powershell
python --version
```

## ステップ4: uvのインストール

PowerShellで実行：

```powershell
# uvをインストール
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# PATHを更新（新しいPowerShellセッションを開く）
refreshenv

# 確認
uv --version
```

## ステップ5: プロジェクトのセットアップ

### 方法A: 自動セットアップ（推奨）

PowerShellで実行：

```powershell
# プロジェクトディレクトリに移動
cd C:\developments\project\genai-app-docs

# セットアップスクリプトを実行
.\scripts\setup-windows.ps1
```

スクリプトが自動的に以下を実行します：
- PostgreSQLの起動確認
- uvのインストール確認
- Python依存関係のインストール（uv sync）
- .env.localファイルの作成（.env.local.exampleからコピー）

**注意**: スクリプト実行ポリシーの警告が出た場合：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 方法B: 手動セットアップ

```powershell
# プロジェクトディレクトリに移動
cd C:\developments\project\genai-app-docs

# Python依存関係をインストール
uv sync

# 環境変数ファイルを作成
Copy-Item .env.local.example .env.local

# .env.localを編集（PostgreSQL接続情報を設定）
notepad .env.local
```

**.env.localの確認と編集：**

セットアップスクリプトで作成された`.env.local`を確認し、必要に応じて編集してください：

```ini
# データベース設定
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/genai_app

# セキュリティ設定（開発環境用）
SECRET_KEY=your-secret-key-here-min-32-characters-long

# 環境
ENVIRONMENT=local

# デバッグモード
DEBUG=true
```

**重要**: PostgreSQLのパスワードを変更している場合は、`DATABASE_URL`の`postgres:postgres`部分を`postgres:あなたのパスワード`に変更してください。

## ステップ6: 動作確認

### テストの実行

```powershell
# プロジェクトディレクトリにいることを確認
cd C:\developments\project\genai-app-docs

# テストを実行
uv run pytest tests/ -v
```

すべてのテストがPASSすれば、セットアップは成功です！

### アプリケーションの起動

```powershell
# アプリケーションを起動
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ブラウザで以下にアクセスして動作確認：

- **API Root**: <http://localhost:8000>
- **API ドキュメント (Swagger UI)**: <http://localhost:8000/docs>
- **API ドキュメント (ReDoc)**: <http://localhost:8000/redoc>
- **ヘルスチェック**: <http://localhost:8000/health>

## トラブルシューティング

### PostgreSQLに接続できない（Scoop版）

1. PostgreSQLプロセスが起動しているか確認：

```powershell
# プロセスを確認
Get-Process postgres -ErrorAction SilentlyContinue
```

2. PostgreSQLを起動：

```powershell
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data -l "$env:USERPROFILE\scoop\apps\postgresql\current\logfile" start
```

3. 起動確認：

```powershell
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data status
```

### PostgreSQLに接続できない（公式インストーラー版）

1. PostgreSQLサービスが起動しているか確認：

```powershell
Get-Service postgresql*
```

2. サービスを起動：

```powershell
Start-Service postgresql-x64-16  # バージョンによって名前が異なります
```

### ポート5432が既に使用されている

```powershell
# ポート5432を使用しているプロセスを確認
netstat -ano | findstr :5432
```

別のPostgreSQLインスタンスが起動している可能性があります。

### uvコマンドが見つからない

新しいPowerShellセッションを開いてください。それでも解決しない場合：

```powershell
# 手動でPATHを追加
$env:Path += ";$env:USERPROFILE\.local\bin"
```

### テストが失敗する

1. データベースが作成されているか確認：

```powershell
psql -U postgres -l | findstr genai_app
```

2. .env.localのDATABASE_URLが正しいか確認：

```powershell
Get-Content .env.local | Select-String DATABASE_URL
```

3. PostgreSQLに接続できるか確認：

```powershell
psql -U postgres -d genai_app -c "SELECT version();"
```

### SECRET_KEY警告が表示される

.env.localファイルを編集して、SECRET_KEYを設定してください：

```powershell
notepad .env.local
```

32文字以上のランダムな文字列を設定します。

## 次のステップ

- [開発ガイド](../02-development/01-project-structure.md)
- [API仕様](../03-api/01-overview.md)
