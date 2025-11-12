# バックエンドAPI ドキュメント

FastAPI + LangChain/LangGraphによるAIエージェントアプリケーションのバックエンドAPI開発者向けドキュメントです。

---

## 📖 目次

### [01. はじめに](./01-getting-started/)

> プロジェクトを始めるための必須ガイド

| ドキュメント | 内容 |
|------------|------|
| [前提条件](./01-getting-started/01-prerequisites.md) | Python 3.13、uv、PostgreSQL、Visual Studio Code |
| [Windows環境セットアップ](./01-getting-started/02-windows-setup.md) | PostgreSQL、Python、uvのインストール手順 |
| [VSCode セットアップ](./01-getting-started/03-vscode-setup.md) | 開発環境の設定と推奨拡張機能 |
| [環境設定](./01-getting-started/04-environment-config.md) | 環境別設定ファイルの管理 |
| [クイックスタート](./01-getting-started/05-quick-start.md) | 最速でAPIを起動する方法 |
| [プロジェクト概要](./01-getting-started/06-project-overview.md) | 全体構成・技術スタック・アーキテクチャ概要 |
| [データベース基礎](./01-getting-started/07-database-basics.md) | PostgreSQL & Redis の基本操作 |

---

### [02. アーキテクチャ](./02-architecture/)

> システム設計の理解

| ドキュメント | 内容 |
|------------|------|
| [プロジェクト構造](./02-architecture/01-project-structure.md) | ディレクトリ構造、各層の役割、命名規則 |
| [レイヤードアーキテクチャ](./02-architecture/02-layered-architecture.md) | 4層構造、データフロー、トランザクション管理 |
| [依存性注入](./02-architecture/03-dependency-injection.md) | FastAPI DIシステム、Dependsの使い方 |
| [コードリーディングガイド](./02-architecture/04-code-reading-guide.md) | コードベースを理解するための詳細ガイド |

---

### [03. コアコンセプト](./03-core-concepts/)

> 技術スタックと主要機能

#### [テックスタック](./03-core-concepts/01-tech-stack/)

| ドキュメント | 内容 |
|------------|------|
| [Webフレームワーク](./03-core-concepts/01-tech-stack/01-web.md) | FastAPI、Pydantic、Alembic |
| [データレイヤー](./03-core-concepts/01-tech-stack/02-data.md) | PostgreSQL、SQLAlchemy、Redis |
| [AI・開発ツール](./03-core-concepts/01-tech-stack/03-ai-tools.md) | LangChain、LangGraph、uv、Ruff、pytest |

#### データベース設計

- [データベース設計](./03-core-concepts/02-database-design/index.md) - モデル定義、リレーションシップ、パフォーマンス最適化

#### [セキュリティ](./03-core-concepts/03-security/)

| ドキュメント | 内容 |
|------------|------|
| [セキュリティ概要](./03-core-concepts/03-security/index.md) | セキュリティ全体像 |
| [認証・認可](./03-core-concepts/03-security/01-authentication.md) | JWT、bcrypt、パスワード強度検証 |
| [リクエスト保護](./03-core-concepts/03-security/02-request-protection.md) | CORS、レート制限、バリデーション |
| [データ保護](./03-core-concepts/03-security/03-data-protection.md) | DBセキュリティ、ファイルアップロード |
| [インフラストラクチャ](./03-core-concepts/03-security/04-infrastructure.md) | エラーハンドリング、環境設定 |
| [ベストプラクティス](./03-core-concepts/03-security/05-best-practices.md) | セキュリティ強化の推奨事項 |

---

### [04. 開発ガイド](./04-development/)

> 実装のためのベストプラクティス

#### [コーディング規約](./04-development/01-coding-standards/)

| ドキュメント | 内容 |
|------------|------|
| [基本原則](./04-development/01-coding-standards/01-basic-principles.md) | 型安全性、単一責任、DRY、KISS |
| [設計原則](./04-development/01-coding-standards/02-design-principles.md) | SOLID、Clean Architecture |
| [リーダブルコード](./04-development/01-coding-standards/03-readable-code.md) | 読みやすいコード14原則 |
| [命名規則](./04-development/01-coding-standards/04-naming-conventions.md) | ファイル、変数、関数、クラス |
| [Python規約](./04-development/01-coding-standards/05-python-rules.md) | PEP 8、型ヒント、docstring |
| [FastAPI規約](./04-development/01-coding-standards/06-fastapi-rules.md) | エンドポイント、DI、async/await |
| [ツール設定](./04-development/01-coding-standards/07-tools-setup.md) | Ruff、pytest、VSCode |

#### [レイヤー別実装](./04-development/02-layer-implementation/)

