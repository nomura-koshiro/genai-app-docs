# AI Agent App (Backend)

FastAPI + LangChain + LangGraphをベースにした、AIエージェント機能とファイル管理機能を持つバックエンドAPIです。

## ✨ 特徴

- 🤖 **LangGraph AI Agent** - ツールサポート付きエージェント
- 🌐 **マルチLLM対応** - Anthropic Claude、OpenAI、Azure OpenAI
- 📁 **ファイル管理** - アップロード/ダウンロード機能
- ☁️ **複数ストレージ対応** - ローカル / Azure Blob Storage
- ⚡ **FastAPI** - 高速・自動ドキュメント生成
- 📊 **LangSmith統合** - トレーシング・可観測性
- 🗄️ **SQLAlchemy** - ORM・マイグレーション対応
- 🔧 **uv** - 高速パッケージマネージャー
- 🎨 **Ruff** - リント＆フォーマット

## 🚀 クイックスタート

### 前提条件

- Python 3.13+
- uvパッケージマネージャー

### セットアップ

```bash
# 依存関係のインストール
uv sync

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPIキーや設定を記入

# 開発サーバーの起動
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ブラウザで [http://localhost:8000/docs](http://localhost:8000/docs) を開いてAPIドキュメントを確認してください。

## 📁 ディレクトリ構成

```text
backend/
├── src/
│   ├── app/
│   │   ├── main.py              # FastAPIアプリケーションのエントリーポイント
│   │   ├── config.py            # 設定管理（環境変数）
│   │   ├── database.py          # データベース接続・セッション管理
│   │   │
│   │   ├── api/                 # APIレイヤー
│   │   │   ├── routes/          # エンドポイント定義
│   │   │   │   ├── agents.py   # AIエージェントAPI
│   │   │   │   └── files.py    # ファイル管理API
│   │   │   ├── dependencies.py # 依存性注入
│   │   │   └── middlewares/    # ミドルウェア
│   │   │
│   │   ├── agents/              # AIエージェント
│   │   │   ├── graph.py         # LangGraphエージェント定義
│   │   │   └── tools.py         # カスタムツール
│   │   │
│   │   ├── models/              # SQLAlchemyモデル
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   └── file.py
│   │   │
│   │   ├── schemas/             # Pydanticスキーマ（バリデーション）
│   │   │   ├── user.py
│   │   │   ├── agent.py
│   │   │   └── file.py
│   │   │
│   │   ├── repositories/        # データアクセス層
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   └── file.py
│   │   │
│   │   ├── services/            # ビジネスロジック層
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   └── file.py
│   │   │
│   │   ├── storage/             # ファイルストレージ
│   │   │   ├── base.py          # ストレージインターフェース
│   │   │   ├── local.py         # ローカルファイルシステム
│   │   │   └── azure_blob.py   # Azure Blob Storage
│   │   │
│   │   └── core/                # コア機能
│   │       ├── exceptions.py   # カスタム例外
│   │       ├── logging.py      # ログ設定
│   │       └── security.py     # 認証・セキュリティ
│   │
│   └── alembic/                 # データベースマイグレーション
│       └── env.py
│
├── tests/                       # テストコード
├── uploads/                     # ローカルファイルストレージ（開発環境）
├── pyproject.toml               # プロジェクト設定・依存関係
└── .env.example                 # 環境変数テンプレート
```

## 📜 よく使うコマンド

### 開発サーバー

```bash
# 開発サーバー起動（ホットリロード）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# または（VSCodeのF5キーでも起動可能）
```

### コード品質

```bash
# リント実行
uv run ruff check src tests

# フォーマット実行
uv run ruff format src tests

# リント問題を自動修正
uv run ruff check --fix src tests

# すべてのチェック（リント + フォーマット）
uv run ruff check src tests && uv run ruff format --check src tests
```

### テスト

```bash
# すべてのテストを実行
uv run pytest

# 詳細出力付き
uv run pytest -v

# カバレッジ付きで実行
uv run pytest --cov=app --cov-report=html --cov-report=term

# 特定のテストファイルを実行
uv run pytest tests/test_agents.py
```

### データベース（Alembic）

```bash
# マイグレーションファイルを自動生成
cd src && uv run alembic revision --autogenerate -m "migration message"

# マイグレーションを適用
cd src && uv run alembic upgrade head

# 1つ前に戻す
cd src && uv run alembic downgrade -1

# マイグレーション履歴を確認
cd src && uv run alembic history
```

### 依存関係管理

```bash
# 依存関係のインストール
uv sync

# 開発用依存関係も含めてインストール
uv sync --all-groups

# パッケージを追加
uv add {package-name}

# 開発用パッケージを追加
uv add --dev {package-name}
```

## 🛠️ 技術スタック

| カテゴリ | 技術 |
|---------|------|
| **フレームワーク** | FastAPI 0.115+, Uvicorn |
| **AI/エージェント** | LangChain 0.3+, LangGraph 0.2+, LangServe 0.3+ |
| **LLM統合** | langchain-anthropic, langchain-openai |
| **データベース** | SQLAlchemy 2.0+, Alembic, PostgreSQL / SQLite |
| **ストレージ** | Azure Blob Storage, ローカルファイルシステム |
| **バリデーション** | Pydantic, Pydantic Settings |
| **セキュリティ** | python-jose, passlib, bcrypt |
| **テスト** | pytest, pytest-asyncio |
| **開発ツール** | Ruff (linter & formatter), uv (package manager) |
| **可観測性** | LangSmith |

## 🔧 環境設定

`.env`ファイルで以下の環境変数を設定してください。

### 必須設定

```bash
# 環境（development / staging / production）
ENVIRONMENT=development

