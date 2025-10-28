# camp-backend

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

- Python 3.13
- uv（Pythonパッケージマネージャー）
- PostgreSQL（ローカルインストール）

### セットアップ

```powershell
# 1. uvのインストール（未インストールの場合）
Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression

# 2. プロジェクトディレクトリに移動
cd C:\path\to\camp_backend

# 3. 依存関係のインストール
uv sync

# 4. 環境変数ファイルの作成
Copy-Item .env.local.example .env.local
# .env.localファイルを編集して、必要な環境変数を設定してください

# 5. PostgreSQLの起動（事前に起動しておいてください）

# 6. データベースマイグレーション
cd src
uv run alembic upgrade head
cd ..

# 7. 開発サーバー起動
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

完了後、ブラウザで [http://localhost:8000/docs](http://localhost:8000/docs) を開いてAPIドキュメントを確認してください。

## 📁 ディレクトリ構成

```text
camp_backend/
├── src/
│   ├── alembic/                 # データベースマイグレーション
│   ├── alembic.ini              # Alembic設定ファイル
│   └── app/
│       ├── main.py              # アプリケーションエントリーポイント
│       │
│       ├── api/                 # APIレイヤー
│       │   ├── core/            # APIコア機能
│       │   ├── decorators/      # デコレータ
│       │   ├── middlewares/     # ミドルウェア
│       │   └── routes/          # エンドポイント定義
│       │       ├── v1/          # API v1（ビジネスロジック）
│       │       └── system/      # システムエンドポイント
│       │
│       ├── core/                # コア機能
│       │   ├── app_factory.py   # アプリケーションファクトリ
│       │   ├── cache.py         # キャッシュ管理
│       │   ├── config.py        # 設定管理（環境変数）
│       │   ├── database.py      # データベース接続・セッション管理
│       │   ├── exceptions.py    # 例外定義
│       │   ├── lifespan.py      # ライフサイクル管理
│       │   ├── logging.py       # ログ設定
│       │   └── security/        # セキュリティ機能
│       │
│       ├── models/              # SQLAlchemyモデル
│       ├── schemas/             # Pydanticスキーマ
│       ├── repositories/        # データアクセス層
│       └── services/            # ビジネスロジック層
│
├── tests/                       # テストコード
├── docs/                        # ドキュメント
├── scripts/                     # ユーティリティスクリプト
├── uploads/                     # アップロードファイル
├── pyproject.toml               # プロジェクト設定・依存関係
└── uv.lock                      # 依存関係ロックファイル
```

詳細は [プロジェクト構造](./docs/02-architecture/01-project-structure.md) を参照してください。

## 📜 よく使うコマンド

```powershell
# 開発サーバー起動
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# または VSCode で F5 キーを押してデバッグ起動

# テスト実行
uv run pytest                           # すべてのテスト
uv run pytest tests/test_services.py -v # 特定のテスト

# コード品質
uv run ruff check src tests             # リント実行
uv run ruff format src tests            # フォーマット実行
uv run ruff check --fix src tests       # リント自動修正

# データベース (Alembic)
cd src
uv run alembic revision --autogenerate -m "message"  # マイグレーション生成
uv run alembic upgrade head                          # マイグレーション適用
cd ..
```

## 📖 ドキュメント

詳細なドキュメントは `docs/` ディレクトリを参照してください。

| ドキュメント | 内容 |
|------------|------|
| [📚 ドキュメント目次](./docs/README.md) | 全ドキュメントの一覧 |
| [⚡ クイックスタート](./docs/01-getting-started/05-quick-start.md) | 最速でAPIを起動 |
| [🎓 プロジェクト概要](./docs/01-getting-started/06-project-overview.md) | 全体像の理解 |
| [🏗️ プロジェクト構造](./docs/02-architecture/01-project-structure.md) | ディレクトリ構成 |
| [💻 技術スタック](./docs/03-core-concepts/01-tech-stack/index.md) | 使用技術 |
| [📝 コーディング規約](./docs/04-development/03-coding-standards/) | 規約とベストプラクティス |
| [🧪 テスト戦略](./docs/05-testing/01-testing-strategy/index.md) | テストの書き方 |

## 🛠️ 技術スタック

| カテゴリ | 技術 |
|---------|------|
| **フレームワーク** | FastAPI 0.115+, Uvicorn |
| **AI/エージェント** | LangChain 0.3+, LangGraph 0.2+, LangServe 0.3+ |
| **LLM統合** | langchain-anthropic, langchain-openai |
| **データベース** | SQLAlchemy 2.0+, Alembic, PostgreSQL |
| **ストレージ** | Azure Blob Storage, ローカルファイルシステム |
| **バリデーション** | Pydantic, Pydantic Settings |
| **セキュリティ** | python-jose, passlib, bcrypt |
| **テスト** | pytest, pytest-asyncio |
| **開発ツール** | Ruff, uv |
| **可観測性** | LangSmith |

詳細は [技術スタック](./docs/03-core-concepts/01-tech-stack/index.md) を参照してください。

## 🏗️ アーキテクチャ

このプロジェクトはレイヤードアーキテクチャを採用しています。

### 主要原則

1. **関心の分離** - 各層が明確な責任を持つ
2. **依存性の注入** - テスタビリティの向上
3. **単一方向のデータフロー** - API → Service → Repository → Model
4. **型安全性** - Pydantic、Type Hintsによる型チェック

### レイヤー構成

```text
API Layer (routes/)
    ↓
Service Layer (services/)
    ↓
Repository Layer (repositories/)
    ↓
Data Layer (models/)
```

詳細は [レイヤードアーキテクチャ](./docs/02-architecture/02-layered-architecture.md) を参照してください。

## 🔗 関連リンク

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