| ドキュメント | 内容 |
|------------|------|
| [モデル層](./04-development/02-layer-implementation/01-models.md) | SQLAlchemyモデル定義 |
| [スキーマ層](./04-development/02-layer-implementation/02-schemas.md) | Pydanticスキーマ |
| [リポジトリ層](./04-development/02-layer-implementation/03-repositories.md) | データアクセス層 |
| [サービス層](./04-development/02-layer-implementation/04-services.md) | ビジネスロジック層 |
| [API層](./04-development/02-layer-implementation/05-api.md) | エンドポイント実装 |

#### [デコレータ活用](./04-development/03-decorators/)

- [デコレータ使用例](./04-development/03-decorators/index.md) - ログ、トランザクション、キャッシュ、リトライなどの実践的な使用例

#### [データベース](./04-development/04-database/)

| ドキュメント | 内容 |
|------------|------|
| [SQLAlchemy基本](./04-development/04-database/01-sqlalchemy-basics.md) | ORM基礎 |
| [モデル関係](./04-development/04-database/02-model-relationships.md) | リレーションシップ定義 |
| [Alembic マイグレーション](./04-development/04-database/03-alembic-migrations.md) | マイグレーション管理 |
| [クエリパターン](./04-development/04-database/04-query-patterns.md) | 効率的なクエリ |

#### [API設計](./04-development/05-api-design/)

| ドキュメント | 内容 |
|------------|------|
| [API概要](./04-development/05-api-design/01-api-overview.md) | エンドポイント一覧 |
| [エンドポイント設計](./04-development/05-api-design/02-endpoint-design.md) | RESTful原則 |
| [バリデーション](./04-development/05-api-design/03-validation.md) | リクエスト検証 |
| [レスポンス設計](./04-development/05-api-design/04-response-design.md) | 統一的なレスポンス |
| [ページネーション](./04-development/05-api-design/05-pagination.md) | リスト取得パターン |
| [エラーレスポンス](./04-development/05-api-design/06-error-responses.md) | エラー処理 |

#### [セキュリティ実装](./04-development/06-security/)

| ドキュメント | 内容 |
|------------|------|
| [認証実装](./04-development/06-security/01-authentication.md) | JWT、OAuth2 |
| [認可制御](./04-development/06-security/02-authorization.md) | ロールベース制御 |
| [セキュリティベストプラクティス](./04-development/06-security/03-best-practices.md) | OWASP対策 |

#### [テスト](./04-development/07-testing/)

- [基本的なテスト](./04-development/07-testing/index.md) - ユニットテスト・APIテストの基礎

---

### [05. テスト](./05-testing/)

> 品質保証のためのテスト戦略

| ドキュメント | 内容 |
|------------|------|
| [テスト戦略](./05-testing/01-testing-strategy/index.md) | テストピラミッド、カバレッジ |
| [ユニットテスト](./05-testing/02-unit-testing/index.md) | pytest基礎 |
| [APIテスト](./05-testing/03-api-testing/index.md) | TestClient使用 |
| [データベーステスト](./05-testing/04-database-testing/index.md) | テストDB設定とパターン |
| [データベーステスト - セットアップ](./05-testing/04-database-testing/01-setup.md) | テストDB設定詳細 |
| [データベーステスト - パターン](./05-testing/04-database-testing/02-patterns.md) | テストパターン実装 |
| [モック・フィクスチャ](./05-testing/05-mocks-fixtures/index.md) | テストデータ管理 |
| [ベストプラクティス](./05-testing/06-best-practices/index.md) | 効果的なテスト |

---

### [06. 実装ガイド](./06-guides/)

> 具体的な実装手順

| ドキュメント | 内容 |
|------------|------|
| [エンドポイント追加](./06-guides/01-add-endpoint/index.md) | 新しいエンドポイントの作成 |
| [モデル追加](./06-guides/02-add-model/index.md) | モデル追加とマイグレーション |
| [機能モジュール追加](./06-guides/03-add-feature/index.md) | 機能全体の実装（モデル→API→テスト） |
| [ファイルアップロード実装](./06-guides/04-file-upload/index.md) | ファイル処理の実装 |
| [バックグラウンドタスク](./06-guides/05-background-tasks/index.md) | 非同期タスク処理 |
| [デプロイメント](./06-guides/06-deployment/index.md) | 本番環境デプロイ |
| [トラブルシューティング](./06-guides/07-troubleshooting/index.md) | よくある問題と解決方法 |

---

### [07. リファレンス](./07-reference/)

> 技術資料とリンク集

| ドキュメント | 内容 |
|------------|------|
| [API仕様](./07-reference/01-api-specification.md) | OpenAPI/Swagger仕様 |
| [データベーススキーマ](./07-reference/02-database-schema.md) | テーブル定義 |
| [環境変数](./07-reference/03-environment-variables.md) | 設定変数一覧 |
| [ユーティリティ関数](./07-reference/04-utils.md) | 共通関数リファレンス |
| [外部リソース](./07-reference/05-resources.md) | 学習リソース・公式ドキュメント |

