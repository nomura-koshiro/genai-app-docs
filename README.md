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

- **Windows 10/11**
- **uv** - Pythonパッケージマネージャー（Python 3.13を自動管理）
- **PostgreSQL** - データベースサーバー（ローカルインストール）

### セットアップ

#### 方法1: スクリプトで自動セットアップ（推奨）

```powershell
# 1. PostgreSQLとuvをインストール（未インストールの場合）
# PostgreSQL: scoop install postgresql
# uv: Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression

# 2. プロジェクトディレクトリに移動
cd C:\path\to\camp_backend

# 3. 自動セットアップを実行
.\scripts\setup-windows.ps1

# 4. データベースをセットアップ
.\scripts\reset-database.ps1

# 5. 開発サーバー起動
# VS CodeでF5キーを押す、または:
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 方法2: 手動セットアップ

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

# 5. PostgreSQLの起動
.\scripts\start-postgres.ps1

# 6. データベースマイグレーション
cd src
uv run alembic upgrade head
cd ..

# 7. 開発サーバー起動
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

完了後、ブラウザで [http://localhost:8000/docs](http://localhost:8000/docs) を開いてAPIドキュメントを確認してください。

詳細なセットアップ手順は [Windows環境セットアップ](./docs/developer-guide/01-getting-started/02-windows-setup.md) を参照してください。

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
│       │       ├── v1/          # API v1（機能別サブディレクトリ）
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
│       ├── data/                # データファイル・テンプレート
│       │   └── analysis/        # 分析機能用データ
│       │
│       ├── models/              # SQLAlchemyモデル（機能別サブディレクトリ）
│       │   ├── analysis/        # 分析機能モデル
│       │   ├── driver_tree/     # ドライバーツリーモデル
│       │   ├── project/         # プロジェクト管理モデル
│       │   ├── sample/          # サンプル機能モデル
│       │   └── user/            # ユーザーモデル
│       │
│       ├── schemas/             # Pydanticスキーマ（機能別サブディレクトリ）
│       │   ├── analysis/        # 分析機能スキーマ
│       │   ├── driver_tree/     # ドライバーツリースキーマ
│       │   ├── ppt_generator/   # PPT生成スキーマ
│       │   ├── project/         # プロジェクト管理スキーマ
│       │   ├── sample/          # サンプル機能スキーマ
│       │   └── user/            # ユーザースキーマ
│       │
│       ├── repositories/        # データアクセス層（機能別サブディレクトリ）
│       │   ├── analysis/        # 分析機能リポジトリ
│       │   ├── driver_tree/     # ドライバーツリーリポジトリ
│       │   ├── project/         # プロジェクト管理リポジトリ
│       │   ├── sample/          # サンプル機能リポジトリ
│       │   └── user/            # ユーザーリポジトリ
│       │
│       ├── services/            # ビジネスロジック層（機能別サブディレクトリ）
│       │   ├── analysis/        # 分析機能サービス（エージェント含む）
│       │   ├── driver_tree/     # ドライバーツリーサービス
│       │   ├── ppt_generator/   # PPT生成サービス
│       │   ├── project/         # プロジェクト管理サービス
│       │   ├── sample/          # サンプル機能サービス
│       │   └── user/            # ユーザーサービス
│       │
│       └── utils/               # ユーティリティ関数
│
├── tests/                       # テストコード
├── docs/                        # ドキュメント
├── scripts/                     # 環境セットアップ・管理スクリプト
│   ├── lib/                     # 共通関数ライブラリ
│   ├── setup-windows.ps1        # 初回環境セットアップ
│   ├── start-postgres.ps1       # PostgreSQL起動
│   ├── reset-database.ps1       # データベースリセット
│   └── reset-environment.ps1    # 環境リセット
├── uploads/                     # アップロードファイル
├── pyproject.toml               # プロジェクト設定・依存関係
└── uv.lock                      # 依存関係ロックファイル
```

詳細は [プロジェクト構造](./docs/developer-guide/02-architecture/01-project-structure.md) を参照してください。

## 📜 よく使うコマンド

### 開発サーバー

```powershell
# 開発サーバー起動
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# または VSCode で F5 キーを押してデバッグ起動
```

### 環境管理スクリプト

```powershell
# PostgreSQL起動
.\scripts\start-postgres.ps1

# 初回セットアップ
.\scripts\setup-windows.ps1

# データベースリセット（削除・再作成・マイグレーション）
.\scripts\reset-database.ps1

# 環境リセット（仮想環境・依存関係の再構築）
.\scripts\reset-environment.ps1
```

### テスト実行

```powershell
uv run pytest                           # すべてのテスト
uv run pytest tests/test_services.py -v # 特定のテスト
```

### コード品質

```powershell
uv run ruff check src tests             # リント実行
uv run ruff format src tests            # フォーマット実行
uv run ruff check --fix src tests       # リント自動修正
```

### データベース (Alembic)

```powershell
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
| [⚡ クイックスタート](./docs/developer-guide/01-getting-started/05-quick-start.md) | 最速でAPIを起動 |
| [🎓 プロジェクト概要](./docs/developer-guide/01-getting-started/06-project-overview.md) | 全体像の理解 |
| [🏗️ プロジェクト構造](./docs/developer-guide/02-architecture/01-project-structure.md) | ディレクトリ構成 |
| [💻 技術スタック](./docs/developer-guide/03-core-concepts/01-tech-stack/index.md) | 使用技術 |
| [📝 コーディング規約](./docs/developer-guide/04-development/01-coding-standards/) | 規約とベストプラクティス |
| [🧪 テスト戦略](./docs/developer-guide/05-testing/01-testing-strategy/index.md) | テストの書き方 |
| [📋 設計仕様書](./docs/specifications/) | ユースケース、画面設計、アーキテクチャ等の詳細設計（全13カテゴリ） |

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

詳細は [技術スタック](./docs/developer-guide/03-core-concepts/01-tech-stack/index.md) を参照してください。

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

詳細は [レイヤードアーキテクチャ](./docs/developer-guide/02-architecture/02-layered-architecture.md) を参照してください。

## 🔗 関連リンク

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
