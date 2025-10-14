# バックエンドAPI 開発者ドキュメント

FastAPI + LangChain/LangGraphによるAIエージェントアプリケーションのバックエンドAPI開発者向けドキュメントです。

## 📚 ドキュメント構成

### 01. Getting Started

プロジェクトを始めるための基本情報。

- **[セットアップガイド](./01-getting-started/01-setup.md)** - 開発環境の構築手順
  - 前提条件（Python 3.13+、uv）
  - インストール手順
  - 環境変数設定
  - 初回起動とトラブルシューティング

- **[クイックスタート](./01-getting-started/02-quick-start.md)** - 最速でAPIを起動するガイド
  - 最速起動方法
  - APIドキュメント確認（/docs）
  - 基本的なAPI呼び出し例
  - Swagger UIでのテスト

- **[データベースセットアップ](./01-getting-started/03-database-setup.md)** - データベースとマイグレーション
  - データベース初期化
  - Alembicマイグレーション（将来実装）
  - マイグレーション作成と適用
  - データベース管理コマンド

### 02. Architecture

プロジェクトのアーキテクチャと設計原則。

- **[プロジェクト構造](./02-architecture/01-project-structure.md)** - ディレクトリ構造の説明
  - 全体構造
  - 各レイヤーの役割（models, schemas, repositories, services, api）
  - ファイル命名規則
  - 各モジュールの責務

- **[レイヤードアーキテクチャ](./02-architecture/02-layered-architecture.md)** - エンタープライズアーキテクチャ
  - 4層アーキテクチャの説明
  - データフロー（API → Service → Repository → Database）
  - 各層の責務と依存関係
  - トランザクション管理

- **[依存性注入](./02-architecture/03-dependency-injection.md)** - FastAPIのDI実装
  - FastAPIの依存性注入システム
  - Dependsの使い方
  - 依存性のスコープ
  - テストでのオーバーライド

### 03. Core Concepts

技術スタックと主要概念。

- **[テックスタック](./03-core-concepts/01-tech-stack.md)** - 使用技術の詳細
  - FastAPI - Webフレームワーク
  - SQLAlchemy - ORM
  - Pydantic - データバリデーション
  - Alembic - マイグレーション
  - LangChain/LangGraph - AI Agent
  - uv - パッケージマネージャー
  - Ruff - リンター/フォーマッター
  - pytest - テストフレームワーク

- **[データベース設計](./03-core-concepts/02-database-design.md)** - SQLAlchemyモデル設計
  - SQLAlchemyモデル定義
  - テーブル設計（users, sessions, messages, files）
  - リレーションシップの定義
  - 非同期SQLAlchemy
  - パフォーマンス最適化

### 04. Development

開発ガイドとベストプラクティス。

#### [01. コーディング規約](./04-development/01-coding-standards/)

Pythonコーディング規約とベストプラクティス

- [基本原則](./04-development/01-coding-standards/01-basic-principles.md) - 型安全性、単一責任の原則、DRY、KISS
- [設計原則](./04-development/01-coding-standards/02-design-principles.md) - SOLID、Clean Architecture、依存性逆転
- [リーダブルコード](./04-development/01-coding-standards/03-readable-code.md) - 読みやすいコードの14原則
- [命名規則](./04-development/01-coding-standards/04-naming-conventions.md) - ファイル、変数、関数、クラス
- [Python規約](./04-development/01-coding-standards/05-python-rules.md) - PEP 8、型ヒント、docstring
- [FastAPI規約](./04-development/01-coding-standards/06-fastapi-rules.md) - エンドポイント、依存性注入、async/await
- [ツール設定](./04-development/01-coding-standards/07-tools-setup.md) - Ruff、pytest、VSCode

#### [02. レイヤー別実装ガイド](./04-development/02-layer-implementation/)

各レイヤーの実装パターン

