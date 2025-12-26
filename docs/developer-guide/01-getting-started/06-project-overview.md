# プロジェクト概要

このドキュメントでは、プロジェクト全体の構成を高レベルで理解します。

---

## プロジェクトの目的

このプロジェクトは、**FastAPI + LangChain/LangGraphによるAIエージェントアプリケーション**のバックエンドAPIです。

主な機能:

- ユーザー認証・認可（JWT）
- AIエージェントとの対話セッション管理
- ファイルアップロード・管理
- RESTful API提供

---

## 技術スタック概要

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| **Webフレームワーク** | FastAPI | 高速なREST API構築 |
| **データベース** | PostgreSQL | メインデータストア |
| **キャッシュ** | Redis | セッション・レート制限 |
| **ORM** | SQLAlchemy | データベース操作 |
| **AI** | LangChain/LangGraph | AIエージェント実装 |
| **認証** | JWT + bcrypt | セキュアな認証 |

---

## ディレクトリ構造の概要

```text
src/app/
├── api/                      # APIレイヤー
│   ├── routes/               # エンドポイント定義
│   │   ├── v1/               # APIバージョン1
│   │   │   ├── user_accounts/  # ユーザーアカウント管理（Azure AD）
│   │   │   ├── project/        # プロジェクト管理
│   │   │   ├── analysis/       # 分析機能（LangGraph）
│   │   │   ├── driver_tree/    # ドライバーツリー
│   │   │   ├── ppt_generator/  # PPT生成
│   │   │   └── sample/         # サンプル機能（JWT認証）
│   │   └── system/           # システムAPI（ヘルスチェック等）
│   ├── middlewares/          # ミドルウェア
│   ├── decorators/           # デコレータ
│   └── core/                 # API共通機能
├── models/                   # データベースモデル（テーブル定義）
│   ├── user_account/         # ユーザーアカウントモデル
│   ├── project/              # プロジェクト関連モデル
│   ├── analysis/             # 分析関連モデル
│   ├── driver_tree/          # ドライバーツリーモデル
│   └── sample/               # サンプルモデル
├── schemas/                  # Pydanticスキーマ（バリデーション）
├── repositories/             # データアクセス層
├── services/                 # ビジネスロジック層
├── utils/                    # ユーティリティ
├── data/                     # データファイル（YML、JSON等）
└── core/                     # コア機能（設定・セキュリティ・例外・ログ）
```

---

## アーキテクチャの階層

このプロジェクトは**4層アーキテクチャ**を採用しています:

```text
┌─────────────────────────┐
│   API層 (api/)          │  ← HTTPリクエスト受付
├─────────────────────────┤
│   サービス層 (services/)│  ← ビジネスロジック
├─────────────────────────┤
│ リポジトリ層 (repos/)   │  ← データアクセス
├─────────────────────────┤
│   モデル層 (models/)    │  ← データベーステーブル
└─────────────────────────┘
```

**各層の役割**:

- **API層**: エンドポイント定義、リクエスト検証、レスポンス返却
- **サービス層**: ビジネスロジック、トランザクション管理
- **リポジトリ層**: データベースCRUD操作
- **モデル層**: テーブル構造定義、リレーション定義

---

## データフロー例

### 例1: プロジェクト作成（本番機能、Azure AD認証）

```text
1. クライアント → POST /api/v1/projects
   - Authorizationヘッダー: Bearer <Azure AD token>
                   ↓
2. API層 (routes/v1/project/project.py)
   - Azure ADトークン検証（認証ミドルウェア）
   - リクエストボディをバリデーション (Pydanticスキーマ)
                   ↓
3. サービス層 (services/project/project/__init__.py → crud.py)
   - ProjectService（Facade）→ ProjectCrudService に委譲
   - プロジェクトコード重複チェック
   - トランザクション管理
   - プロジェクトメンバーシップ作成（作成者をOWNERとして追加）
                   ↓
4. リポジトリ層 (repositories/project/project.py)
   - データベースにINSERT
                   ↓
5. モデル層 (models/project/project.py, models/project/project_member.py)
   - projectsテーブルとproject_membersテーブルに保存
                   ↓
6. レスポンス ← 201 Created + プロジェクト情報
```

### 例2: ユーザー認証（Azure AD）

