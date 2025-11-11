# データベース設計書

## 文書管理情報

| 項目 | 内容 |
|------|------|
| 文書名 | データベース設計書 |
| バージョン | 1.0 |
| 作成日 | 2025-01-11 |
| 最終更新日 | 2025-01-11 |
| 作成者 | Claude Code |
| 対象システム | genai-app-docs (camp-backend) |
| DBMS | PostgreSQL 14+ |
| ORM | SQLAlchemy 2.0 (非同期) |

---

## 目次

1. [概要](#1-概要)
2. [データベース全体設計](#2-データベース全体設計)
3. [テーブル定義](#3-テーブル定義)
4. [ER図](#4-er図)
5. [インデックス設計](#5-インデックス設計)
6. [データ型設計](#6-データ型設計)
7. [制約設計](#7-制約設計)
8. [接続管理](#8-接続管理)
9. [パフォーマンス最適化](#9-パフォーマンス最適化)
10. [バックアップ戦略](#10-バックアップ戦略)
11. [マイグレーション戦略](#11-マイグレーション戦略)
12. [付録](#12-付録)

---

## 1. 概要

### 1.1 目的

本文書は、genai-app-docsプロジェクトのデータベース設計の詳細を定義します。

### 1.2 データベース構成

**DBMS:** PostgreSQL 14以降
**ORM:** SQLAlchemy 2.0（非同期）
**マイグレーションツール:** Alembic 1.13+

### 1.3 設計方針

1. **UUID主キー**: すべてのテーブルでUUID v4を使用
2. **タイムスタンプ管理**: created_at/updated_atを自動管理
3. **非同期対応**: SQLAlchemy 2.0の非同期APIを使用
4. **JSONB活用**: 柔軟なデータ構造にはJSONBを使用
5. **カスケード削除**: 親レコード削除時の子レコード処理を明確化

### 1.4 テーブルカテゴリ

| カテゴリ | 説明 | テーブル数 |
|---------|------|-----------|
| ユーザー管理 | 認証・認可 | 2 |
| プロジェクト管理 | プロジェクト・メンバー・ファイル | 3 |
| データ分析 | 分析セッション・ステップ・テンプレート | 5 |
| ドライバーツリー | ツリー構造・ノード・カテゴリ | 3 |
| サンプル | 開発用サンプルデータ | 3 |
| **合計** | | **16** |

---

## 2. データベース全体設計

### 2.1 全体ER図

```mermaid
erDiagram
    %% ユーザー管理
    User ||--o{ ProjectMember : "has many"
    User ||--o{ AnalysisSession : "creates"

    %% プロジェクト管理
    Project ||--o{ ProjectMember : "has many"
    Project ||--o{ ProjectFile : "has many"
    Project ||--o{ AnalysisSession : "has many"

    ProjectMember }o--|| User : "belongs to"
    ProjectMember }o--|| Project : "belongs to"

    ProjectFile }o--|| Project : "belongs to"

    %% データ分析
    AnalysisSession ||--o{ AnalysisStep : "has many"
    AnalysisSession ||--o{ AnalysisFile : "has many"
    AnalysisSession }o--|| Project : "belongs to"
    AnalysisSession }o--|| User : "created by"

    AnalysisStep }o--|| AnalysisSession : "belongs to"
    AnalysisFile }o--|| AnalysisSession : "belongs to"

    AnalysisTemplate ||--o{ AnalysisTemplateChart : "has many"
    AnalysisTemplateChart }o--|| AnalysisTemplate : "belongs to"

    %% ドライバーツリー
    DriverTree ||--o{ DriverTreeNode : "has many"
    DriverTreeNode }o--|| DriverTree : "belongs to"
    DriverTreeNode }o--o| DriverTreeNode : "parent-child"

    DriverTreeCategory ||--o{ DriverTreeNode : "categorizes"
    DriverTreeNode }o--|| DriverTreeCategory : "has category"

    User {
        uuid id PK
        string azure_oid UK
        string email UK
        string display_name
        json roles "SystemRole[]"
        boolean is_active
        timestamp last_login
        timestamp created_at
        timestamp updated_at
    }

    Project {
        uuid id PK
        string name
        string code UK
        text description
        boolean is_active
        uuid created_by
        timestamp created_at
        timestamp updated_at
    }

    ProjectMember {
        uuid id PK
        uuid project_id FK
        uuid user_id FK
        enum role "ProjectRole"
        uuid added_by FK
        timestamp joined_at
    }

    ProjectFile {
        uuid id PK
        uuid project_id FK
        string filename
        string file_path
        integer file_size
        string mime_type
        uuid uploaded_by FK
        timestamp uploaded_at
    }

    AnalysisSession {
        uuid id PK
        uuid project_id FK
        uuid created_by FK
        string session_name
        jsonb validation_config
        jsonb chat_history
        jsonb snapshot_history
        uuid original_file_id
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    AnalysisStep {
        uuid id PK
        uuid session_id FK
        string step_name
        string step_type
        integer step_order
        string data_source
        jsonb config
        text result_data_path
        jsonb result_chart
        jsonb result_formula
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    AnalysisFile {
        uuid id PK
        uuid session_id FK
        string filename
        string file_path
        integer file_size
        string mime_type
        timestamp uploaded_at
    }

    AnalysisTemplate {
        uuid id PK
        string template_name
        text description
        jsonb config
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    AnalysisTemplateChart {
        uuid id PK
        uuid template_id FK
        string chart_name
        string chart_type
        jsonb config
        integer display_order
        timestamp created_at
    }

    DriverTree {
        uuid id PK
        string tree_name
        text description
        jsonb metadata
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeNode {
        uuid id PK
        uuid tree_id FK
        uuid parent_id FK
        uuid category_id FK
        string node_name
        text description
        integer level
        integer display_order
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeCategory {
        uuid id PK
        string category_name
        string color_code
        integer display_order
        timestamp created_at
    }
```

### 2.2 テーブル一覧

| # | テーブル名 | 説明 | 行数目安 |
|---|-----------|------|---------|
| **ユーザー管理** | | | |
| 1 | `users` | Azure AD認証用ユーザー | 100-1,000 |
| **プロジェクト管理** | | | |
| 2 | `projects` | プロジェクト | 10-100 |
| 3 | `project_members` | プロジェクトメンバーシップ | 100-10,000 |
| 4 | `project_files` | プロジェクトファイル | 1,000-100,000 |
| **データ分析** | | | |
| 5 | `analysis_sessions` | 分析セッション | 100-10,000 |
| 6 | `analysis_steps` | 分析ステップ | 1,000-100,000 |
| 7 | `analysis_files` | 分析ファイル | 1,000-100,000 |
| 8 | `analysis_templates` | 分析テンプレート | 10-100 |
| 9 | `analysis_template_charts` | テンプレートチャート | 50-500 |
| **ドライバーツリー** | | | |
| 10 | `driver_trees` | ドライバーツリー | 10-100 |
| 11 | `driver_tree_nodes` | ツリーノード | 100-10,000 |
| 12 | `driver_tree_categories` | ノードカテゴリ | 5-20 |
| **サンプル（開発用）** | | | |
| 13 | `sample_users` | サンプルユーザー | 開発用 |
| 14 | `sample_sessions` | サンプルセッション | 開発用 |
| 15 | `sample_messages` | サンプルメッセージ | 開発用 |
| 16 | `sample_files` | サンプルファイル | 開発用 |

---

## 3. テーブル定義

### 3.1 ユーザー管理

#### 3.1.1 users（ユーザー）

**目的:** Azure AD認証用のユーザー情報を管理

**実装ファイル:** `src/app/models/user.py`

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| azure_oid | VARCHAR(255) | NO | - | Azure AD Object ID（一意） |
| email | VARCHAR(255) | NO | - | メールアドレス（一意） |
| display_name | VARCHAR(255) | YES | NULL | 表示名 |
| roles | JSON | NO | [] | システムロール配列 |
| is_active | BOOLEAN | NO | true | アクティブフラグ |
| last_login | TIMESTAMPTZ | YES | NULL | 最終ログイン日時 |
| created_at | TIMESTAMPTZ | NO | now() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | now() | 更新日時 |

**インデックス:**

- PRIMARY KEY: `id`
- UNIQUE: `idx_users_azure_oid` (azure_oid)
- UNIQUE: `idx_users_email` (email)

**制約:**

- `roles`は有効なSystemRole値の配列（["system_admin", "user"]）
- `email`は有効なメールアドレス形式

**サンプルデータ:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "azure_oid": "00000000-0000-0000-0000-000000000001",
  "email": "admin@company.com",
  "display_name": "システム管理者",
  "roles": ["system_admin", "user"],
  "is_active": true,
  "last_login": "2025-01-11T10:30:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-11T10:30:00Z"
}
```

### 3.2 プロジェクト管理

#### 3.2.1 projects（プロジェクト）

**目的:** プロジェクトの基本情報を管理

**実装ファイル:** `src/app/models/project.py`

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| name | VARCHAR(255) | NO | - | プロジェクト名 |
| code | VARCHAR(50) | NO | - | プロジェクトコード（一意） |
| description | TEXT | YES | NULL | プロジェクト説明 |
| is_active | BOOLEAN | NO | true | アクティブフラグ |
| created_by | UUID | YES | NULL | 作成者ユーザーID |
| created_at | TIMESTAMPTZ | NO | now() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | now() | 更新日時 |

**インデックス:**

- PRIMARY KEY: `id`
- UNIQUE: `idx_projects_code` (code)

**サンプルデータ:**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "name": "新規事業企画プロジェクト",
  "code": "PROJ-2025-001",
  "description": "2025年度の新規事業企画に関するプロジェクト",
  "is_active": true,
  "created_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-10T15:30:00Z"
}
```

#### 3.2.2 project_members（プロジェクトメンバー）

**目的:** プロジェクトとユーザーの多対多関係とロールを管理

**実装ファイル:** `src/app/models/project_member.py`

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| project_id | UUID | NO | - | プロジェクトID |
| user_id | UUID | NO | - | ユーザーID |
| role | ENUM | NO | member | プロジェクトロール |
| added_by | UUID | YES | NULL | 追加者ユーザーID |
| joined_at | TIMESTAMPTZ | NO | now() | 参加日時 |

**ENUM値 (ProjectRole):**

- `project_manager`: プロジェクトマネージャー
- `project_moderator`: 権限管理者
- `member`: 一般メンバー
- `viewer`: 閲覧者

**インデックス:**

- PRIMARY KEY: `id`
- INDEX: `idx_project_members_project_id` (project_id)
- INDEX: `idx_project_members_user_id` (user_id)
- UNIQUE: `uq_project_user` (project_id, user_id)

**外部キー:**

- `project_id` → `projects(id)` ON DELETE CASCADE
- `user_id` → `users(id)` ON DELETE CASCADE
- `added_by` → `users(id)` ON DELETE SET NULL

#### 3.2.3 project_files（プロジェクトファイル）

**目的:** プロジェクトにアップロードされたファイルを管理

**実装ファイル:** `src/app/models/project_file.py`

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| project_id | UUID | NO | - | プロジェクトID |
| filename | VARCHAR(255) | NO | - | ファイル名 |
| file_path | TEXT | NO | - | ストレージパス |
| file_size | INTEGER | NO | - | ファイルサイズ（バイト） |
| mime_type | VARCHAR(100) | NO | - | MIMEタイプ |
| uploaded_by | UUID | YES | NULL | アップロード者ID |
| uploaded_at | TIMESTAMPTZ | NO | now() | アップロード日時 |

**インデックス:**

- PRIMARY KEY: `id`
- INDEX: `idx_project_files_project` (project_id)

**外部キー:**

- `project_id` → `projects(id)` ON DELETE CASCADE
- `uploaded_by` → `users(id)` ON DELETE SET NULL

### 3.3 データ分析

#### 3.3.1 analysis_sessions（分析セッション）

**目的:** AIエージェントによるデータ分析セッションを管理

**実装ファイル:** `src/app/models/analysis_session.py`

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| project_id | UUID | NO | - | プロジェクトID |
| created_by | UUID | YES | NULL | 作成者ユーザーID |
| session_name | VARCHAR(255) | YES | NULL | セッション名 |
| validation_config | JSONB | NO | {} | 分析設定 |
| chat_history | JSONB | NO | [] | チャット履歴 |
| snapshot_history | JSONB | YES | NULL | スナップショット履歴 |
| original_file_id | UUID | YES | NULL | 選択中のファイルID |
| is_active | BOOLEAN | NO | true | アクティブフラグ |
| created_at | TIMESTAMPTZ | NO | now() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | now() | 更新日時 |

**JSONB構造:**

`validation_config`:

```json
{
  "policy": "市場拡大戦略",
  "issue": "新規参入障壁の分析",
  "custom_params": {}
}
```

`chat_history`:

```json
[
  {
    "role": "user",
    "content": "売上データを分析してください",
    "timestamp": "2025-01-11T10:30:00Z"
  },
  {
    "role": "assistant",
    "content": "売上データを分析します...",
    "timestamp": "2025-01-11T10:30:05Z"
  }
]
```

**インデックス:**

- PRIMARY KEY: `id`
- INDEX: `idx_analysis_sessions_project` (project_id)
- INDEX: `idx_analysis_sessions_created_by` (created_by)

**外部キー:**

- `project_id` → `projects(id)` ON DELETE CASCADE
- `created_by` → `users(id)` ON DELETE SET NULL

#### 3.3.2 analysis_steps（分析ステップ）

**目的:** 分析セッション内の個別ステップを管理

**実装ファイル:** `src/app/models/analysis_step.py`

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| session_id | UUID | NO | - | セッションID |
| step_name | VARCHAR(255) | NO | - | ステップ名 |
| step_type | VARCHAR(50) | NO | - | ステップタイプ |
| step_order | INTEGER | NO | - | ステップ順序（0〜） |
| data_source | VARCHAR(100) | NO | original | データソース |
| config | JSONB | NO | {} | ステップ設定 |
| result_data_path | TEXT | YES | NULL | 結果データパス |
| result_chart | JSONB | YES | NULL | 結果チャート |
| result_formula | JSONB | YES | NULL | 結果数式 |
| is_active | BOOLEAN | NO | true | アクティブフラグ |
| created_at | TIMESTAMPTZ | NO | now() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | now() | 更新日時 |

**step_type値:**

- `filter`: データフィルタリング
- `aggregate`: データ集計
- `transform`: データ変換
- `summary`: 結果サマリー

**インデックス:**

- PRIMARY KEY: `id`
- INDEX: `idx_analysis_steps_session` (session_id)
- INDEX: `idx_analysis_steps_order` (session_id, step_order)

**外部キー:**

- `session_id` → `analysis_sessions(id)` ON DELETE CASCADE

#### 3.3.3 analysis_files（分析ファイル）

**目的:** 分析セッションにアップロードされたファイルを管理

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| session_id | UUID | NO | - | セッションID |
| filename | VARCHAR(255) | NO | - | ファイル名 |
| file_path | TEXT | NO | - | ストレージパス |
| file_size | INTEGER | NO | - | ファイルサイズ（バイト） |
| mime_type | VARCHAR(100) | NO | - | MIMEタイプ |
| uploaded_at | TIMESTAMPTZ | NO | now() | アップロード日時 |

**インデックス:**

- PRIMARY KEY: `id`
- INDEX: `idx_analysis_files_session` (session_id)

**外部キー:**

- `session_id` → `analysis_sessions(id)` ON DELETE CASCADE

#### 3.3.4 analysis_templates（分析テンプレート）

**目的:** 事前定義された分析テンプレートを管理

**実装ファイル:** `src/app/models/analysis_template.py`

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| template_name | VARCHAR(255) | NO | - | テンプレート名 |
| description | TEXT | YES | NULL | 説明 |
| config | JSONB | NO | {} | テンプレート設定 |
| is_active | BOOLEAN | NO | true | アクティブフラグ |
| created_at | TIMESTAMPTZ | NO | now() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | now() | 更新日時 |

**インデックス:**

- PRIMARY KEY: `id`

#### 3.3.5 analysis_template_charts（テンプレートチャート）

**目的:** テンプレートに含まれるチャート定義を管理

**実装ファイル:** `src/app/models/analysis_template_chart.py`

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| template_id | UUID | NO | - | テンプレートID |
| chart_name | VARCHAR(255) | NO | - | チャート名 |
| chart_type | VARCHAR(50) | NO | - | チャートタイプ |
| config | JSONB | NO | {} | チャート設定 |
| display_order | INTEGER | NO | - | 表示順序 |
| created_at | TIMESTAMPTZ | NO | now() | 作成日時 |

**chart_type値:**

- `bar`, `line`, `pie`, `scatter`, `heatmap`, `box`, `histogram`, `area`, `waterfall`, `treemap`, `sunburst`

**インデックス:**

- PRIMARY KEY: `id`
- INDEX: `idx_analysis_template_charts_template` (template_id)
- INDEX: `idx_analysis_template_charts_order` (template_id, display_order)

**外部キー:**

- `template_id` → `analysis_templates(id)` ON DELETE CASCADE

### 3.4 ドライバーツリー

#### 3.4.1 driver_trees（ドライバーツリー）

**目的:** ドライバーツリーの基本情報を管理

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| tree_name | VARCHAR(255) | NO | - | ツリー名 |
| description | TEXT | YES | NULL | 説明 |
| metadata | JSONB | YES | NULL | メタデータ |
| is_active | BOOLEAN | NO | true | アクティブフラグ |
| created_at | TIMESTAMPTZ | NO | now() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | now() | 更新日時 |

**インデックス:**

- PRIMARY KEY: `id`

#### 3.4.2 driver_tree_nodes（ツリーノード）

**目的:** ドライバーツリーのノードを管理（階層構造）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| tree_id | UUID | NO | - | ツリーID |
| parent_id | UUID | YES | NULL | 親ノードID |
| category_id | UUID | YES | NULL | カテゴリID |
| node_name | VARCHAR(255) | NO | - | ノード名 |
| description | TEXT | YES | NULL | 説明 |
| level | INTEGER | NO | - | 階層レベル（0〜） |
| display_order | INTEGER | NO | - | 表示順序 |
| metadata | JSONB | YES | NULL | メタデータ |
| created_at | TIMESTAMPTZ | NO | now() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | now() | 更新日時 |

**インデックス:**

- PRIMARY KEY: `id`
- INDEX: `idx_driver_tree_nodes_tree` (tree_id)
- INDEX: `idx_driver_tree_nodes_parent` (parent_id)
- INDEX: `idx_driver_tree_nodes_level` (tree_id, level)

**外部キー:**

- `tree_id` → `driver_trees(id)` ON DELETE CASCADE
- `parent_id` → `driver_tree_nodes(id)` ON DELETE CASCADE
- `category_id` → `driver_tree_categories(id)` ON DELETE SET NULL

#### 3.4.3 driver_tree_categories（ノードカテゴリ）

**目的:** ツリーノードのカテゴリを管理

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | プライマリキー |
| category_name | VARCHAR(100) | NO | - | カテゴリ名 |
| color_code | VARCHAR(7) | NO | - | カラーコード（#RRGGBB） |
| display_order | INTEGER | NO | - | 表示順序 |
| created_at | TIMESTAMPTZ | NO | now() | 作成日時 |

**インデックス:**

- PRIMARY KEY: `id`

---

## 4. ER図

### 4.1 ドメインモデル図

```mermaid
graph TB
    subgraph "ユーザー・プロジェクト管理ドメイン"
        User[User<br/>ユーザー]
        Project[Project<br/>プロジェクト]
        ProjectMember[ProjectMember<br/>メンバーシップ]
        ProjectFile[ProjectFile<br/>ファイル]
    end

    subgraph "データ分析ドメイン"
        AnalysisSession[AnalysisSession<br/>分析セッション]
        AnalysisStep[AnalysisStep<br/>分析ステップ]
        AnalysisFile[AnalysisFile<br/>分析ファイル]
        AnalysisTemplate[AnalysisTemplate<br/>テンプレート]
        AnalysisTemplateChart[TemplateChart<br/>チャート]
    end

    subgraph "ドライバーツリードメイン"
        DriverTree[DriverTree<br/>ツリー]
        DriverTreeNode[DriverTreeNode<br/>ノード]
        DriverTreeCategory[Category<br/>カテゴリ]
    end

    User -->|1:N| ProjectMember
    Project -->|1:N| ProjectMember
    Project -->|1:N| ProjectFile
    Project -->|1:N| AnalysisSession

    User -->|1:N| AnalysisSession

    AnalysisSession -->|1:N| AnalysisStep
    AnalysisSession -->|1:N| AnalysisFile

    AnalysisTemplate -->|1:N| AnalysisTemplateChart

    DriverTree -->|1:N| DriverTreeNode
    DriverTreeNode -->|1:N| DriverTreeNode
    DriverTreeCategory -->|1:N| DriverTreeNode

    style User fill:#4dabf7
    style Project fill:#51cf66
    style AnalysisSession fill:#ffd43b
    style DriverTree fill:#ff6b6b
```

### 4.2 リレーションシップ詳細

| 親テーブル | 子テーブル | 種別 | 削除時 | 説明 |
|-----------|----------|------|--------|------|
| projects | project_members | 1:N | CASCADE | プロジェクト削除時、全メンバー削除 |
| projects | project_files | 1:N | CASCADE | プロジェクト削除時、全ファイル削除 |
| projects | analysis_sessions | 1:N | CASCADE | プロジェクト削除時、全セッション削除 |
| users | project_members | 1:N | CASCADE | ユーザー削除時、全メンバーシップ削除 |
| users | analysis_sessions | 1:N | SET NULL | ユーザー削除時、created_byをNULL化 |
| analysis_sessions | analysis_steps | 1:N | CASCADE | セッション削除時、全ステップ削除 |
| analysis_sessions | analysis_files | 1:N | CASCADE | セッション削除時、全ファイル削除 |
| analysis_templates | analysis_template_charts | 1:N | CASCADE | テンプレート削除時、全チャート削除 |
| driver_trees | driver_tree_nodes | 1:N | CASCADE | ツリー削除時、全ノード削除 |
| driver_tree_nodes | driver_tree_nodes | 1:N | CASCADE | 親ノード削除時、子ノード削除 |
| driver_tree_categories | driver_tree_nodes | 1:N | SET NULL | カテゴリ削除時、category_idをNULL化 |

---

## 5. インデックス設計

### 5.1 インデックス一覧

| テーブル | インデックス名 | カラム | 種別 | 目的 |
|---------|--------------|--------|------|------|
| users | PRIMARY KEY | id | UNIQUE | 主キー |
| users | idx_users_azure_oid | azure_oid | UNIQUE | Azure AD認証 |
| users | idx_users_email | email | UNIQUE | メール検索 |
| projects | PRIMARY KEY | id | UNIQUE | 主キー |
| projects | idx_projects_code | code | UNIQUE | プロジェクトコード検索 |
| project_members | PRIMARY KEY | id | UNIQUE | 主キー |
| project_members | idx_project_members_project_id | project_id | INDEX | プロジェクト別メンバー検索 |
| project_members | idx_project_members_user_id | user_id | INDEX | ユーザー別プロジェクト検索 |
| project_members | uq_project_user | (project_id, user_id) | UNIQUE | 重複メンバー防止 |
| project_files | PRIMARY KEY | id | UNIQUE | 主キー |
| project_files | idx_project_files_project | project_id | INDEX | プロジェクト別ファイル検索 |
| analysis_sessions | PRIMARY KEY | id | UNIQUE | 主キー |
| analysis_sessions | idx_analysis_sessions_project | project_id | INDEX | プロジェクト別セッション検索 |
| analysis_sessions | idx_analysis_sessions_created_by | created_by | INDEX | ユーザー別セッション検索 |
| analysis_steps | PRIMARY KEY | id | UNIQUE | 主キー |
| analysis_steps | idx_analysis_steps_session | session_id | INDEX | セッション別ステップ検索 |
| analysis_steps | idx_analysis_steps_order | (session_id, step_order) | INDEX | ステップ順序取得の最適化 |
| analysis_files | PRIMARY KEY | id | UNIQUE | 主キー |
| analysis_files | idx_analysis_files_session | session_id | INDEX | セッション別ファイル検索 |
| analysis_templates | PRIMARY KEY | id | UNIQUE | 主キー |
| analysis_template_charts | PRIMARY KEY | id | UNIQUE | 主キー |
| analysis_template_charts | idx_analysis_template_charts_template | template_id | INDEX | テンプレート別チャート検索 |
| analysis_template_charts | idx_analysis_template_charts_order | (template_id, display_order) | INDEX | 表示順序取得の最適化 |
| driver_trees | PRIMARY KEY | id | UNIQUE | 主キー |
| driver_tree_nodes | PRIMARY KEY | id | UNIQUE | 主キー |
| driver_tree_nodes | idx_driver_tree_nodes_tree | tree_id | INDEX | ツリー別ノード検索 |
| driver_tree_nodes | idx_driver_tree_nodes_parent | parent_id | INDEX | 親ノード別子ノード検索 |
| driver_tree_nodes | idx_driver_tree_nodes_level | (tree_id, level) | INDEX | 階層別ノード検索 |
| driver_tree_categories | PRIMARY KEY | id | UNIQUE | 主キー |

### 5.2 インデックス設計方針

1. **主キー:** すべてのテーブルでUUID型の主キーにB-treeインデックス
2. **外部キー:** すべての外部キーにインデックス（JOIN最適化）
3. **ユニーク制約:** 重複防止が必要なカラムにUNIQUEインデックス
4. **複合インデックス:** 頻繁に組み合わせて検索されるカラムに複合インデックス
5. **JSONB:** 頻繁にクエリされるJSONBフィールドにはGINインデックス（将来検討）

### 5.3 パフォーマンス考慮事項

**良い例:**

```sql
-- 複合インデックスを活用
SELECT * FROM analysis_steps
WHERE session_id = 'xxx' AND step_order = 0;
-- → idx_analysis_steps_order を使用

-- 外部キーインデックスを活用
SELECT * FROM project_members WHERE project_id = 'xxx';
-- → idx_project_members_project_id を使用
```

**悪い例（インデックスが使われない）:**

```sql
-- LIKE演算子の前方一致以外
SELECT * FROM users WHERE email LIKE '%@example.com';

-- 関数を使用
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';

-- OR条件（場合による）
SELECT * FROM projects WHERE name = 'A' OR description LIKE '%B%';
```

---

## 6. データ型設計

### 6.1 標準データ型マッピング

| 用途 | PostgreSQL型 | Python型 | SQLAlchemy型 | 説明 |
|------|-------------|----------|-------------|------|
| 主キー | UUID | uuid.UUID | UUID(as_uuid=True) | UUID v4 |
| 短文字列 | VARCHAR(255) | str | String(255) | 名前、コードなど |
| 長文字列 | TEXT | str | Text | 説明文など |
| 真偽値 | BOOLEAN | bool | Boolean | フラグ |
| 整数 | INTEGER | int | Integer | カウント、順序など |
| 日時 | TIMESTAMPTZ | datetime | DateTime(timezone=True) | UTC日時 |
| JSON | JSONB | dict/list | JSONB | 柔軟なデータ構造 |
| ENUM | ENUM | str | SQLEnum | 限定された値 |

### 6.2 UUID使用の理由

1. **グローバル一意性**: 分散システムでも重複なし
2. **セキュリティ**: 連番IDと違い推測不可
3. **マージ容易性**: 複数DBのマージが簡単
4. **パフォーマンス**: PostgreSQLはUUIDに最適化

**実装例:**

```python
from sqlalchemy.dialects.postgresql import UUID
import uuid

id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4
)
```

### 6.3 JSONB使用ガイドライン

**使用すべき場合:**

- スキーマが頻繁に変わる設定データ
- 階層構造を持つデータ
- 柔軟性が必要なメタデータ

**使用すべきでない場合:**

- リレーショナル制約が必要なデータ
- 頻繁にJOINされるデータ
- 厳密な型チェックが必要なデータ

**例:**

```python
# Good: 柔軟な設定データ
validation_config: Mapped[dict[str, Any]] = mapped_column(JSONB)

# Bad: リレーションシップで管理すべき
# members: Mapped[dict[str, Any]] = mapped_column(JSONB)  # ❌
# members: Mapped[list["ProjectMember"]] = relationship(...)  # ✅
```

---

## 7. 制約設計

### 7.1 主キー制約

すべてのテーブルでUUID型の主キーを使用：

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ...
);
```

### 7.2 外部キー制約

**カスケード削除（CASCADE）:**

- 親レコード削除時、子レコードも削除
- 例: プロジェクト削除時、全メンバー・ファイルを削除

```sql
ALTER TABLE project_members
ADD CONSTRAINT fk_project_members_project
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
```

**SET NULL:**

- 親レコード削除時、外部キーをNULLに設定
- 例: ユーザー削除時、created_byをNULL化

```sql
ALTER TABLE analysis_sessions
ADD CONSTRAINT fk_analysis_sessions_created_by
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
```

### 7.3 ユニーク制約

**単一カラム:**

```sql
ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);
```

**複合カラム:**

```sql
ALTER TABLE project_members
ADD CONSTRAINT uq_project_user UNIQUE (project_id, user_id);
```

### 7.4 CHECK制約（推奨）

```sql
-- メールアドレス形式チェック
ALTER TABLE users
ADD CONSTRAINT chk_users_email_format
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$');

-- ファイルサイズチェック（最大100MB）
ALTER TABLE project_files
ADD CONSTRAINT chk_project_files_size
CHECK (file_size > 0 AND file_size <= 104857600);

-- ステップ順序チェック
ALTER TABLE analysis_steps
ADD CONSTRAINT chk_analysis_steps_order
CHECK (step_order >= 0);
```

---

## 8. 接続管理

### 8.1 接続プール設定

**実装ファイル:** `src/app/core/database.py`

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,           # 接続前のPINGチェック
    pool_size=5,                  # 通常時の接続数
    max_overflow=10,              # ピーク時の追加接続数（最大15接続）
    pool_recycle=1800,            # 30分ごとに接続をリサイクル
    pool_timeout=30,              # タイムアウト30秒
)
```

### 8.2 接続プール設計

```mermaid
graph LR
    subgraph "アプリケーション"
        A1[リクエスト1]
        A2[リクエスト2]
        A3[リクエスト3]
    end

    subgraph "接続プール"
        P1[接続1]
        P2[接続2]
        P3[接続3]
        P4[接続4]
        P5[接続5]
        O1[追加接続1]
        O2[追加接続2]
        O3[...<br/>最大10個]
    end

    subgraph "PostgreSQL"
        DB[(Database)]
    end

    A1 --> P1
    A2 --> P2
    A3 --> P3

    P1 --> DB
    P2 --> DB
    P3 --> DB
    P4 --> DB
    P5 --> DB
    O1 -.ピーク時.-> DB
    O2 -.ピーク時.-> DB

    style P1 fill:#51cf66
    style P2 fill:#51cf66
    style P3 fill:#51cf66
    style P4 fill:#51cf66
    style P5 fill:#51cf66
    style O1 fill:#ffd43b
    style O2 fill:#ffd43b
```

**設定の意図:**

- **pool_size=5**: 通常時の接続数（CPUコア数 + 1が目安）
- **max_overflow=10**: ピーク時の追加接続（最大15接続）
- **pool_recycle=1800**: 30分で接続をリフレッシュ（接続切れ防止）
- **pool_pre_ping=True**: 接続前にPINGで確認（無効な接続を排除）

### 8.3 セッション管理

```python
async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI依存性注入用のDBセッション"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**ライフサイクル:**

1. リクエスト開始 → セッション作成
2. ビジネスロジック実行
3. エラー発生 → 自動ロールバック
4. リクエスト終了 → セッションクローズ

---

## 9. パフォーマンス最適化

### 9.1 クエリ最適化

#### N+1問題の回避

**悪い例（N+1問題）:**

```python
# セッションを取得
sessions = await db.execute(select(AnalysisSession))

# 各セッションのステップを個別に取得（N回のクエリ）
for session in sessions:
    steps = await db.execute(
        select(AnalysisStep).where(AnalysisStep.session_id == session.id)
    )
```

**良い例（JOIN使用）:**

```python
# 1回のクエリで取得
result = await db.execute(
    select(AnalysisSession)
    .options(selectinload(AnalysisSession.steps))
)
```

### 9.2 インデックス活用

```python
# インデックスを活用したクエリ
result = await db.execute(
    select(ProjectMember)
    .where(ProjectMember.project_id == project_id)  # インデックス使用
    .where(ProjectMember.role == ProjectRole.PROJECT_MANAGER)
)
```

### 9.3 ページネーション

```python
# LIMIT/OFFSET使用
result = await db.execute(
    select(Project)
    .order_by(Project.created_at.desc())
    .limit(20)
    .offset(skip)
)
```

### 9.4 EXPLAIN ANALYZE

```sql
-- クエリプランの確認
EXPLAIN ANALYZE
SELECT * FROM project_members
WHERE project_id = 'xxx'
AND role = 'project_manager';

-- 結果例：
-- Index Scan using idx_project_members_project_id on project_members
-- (cost=0.29..8.31 rows=1 width=100) (actual time=0.015..0.016 rows=1 loops=1)
```

---

## 10. バックアップ戦略

### 10.1 バックアップ種別

| 種別 | 頻度 | 保持期間 | 目的 |
|------|------|---------|------|
| フルバックアップ | 毎日深夜 | 30日 | 完全復旧 |
| 差分バックアップ | 6時間ごと | 7日 | 高速復旧 |
| トランザクションログ | リアルタイム | 7日 | ポイントインタイムリカバリ |

### 10.2 バックアップスクリプト

```bash
#!/bin/bash
# フルバックアップ
pg_dump -Fc genai_app_db > backup_$(date +%Y%m%d_%H%M%S).dump

# 特定テーブルのバックアップ
pg_dump -t users -t projects --data-only --column-inserts genai_app_db > critical_data.sql
```

### 10.3 リストア手順

```bash
# フルリストア
pg_restore -d genai_app_db backup_20250111_000000.dump

# 特定テーブルのみリストア
pg_restore -t users -d genai_app_db backup_20250111_000000.dump
```

---

## 11. マイグレーション戦略

### 11.1 Alembic設定

**設定ファイル:** `src/alembic.ini`

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/genai_app_db
```

### 11.2 マイグレーション作成

```bash
# マイグレーションファイル自動生成
cd src
uv run alembic revision --autogenerate -m "Add new column to users table"

# マイグレーション適用
uv run alembic upgrade head

# ロールバック
uv run alembic downgrade -1
```

### 11.3 マイグレーション例

```python
# alembic/versions/xxx_add_user_profile.py
def upgrade() -> None:
    op.add_column('users', sa.Column('profile_image_url', sa.String(500), nullable=True))
    op.create_index('idx_users_profile_image', 'users', ['profile_image_url'])

def downgrade() -> None:
    op.drop_index('idx_users_profile_image', table_name='users')
    op.drop_column('users', 'profile_image_url')
```

---

## 12. 付録

### 12.1 モデルファイル一覧

| ファイル | モデル | 説明 |
|---------|-------|------|
| `src/app/models/base.py` | Base, TimestampMixin, PrimaryKeyMixin | 基底クラス |
| `src/app/models/user.py` | User, SystemRole | ユーザー |
| `src/app/models/project.py` | Project | プロジェクト |
| `src/app/models/project_member.py` | ProjectMember, ProjectRole | メンバーシップ |
| `src/app/models/project_file.py` | ProjectFile | プロジェクトファイル |
| `src/app/models/analysis_session.py` | AnalysisSession | 分析セッション |
| `src/app/models/analysis_step.py` | AnalysisStep | 分析ステップ |
| `src/app/models/analysis_file.py` | AnalysisFile | 分析ファイル |
| `src/app/models/analysis_template.py` | AnalysisTemplate | 分析テンプレート |
| `src/app/models/analysis_template_chart.py` | AnalysisTemplateChart | テンプレートチャート |
| `src/app/models/driver_tree.py` | DriverTree | ドライバーツリー |
| `src/app/models/driver_tree_node.py` | DriverTreeNode | ツリーノード |
| `src/app/models/driver_tree_category.py` | DriverTreeCategory | ノードカテゴリ |

### 12.2 参考リンク

#### 内部ドキュメント

- [RBAC設計書](../03-security/01-rbac-design.md)
- [アーキテクチャ設計](../01-architecture/01-system-design.md)

#### 外部リソース

- [PostgreSQL公式ドキュメント](https://www.postgresql.org/docs/)
- [SQLAlchemy 2.0ドキュメント](https://docs.sqlalchemy.org/en/20/)
- [Alembicドキュメント](https://alembic.sqlalchemy.org/)

### 12.3 データベース統計情報

```sql
-- テーブルサイズ確認
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- インデックスサイズ確認
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_indexes
JOIN pg_class ON pg_indexes.indexname = pg_class.relname
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- テーブル統計情報
SELECT
    schemaname,
    tablename,
    n_live_tup AS row_count,
    n_dead_tup AS dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public';
```

### 12.4 変更履歴

| 日付 | バージョン | 変更内容 | 作成者 |
|------|-----------|---------|--------|
| 2025-01-11 | 1.0 | 初版作成 | Claude Code |

---

**作成者**: Claude Code
**最終更新**: 2025-01-11
**承認者**: （承認後に記入）
