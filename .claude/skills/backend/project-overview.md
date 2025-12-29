# バックエンドAPI - プロジェクト概要

## プロジェクト概要

FastAPI + LangChain/LangGraphによるAIエージェントアプリケーションのバックエンドAPIです。
レイヤードアーキテクチャとSOLID原則に基づいて設計されています。

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| Webフレームワーク | FastAPI |
| 言語 | Python 3.13 |
| パッケージ管理 | uv |
| ORM | SQLAlchemy 2.0 |
| バリデーション | Pydantic v2 |
| データベース | PostgreSQL |
| キャッシュ | Redis |
| マイグレーション | Alembic |
| AI/エージェント | LangChain, LangGraph |

## 品質管理ツール

- **Ruff**: リンター・フォーマッター
- **mypy**: 静的型チェック
- **pytest**: テストフレームワーク
- **bandit**: セキュリティチェック

## ディレクトリ構造

```text
apps/backend/
├── app/
│   ├── api/v1/endpoints/    # APIエンドポイント
│   ├── models/              # SQLAlchemyモデル
│   ├── schemas/             # Pydanticスキーマ
│   ├── repositories/        # データアクセス層
│   ├── services/            # ビジネスロジック層
│   ├── core/                # 設定・セキュリティ
│   └── utils/               # ユーティリティ
├── tests/                   # テスト
├── alembic/                 # マイグレーション
└── requirements.txt
```

## 開発コマンド

```bash
# 開発サーバー起動
cd apps/backend && uvicorn app.main:app --reload

# テスト実行
cd apps/backend && python -m pytest

# 型チェック
cd apps/backend && mypy app/

# リント・フォーマット
cd apps/backend && ruff check app/ --fix
cd apps/backend && ruff format app/

# マイグレーション
cd apps/backend && alembic upgrade head
cd apps/backend && alembic revision --autogenerate -m "description"
```

## ドキュメント参照

詳細は以下のドキュメントを参照：

- [プロジェクト概要](docs/developer-guide/01-getting-started/06-project-overview.md)
- [クイックスタート](docs/developer-guide/01-getting-started/05-quick-start.md)
- [テックスタック](docs/developer-guide/03-core-concepts/01-tech-stack/index.md)