```text
1. クライアント → GET /api/v1/user-accounts/me
   - Authorizationヘッダー: Bearer <Azure AD token>
                   ↓
2. API層 (routes/v1/user_accounts/user_accounts.py)
   - Azure ADトークン検証
                   ↓
3. サービス層 (services/user_account/user_account/__init__.py → auth.py)
   - UserAccountService（Facade）→ UserAccountAuthService に委譲
   - Azure OIDでユーザー取得または作成
                   ↓
4. リポジトリ層 (repositories/user_account/user_account.py)
   - データベースからSELECT/INSERT
                   ↓
5. モデル層 (models/user_account/user_account.py)
   - user_accountsテーブル
                   ↓
6. レスポンス ← 200 OK + ユーザー情報
```

---

## 主要な機能モジュール

このプロジェクトは、**本番機能**と**レガシーサンプル機能**に分かれています。

### 本番機能（Azure AD認証対応）

#### 1. ユーザーアカウント管理 (`user_accounts`)

- Azure AD Object IDによるユーザー識別
- システムレベルのロール管理（SystemAdmin/User）
- プロジェクトメンバーシップとの関連
- テーブル: `users`（UUID主キー）

#### 2. プロジェクト管理 (`project`)

- プロジェクト作成・管理
- プロジェクトメンバーシップ管理
- プロジェクトレベルのロール（ProjectManager/ProjectModerator/Member/Viewer）
- ファイルアップロード・管理
- テーブル: `projects`, `project_members`, `project_files`

#### 3. 分析機能 (`analysis`)

- LangGraphエージェントによるデータ分析
- 分析セッション管理
- 分析ステップとチャート管理
- validation設定管理
- チャット履歴・スナップショット履歴
- テーブル: `analysis_sessions`, `analysis_steps`, `analysis_files`, `analysis_templates`, `analysis_template_charts`

#### 4. ドライバーツリー (`driver_tree`)

- KPI分解ツリーの管理
- ノード間の親子関係管理
- 数式演算子の定義
- カテゴリ管理
- テーブル: `driver_trees`, `driver_tree_nodes`, `driver_tree_categories`

#### 5. PPT生成 (`ppt_generator`)

- PowerPointファイル生成
- テンプレートベースのスライド作成

### レガシー機能（JWT認証サンプル）

#### 6. サンプルユーザー認証 (`sample`)

- ユーザー登録・ログイン（JWT）
- パスワードハッシュ化（bcrypt）
- リフレッシュトークン・APIキー生成
- セッション管理
- ファイルアップロード
- テーブル: `sample_users`, `sample_sessions`, `sample_files`（integer主キー）

**注意**: `sample`機能は開発・学習用のレガシーコードです。本番環境では`user_accounts`とAzure AD認証を使用してください。

---

## セキュリティ機能

### 本番環境（Azure AD認証）

- **Azure AD認証**: Microsoft IDプラットフォームによる統合認証
- **トークン検証**: JWTベアラートークン検証
- **RBAC**: システムレベル（SystemAdmin/User）とプロジェクトレベル（ProjectManager/ProjectModerator/Member/Viewer）のロール管理
- **CORS設定**: オリジン制限、認証情報の許可
- **入力バリデーション**: Pydantic自動検証
- **SQLインジェクション対策**: SQLAlchemy ORM使用
- **セキュリティヘッダー**: X-Content-Type-Options、X-Frame-Options等

### レガシー環境（JWT認証）

- **パスワードハッシュ化**: bcrypt（コスト12ラウンド）
- **JWT認証**: HS256署名、有効期限管理
- **リフレッシュトークン**: トークン更新機能
- **アカウントロック**: ログイン失敗回数制限
- **レート制限**: Redisベース（オプション）

---

## 開発環境

- **Python**: 3.13
- **パッケージマネージャ**: uv（高速な依存関係管理）
- **データベース**: PostgreSQL（ローカルインストール）
- **キャッシュ**: Redis（オプション）
- **VSCode**: 推奨エディタ（拡張機能設定済み）
- **Linter/Formatter**: Ruff（高速なPythonツール）

---

## 次のステップ

このプロジェクト概要を理解したら、次はアーキテクチャの詳細を学びましょう:

1. **[プロジェクト構造](../02-architecture/01-project-structure.md)** - ディレクトリ構造の詳細
2. **[レイヤードアーキテクチャ](../02-architecture/02-layered-architecture.md)** - 4層アーキテクチャの詳細
3. **[依存性注入](../02-architecture/03-dependency-injection.md)** - FastAPI DIの使い方

---

## 関連ドキュメント

- [前提条件](./01-prerequisites.md) - 開発環境の準備
- [Windows環境セットアップ](./02-windows-setup.md) - PostgreSQL、Python、uvのインストール
- [クイックスタート](./05-quick-start.md) - 最速でAPIを起動
