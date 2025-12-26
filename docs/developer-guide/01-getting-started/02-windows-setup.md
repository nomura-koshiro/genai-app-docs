# Windows環境セットアップガイド

WSL2を使用せず、Windows上で直接開発環境を構築する手順です。

## 前提条件

- Windows 10/11
- 管理者権限（PostgreSQLインストール時に必要な場合があります）

---

## セットアップ方法の選択

### 🚀 方法1: スクリプトで自動セットアップ（推奨・初心者向け）

**最速でセットアップ完了！** スクリプトがすべて自動実行します。

- ⏱️ **所要時間**: 約10分
- ✅ **対象**: 素早くセットアップしたい方、初めての方
- 📝 **手順**: 最小限のコマンド実行のみ

**→ [方法1へジャンプ](#方法1-スクリプトで自動セットアップ推奨)**

### 🔧 方法2: 手動セットアップ（詳細を理解したい方向け）

各ステップを手動で実行し、構成を理解しながらセットアップします。

- ⏱️ **所要時間**: 約20-30分
- ✅ **対象**: 詳細を理解したい方、カスタマイズしたい方
- 📝 **手順**: 各コンポーネントを個別にインストール

**→ [方法2へジャンプ](#方法2-手動セットアップ詳細を理解したい方向け)**

---

## 方法1: スクリプトで自動セットアップ（推奨）

### ステップ1: PostgreSQLとuvのインストール

まず、PostgreSQLとuvを手動でインストールします。

#### 1-1. PostgreSQLのインストール

**Scoop使用（推奨）:**

```powershell
# Scoopをインストール
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# PostgreSQLをインストール
scoop install postgresql

# PostgreSQLを初期化・起動
$PGDATA = "$env:USERPROFILE\scoop\apps\postgresql\current\data"
if (-not (Test-Path "$PGDATA\PG_VERSION")) {
    initdb -D $PGDATA -U postgres -W -E UTF8 --locale=C
}
pg_ctl -D $PGDATA -l "$env:USERPROFILE\scoop\apps\postgresql\current\logfile" start
```

**または公式インストーラー:**

- [PostgreSQL公式サイト](https://www.postgresql.org/download/windows/)からダウンロード
- パスワード: `postgres`（開発用）
- ポート: `5432`（デフォルト）

#### 1-2. uvのインストール

```powershell
# uvをインストール（Pythonはuvが自動管理します）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 新しいPowerShellセッションを開く（PATHを反映）
```

### ステップ2: プロジェクトのセットアップ

```powershell
# プロジェクトディレクトリに移動
cd C:\path\to\camp_backend

# セットアップスクリプトを実行
.\scripts\setup-windows.ps1
```

スクリプトが以下を自動実行します：

- ✅ PostgreSQL起動確認
- ✅ uvインストール確認
- ✅ Python 3.13の自動インストール
- ✅ 依存関係のインストール（118パッケージ）
- ✅ .env.localファイルの作成
- ✅ データベースの作成（camp_backend_db / camp_backend_db_test）

### ステップ3: データベースのセットアップ

```powershell
# データベースをリセット＆マイグレーション実行
.\scripts\reset-database.ps1
```

このスクリプトは以下を自動実行します：

- ✅ データベース削除・再作成
- ✅ テストデータベース削除・再作成
- ✅ マイグレーション実行

### ステップ4: 動作確認

```powershell
# テスト実行
uv run pytest tests/ -v
```

すべてのテストがPASSすれば **セットアップ完了** です！🎉

### ステップ5: アプリケーション起動

#### VS Codeで起動（推奨）

1. VS Codeでプロジェクトを開く
2. **F5キー**を押す

PostgreSQLが自動起動し、FastAPIアプリケーションが起動します。

ブラウザで <http://localhost:8000/docs> にアクセスして動作確認してください。

---

## 方法2: 手動セットアップ（詳細を理解したい方向け）

### ステップ1: PostgreSQLのインストール

#### 方法A: Scoopを使用（推奨）

Scoopは軽量なWindows用パッケージマネージャーです。

1. **PowerShellを管理者として起動**

2. **Scoopをインストール：**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

1. **PostgreSQLをインストール：**

```powershell
scoop install postgresql
```

1. **PostgreSQLを起動：**

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

#### 方法B: 公式インストーラー

1. [PostgreSQL公式サイト](https://www.postgresql.org/download/windows/)からインストーラーをダウンロード

2. インストーラーを実行：
   - インストール先：デフォルト（`C:\Program Files\PostgreSQL\16`）
   - パスワード：開発用の簡単なパスワードを設定（例：`postgres`）
   - ポート：`5432`（デフォルト）
   - ロケール：`Japanese, Japan`または`C`

3. インストール完了後、環境変数PATHに追加：

   ```text
   C:\Program Files\PostgreSQL\16\bin
   ```

4. PostgreSQLサービスが自動起動するように設定されています

### ステップ2: データベースの作成と確認

PowerShellで実行：

```powershell
# データベースを作成（存在しない場合）
psql -U postgres -c "CREATE DATABASE camp_backend_db;"

# データベース一覧を確認
psql -U postgres -l
```

**注意**: データベースが既に存在する場合は、エラーが表示されますが問題ありません。`psql -U postgres -l`でcamp_backend_dbが表示されていればOKです。

### ステップ3: uvのインストール

uvは高速なPythonパッケージマネージャーで、**Pythonのインストールも自動的に管理**します。

PowerShellで実行：

```powershell
# uvをインストール
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# PATHを更新（新しいPowerShellセッションを開く）
refreshenv

# 確認
uv --version
```

**重要**: uvをインストールすると、プロジェクトのセットアップ時に必要なPython 3.13が自動的にインストールされます。手動でPythonをインストールする必要はありません。

### ステップ4: プロジェクトのセットアップ

```powershell
# プロジェクトディレクトリに移動
cd path\to\camp_backend

# Python依存関係をインストール
uv sync

# 環境変数ファイルを作成
Copy-Item .env.local.example .env.local

# .env.localを編集（PostgreSQL接続情報を設定）
notepad .env.local
```

**.env.localの確認と編集：**

以下の設定を確認してください：

```ini
# データベース設定
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camp_backend_db?ssl=disable

# セキュリティ設定（開発環境用）
SECRET_KEY=your-secret-key-here-min-32-characters-long

# 環境
ENVIRONMENT=development

# デバッグモード
DEBUG=true
```

**重要**: PostgreSQLのパスワードを変更している場合は、`DATABASE_URL`の`postgres:postgres`部分を`postgres:あなたのパスワード`に変更してください。

### ステップ5: データベースのセットアップ

データベースをセットアップします：

```powershell
# データベースリセットスクリプトを実行
.\scripts\reset-database.ps1
```

このスクリプトは以下を自動実行します：

- データベース削除・再作成
- テストデータベース削除・再作成
- マイグレーション実行

### ステップ6: 動作確認

#### テストの実行

```powershell
# プロジェクトディレクトリにいることを確認
cd path\to\camp_backend

# テストを実行
uv run pytest tests/ -v
```

すべてのテストがPASSすれば、セットアップは成功です！

#### アプリケーションの起動

##### 推奨: VS Codeで起動（PostgreSQL自動起動）

1. VS Codeでプロジェクトを開く
2. **F5キー**を押す

PostgreSQLが自動的に起動し、FastAPIアプリケーションが起動します。

##### または: コマンドラインで起動

```powershell
# PostgreSQLを起動（未起動の場合）
.\scripts\start-postgres.ps1

# アプリケーションを起動
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ブラウザで以下にアクセスして動作確認：

- **API Root**: <http://localhost:8000>
- **API ドキュメント (Swagger UI)**: <http://localhost:8000/docs>
- **API ドキュメント (ReDoc)**: <http://localhost:8000/redoc>
- **ヘルスチェック**: <http://localhost:8000/health>

---

## Pre-commitフックのセットアップ

Pre-commitは、git commitの前に自動的にコード品質チェックを実行するツールです。
このプロジェクトでは、Ruffによるlintingとformattingを自動実行します。

### Pre-commitとは

Pre-commitフックを設定すると、`git commit`実行時に以下が自動実行されます：

- ✅ **Ruff Linter**: コード品質チェック
- ✅ **Ruff Formatter**: コードフォーマット
- ✅ **末尾の空白削除**: ファイル末尾の不要な空白を削除
- ✅ **ファイル末尾の改行**: ファイル末尾に改行を追加

問題が検出された場合、commitは中断され、自動修正が適用されます。
修正されたファイルを再度`git add`して`git commit`すれば完了です。

### インストール手順

#### 1. Pre-commitのインストール

```powershell
# プロジェクトディレクトリで実行
uv pip install pre-commit
```

#### 2. Git フックの有効化

```powershell
# プロジェクトディレクトリで実行
pre-commit install
```

これで、`git commit`時に自動的にpre-commitフックが実行されるようになります。

### 使用方法

#### 自動実行（推奨）

通常通り`git commit`すると、自動的にチェックが実行されます：

```powershell
git add .
git commit -m "feat: 新機能を追加"
```

チェックが失敗した場合：

1. Pre-commitが自動修正を適用
2. 修正されたファイルを再度addする
3. 再度commitする

```powershell
# 修正されたファイルを再度add
git add .
# 再度commit
git commit -m "feat: 新機能を追加"
```

#### 手動実行

全ファイルに対してチェックを実行する場合：

```powershell
# すべてのファイルをチェック
pre-commit run --all-files
```

特定のファイルのみチェックする場合：

```powershell
# ステージングされたファイルのみチェック
pre-commit run
```

### Ruffコマンドの直接実行

Pre-commitを使わずに直接Ruffを実行することもできます：

```powershell
# Lintチェック
uv run ruff check .

# Lint修正を自動適用
uv run ruff check --fix .

# フォーマットチェック
uv run ruff format --check .

# フォーマットを適用
uv run ruff format .

# Lint + フォーマットを一括実行
uv run ruff check --fix . && uv run ruff format .
```

### トラブルシューティング

#### Pre-commitが実行されない

Gitフックが正しくインストールされているか確認：

```powershell
# .git/hooks/pre-commitファイルが存在するか確認
Test-Path .git\hooks\pre-commit
```

存在しない場合は、再度インストール：

```powershell
pre-commit install
```

#### Pre-commitをスキップしたい場合

緊急時のみ、`--no-verify`フラグでスキップできます：

```powershell
git commit -m "メッセージ" --no-verify
```

**注意**: 通常はpre-commitをスキップしないでください。コード品質を保つために重要です。

---

## トラブルシューティング

### PostgreSQLに接続できない（Scoop版）

1. PostgreSQLプロセスが起動しているか確認：

```powershell
# プロセスを確認
Get-Process postgres -ErrorAction SilentlyContinue
```

1. PostgreSQLを起動：

```powershell
.\scripts\start-postgres.ps1
```

1. 起動確認：

```powershell
pg_ctl -D $env:USERPROFILE\scoop\apps\postgresql\current\data status
```

### PostgreSQLに接続できない（公式インストーラー版）

1. PostgreSQLサービスが起動しているか確認：

```powershell
Get-Service postgresql*
```

1. サービスを起動：

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
psql -U postgres -l | findstr camp_backend_db
```

1. .env.localのDATABASE_URLが正しいか確認：

```powershell
Get-Content .env.local | Select-String DATABASE_URL
```

1. PostgreSQLに接続できるか確認：

```powershell
psql -U postgres -d camp_backend_db -c "SELECT version();"
```

### SECRET_KEY警告が表示される

.env.localファイルを編集して、SECRET_KEYを設定してください：

```powershell
notepad .env.local
```

32文字以上のランダムな文字列を設定します。

### 環境をリセットしたい

```powershell
# 環境リセット（仮想環境・依存関係）
.\scripts\reset-environment.ps1

# データベースリセット
.\scripts\reset-database.ps1
```

---

## 次のステップ

- [VSCodeセットアップ](./03-vscode-setup.md)
- [環境設定](./04-environment-config.md)
- [クイックスタート](./05-quick-start.md)