# LLMプロバイダー（いずれか1つ以上必要）
ANTHROPIC_API_KEY=your-api-key
OPENAI_API_KEY=your-api-key
# または Azure OpenAI
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# データベース
DATABASE_URL=sqlite:///./app.db  # 開発環境
# DATABASE_URL=postgresql://user:password@localhost/dbname  # 本番環境
```

### オプション設定

```bash
# ストレージ設定
STORAGE_BACKEND=local  # local または azure
UPLOAD_DIR=uploads

# Azure Blob Storage（STORAGE_BACKEND=azureの場合）
AZURE_STORAGE_ACCOUNT_NAME=your-account
AZURE_STORAGE_CONTAINER_NAME=your-container

# LangSmithトレーシング（オプション）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=your-project-name

# セキュリティ
SECRET_KEY=your-secret-key-here  # 本番環境では必ず変更
```

## 📖 APIドキュメント

開発サーバー起動後、以下のURLでAPIドキュメントにアクセスできます：

| ドキュメント | URL | 説明 |
|------------|-----|------|
| **Swagger UI** | http://localhost:8000/docs | インタラクティブなAPIドキュメント |
| **ReDoc** | http://localhost:8000/redoc | 読みやすいAPIリファレンス |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | OpenAPI仕様（JSON） |

## 🏗️ アーキテクチャ

### レイヤードアーキテクチャ

このプロジェクトはレイヤードアーキテクチャを採用しています：

```text
┌─────────────────────────────────────┐
│  API Layer (routes)                 │  エンドポイント定義
│  - Request/Response handling         │
│  - Validation (Pydantic)            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Service Layer (services)           │  ビジネスロジック
│  - Business logic                   │
│  - Transaction management           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Repository Layer (repositories)    │  データアクセス
│  - Database operations              │
│  - Query abstraction                │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Data Layer (models)                │  データモデル
│  - SQLAlchemy models                │
│  - Database schema                  │
└─────────────────────────────────────┘
```

### 主要原則

1. **関心の分離** - 各層が明確な責任を持つ
2. **依存性の注入** - テスタビリティの向上
3. **単一方向のデータフロー** - API → Service → Repository → Model
4. **型安全性** - Pydantic、Type Hintsによる型チェック

## 💻 VSCode設定

このプロジェクトには`.vscode/`ディレクトリに推奨設定が含まれています：

### 含まれる設定ファイル

| ファイル | 内容 |
|---------|------|
| **settings.json** | Ruff、Python、フォーマット設定 |
| **launch.json** | FastAPIのデバッグ設定（F5キーで起動） |
| **tasks.json** | よく使うタスク（Ctrl+Shift+Bでサーバー起動） |
| **extensions.json** | 推奨VSCode拡張機能 |

### クイックスタート

1. VSCodeでプロジェクトを開く
2. 拡張機能パネルで「推奨」タブを確認
3. 「すべてインストール」をクリック
4. **F5キー**でFastAPIをデバッグ起動
5. **Ctrl+Shift+B**で開発サーバー起動

### おすすめ拡張機能

- **ms-python.python** - Python開発の基本
- **charliermarsh.ruff** - Ruffサポート（リント・フォーマット）
- **humao.rest-client** - VSCode内でAPIテスト
- **mtxr.sqltools** - データベース管理

## 🚀 デプロイ

### 開発環境

```bash
# ストレージ: ローカルファイルシステム
STORAGE_BACKEND=local

# データベース: SQLite
DATABASE_URL=sqlite:///./app.db
```

### 本番環境

```bash
# ストレージ: Azure Blob Storage
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_NAME=your-account
AZURE_STORAGE_CONTAINER_NAME=your-container

# データベース: PostgreSQL
DATABASE_URL=postgresql://user:password@host:5432/database

# 環境設定
ENVIRONMENT=production
```

### Dockerデプロイ（予定）

```bash
# Dockerイメージのビルド
docker build -t ai-agent-app .

# コンテナの起動
docker run -p 8000:8000 --env-file .env ai-agent-app
```

## 🧪 テスト

### テスト構成

```text
tests/
├── conftest.py           # pytestフィクスチャ
├── test_agents/          # エージェント関連テスト
├── test_api/             # APIエンドポイントテスト
├── test_repositories/    # リポジトリテスト
└── test_services/        # サービスロジックテスト
```

### テスト実行

```bash
# すべてのテストを実行
uv run pytest

# VSCodeのテストエクスプローラーからも実行可能
# または launch.json の "Python: Pytest すべて" を使用
```

## 🔗 関連リンク

### ドキュメント

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

### ツール

- [uv Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

### クラウド

- [Azure Blob Storage](https://azure.microsoft.com/ja-jp/products/storage/blobs)
- [LangSmith](https://smith.langchain.com/)

## 📝 ライセンス

MIT