- [モデル層](./04-development/02-layer-implementation/01-models.md) - SQLAlchemyモデル定義
- [スキーマ層](./04-development/02-layer-implementation/02-schemas.md) - Pydanticスキーマ
- [リポジトリ層](./04-development/02-layer-implementation/03-repositories.md) - データアクセス層
- [サービス層](./04-development/02-layer-implementation/04-services.md) - ビジネスロジック層
- [API層](./04-development/02-layer-implementation/05-api.md) - エンドポイント実装

#### [03. データベース](./04-development/03-database/)

データベース操作とマイグレーション

- [SQLAlchemy基本](./04-development/03-database/01-sqlalchemy-basics.md) - ORM基礎
- [モデル関係](./04-development/03-database/02-model-relationships.md) - リレーションシップ定義
- [Alembicマイグレーション](./04-development/03-database/03-alembic-migrations.md) - マイグレーション管理
- [クエリパターン](./04-development/03-database/04-query-patterns.md) - 効率的なクエリ

#### [04. API設計](./04-development/04-api-design/)

RESTful API設計ガイドライン

- [エンドポイント設計](./04-development/04-api-design/01-endpoint-design.md) - RESTful原則
- [バリデーション](./04-development/04-api-design/02-validation.md) - リクエスト検証
- [レスポンス設計](./04-development/04-api-design/03-response-design.md) - 統一的なレスポンス
- [ページネーション](./04-development/04-api-design/04-pagination.md) - リスト取得パターン
- [エラーレスポンス](./04-development/04-api-design/05-error-responses.md) - エラー処理

#### [05. セキュリティ](./04-development/05-security/)

セキュリティ実装ガイド

- [認証実装](./04-development/05-security/01-authentication.md) - JWT、OAuth2
- [認可制御](./04-development/05-security/02-authorization.md) - ロールベース制御
- [セキュリティベストプラクティス](./04-development/05-security/03-best-practices.md) - OWASP対策

### 05. Testing

テスト戦略と実装方法

- [01. テスト戦略](./05-testing/01-testing-strategy.md) - テストピラミッドとカバレッジ
- [02. ユニットテスト](./05-testing/02-unit-testing.md) - pytest基礎
- [03. APIテスト](./05-testing/03-api-testing.md) - TestClient使用
- [04. データベーステスト](./05-testing/04-database-testing.md) - テストDB設定
- [05. モックとフィクスチャ](./05-testing/05-mocks-fixtures.md) - テストデータ管理
- [06. ベストプラクティス](./05-testing/06-best-practices.md) - 効果的なテスト

### 06. Guides

実装ガイド

- [01. 新しいエンドポイント追加](./06-guides/01-add-endpoint.md) - エンドポイント作成手順
- [02. 新しいモデル追加](./06-guides/02-add-model.md) - モデル追加とマイグレーション
- [03. 新しい機能モジュール追加](./06-guides/03-add-feature.md) - 機能モジュール作成
- [04. ファイルアップロード実装](./06-guides/04-file-upload.md) - ファイル処理実装
- [05. バックグラウンドタスク](./06-guides/05-background-tasks.md) - 非同期タスク処理
- [06. デプロイメント](./06-guides/06-deployment.md) - 本番環境デプロイ
- [07. トラブルシューティング](./06-guides/07-troubleshooting.md) - よくある問題と解決方法

### 07. Reference

参考資料とリンク集

- [01. API仕様](./07-reference/01-api-specification.md) - OpenAPI/Swagger仕様
- [02. データベーススキーマ](./07-reference/02-database-schema.md) - テーブル定義
- [03. 環境変数](./07-reference/03-environment-variables.md) - 設定変数一覧
- [04. ユーティリティ関数](./07-reference/04-utils.md) - 共通関数リファレンス
- [05. リソース](./07-reference/05-resources.md) - 外部リンク・学習リソース

## 🚀 クイックリンク

- [プロジェクト README](../README.md)
- [API ドキュメント](http://localhost:8000/docs) (開発サーバー起動時)
- [OpenAPI スキーマ](http://localhost:8000/openapi.json)

## 📝 ドキュメント更新

ドキュメントは継続的に更新されます。不明点や改善提案があれば、Issue または Pull Request でお知らせください。
