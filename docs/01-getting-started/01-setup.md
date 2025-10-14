# セットアップガイド

このガイドでは、AI Agent Appの開発環境をセットアップする方法を説明します。

## 前提条件

開発を始める前に、以下のツールがインストールされていることを確認してください。

### 必須要件

- **Python 3.13以上**
  - Python 3.13以降が必要です
  - バージョン確認: `python --version`

- **uv（パッケージマネージャー）**
  - 高速なPythonパッケージマネージャー
  - インストール: https://github.com/astral-sh/uv
  ```bash
  # Windows (PowerShell)
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### 推奨ツール

- **Git** - バージョン管理
- **Visual Studio Code** - コードエディタ（推奨）
- **PostgreSQL** - 本番環境用データベース（開発環境ではSQLiteを使用）

## インストール手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd backend
```

### 2. 依存関係のインストール

uvを使用してプロジェクトの依存関係をインストールします。

```bash
uv sync
```

このコマンドは以下を実行します：
- 仮想環境の作成（`.venv/`）
- `pyproject.toml`に定義された全依存関係のインストール
- 開発用依存関係（pytest、ruffなど）のインストール

インストールされる主なライブラリ：
- **FastAPI** - Webフレームワーク
- **SQLAlchemy** - ORM（データベース操作）
- **LangChain/LangGraph** - AI Agent機能
- **Pydantic** - データバリデーション
- **Uvicorn** - ASGIサーバー

### 3. 環境変数の設定

プロジェクトルートに`.env.example`ファイルがあります。これをコピーして設定をカスタマイズします。

```bash
# .env.exampleをコピー
cp .env.example .env
```

`.env`ファイルを編集して、必要な設定を行います：

```bash
# アプリケーション設定
APP_NAME=AI Agent App
VERSION=0.1.0
DEBUG=true
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=*

# 環境
ENVIRONMENT=development

# データベース（開発環境ではSQLiteを使用）
DATABASE_URL=sqlite+aiosqlite:///./app.db

# ストレージ設定（開発環境ではローカルストレージを使用）
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads

# LLM設定（使用するプロバイダーのAPIキーを設定）
# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI
# OPENAI_API_KEY=your_openai_api_key_here

# セキュリティ（本番環境では必ず変更してください）
SECRET_KEY=your-secret-key-here-change-in-production-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 重要な環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------------|
| `DATABASE_URL` | データベース接続URL | `sqlite+aiosqlite:///./app.db` |
| `STORAGE_BACKEND` | ストレージバックエンド（local/azure） | `local` |
| `ANTHROPIC_API_KEY` | Anthropic Claude APIキー | なし（必須） |
| `SECRET_KEY` | JWT認証用シークレットキー | 変更必須 |
| `DEBUG` | デバッグモード | `false` |

#### SECRET_KEYの生成

セキュアなシークレットキーを生成するには：

```bash
# Pythonを使用
python -c "import secrets; print(secrets.token_hex(32))"

# または OpenSSLを使用
openssl rand -hex 32
```

### 4. データベースの初期化

アプリケーションを初回起動すると、SQLAlchemyが自動的にデータベーステーブルを作成します。

手動で初期化する場合：

```python
# Pythonインタラクティブシェルで実行
uv run python

>>> from app.database import init_db
>>> import asyncio
>>> asyncio.run(init_db())
```

## 初回起動

### 開発サーバーの起動

以下のコマンドでアプリケーションを起動できます：

```bash
# 方法1: プロジェクトスクリプトを使用
uv run ai-agent-app

# 方法2: Pythonモジュールとして実行
uv run python -m app.main

# 方法3: 直接実行
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

起動に成功すると、以下のようなメッセージが表示されます：

```
Starting AI Agent App v0.1.0
Environment: development
Database: sqlite+aiosqlite:///./app.db
Database initialized
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### 動作確認

ブラウザまたはcurlで以下のエンドポイントにアクセスして動作を確認します：

1. **ルートエンドポイント**
```bash
curl http://localhost:8000/

# レスポンス例
{
  "message": "Welcome to AI Agent App",
  "version": "0.1.0",
  "docs": "/docs"
}
```

2. **ヘルスチェック**
```bash
curl http://localhost:8000/health

# レスポンス例
{
  "status": "healthy",
  "timestamp": "2025-10-14T08:00:00.000000",
  "version": "0.1.0",
  "environment": "development"
}
```

3. **APIドキュメント**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## トラブルシューティング

### Pythonバージョンエラー

```
Error: Python 3.13 or higher is required
```

**解決方法**: Python 3.13以上をインストールしてください。

### ポート使用エラー

```
Error: [Errno 48] Address already in use
```

**解決方法**: 別のアプリケーションがポート8000を使用しています。
- 他のアプリケーションを停止する、または
- `.env`ファイルで`PORT`を変更する

### データベース接続エラー

```
Error: Could not connect to database
```

**解決方法**:
1. `DATABASE_URL`が正しく設定されているか確認
2. SQLiteの場合、ファイルの書き込み権限を確認
3. PostgreSQLの場合、サーバーが起動しているか確認

### 依存関係のエラー

```
Error: Package not found
```

**解決方法**:
```bash
# 依存関係を再インストール
uv sync --reinstall

# または仮想環境を削除して再作成
rm -rf .venv
uv sync
```

## 次のステップ

セットアップが完了したら、以下のドキュメントを参照してください：

- [クイックスタート](./02-quick-start.md) - 最速で動作を確認する
- [データベースセットアップ](./03-database-setup.md) - データベースマイグレーション
- [プロジェクト構造](../02-architecture/01-project-structure.md) - コードベースの理解
