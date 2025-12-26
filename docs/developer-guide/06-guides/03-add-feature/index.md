# 新しい機能モジュールの追加

このガイドでは、完全な機能モジュール（モデル、リポジトリ、サービス、API）を追加する手順を説明します。

## 目次

- [概要](#概要)
- [前提条件](#前提条件)
- [例: タスク管理機能](#例-タスク管理機能)
- [実装ステップ](#実装ステップ)
- [参考リンク](#参考リンク)

## 概要

完全な機能モジュールには以下のコンポーネントが含まれます：

```text
タスク管理機能
├── モデル層（models/task/task.py）
├── リポジトリ層（repositories/task/task.py）
├── サービス層（services/task/__init__.py, crud.py）  ← Facadeパターン
├── スキーマ層（schemas/task/task.py）
├── API層（api/routes/v1/task/tasks.py）
├── マイグレーション（alembic/versions/xxx_add_task_table.py）
└── テスト（tests/api/routes/v1/task/test_tasks.py）
```

**プロジェクト構造について:**

このプロジェクトでは、機能ごとにサブディレクトリを作成して整理しています。各機能は以下のような構造になります：

```text
src/app/
├── models/task/           # タスク機能のモデル
│   ├── __init__.py
│   └── task.py
├── repositories/task/     # タスク機能のリポジトリ
│   ├── __init__.py
│   └── task.py
├── schemas/task/          # タスク機能のスキーマ
│   ├── __init__.py
│   └── task.py
├── services/task/         # タスク機能のサービス（Facadeパターン）
│   ├── __init__.py        # TaskService（Facade）
│   ├── base.py            # 共通ベースクラス
│   └── crud.py            # TaskCrudService
└── api/routes/v1/task/    # タスク機能のエンドポイント
    ├── __init__.py
    └── tasks.py
```

## 前提条件

- [新しいモデル追加](./02-add-model.md)の理解
- [新しいエンドポイント追加](./01-add-endpoint.md)の理解
- プロジェクトのアーキテクチャパターンの理解
- FastAPIとSQLAlchemyの基礎知識

## 例: タスク管理機能

このガイドでは、完全なCRUD機能を持つタスク管理モジュールを例として使用します。

**タスク管理機能の要件:**

- タスクの作成、読み取り、更新、削除（CRUD）
- タスクの優先度設定（低、中、高）
- タスクのステータス管理（未着手、進行中、完了）
- ユーザーごとのタスク管理
- タスクの期限設定
- タスクの検索とフィルタリング

## 実装ステップ

機能モジュール追加は以下の手順で行います：

### ステップ1-3: データモデルの作成

モデル定義、マイグレーション作成について詳しく知りたい場合は、以下のドキュメントを参照してください：

**[→ ステップ1-3: データモデルとマイグレーション](./03-add-feature-models.md)**

- ステップ1: 要件定義
- ステップ2: データモデルの設計（エンティティ定義、既存モデルの更新、モデルのインポート）
- ステップ3: マイグレーションの作成と適用

### ステップ4-5: スキーマとリポジトリの作成

Pydanticスキーマとリポジトリの実装について詳しく知りたい場合は、以下のドキュメントを参照してください：

**[→ ステップ4-5: スキーマとリポジトリ](./03-add-feature-schemas-repos.md)**

- ステップ4: Pydanticスキーマの作成（Base/Create/Update/Response/List/Stats）
- ステップ5: リポジトリの作成（カスタムクエリメソッド含む）

### ステップ6-9: サービスとAPIの実装

ビジネスロジック、依存性注入、APIルートの作成について詳しく知りたい場合は、以下のドキュメントを参照してください：

**[→ ステップ6-9: サービスとAPI](./03-add-feature-services-api.md)**

- ステップ6: サービスの作成（ビジネスロジック実装）
- ステップ7: 依存性注入の設定
- ステップ8: APIルートの作成
- ステップ9: ルーターの登録

### ステップ10: テストの作成

テスト作成とベストプラクティスについて詳しく知りたい場合は、以下のドキュメントを参照してください：

**[→ ステップ10: テストとベストプラクティス](./03-add-feature-testing.md)**

- ステップ10: テストの作成（サービステスト、APIテスト）
- チェックリスト（計画・設計、実装、テスト、ドキュメント）
- よくある落とし穴
- ベストプラクティス

## 参考リンク

### プロジェクト内リンク

- [新しいモデル追加](./02-add-model.md)
- [新しいエンドポイント追加](./01-add-endpoint.md)
- [アーキテクチャ概要](../02-architecture/01-overview.md)
- [テスト戦略](../05-testing/01-unit-testing.md)

### 公式ドキュメント

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Pydantic](https://docs.pydantic.dev/)
