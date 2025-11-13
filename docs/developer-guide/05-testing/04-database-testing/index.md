# データベーステスト

このドキュメントでは、SQLAlchemyを使用した非同期データベーステストの方法を説明します。

## 目次

- [概要](#概要)
- [ドキュメント構成](#ドキュメント構成)
- [参考リンク](#参考リンク)

## 概要

データベーステストは、データベース層の操作（CRUD操作、クエリ、リレーション）が正しく動作するかを検証します。

### データベーステストの重要性

- **データ整合性の保証**: モデルの制約とリレーションが正しく機能することを確認
- **クエリの正確性**: 複雑なクエリが期待通りの結果を返すことを検証
- **パフォーマンスの確認**: N+1問題などの性能問題を早期発見
- **リグレッションの防止**: データベーススキーマ変更時の影響を検出

### テスト戦略

このプロジェクトでは、以下のテスト戦略を採用しています：

1. **独立したテストデータベース**: PostgreSQL（Docker）を使用
2. **自動セットアップ**: pytest fixtureによる自動的なテーブル作成・削除
3. **テスト間の独立性**: 各テスト関数で完全にクリーンな状態を保証
4. **非同期対応**: AsyncSessionとasyncioを使用した効率的なテスト

## ドキュメント構成

データベーステストに関する詳細な情報は、以下のドキュメントに分割されています：

### テストデータベースのセットアップ

テストデータベースの構築、環境設定、conftest.pyの実装について詳しく知りたい場合は、以下のドキュメントを参照してください：

**[→ テストデータベースのセットアップ](./04-database-testing-setup.md)**

- テスト専用データベースの自動作成
- 環境設定
- conftest.pyの実装例
- フィクスチャの作成
- テストの実行方法

### テストパターンとベストプラクティス

具体的なテストパターン、よくある問題と解決策、ベストプラクティスについて詳しく知りたい場合は、以下のドキュメントを参照してください：

**[→ テストパターンとベストプラクティス](./04-database-testing-patterns.md)**

- モデルのテスト（CRUD操作、ユニーク制約）
- リレーションシップのテスト（1対多、多対多、カスケード削除）
- クエリのテスト（基本クエリ、複雑なクエリ、集計）
- トランザクションのテスト
- テストデータの管理（ファクトリパターン、フィクスチャ）
- よくある間違いと対処法
- ベストプラクティス

## 参考リンク

### 公式ドキュメント

- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Database Testing](https://fastapi.tiangolo.com/advanced/testing-database/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

### プロジェクト内リンク

- [ユニットテスト](./01-unit-testing.md)
- [統合テスト](./02-integration-testing.md)
- [モックとフィクスチャ](./05-mocks-fixtures.md)
- [テストベストプラクティス](./06-best-practices.md)

## 次のステップ

データベーステストの詳細を学ぶには、以下のドキュメントから始めてください：

1. まず **[テストデータベースのセットアップ](./04-database-testing-setup.md)** でテスト環境を構築
2. 次に **[テストパターンとベストプラクティス](./04-database-testing-patterns.md)** で実践的なテスト方法を学習
