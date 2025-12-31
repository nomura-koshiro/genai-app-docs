# バックエンドAPI ドキュメント

FastAPI + LangChain/LangGraphによるAIエージェントアプリケーションのバックエンドAPI開発者向けドキュメントです。

---

## 📖 目次

本ドキュメントは以下の2部構成になっています。

| Part | 内容 | 対象者 |
|------|------|--------|
| [Part 1: 開発者ガイド](#part-1-開発者ガイド) | 環境構築、実装方法、テスト、ベストプラクティス | 実装を行う開発者 |
| [Part 2: 詳細設計書](#part-2-詳細設計書) | システム設計、アーキテクチャ、機能仕様 | 設計理解・レビュー担当者 |

---

## Part 1: 開発者ガイド

> 実装を行う開発者向けの実践的なガイド

---

### [01. はじめに](./developer-guide/01-getting-started/)

> プロジェクトを始めるための必須ガイド

| ドキュメント | 内容 |
|------------|------|
| [前提条件](./developer-guide/01-getting-started/01-prerequisites.md) | Python 3.13、uv、PostgreSQL、Visual Studio Code |
| [Windows環境セットアップ](./developer-guide/01-getting-started/02-windows-setup.md) | PostgreSQL、Python、uvのインストール手順 |
| [VSCode セットアップ](./developer-guide/01-getting-started/03-vscode-setup.md) | 開発環境の設定と推奨拡張機能 |
| [環境設定](./developer-guide/01-getting-started/04-environment-config.md) | 環境別設定ファイルの管理 |
| [クイックスタート](./developer-guide/01-getting-started/05-quick-start.md) | 最速でAPIを起動する方法 |
| [プロジェクト概要](./developer-guide/01-getting-started/06-project-overview.md) | 全体構成・技術スタック・アーキテクチャ概要 |
| [データベース基礎](./developer-guide/01-getting-started/07-database-basics.md) | PostgreSQL & Redis の基本操作 |

---

### [02. アーキテクチャ](./developer-guide/02-architecture/)

> システム設計の理解

| ドキュメント | 内容 |
|------------|------|
| [プロジェクト構造](./developer-guide/02-architecture/01-project-structure.md) | ディレクトリ構造、各層の役割、命名規則 |
| [レイヤードアーキテクチャ](./developer-guide/02-architecture/02-layered-architecture.md) | 4層構造、データフロー、トランザクション管理 |
| [依存性注入](./developer-guide/02-architecture/03-dependency-injection.md) | FastAPI DIシステム、Dependsの使い方 |
| [コードリーディングガイド](./developer-guide/02-architecture/04-code-reading-guide.md) | コードベースを理解するための詳細ガイド |

---

### [03. コアコンセプト](./developer-guide/03-core-concepts/)

> 技術スタックと主要機能

### [テックスタック](./developer-guide/03-core-concepts/01-tech-stack/)

| ドキュメント | 内容 |
|------------|------|
| [Webフレームワーク](./developer-guide/03-core-concepts/01-tech-stack/01-web.md) | FastAPI、Pydantic、Alembic |
| [データレイヤー](./developer-guide/03-core-concepts/01-tech-stack/02-data.md) | PostgreSQL、SQLAlchemy、Redis |
| [AI・開発ツール](./developer-guide/03-core-concepts/01-tech-stack/03-ai-tools.md) | LangChain、LangGraph、uv、Ruff、pytest |

### データベース設計

- [データベース設計](./developer-guide/03-core-concepts/02-database-design/index.md) - モデル定義、リレーションシップ、パフォーマンス最適化

### [セキュリティ](./developer-guide/03-core-concepts/03-security/)

| ドキュメント | 内容 |
|------------|------|
| [セキュリティ概要](./developer-guide/03-core-concepts/03-security/index.md) | セキュリティ全体像 |
| [認証・認可](./developer-guide/03-core-concepts/03-security/01-authentication.md) | JWT、bcrypt、パスワード強度検証 |
| [リクエスト保護](./developer-guide/03-core-concepts/03-security/02-request-protection.md) | CORS、レート制限、バリデーション |
| [データ保護](./developer-guide/03-core-concepts/03-security/03-data-protection.md) | DBセキュリティ、ファイルアップロード |
| [インフラストラクチャ](./developer-guide/03-core-concepts/03-security/04-infrastructure.md) | エラーハンドリング、環境設定 |
| [ベストプラクティス](./developer-guide/03-core-concepts/03-security/05-best-practices.md) | セキュリティ強化の推奨事項 |

---

### [04. 開発ガイド](./developer-guide/04-development/)

> 実装のためのベストプラクティス

### [コーディング規約](./developer-guide/04-development/01-coding-standards/)

| ドキュメント | 内容 |
|------------|------|
| [基本原則](./developer-guide/04-development/01-coding-standards/01-basic-principles.md) | 型安全性、単一責任、DRY、KISS |
| [設計原則](./developer-guide/04-development/01-coding-standards/02-design-principles.md) | SOLID、Clean Architecture |
| [リーダブルコード](./developer-guide/04-development/01-coding-standards/03-readable-code.md) | 読みやすいコード14原則 |
| [命名規則](./developer-guide/04-development/01-coding-standards/04-naming-conventions.md) | ファイル、変数、関数、クラス |
| [Python規約](./developer-guide/04-development/01-coding-standards/05-python-rules.md) | PEP 8、型ヒント、docstring |
| [FastAPI規約](./developer-guide/04-development/01-coding-standards/06-fastapi-rules.md) | エンドポイント、DI、async/await |
| [ツール設定](./developer-guide/04-development/01-coding-standards/07-tools-setup.md) | Ruff、pytest、VSCode |

### [レイヤー別実装](./developer-guide/04-development/02-layer-implementation/)

| ドキュメント | 内容 |
|------------|------|
| [モデル層](./developer-guide/04-development/02-layer-implementation/01-models.md) | SQLAlchemyモデル定義 |
| [スキーマ層](./developer-guide/04-development/02-layer-implementation/02-schemas.md) | Pydanticスキーマ |
| [リポジトリ層](./developer-guide/04-development/02-layer-implementation/03-repositories.md) | データアクセス層 |
| [サービス層](./developer-guide/04-development/02-layer-implementation/04-services.md) | ビジネスロジック層 |
| [API層](./developer-guide/04-development/02-layer-implementation/05-api.md) | エンドポイント実装 |

### [デコレータ活用](./developer-guide/04-development/03-decorators/)

- [デコレータ使用例](./developer-guide/04-development/03-decorators/index.md) - ログ、トランザクション、キャッシュ、リトライなどの実践的な使用例

### [データベース](./developer-guide/04-development/04-database/)

| ドキュメント | 内容 |
|------------|------|
| [SQLAlchemy基本](./developer-guide/04-development/04-database/01-sqlalchemy-basics.md) | ORM基礎 |
| [モデル関係](./developer-guide/04-development/04-database/02-model-relationships.md) | リレーションシップ定義 |
| [Alembic マイグレーション](./developer-guide/04-development/04-database/03-alembic-migrations.md) | マイグレーション管理 |
| [クエリパターン](./developer-guide/04-development/04-database/04-query-patterns.md) | 効率的なクエリ |

### [API設計](./developer-guide/04-development/05-api-design/)

| ドキュメント | 内容 |
|------------|------|
| [API概要](./developer-guide/04-development/05-api-design/01-api-overview.md) | エンドポイント一覧 |
| [エンドポイント設計](./developer-guide/04-development/05-api-design/02-endpoint-design.md) | RESTful原則 |
| [バリデーション](./developer-guide/04-development/05-api-design/03-validation.md) | リクエスト検証 |
| [レスポンス設計](./developer-guide/04-development/05-api-design/04-response-design.md) | 統一的なレスポンス |
| [ページネーション](./developer-guide/04-development/05-api-design/05-pagination.md) | リスト取得パターン |
| [エラーレスポンス](./developer-guide/04-development/05-api-design/06-error-responses.md) | エラー処理 |

### [セキュリティ実装](./developer-guide/04-development/06-security/)

| ドキュメント | 内容 |
|------------|------|
| [認証実装](./developer-guide/04-development/06-security/01-authentication.md) | JWT、OAuth2 |
| [認可制御](./developer-guide/04-development/06-security/02-authorization.md) | ロールベース制御 |
| [セキュリティベストプラクティス](./developer-guide/04-development/06-security/03-best-practices.md) | OWASP対策 |

### [テスト](./developer-guide/04-development/07-testing/)

- [基本的なテスト](./developer-guide/04-development/07-testing/index.md) - ユニットテスト・APIテストの基礎

---

### [05. テスト](./developer-guide/05-testing/)

> 品質保証のためのテスト戦略

| ドキュメント | 内容 |
|------------|------|
| [テスト戦略](./developer-guide/05-testing/01-testing-strategy/index.md) | テストピラミッド、カバレッジ |
| [ユニットテスト](./developer-guide/05-testing/02-unit-testing/index.md) | pytest基礎 |
| [APIテスト](./developer-guide/05-testing/03-api-testing/index.md) | TestClient使用 |
| [データベーステスト](./developer-guide/05-testing/04-database-testing/index.md) | テストDB設定とパターン |
| [データベーステスト - セットアップ](./developer-guide/05-testing/04-database-testing/01-setup.md) | テストDB設定詳細 |
| [データベーステスト - パターン](./developer-guide/05-testing/04-database-testing/02-patterns.md) | テストパターン実装 |
| [モック・フィクスチャ](./developer-guide/05-testing/05-mocks-fixtures/index.md) | テストデータ管理 |
| [ベストプラクティス](./developer-guide/05-testing/06-best-practices/index.md) | 効果的なテスト |

---

### [06. 実装ガイド](./developer-guide/06-guides/)

> 具体的な実装手順

| ドキュメント | 内容 |
|------------|------|
| [エンドポイント追加](./developer-guide/06-guides/01-add-endpoint/index.md) | 新しいエンドポイントの作成 |
| [モデル追加](./developer-guide/06-guides/02-add-model/index.md) | モデル追加とマイグレーション |
| [機能モジュール追加](./developer-guide/06-guides/03-add-feature/index.md) | 機能全体の実装（モデル→API→テスト） |
| [ファイルアップロード実装](./developer-guide/06-guides/04-file-upload/index.md) | ファイル処理の実装 |
| [バックグラウンドタスク](./developer-guide/06-guides/05-background-tasks/index.md) | 非同期タスク処理 |
| [デプロイメント](./developer-guide/06-guides/06-deployment/index.md) | 本番環境デプロイ |
| [トラブルシューティング](./developer-guide/06-guides/07-troubleshooting/index.md) | よくある問題と解決方法 |

---

### [07. リファレンス](./developer-guide/07-reference/)

> 技術資料とリンク集

| ドキュメント | 内容 |
|------------|------|
| [API仕様](./developer-guide/07-reference/01-api-specification.md) | OpenAPI/Swagger仕様 |
| [データベーススキーマ](./developer-guide/07-reference/02-database-schema.md) | テーブル定義 |
| [環境変数](./developer-guide/07-reference/03-environment-variables.md) | 設定変数一覧 |
| [ユーティリティ関数](./developer-guide/07-reference/04-utils.md) | 共通関数リファレンス |
| [外部リソース](./developer-guide/07-reference/05-resources.md) | 学習リソース・公式ドキュメント |

---

## Part 2: 詳細設計書

> システム設計・アーキテクチャ・機能仕様の詳細ドキュメント

---

### [01. ユースケース](./specifications/01-usercases/)

> ユーザーストーリーと業務フロー

| ドキュメント | 内容 |
|------------|------|
| [ユースケース定義](./specifications/01-usercases/01-usecases.md) | ユーザーストーリー、機能要件 |
| [ユースケースフロー分析](./specifications/01-usercases/02-usecase-flow-analysis.md) | 業務フロー、処理フロー分析 |
| [ユースケースシーケンス図](./specifications/01-usercases/03-usecase-sequence-diagrams.md) | システム間連携、シーケンス図 |
| [ユースケースフローチャート](./specifications/01-usercases/04-usecase-flowcharts.md) | 処理フローチャート |

---

### [02. 画面遷移](./specifications/02-screen-transition/)

> UI/UX設計

| ドキュメント | 内容 |
|------------|------|
| [画面遷移図](./specifications/02-screen-transition/01-screen-transition.md) | 画面フロー、ナビゲーション設計 |

---

### [03. モックアップ](./specifications/03-mockup/)

> UI設計・画面レイアウト

| ドキュメント | 内容 |
|------------|------|
| ワイヤーフレーム | UI設計、画面レイアウト |

---

### [04. アーキテクチャ仕様](./specifications/04-architecture/)

> システム構成と設計パターン

| ドキュメント | 内容 |
|------------|------|
| [システムアーキテクチャ設計](./specifications/04-architecture/01-system-architecture.md) | 5層アーキテクチャ、技術スタック、設計パターン、データフロー |

---

### [05. セキュリティ仕様](./specifications/05-security/)

> 認証・認可・セキュリティ対策

| ドキュメント | 内容 |
|------------|------|
| [RBAC設計](./specifications/05-security/01-rbac-design.md) | 2層ロール構造（System/Project）、権限マトリックス |
| [認証/認可設計](./specifications/05-security/02-authentication-design.md) | マルチモード認証、Azure AD JWT連携フロー |
| [セキュリティ実装詳細](./specifications/05-security/03-security-implementation.md) | OWASP Top 10対策、多層防御モデル、セキュリティヘッダー |

---

### [06. データベース仕様](./specifications/06-database/)

> データモデルとスキーマ設計

| ドキュメント | 内容 |
|------------|------|
| [データベース設計](./specifications/06-database/01-database-design.md) | テーブル設計、カラム仕様、インデックス戦略 |
| [ER図](./specifications/06-database/02-er-diagram.md) | エンティティ関連図 |

---

### [07. データフロー仕様](./specifications/07-dataflow/)

> システム間のデータ連携

| ドキュメント | 内容 |
|------------|------|
| [データフロー設計](./specifications/07-dataflow/01-dataflow-design.md) | リクエスト/レスポンスフロー、分析フロー、認証フロー |

---

### [08. コンポーネント仕様](./specifications/08-components/)

> 共通コンポーネントと基盤機能

| ドキュメント | 内容 |
|------------|------|
| [コンポーネント設計](./specifications/08-components/01-component-design.md) | BaseRepository、デコレータ、StorageService、CacheManager |

---

### [09. ミドルウェア仕様](./specifications/09-middleware/)

> リクエスト処理パイプライン

| ドキュメント | 内容 |
|------------|------|
| [ミドルウェア設計](./specifications/09-middleware/01-middleware-design.md) | ミドルウェアスタック、実行順序、パフォーマンス影響 |

---

### [10. AI/エージェント仕様](./specifications/10-ai-agent/)

> LangChain/LangGraph統合

| ドキュメント | 内容 |
|------------|------|
| [AI/エージェント機能設計](./specifications/10-ai-agent/01-ai-agent-design.md) | LangChain AnalysisAgent、ツール実装、状態管理 |

---

### [11. 機能別詳細設計](./specifications/11-features/)

> 各機能の詳細仕様

| ドキュメント | 内容 |
|------------|------|
| [API概要](./specifications/11-features/01-api-overview/01-api-overview.md) | エンドポイント一覧、API設計方針 |
| [ユーザー管理](./specifications/11-features/02-user-management/01-user-management-design.md) | ユーザーアカウント、認証、セッション管理 |
| [プロジェクト管理](./specifications/11-features/03-project-management/01-project-management-design.md) | プロジェクトCRUD、メンバー管理、ファイル管理 |
| [分析機能](./specifications/11-features/04-analysis/01-analysis-design.md) | 分析セッション、AIエージェント連携 |
| [ドライバーツリー](./specifications/11-features/05-driver-tree/01-driver-tree-design.md) | ツリー構造、ノード管理、計算ロジック |
| [ダッシュボード](./specifications/11-features/06-dashboard/01-dashboard-design.md) | メトリクス表示、グラフ、統計情報 |
| [テンプレート](./specifications/11-features/07-template/01-template-design.md) | 分析テンプレート管理 |
| [コピー/エクスポート](./specifications/11-features/08-copy-export/01-copy-export-design.md) | データコピー、エクスポート機能 |
| [ファイルバージョン](./specifications/11-features/09-file-version/01-file-version-design.md) | ファイルバージョン管理 |
| [システム管理](./specifications/11-features/10-system-admin/01-system-admin-design.md) | システム設定、監査ログ、アクティビティ追跡 |

---

### [12. 環境設定仕様](./specifications/12-configuration/)

> 環境別設定管理

| ドキュメント | 内容 |
|------------|------|
| [環境設定書](./specifications/12-configuration/01-environment-configuration.md) | 環境別設定管理（local/staging/production）、設定項目、Pydantic検証 |

---

### [13. テスト仕様](./specifications/13-testing/)

> テスト戦略と品質基準

| ドキュメント | 内容 |
|------------|------|
| [テスト戦略](./specifications/13-testing/01-test-strategy.md) | テストピラミッド、カバレッジ目標 |

---

## クイックリンク

- **[プロジェクト README](../README.md)** - プロジェクト概要
- **[API ドキュメント](http://localhost:8000/docs)** - Swagger UI（開発サーバー起動時）
- **[OpenAPI スキーマ](http://localhost:8000/openapi.json)** - API仕様

---

## 推奨学習パス

### 初心者向け

1. [前提条件](./developer-guide/01-getting-started/01-prerequisites.md) → 環境準備
2. [Windows環境セットアップ](./developer-guide/01-getting-started/02-windows-setup.md) → PostgreSQL、Python、uvのインストール
3. [環境設定](./developer-guide/01-getting-started/04-environment-config.md) → 設定ファイル
4. [クイックスタート](./developer-guide/01-getting-started/05-quick-start.md) → APIを起動
5. [プロジェクト概要](./developer-guide/01-getting-started/06-project-overview.md) → 全体像を理解
6. [プロジェクト構造](./developer-guide/02-architecture/01-project-structure.md) → ディレクトリ構成
7. [レイヤードアーキテクチャ](./developer-guide/02-architecture/02-layered-architecture.md) → 4層アーキテクチャ

### 中級者向け

1. [コーディング規約](./developer-guide/04-development/01-coding-standards/) → 品質向上の基礎
2. [レイヤー別実装](./developer-guide/04-development/02-layer-implementation/) → 各層の実装方法
3. [デコレータ活用](./developer-guide/04-development/03-decorators/index.md) → 横断的関心事の実装
4. [基本的なテスト](./developer-guide/04-development/07-testing/index.md) → テストの書き方
5. [API設計](./developer-guide/04-development/05-api-design/) → RESTful設計
6. [機能モジュール追加](./developer-guide/06-guides/03-add-feature/index.md) → 機能実装の流れ
7. [コードリーディングガイド](./developer-guide/02-architecture/04-code-reading-guide.md) → コード詳細理解

### 上級者向け

1. [データベース詳細](./developer-guide/04-development/04-database/) → 高度なDB操作
2. [セキュリティ](./developer-guide/03-core-concepts/03-security/) → セキュリティ強化
3. [テスト戦略詳細](./developer-guide/05-testing/) → 包括的なテスト
4. [デプロイメント](./developer-guide/06-guides/06-deployment/index.md) → 本番運用
5. [詳細設計書](./specifications/) → システム設計の深掘り

---

### 貢献

ドキュメントの改善提案や不明点があれば、Issue または Pull Request でお知らせください。
