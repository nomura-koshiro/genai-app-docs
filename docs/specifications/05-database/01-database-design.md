# データベース設計書

## 1. 概要

本文書は、CAMPシステムのデータベース設計を定義します。
PostgreSQLを使用し、SQLAlchemy 2.0 ORM（非同期対応）によるデータアクセスを実装しています。

### 1.1 データベース仕様

- **RDBMS**: PostgreSQL（バージョン指定なし、推奨14+）
- **文字コード**: UTF-8
- **タイムゾーン**: UTC（アプリケーション層でタイムゾーン変換）
- **ORM**: SQLAlchemy 2.0+（非同期）
- **マイグレーション**: Alembic 1.13+

### 1.2 データベース接続設定

```python
# 接続プール設定
pool_size = 5              # 通常時の接続数
max_overflow = 10          # ピーク時の追加接続数（最大15接続）
pool_recycle = 1800        # 30分で接続再生成
pool_pre_ping = True       # 接続前にPING実行
pool_timeout = 30          # 接続タイムアウト（秒）
```

---

## 2. ER図（全体）

### 2.1 主要エンティティ関連図

::: mermaid
erDiagram
    UserAccount ||--o{ ProjectMember : "participates"
    UserAccount ||--o{ AnalysisSession : "creates"

    Project ||--o{ ProjectMember : "has"
    Project ||--o{ ProjectFile : "contains"
    Project ||--o{ AnalysisSession : "includes"
    Project ||--o{ DriverTree : "has"

    ProjectFile ||--o{ AnalysisFile : "used in"
    ProjectFile ||--o{ DriverTreeFile : "used in"

    AnalysisSession ||--o{ AnalysisFile : "has"
    AnalysisSession ||--o{ AnalysisSnapshot : "has"
    AnalysisSession }o--|| AnalysisIssueMaster : "based on"

    AnalysisSnapshot ||--o{ AnalysisChat : "has"
    AnalysisSnapshot ||--o{ AnalysisStep : "has"

    AnalysisValidationMaster ||--o{ AnalysisIssueMaster : "has"
    AnalysisIssueMaster ||--o{ AnalysisGraphAxisMaster : "has"
    AnalysisIssueMaster ||--o{ AnalysisDummyFormulaMaster : "has"
    AnalysisIssueMaster ||--o{ AnalysisDummyChartMaster : "has"

    DriverTree ||--o{ DriverTreeRelationship : "has"
    DriverTree }o--o| DriverTreeNode : "root"
    DriverTree }o--o| DriverTreeFormula : "uses"

    DriverTreeCategory ||--o{ DriverTreeFormula : "has"

    DriverTreeRelationship ||--o{ DriverTreeRelationshipChild : "has"
    DriverTreeRelationship }o--|| DriverTreeNode : "parent"

    DriverTreeRelationshipChild }o--|| DriverTreeNode : "child"

    DriverTreeNode ||--o{ DriverTreePolicy : "has"
    DriverTreeNode }o--o| DriverTreeDataFrame : "uses"

    DriverTreeFile ||--o{ DriverTreeDataFrame : "has"

    UserAccount {
        uuid id PK
        string azure_oid UK
        string email UK
        string display_name
        json roles
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
        enum role
        timestamp joined_at
        uuid added_by FK
    }

    ProjectFile {
        uuid id PK
        uuid project_id FK
        string filename
        string original_filename
        string file_path
        integer file_size
        string mime_type
        uuid uploaded_by FK
        timestamp uploaded_at
    }
:::

---

## 3. テーブル詳細設計

### 3.1 ベースクラス

すべてのモデルは以下のMixinを継承します：

#### 3.1.1 TimestampMixin

```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

**重要**: `timezone=False`を指定していますが、デフォルト値でUTCを使用しているため、実質的にUTCタイムスタンプとして扱われます。

---

### 3.2 ユーザー管理

#### 3.2.1 user_account（ユーザーアカウント）

**テーブル名**: `user_account`
**実装**: `src/app/models/user_account/user_account.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| azure_oid | String(255) | UNIQUE, NOT NULL | Azure AD Object ID |
| email | String(255) | UNIQUE, NOT NULL | メールアドレス |
| display_name | String(255) | NULLABLE | 表示名 |
| roles | JSON | NOT NULL | システムロール（例: ["SystemAdmin", "User"]） |
| is_active | Boolean | DEFAULT TRUE | アクティブフラグ |
| last_login | DateTime | NULLABLE | 最終ログイン日時 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### インデックス

- PRIMARY KEY: `id`
- UNIQUE: `azure_oid` (idx_users_azure_oid)
- UNIQUE: `email` (idx_users_email)

##### 列挙型: SystemUserRole

```python
class SystemUserRole(str, Enum):
    SYSTEM_ADMIN = "system_admin"  # システム管理者
    USER = "user"                  # 一般ユーザー
```

##### リレーションシップ

- `project_memberships`: ProjectMember（1対多）
- `analysis_sessions`: AnalysisSession（1対多）

---

### 3.3 プロジェクト管理

#### 3.3.1 project（プロジェクト）

**テーブル名**: `project`
**実装**: `src/app/models/project/project.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| name | String(255) | NOT NULL | プロジェクト名 |
| code | String(50) | UNIQUE, NOT NULL | プロジェクトコード |
| description | Text | NULLABLE | 説明 |
| is_active | Boolean | DEFAULT TRUE | アクティブフラグ |
| created_by | UUID | NULLABLE | 作成者ID |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### インデックス

- PRIMARY KEY: `id`
- UNIQUE: `code` (idx_projects_code)

##### リレーションシップ

- `members`: ProjectMember（1対多、CASCADE削除）
- `files`: ProjectFile（1対多、CASCADE削除）
- `analysis_sessions`: AnalysisSession（1対多、CASCADE削除）
- `driver_trees`: DriverTree（1対多、CASCADE削除）

#### 3.3.2 project_member（プロジェクトメンバー）

**テーブル名**: `project_member`
**実装**: `src/app/models/project/project_member.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| project_id | UUID | FK(project.id), NOT NULL | プロジェクトID |
| user_id | UUID | FK(user_account.id), NOT NULL | ユーザーID |
| role | Enum(ProjectRole) | NOT NULL | プロジェクトロール |
| joined_at | DateTime | NOT NULL | 参加日時 |
| added_by | UUID | FK(user_account.id), NULLABLE | 追加者ID |

##### インデックス

- PRIMARY KEY: `id`
- UNIQUE: `(project_id, user_id)` (uq_project_user)
- INDEX: `project_id` (idx_project_members_project_id)
- INDEX: `user_id` (idx_project_members_user_id)
- FOREIGN KEY: `project_id` → `project(id)` ON DELETE CASCADE
- FOREIGN KEY: `user_id` → `user_account(id)` ON DELETE CASCADE

##### 列挙型: ProjectRole

```python
class ProjectRole(str, Enum):
    PROJECT_MANAGER = "project_manager"      # プロジェクトマネージャー（最高権限）
    PROJECT_MODERATOR = "project_moderator"  # 権限管理者
    MEMBER = "member"                        # 一般メンバー
    VIEWER = "viewer"                        # 閲覧者
```

#### 3.3.3 project_file（プロジェクトファイル）

**テーブル名**: `project_file`
**実装**: `src/app/models/project/project_file.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| project_id | UUID | FK(project.id), NOT NULL | プロジェクトID |
| filename | String(255) | NOT NULL | 保存ファイル名 |
| original_filename | String(255) | NOT NULL | 元のファイル名 |
| file_path | String(512) | NOT NULL | ファイルパス |
| file_size | Integer | NOT NULL | ファイルサイズ（バイト） |
| mime_type | String(100) | NULLABLE | MIMEタイプ |
| uploaded_by | UUID | FK(user_account.id), NOT NULL | アップロードユーザーID |
| uploaded_at | DateTime | NOT NULL | アップロード日時 |

##### インデックス

- PRIMARY KEY: `id`
- INDEX: `project_id` (idx_project_files_project_id)
- FOREIGN KEY: `project_id` → `project(id)` ON DELETE CASCADE
- FOREIGN KEY: `uploaded_by` → `user_account(id)` ON DELETE RESTRICT

##### リレーションシップ

- `project`: Project（多対1）
- `uploader`: UserAccount（多対1）
- `analysis_files`: AnalysisFile（1対多、CASCADE削除）
- `driver_tree_files`: DriverTreeFile（1対多、CASCADE削除）

---

### 3.4 個別施策分析機能

#### 3.4.1 マスタテーブル

##### analysis_validation_master（分析検証マスタ）

**テーブル名**: `analysis_validation_master`
**実装**: `src/app/models/analysis/analysis_validation_master.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| name | String(255) | NOT NULL | 検証名 |
| validation_order | Integer | NOT NULL | 表示順序 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### analysis_issue_master（分析課題マスタ）

**テーブル名**: `analysis_issue_master`
**実装**: `src/app/models/analysis/analysis_issue_master.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| validation_id | UUID | FK, NOT NULL | 検証マスタID |
| name | String(255) | NOT NULL | 課題名 |
| description | Text | NULLABLE | 説明 |
| agent_prompt | Text | NULLABLE | エージェントプロンプト |
| initial_msg | Text | NULLABLE | 初期メッセージ |
| dummy_hint | Text | NULLABLE | ダミーヒント |
| dummy_input | LargeBinary | NULLABLE | ダミー入力データ |
| issue_order | Integer | NOT NULL | 表示順序 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### analysis_graph_axis_master（グラフ軸マスタ）

**テーブル名**: `analysis_graph_axis_master`
**実装**: `src/app/models/analysis/analysis_graph_axis_master.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| issue_id | UUID | FK, NOT NULL | 課題マスタID |
| name | String(255) | NOT NULL | 軸名 |
| option | String(255) | NOT NULL | オプション |
| multiple | Boolean | NOT NULL | 複数選択可否 |
| axis_order | Integer | NOT NULL | 表示順序 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### analysis_dummy_formula_master（ダミー数式マスタ）

**テーブル名**: `analysis_dummy_formula_master`
**実装**: `src/app/models/analysis/analysis_dummy_formula_master.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| issue_id | UUID | FK, NOT NULL | 課題マスタID |
| name | String(255) | NOT NULL | 数式名 |
| value | String(255) | NOT NULL | 数式値 |
| formula_order | Integer | NOT NULL | 表示順序 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### analysis_dummy_chart_master（ダミーチャートマスタ）

**テーブル名**: `analysis_dummy_chart_master`
**実装**: `src/app/models/analysis/analysis_dummy_chart_master.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| issue_id | UUID | FK, NOT NULL | 課題マスタID |
| chart | LargeBinary | NOT NULL | チャートデータ |
| chart_order | Integer | NOT NULL | 表示順序 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

#### 3.4.2 セッション系テーブル

##### analysis_session（分析セッション）

**テーブル名**: `analysis_session`
**実装**: `src/app/models/analysis/analysis_session.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| issue_id | UUID | FK, NOT NULL | 課題マスタID |
| creator_id | UUID | FK, NOT NULL | 作成者ID |
| project_id | UUID | FK, NOT NULL | プロジェクトID |
| input_file_id | UUID | FK, NULLABLE | 入力ファイルID |
| current_snapshot | Integer | NOT NULL, DEFAULT 0 | 現在のスナップショット番号 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### analysis_file（分析ファイル）

**テーブル名**: `analysis_file`
**実装**: `src/app/models/analysis/analysis_file.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| session_id | UUID | FK, NOT NULL | セッションID |
| project_file_id | UUID | FK, NOT NULL | プロジェクトファイルID |
| sheet_name | String(255) | NOT NULL | シート名 |
| axis_config | JSONB | NOT NULL | 軸設定 |
| data | JSONB | NOT NULL | データ |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### analysis_snapshot（分析スナップショット）

**テーブル名**: `analysis_snapshot`
**実装**: `src/app/models/analysis/analysis_snapshot.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| session_id | UUID | FK, NOT NULL | セッションID |
| snapshot_order | Integer | NOT NULL | スナップショット順序 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### analysis_chat（分析チャット）

**テーブル名**: `analysis_chat`
**実装**: `src/app/models/analysis/analysis_chat.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| snapshot_id | UUID | FK, NOT NULL | スナップショットID |
| chat_order | Integer | NOT NULL | チャット順序 |
| role | String(50) | NOT NULL | ロール（user/assistant） |
| message | Text | NULLABLE | メッセージ内容 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### analysis_step（分析ステップ）

**テーブル名**: `analysis_step`
**実装**: `src/app/models/analysis/analysis_step.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| snapshot_id | UUID | FK, NOT NULL | スナップショットID |
| config | JSONB | NOT NULL | ステップ設定 |
| name | String(255) | NOT NULL | ステップ名 |
| step_order | Integer | NOT NULL | ステップ順序 |
| type | String(50) | NOT NULL | ステップタイプ |
| input | String(255) | NOT NULL | 入力 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

---

### 3.5 ドライバーツリー

#### 3.5.1 driver_tree_category（カテゴリマスタ）

**テーブル名**: `driver_tree_category`
**実装**: `src/app/models/driver_tree/driver_tree_category.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | Integer | PK, AUTO INCREMENT | 主キー（自動採番） |
| category_id | Integer | NOT NULL | 業界分類ID |
| category_name | String(255) | NOT NULL | 業界分類 |
| industry_id | Integer | NOT NULL | 業界名ID |
| industry_name | String(255) | NOT NULL | 業界名 |
| driver_type_id | Integer | NOT NULL | ドライバー型ID（1-24） |
| driver_type_name | String(255) | NOT NULL | ドライバー型 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### インデックス

- PRIMARY KEY: `id`
- INDEX: `industry_name` (ix_category_industry)
- INDEX: `driver_type_id` (ix_category_driver)

#### 3.5.2 driver_tree_formula（数式マスタ）

**テーブル名**: `driver_tree_formula`
**実装**: `src/app/models/driver_tree/driver_tree_formula.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| driver_type_id | Integer | NOT NULL | ドライバー型ID（1-24） |
| driver_type | String(255) | NOT NULL | ドライバー型 |
| kpi | String(50) | NOT NULL | KPI（売上、原価、販管費、粗利、営業利益、EBITDA） |
| formulas | JSONB | NOT NULL | 数式リスト（配列） |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### インデックス

- PRIMARY KEY: `id`
- UNIQUE: `(driver_type_id, kpi)` (uq_driver_kpi)
- INDEX: `(driver_type_id, kpi)` (ix_formula_driver_kpi)

#### 3.5.3 driver_tree（ドライバーツリー）

**テーブル名**: `driver_tree`
**実装**: `src/app/models/driver_tree/driver_tree.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| project_id | UUID | FK, NOT NULL | プロジェクトID |
| name | String(255) | NOT NULL | ツリー名 |
| description | Text | NOT NULL, DEFAULT '' | 説明 |
| root_node_id | UUID | FK, NULLABLE | ルートノードID |
| formula_id | UUID | FK, NULLABLE | 数式テンプレートID |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

##### インデックス

- PRIMARY KEY: `id`
- INDEX: `project_id` (idx_driver_tree_project_id)
- FOREIGN KEY: `project_id` → `project(id)` ON DELETE CASCADE
- FOREIGN KEY: `root_node_id` → `driver_tree_node(id)` ON DELETE SET NULL
- FOREIGN KEY: `formula_id` → `driver_tree_formula(id)` ON DELETE SET NULL

#### 3.5.4 driver_tree_node（ノード）

**テーブル名**: `driver_tree_node`
**実装**: `src/app/models/driver_tree/driver_tree_node.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| label | String(255) | NOT NULL | ノードラベル |
| position_x | Integer | NULLABLE, DEFAULT 0 | X座標 |
| position_y | Integer | NULLABLE, DEFAULT 0 | Y座標 |
| node_type | String(50) | NOT NULL | ノードタイプ（計算/入力/定数） |
| data_frame_id | UUID | FK, NULLABLE | データフレームID |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

#### 3.5.5 driver_tree_relationship（リレーションシップ）

**テーブル名**: `driver_tree_relationship`
**実装**: `src/app/models/driver_tree/driver_tree_relationship.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| driver_tree_id | UUID | FK, NOT NULL | ドライバーツリーID |
| parent_node_id | UUID | FK, NOT NULL | 親ノードID |
| operator | String(1) | NULLABLE | 演算子（+, -, *, /） |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

#### 3.5.6 driver_tree_relationship_child（リレーションシップ子ノード）

**テーブル名**: `driver_tree_relationship_child`
**実装**: `src/app/models/driver_tree/driver_tree_relationship_child.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| relationship_id | UUID | FK, NOT NULL | リレーションシップID |
| child_node_id | UUID | FK, NOT NULL | 子ノードID |
| order_index | Integer | NOT NULL, DEFAULT 0 | ノードの順番 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

#### 3.5.7 driver_tree_file（ファイル）

**テーブル名**: `driver_tree_file`
**実装**: `src/app/models/driver_tree/driver_tree_file.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| project_file_id | UUID | FK, NOT NULL | プロジェクトファイルID |
| sheet_name | String(255) | NOT NULL | シート名 |
| axis_config | JSONB | NOT NULL | 軸設定（推移/軸/値/利用しない） |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

#### 3.5.8 driver_tree_data_frame（データフレーム）

**テーブル名**: `driver_tree_data_frame`
**実装**: `src/app/models/driver_tree/driver_tree_data_frame.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| driver_tree_file_id | UUID | FK, NOT NULL | ドライバーツリーファイルID |
| column_name | String(255) | NOT NULL | 列名 |
| data | JSONB | NULLABLE | データ（キャッシュ） |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

#### 3.5.9 driver_tree_policy（施策）

**テーブル名**: `driver_tree_policy`
**実装**: `src/app/models/driver_tree/driver_tree_policy.py`

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PK | 主キー |
| node_id | UUID | FK, NOT NULL | ノードID |
| label | String(255) | NOT NULL | 施策ラベル |
| value | Float | NOT NULL, DEFAULT 0 | 施策値 |
| created_at | DateTime | NOT NULL | 作成日時 |
| updated_at | DateTime | NOT NULL | 更新日時 |

---

## 4. JSONB列の活用

### 4.1 JSONB使用箇所と目的

| テーブル | カラム | 目的 |
|---------|--------|------|
| user_account | roles | システムロールの配列 |
| analysis_file | axis_config | 軸設定の柔軟な構造 |
| analysis_file | data | データの格納 |
| analysis_step | config | ステップ設定の柔軟な構造 |
| driver_tree_formula | formulas | 業界別数式テンプレート |
| driver_tree_file | axis_config | 軸設定（推移/軸/値/利用しない） |
| driver_tree_data_frame | data | 列データのキャッシュ |

### 4.2 JSONB検索とインデックス

PostgreSQLのJSONB型は効率的な検索とインデックスをサポートします：

```sql
-- JSONB GINインデックス作成（推奨）
CREATE INDEX idx_analysis_file_axis_config
ON analysis_file USING GIN (axis_config);

CREATE INDEX idx_analysis_step_config
ON analysis_step USING GIN (config);
```

---

## 5. カスケード削除戦略

### 5.1 カスケード削除関係図

::: mermaid
graph TB
    Project[Project削除]
    Project -->|CASCADE| PM[ProjectMember削除]
    Project -->|CASCADE| PF[ProjectFile削除]
    Project -->|CASCADE| AS[AnalysisSession削除]
    Project -->|CASCADE| DT[DriverTree削除]

    PF -->|CASCADE| AF[AnalysisFile削除]
    PF -->|CASCADE| DTF[DriverTreeFile削除]

    AS -->|CASCADE| ASnap[AnalysisSnapshot削除]
    AS -->|CASCADE| AFile[AnalysisFile削除]

    ASnap -->|CASCADE| AChat[AnalysisChat削除]
    ASnap -->|CASCADE| AStep[AnalysisStep削除]

    DTF -->|CASCADE| DTDF[DriverTreeDataFrame削除]

    DT -->|CASCADE| DTR[DriverTreeRelationship削除]
    DTR -->|CASCADE| DTRC[DriverTreeRelationshipChild削除]

    DTN[DriverTreeNode削除]
    DTN -->|CASCADE| DTP[DriverTreePolicy削除]

    style Project fill:#FF6B6B
    style AS fill:#FFA07A
    style DT fill:#FFB347
:::

### 5.2 削除動作一覧

| 親テーブル | 子テーブル | 削除時動作 | 理由 |
|----------|----------|----------|------|
| project | project_member | CASCADE | プロジェクト削除時、メンバーシップも削除 |
| project | project_file | CASCADE | プロジェクト削除時、ファイルも削除 |
| project | analysis_session | CASCADE | プロジェクト削除時、分析セッションも削除 |
| project | driver_tree | CASCADE | プロジェクト削除時、ドライバーツリーも削除 |
| project_file | analysis_file | CASCADE | ファイル削除時、分析ファイルも削除 |
| project_file | driver_tree_file | CASCADE | ファイル削除時、ドライバーツリーファイルも削除 |
| analysis_session | analysis_snapshot | CASCADE | セッション削除時、スナップショットも削除 |
| analysis_session | analysis_file | CASCADE | セッション削除時、ファイルも削除 |
| analysis_snapshot | analysis_chat | CASCADE | スナップショット削除時、チャットも削除 |
| analysis_snapshot | analysis_step | CASCADE | スナップショット削除時、ステップも削除 |
| analysis_validation_master | analysis_issue_master | CASCADE | 検証マスタ削除時、課題マスタも削除 |
| analysis_issue_master | analysis_graph_axis_master | CASCADE | 課題マスタ削除時、グラフ軸マスタも削除 |
| driver_tree | driver_tree_relationship | CASCADE | ツリー削除時、リレーションシップも削除 |
| driver_tree_relationship | driver_tree_relationship_child | CASCADE | リレーションシップ削除時、子も削除 |
| driver_tree_file | driver_tree_data_frame | CASCADE | ファイル削除時、データフレームも削除 |
| driver_tree_node | driver_tree_policy | CASCADE | ノード削除時、施策も削除 |
| user_account | project_member | CASCADE | ユーザー削除時、メンバーシップも削除 |

### 5.3 SET NULL戦略

| 親テーブル | 子テーブル | カラム | 削除時動作 |
|----------|----------|--------|----------|
| driver_tree_node | driver_tree | root_node_id | SET NULL |
| driver_tree_formula | driver_tree | formula_id | SET NULL |
| driver_tree_data_frame | driver_tree_node | data_frame_id | SET NULL |
| analysis_file | analysis_session | input_file_id | SET NULL |
| user_account | analysis_session | creator_id | SET NULL |

---

## 6. トランザクション管理

### 6.1 トランザクション実装パターン

#### 6.1.1 基本パターン（BaseRepository）

```python
# src/app/repositories/base.py

async def create(self, db: AsyncSession, **obj_in) -> ModelType:
    """作成（flush()のみ、commit()は呼び出し側）"""
    db_obj = self.model(**obj_in)
    db.add(db_obj)
    await db.flush()  # IDを取得するがcommitしない
    await db.refresh(db_obj)  # リレーションシップを読み込む
    return db_obj
```

#### 6.1.2 サービス層でのcommit

```python
# src/app/services/project/project/crud.py

async def create_project(
    self,
    db: AsyncSession,
    project_data: ProjectCreate,
    creator_id: UUID
) -> Project:
    """プロジェクトとメンバーを同一トランザクションで作成"""
    # 1. プロジェクト作成（flush）
    project = await self.project_repo.create(
        db,
        name=project_data.name,
        code=project_data.code,
        created_by=creator_id
    )

    # 2. メンバー追加（flush）
    await self.member_repo.create(
        db,
        project_id=project.id,
        user_id=creator_id,
        role=ProjectRole.PROJECT_MANAGER
    )

    # 3. 全処理成功後にcommit
    await db.commit()

    return project
```

---

## 7. パフォーマンスチューニング

### 7.1 N+1クエリ対策

```python
# src/app/repositories/base.py

async def get_multi(
    self,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    load_relations: list[str] | None = None,
    **filters
) -> list[ModelType]:
    """複数取得（N+1対策付き）"""
    stmt = select(self.model)

    # リレーションシップの事前読み込み
    if load_relations:
        for relation in load_relations:
            stmt = stmt.options(selectinload(getattr(self.model, relation)))

    # フィルタ適用
    for key, value in filters.items():
        if hasattr(self.model, key):
            stmt = stmt.where(getattr(self.model, key) == value)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
```

### 7.2 クエリパフォーマンス最適化

| 手法 | 実装 | 効果 |
|------|------|------|
| **selectinload** | 1対多リレーション | N+1解消 |
| **joinedload** | 多対1リレーション | JOINで1クエリ化 |
| **lazy='selectin'** | デフォルト読み込み戦略 | 自動N+1対策 |
| **LIMIT/OFFSET** | ページネーション | 大量データ対策 |
| **INDEX** | 検索キーにインデックス | クエリ高速化 |
| **Connection Pool** | pool_size=5, max_overflow=10 | 接続再利用 |

---

## 8. まとめ

### 8.1 テーブル数

**合計: 21テーブル**

- ユーザー管理: 1テーブル
- プロジェクト管理: 3テーブル
- 個別施策分析: 10テーブル（マスタ5 + セッション系5）
- ドライバーツリー: 7テーブル

### 8.2 データベース設計の特徴

- **UUID主キー**: 分散システム対応、セキュリティ向上
- **JSONB活用**: 柔軟なスキーマ設計（軸設定、ステップ設定、数式等）
- **適切なカスケード**: データ整合性保証
- **インデックス戦略**: 検索性能最適化
- **N+1対策**: selectinload/joinedload標準実装
- **トランザクション管理**: flush/commit分離パターン
- **非同期ORM**: AsyncSession、asyncpg

---

##### ドキュメント管理情報

- **作成日**: 2025年
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - ER図: `02-er-diagram.md`
  - API仕様書: `04-api/01-api-specifications.md`