---

### [08. 設計仕様書](./specifications/)

> 詳細な設計仕様書（アーキテクチャ、データベース、セキュリティ、API、インフラ、運用）

#### [アーキテクチャ仕様](./specifications/01-architecture/)

| ドキュメント | 内容 |
|------------|------|
| [システム設計](./specifications/01-architecture/01-system-design.md) | 全体アーキテクチャ |
| [コンポーネント設計](./specifications/01-architecture/02-component-design.md) | 各コンポーネントの詳細 |

#### [データベース仕様](./specifications/02-database/)

| ドキュメント | 内容 |
|------------|------|
| [データベース設計](./specifications/02-database/01-database-design.md) | DB設計詳細 |
| [ER図](./specifications/02-database/02-er-diagram.md) | エンティティ関係図 |
| [マイグレーション戦略](./specifications/02-database/03-migration-strategy.md) | マイグレーション管理 |

#### [セキュリティ仕様](./specifications/03-security/)

| ドキュメント | 内容 |
|------------|------|
| [RBAC設計](./specifications/03-security/01-rbac-design.md) | ロールベースアクセス制御 |
| [認証設計](./specifications/03-security/02-authentication-design.md) | 認証システム設計 |
| [セキュリティ実装](./specifications/03-security/03-security-implementation.md) | セキュリティ実装詳細 |

#### [API仕様](./specifications/04-api/)

| ドキュメント | 内容 |
|------------|------|
| [API設計](./specifications/04-api/01-api-design.md) | API設計詳細 |
| [エンドポイント仕様](./specifications/04-api/02-endpoint-specifications.md) | 各エンドポイント詳細 |
| [レスポンススキーマ](./specifications/04-api/03-response-schemas.md) | レスポンス定義 |

#### [インフラストラクチャ仕様](./specifications/05-infrastructure/)

| ドキュメント | 内容 |
|------------|------|
| [インフラ設計](./specifications/05-infrastructure/01-infrastructure-design.md) | インフラ構成 |
| [環境設定](./specifications/05-infrastructure/02-environment-configuration.md) | 環境別設定 |

#### [運用仕様](./specifications/06-operations/)

| ドキュメント | 内容 |
|------------|------|
| [デプロイ設計](./specifications/06-operations/01-deployment-design.md) | デプロイ戦略 |
| [モニタリング設計](./specifications/06-operations/02-monitoring-design.md) | 監視・ロギング |
| [保守手順](./specifications/06-operations/03-maintenance-procedures.md) | 運用保守 |

---

## 🚀 クイックリンク

- **[プロジェクト README](../README.md)** - プロジェクト概要
- **[API ドキュメント](http://localhost:8000/docs)** - Swagger UI（開発サーバー起動時）
- **[OpenAPI スキーマ](http://localhost:8000/openapi.json)** - API仕様

---

## 📚 推奨学習パス

### 初心者向け

1. [前提条件](./01-getting-started/01-prerequisites.md) → 環境準備
2. [Windows環境セットアップ](./01-getting-started/02-windows-setup.md) → PostgreSQL、Python、uvのインストール
3. [環境設定](./01-getting-started/04-environment-config.md) → 設定ファイル
4. [クイックスタート](./01-getting-started/05-quick-start.md) → APIを起動
5. [プロジェクト概要](./01-getting-started/06-project-overview.md) → 全体像を理解
6. [プロジェクト構造](./02-architecture/01-project-structure.md) → ディレクトリ構成
7. [レイヤードアーキテクチャ](./02-architecture/02-layered-architecture.md) → 4層アーキテクチャ

### 中級者向け

1. [コーディング規約](./04-development/01-coding-standards/) → 品質向上の基礎
2. [レイヤー別実装](./04-development/02-layer-implementation/) → 各層の実装方法
3. [デコレータ活用](./04-development/03-decorators/index.md) → 横断的関心事の実装
4. [基本的なテスト](./04-development/07-testing/index.md) → テストの書き方
5. [API設計](./04-development/05-api-design/) → RESTful設計
6. [機能モジュール追加](./06-guides/03-add-feature/index.md) → 機能実装の流れ
7. [コードリーディングガイド](./02-architecture/04-code-reading-guide.md) → コード詳細理解

### 上級者向け

1. [データベース詳細](./04-development/04-database/) → 高度なDB操作
2. [セキュリティ](./03-core-concepts/03-security/) → セキュリティ強化
3. [テスト戦略詳細](./05-testing/) → 包括的なテスト
4. [デプロイメント](./06-guides/06-deployment/index.md) → 本番運用
5. [設計仕様書](./specifications/) → 詳細な設計資料

---

## 💡 貢献

ドキュメントの改善提案や不明点があれば、Issue または Pull Request でお知らせください。
