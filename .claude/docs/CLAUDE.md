# バックエンドAPI - プロジェクト設定・メモリ

## プロジェクト概要

FastAPI + LangChain/LangGraphによるAIエージェントアプリケーションのバックエンドAPIです。
レイヤードアーキテクチャとSOLID原則に基づいて設計されています。

## 重要な設計原則

### アーキテクチャ

- **4層アーキテクチャ**: API層 → サービス層 → リポジトリ層 → モデル層
- **SOLID原則**: 単一責任、開放閉鎖、依存性逆転
- **DRY/KISS**: コード重複排除・シンプル設計

### レイヤー責務

- **API層** (`api/v1/endpoints/`): HTTPリクエスト/レスポンス、認証・認可
- **サービス層** (`services/`): ビジネスロジック、トランザクション管理
- **リポジトリ層** (`repositories/`): データアクセス、CRUD操作
- **モデル層** (`models/`, `schemas/`): SQLAlchemy/Pydantic定義

## 技術スタック

### Backend

- Python 3.13
- FastAPI
- SQLAlchemy 2.0 (ORM)
- Pydantic v2 (バリデーション)
- PostgreSQL (データベース)
- Redis (キャッシュ)
- Alembic (マイグレーション)
- LangChain / LangGraph (AI/エージェント)
- uv (パッケージ管理)

### 品質管理ツール

- Ruff (リンター・フォーマッター)
- mypy (静的型チェック)
- pytest (テストフレームワーク)
- bandit (セキュリティチェック)

## 重要な規約

### 命名規則

- **ファイル**: snake_case (`user_service.py`)
- **クラス**: PascalCase (`UserService`)
- **関数・変数**: snake_case (`get_user`, `user_name`)
- **定数**: UPPER_SNAKE_CASE (`API_VERSION`)

### 型安全性

- すべての関数に型ヒントを付与
- Pydanticスキーマでバリデーション
- mypy による静的型チェック

### APIエンドポイント作成時のチェック

- [ ] Pydanticスキーマ（Base, Create, Update, Response）
- [ ] SQLAlchemyモデル
- [ ] リポジトリ層（CRUD操作）
- [ ] サービス層（ビジネスロジック）
- [ ] APIエンドポイント
- [ ] テスト（API、CRUD、モデル）

## 開発コマンド

### よく使用するコマンド

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

### 開発ガイド

- `docs/developer-guide/01-getting-started/` - はじめに
- `docs/developer-guide/02-architecture/` - アーキテクチャ
- `docs/developer-guide/03-core-concepts/` - コアコンセプト
- `docs/developer-guide/04-development/` - 開発ガイド
- `docs/developer-guide/05-testing/` - テスト
- `docs/developer-guide/06-guides/` - 実装ガイド
- `docs/developer-guide/07-reference/` - リファレンス

### 設計仕様書

- `docs/specifications/01-usercases/` - ユースケース
- `docs/specifications/04-architecture/` - アーキテクチャ設計
- `docs/specifications/05-database/` - データベース設計
- `docs/specifications/06-security/` - セキュリティ設計
- `docs/specifications/07-api/` - API仕様

### APIドキュメント

- `docs/api/openapi.json` - OpenAPI仕様
- `docs/api/api-docs.html` - Swagger UI
- `docs/api/redoc.html` - ReDoc

## トラブルシューティング

### よくある問題

- **型エラー**: mypy で確認、型ヒントを修正
- **バリデーションエラー**: Pydanticスキーマを確認
- **マイグレーションエラー**: alembic history で履歴確認
- **依存関係エラー**: uv sync で再インストール

## Agent活用ガイド

### @backend-developer

- 新機能開発、APIエンドポイント作成、リファクタリング
- モデル・スキーマ・リポジトリ・サービス層の実装

### @backend-code-reviewer

- コード品質チェック、SOLID原則確認
- セキュリティレビュー、パフォーマンス最適化

## 重要なファイル・ディレクトリ

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

docs/
├── api/                     # OpenAPI仕様
├── developer-guide/         # 開発者ガイド
└── specifications/          # 設計仕様書
```

このメモリ情報により、Claude は常にプロジェクトのコンテキスト、設計原則、技術選択を理解して開発支援を行います。
