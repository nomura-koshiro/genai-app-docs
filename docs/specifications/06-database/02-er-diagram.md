# ER図（Entity Relationship Diagram）

## 1. 概要

本文書は、CAMPシステムのデータベース構造をEntity Relationship Diagram（ER図）として可視化したものです。

### 1.1 図の凡例

::: mermaid
erDiagram
    ENTITY_A ||--o{ ENTITY_B : "リレーション名"

    ENTITY_A {
        uuid id PK "主キー"
        string name UK "ユニークキー"
        uuid foreign_id FK "外部キー"
    }
:::

**カーディナリティ記法:**

- `||--||`: 1対1（One-to-One）
- `||--o{`: 1対多（One-to-Many）
- `}o--o{`: 多対多（Many-to-Many）
- `}o--||`: 多対1（Many-to-One）
- `}o--o|`: 多対0または1（Many-to-Zero-or-One）

**列の属性:**

- `PK`: Primary Key（主キー）
- `FK`: Foreign Key（外部キー）
- `UK`: Unique Key（ユニーク制約）

---

## 2. 全体ER図

### 2.1 システム全体のエンティティ関連図

::: mermaid
erDiagram
    UserAccount ||--o{ ProjectMember : "participates"
    UserAccount ||--o{ AnalysisSession : "creates"
    UserAccount ||--o{ AuditLog : "logs"
    UserAccount ||--o{ UserActivity : "activity"
    UserAccount ||--o{ UserSession : "sessions"

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

    AnalysisSession {
        uuid id PK
        uuid issue_id FK
        uuid creator_id FK
        uuid project_id FK
        uuid input_file_id FK
        integer current_snapshot
        timestamp created_at
        timestamp updated_at
    }

    AnalysisSnapshot {
        uuid id PK
        uuid session_id FK
        integer snapshot_order
        timestamp created_at
        timestamp updated_at
    }

    AnalysisChat {
        uuid id PK
        uuid snapshot_id FK
        integer chat_order
        string role
        text message
        timestamp created_at
        timestamp updated_at
    }

    AnalysisStep {
        uuid id PK
        uuid snapshot_id FK
        jsonb config
        string name
        integer step_order
        string type
        string input
        timestamp created_at
        timestamp updated_at
    }

    AnalysisFile {
        uuid id PK
        uuid session_id FK
        uuid project_file_id FK
        string sheet_name
        jsonb axis_config
        jsonb data
        timestamp created_at
        timestamp updated_at
    }

    AnalysisValidationMaster {
        uuid id PK
        string name
        integer validation_order
        timestamp created_at
        timestamp updated_at
    }

    AnalysisIssueMaster {
        uuid id PK
        uuid validation_id FK
        string name
        text description
        text agent_prompt
        text initial_msg
        text dummy_hint
        bytea dummy_input
        integer issue_order
        timestamp created_at
        timestamp updated_at
    }

    AnalysisGraphAxisMaster {
        uuid id PK
        uuid issue_id FK
        string name
        string option
        boolean multiple
        integer axis_order
        timestamp created_at
        timestamp updated_at
    }

    AnalysisDummyFormulaMaster {
        uuid id PK
        uuid issue_id FK
        string name
        string value
        integer formula_order
        timestamp created_at
        timestamp updated_at
    }

    AnalysisDummyChartMaster {
        uuid id PK
        uuid issue_id FK
        bytea chart
        integer chart_order
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeCategory {
        integer id PK
        integer category_id
        string category_name
        integer industry_id
        string industry_name
        integer driver_type_id
        string driver_type_name
        timestamp created_at
        timestamp updated_at
    }

    DriverTree {
        uuid id PK
        uuid project_id FK
        string name
        text description
        uuid root_node_id FK
        uuid formula_id FK
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeNode {
        uuid id PK
        string label
        integer position_x
        integer position_y
        string node_type
        uuid data_frame_id FK
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeRelationship {
        uuid id PK
        uuid driver_tree_id FK
        uuid parent_node_id FK
        string operator
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeRelationshipChild {
        uuid id PK
        uuid relationship_id FK
        uuid child_node_id FK
        integer order_index
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeFormula {
        uuid id PK
        integer driver_type_id
        string driver_type
        string kpi
        jsonb formulas
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeFile {
        uuid id PK
        uuid project_file_id FK
        string sheet_name
        jsonb axis_config
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeDataFrame {
        uuid id PK
        uuid driver_tree_file_id FK
        string column_name
        jsonb data
        timestamp created_at
        timestamp updated_at
    }

    DriverTreePolicy {
        uuid id PK
        uuid node_id FK
        string label
        float value
        timestamp created_at
        timestamp updated_at
    }

    AuditLog {
        uuid id PK
        uuid user_id FK
        string event_type
        string action
        string resource_type
        uuid resource_id
        jsonb old_value
        jsonb new_value
        string severity
        timestamp created_at
    }

    UserActivity {
        uuid id PK
        uuid user_id FK
        string action_type
        string endpoint
        string method
        integer response_status
        integer duration_ms
        timestamp created_at
    }

    SystemSetting {
        uuid id PK
        string category
        string key UK
        jsonb value
        string value_type
        boolean is_secret
        timestamp created_at
        timestamp updated_at
    }

    SystemAnnouncement {
        uuid id PK
        string title
        text content
        string announcement_type
        timestamp start_at
        timestamp end_at
        boolean is_active
        uuid created_by FK
        timestamp created_at
    }

    SystemAlert {
        uuid id PK
        string name
        string condition_type
        jsonb threshold
        boolean is_enabled
        uuid created_by FK
        timestamp created_at
    }

    NotificationTemplate {
        uuid id PK
        string name
        string event_type UK
        string subject
        text body
        boolean is_active
        timestamp created_at
    }

    UserSession {
        uuid id PK
        uuid user_id FK
        string session_token_hash
        string ip_address
        timestamp login_at
        timestamp expires_at
        boolean is_active
        timestamp created_at
    }
:::

---

## 3. モジュール別ER図

### 3.1 ユーザー管理モジュール

::: mermaid
erDiagram
    UserAccount ||--o{ ProjectMember : "participates in"
    UserAccount ||--o{ AnalysisSession : "creates"

    UserAccount {
        uuid id PK "主キー"
        string azure_oid UK "Azure AD Object ID（ユニーク）"
        string email UK "メールアドレス（ユニーク）"
        string display_name "表示名"
        json roles "システムロール"
        boolean is_active "アクティブフラグ"
        timestamp last_login "最終ログイン日時"
        timestamp created_at "作成日時"
        timestamp updated_at "更新日時"
    }
:::

**主要な特徴:**

- Azure AD統合: `azure_oid`でAzure ADユーザーと紐付け
- システムロール: JSON配列で複数ロール対応（例: `["SystemAdmin", "User"]`）
- ソフトデリート: `is_active`フラグで論理削除

---

### 3.2 プロジェクト管理モジュール

::: mermaid
erDiagram
    Project ||--o{ ProjectMember : "has members"
    Project ||--o{ ProjectFile : "has files"

    ProjectMember }o--|| Project : "belongs to"
    ProjectMember }o--|| UserAccount : "user"

    ProjectFile }o--|| Project : "in"
    ProjectFile }o--|| UserAccount : "uploaded by"

    Project {
        uuid id PK
        string name "プロジェクト名"
        string code UK "プロジェクトコード（ユニーク）"
        text description "説明"
        boolean is_active "アクティブフラグ"
        uuid created_by "作成者ID"
        timestamp created_at
        timestamp updated_at
    }

    ProjectMember {
        uuid id PK
        uuid project_id FK "プロジェクト"
        uuid user_id FK "ユーザー"
        enum role "プロジェクトロール"
        timestamp joined_at "参加日時"
        uuid added_by FK "追加者ID"
    }

    ProjectFile {
        uuid id PK
        uuid project_id FK "所属プロジェクト"
        string filename "保存ファイル名"
        string original_filename "元ファイル名"
        string file_path "ストレージパス"
        integer file_size "ファイルサイズ（バイト）"
        string mime_type "MIMEタイプ"
        uuid uploaded_by FK "アップロード者"
        timestamp uploaded_at "アップロード日時"
    }
:::

**プロジェクトロール（ProjectRole）:**

- `PROJECT_MANAGER`: プロジェクトマネージャー（最高権限）
- `PROJECT_MODERATOR`: 権限管理者（メンバー管理）
- `MEMBER`: 一般メンバー（編集可能）
- `VIEWER`: 閲覧者（読み取りのみ）

**制約:**

- `(project_id, user_id)`に複合ユニーク制約（同じユーザーは1つのプロジェクトに1回だけ参加可能）
- プロジェクト削除時、関連するメンバーとファイルはカスケード削除

---

### 3.3 個別施策分析モジュール

#### 3.3.1 マスタ系

::: mermaid
erDiagram
    AnalysisValidationMaster ||--o{ AnalysisIssueMaster : "has issues"
    AnalysisIssueMaster ||--o{ AnalysisGraphAxisMaster : "has axes"
    AnalysisIssueMaster ||--o{ AnalysisDummyFormulaMaster : "has formulas"
    AnalysisIssueMaster ||--o{ AnalysisDummyChartMaster : "has charts"

    AnalysisValidationMaster {
        uuid id PK
        string name "検証名"
        integer validation_order "表示順序"
        timestamp created_at
        timestamp updated_at
    }

    AnalysisIssueMaster {
        uuid id PK
        uuid validation_id FK "検証マスタID"
        string name "課題名"
        text description "説明"
        text agent_prompt "エージェントプロンプト"
        text initial_msg "初期メッセージ"
        text dummy_hint "ダミーヒント"
        bytea dummy_input "ダミー入力データ"
        integer issue_order "表示順序"
        timestamp created_at
        timestamp updated_at
    }

    AnalysisGraphAxisMaster {
        uuid id PK
        uuid issue_id FK "課題マスタID"
        string name "軸名"
        string option "オプション"
        boolean multiple "複数選択可否"
        integer axis_order "表示順序"
        timestamp created_at
        timestamp updated_at
    }

    AnalysisDummyFormulaMaster {
        uuid id PK
        uuid issue_id FK "課題マスタID"
        string name "数式名"
        string value "数式値"
        integer formula_order "表示順序"
        timestamp created_at
        timestamp updated_at
    }

    AnalysisDummyChartMaster {
        uuid id PK
        uuid issue_id FK "課題マスタID"
        bytea chart "チャートデータ"
        integer chart_order "表示順序"
        timestamp created_at
        timestamp updated_at
    }
:::

**マスタ階層:**

```text
AnalysisValidationMaster (検証マスタ)
  └── AnalysisIssueMaster (課題マスタ)
        ├── AnalysisGraphAxisMaster (グラフ軸マスタ)
        ├── AnalysisDummyFormulaMaster (ダミー数式マスタ)
        └── AnalysisDummyChartMaster (ダミーチャートマスタ)
```

#### 3.3.2 セッション系

::: mermaid
erDiagram
    AnalysisSession ||--o{ AnalysisSnapshot : "has snapshots"
    AnalysisSession ||--o{ AnalysisFile : "has files"
    AnalysisSession }o--|| Project : "belongs to"
    AnalysisSession }o--|| UserAccount : "created by"
    AnalysisSession }o--|| AnalysisIssueMaster : "uses issue"
    AnalysisSession }o--o| AnalysisFile : "input file"

    AnalysisSnapshot ||--o{ AnalysisChat : "has chats"
    AnalysisSnapshot ||--o{ AnalysisStep : "has steps"

    AnalysisFile }o--|| ProjectFile : "from"

    AnalysisSession {
        uuid id PK
        uuid issue_id FK "課題マスタID"
        uuid creator_id FK "作成者ID"
        uuid project_id FK "プロジェクトID"
        uuid input_file_id FK "入力ファイルID"
        integer current_snapshot "現在のスナップショット番号"
        timestamp created_at
        timestamp updated_at
    }

    AnalysisSnapshot {
        uuid id PK
        uuid session_id FK "セッションID"
        integer snapshot_order "スナップショット順序"
        timestamp created_at
        timestamp updated_at
    }

    AnalysisChat {
        uuid id PK
        uuid snapshot_id FK "スナップショットID"
        integer chat_order "チャット順序"
        string role "ロール（user/assistant）"
        text message "メッセージ"
        timestamp created_at
        timestamp updated_at
    }

    AnalysisStep {
        uuid id PK
        uuid snapshot_id FK "スナップショットID"
        jsonb config "ステップ設定"
        string name "ステップ名"
        integer step_order "ステップ順序"
        string type "ステップタイプ"
        string input "入力"
        timestamp created_at
        timestamp updated_at
    }

    AnalysisFile {
        uuid id PK
        uuid session_id FK "セッションID"
        uuid project_file_id FK "プロジェクトファイルID"
        string sheet_name "シート名"
        jsonb axis_config "軸設定"
        jsonb data "データ"
        timestamp created_at
        timestamp updated_at
    }
:::

**セッション階層:**

```text
AnalysisSession (分析セッション)
  ├── AnalysisFile (分析ファイル) ← ProjectFile
  └── AnalysisSnapshot (スナップショット)
        ├── AnalysisChat (チャット履歴)
        └── AnalysisStep (分析ステップ)
```

---

### 3.4 ドライバーツリーモジュール

::: mermaid
erDiagram
    DriverTree ||--o{ DriverTreeRelationship : "has relationships"
    DriverTree }o--|| Project : "belongs to"
    DriverTree }o--o| DriverTreeNode : "root node"
    DriverTree }o--o| DriverTreeFormula : "uses formula"

    DriverTreeCategory ||--o{ DriverTreeFormula : "has formulas"

    DriverTreeRelationship ||--o{ DriverTreeRelationshipChild : "has children"
    DriverTreeRelationship }o--|| DriverTreeNode : "parent node"

    DriverTreeRelationshipChild }o--|| DriverTreeNode : "child node"

    DriverTreeNode ||--o{ DriverTreePolicy : "has policies"
    DriverTreeNode }o--o| DriverTreeDataFrame : "uses data"

    DriverTreeFile ||--o{ DriverTreeDataFrame : "has frames"
    DriverTreeFile }o--|| ProjectFile : "from"

    DriverTreeCategory {
        integer id PK "主キー（自動採番）"
        integer category_id "業界分類ID"
        string category_name "業界分類"
        integer industry_id "業界名ID"
        string industry_name "業界名"
        integer driver_type_id "ドライバー型ID"
        string driver_type_name "ドライバー型"
        timestamp created_at
        timestamp updated_at
    }

    DriverTree {
        uuid id PK
        uuid project_id FK "プロジェクトID"
        string name "ツリー名"
        text description "説明"
        uuid root_node_id FK "ルートノードID"
        uuid formula_id FK "数式マスタID"
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeNode {
        uuid id PK
        string label "ノードラベル"
        integer position_x "X座標"
        integer position_y "Y座標"
        string node_type "ノードタイプ"
        uuid data_frame_id FK "データフレームID"
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeRelationship {
        uuid id PK
        uuid driver_tree_id FK "ドライバーツリーID"
        uuid parent_node_id FK "親ノードID"
        string operator "演算子"
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeRelationshipChild {
        uuid id PK
        uuid relationship_id FK "リレーションシップID"
        uuid child_node_id FK "子ノードID"
        integer order_index "順番"
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeFormula {
        uuid id PK
        integer driver_type_id "ドライバー型ID"
        string driver_type "ドライバー型"
        string kpi "KPI"
        jsonb formulas "数式"
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeFile {
        uuid id PK
        uuid project_file_id FK "プロジェクトファイルID"
        string sheet_name "シート名"
        jsonb axis_config "軸設定"
        timestamp created_at
        timestamp updated_at
    }

    DriverTreeDataFrame {
        uuid id PK
        uuid driver_tree_file_id FK "ファイルID"
        string column_name "列名"
        jsonb data "データ"
        timestamp created_at
        timestamp updated_at
    }

    DriverTreePolicy {
        uuid id PK
        uuid node_id FK "ノードID"
        string label "施策ラベル"
        float value "施策値"
        timestamp created_at
        timestamp updated_at
    }
:::

**ドライバーツリー構造:**

```text
DriverTreeCategory (カテゴリマスタ)
  └── DriverTreeFormula[] (数式マスタ)

DriverTree (ドライバーツリー)
  ├── name, description (ツリー名、説明)
  ├── root_node → DriverTreeNode (ルートノード)
  ├── formula → DriverTreeFormula (数式マスタ、任意)
  └── DriverTreeRelationship (リレーションシップ)
        ├── parent_node → DriverTreeNode (親ノード)
        └── DriverTreeRelationshipChild[] (子ノード群)
              └── child_node → DriverTreeNode

DriverTreeNode (ノード)
  ├── data_frame → DriverTreeDataFrame (データ、任意)
  └── DriverTreePolicy[] (施策)

DriverTreeFile (ファイル) ← ProjectFile
  └── DriverTreeDataFrame[] (データフレーム)
```

**特徴:**

- **リレーションシップ管理**: `DriverTreeRelationship`で親ノードを定義し、`DriverTreeRelationshipChild`で子ノードを順序付きで管理
- **演算子**: 親ノードの値は子ノードの値を演算子（+, -, *, /）で計算
- **データ連携**: `DriverTreeDataFrame`でExcelデータとノードを紐付け
- **施策管理**: `DriverTreePolicy`でノードに施策を追加

---

### 3.5 監査・操作履歴モジュール

::: mermaid
erDiagram
    UserAccount ||--o{ AuditLog : "logs"
    UserAccount ||--o{ UserActivity : "activity"

    AuditLog {
        uuid id PK "主キー"
        uuid user_id FK "操作ユーザーID（NULL可）"
        string event_type "イベント種別（DATA_CHANGE/SECURITY）"
        string action "アクション（CREATE/UPDATE/DELETE）"
        string resource_type "リソース種別"
        uuid resource_id "リソースID"
        jsonb old_value "変更前の値"
        jsonb new_value "変更後の値"
        jsonb changed_fields "変更フィールド一覧"
        string ip_address "IPアドレス"
        string severity "重要度（INFO/WARNING/CRITICAL）"
        timestamp created_at "作成日時"
    }

    UserActivity {
        uuid id PK "主キー"
        uuid user_id FK "操作ユーザーID（NULL可）"
        string action_type "操作種別（CREATE/READ/UPDATE/DELETE）"
        string resource_type "リソース種別"
        uuid resource_id "リソースID"
        string endpoint "APIエンドポイント"
        string method "HTTPメソッド"
        jsonb request_body "リクエストボディ（マスク済み）"
        integer response_status "レスポンスステータス"
        string error_message "エラーメッセージ"
        integer duration_ms "処理時間（ミリ秒）"
        timestamp created_at "作成日時"
    }
:::

**監査・操作履歴の特徴:**

- **AuditLog**: 重要なデータ変更・セキュリティイベントのみ記録
- **UserActivity**: 全APIリクエストを自動記録
- **機密情報マスク**: パスワード、トークン等は自動マスク
- **ユーザー削除時**: 外部キーはSET NULLで履歴は保持

---

### 3.6 システム管理モジュール

::: mermaid
erDiagram
    UserAccount ||--o{ UserSession : "has sessions"
    UserAccount ||--o{ SystemAnnouncement : "creates"
    UserAccount ||--o{ SystemAlert : "creates"

    SystemSetting {
        uuid id PK "主キー"
        string category "カテゴリ（GENERAL/SECURITY/MAINTENANCE）"
        string key UK "設定キー（カテゴリ内ユニーク）"
        jsonb value "設定値"
        string value_type "値の型（STRING/NUMBER/BOOLEAN/JSON）"
        text description "説明"
        boolean is_secret "機密設定フラグ"
        boolean is_editable "編集可能フラグ"
        uuid updated_by FK "更新者ID"
        timestamp created_at "作成日時"
        timestamp updated_at "更新日時"
    }

    SystemAnnouncement {
        uuid id PK "主キー"
        string title "タイトル"
        text content "本文"
        string announcement_type "種別（INFO/WARNING/MAINTENANCE）"
        integer priority "優先度（1が最高）"
        timestamp start_at "表示開始日時"
        timestamp end_at "表示終了日時"
        boolean is_active "有効フラグ"
        jsonb target_roles "対象ロール"
        uuid created_by FK "作成者ID"
        timestamp created_at "作成日時"
    }

    SystemAlert {
        uuid id PK "主キー"
        string name "アラート名"
        string condition_type "条件種別（ERROR_RATE/STORAGE_USAGE等）"
        jsonb threshold "閾値設定"
        string comparison_operator "比較演算子"
        jsonb notification_channels "通知先"
        boolean is_enabled "有効フラグ"
        timestamp last_triggered_at "最終発火日時"
        integer trigger_count "発火回数"
        uuid created_by FK "作成者ID"
        timestamp created_at "作成日時"
    }

    NotificationTemplate {
        uuid id PK "主キー"
        string name "テンプレート名"
        string event_type UK "イベント種別（ユニーク）"
        string subject "件名テンプレート"
        text body "本文テンプレート"
        jsonb variables "利用可能変数リスト"
        boolean is_active "有効フラグ"
        timestamp created_at "作成日時"
    }

    UserSession {
        uuid id PK "主キー"
        uuid user_id FK "ユーザーID"
        string session_token_hash "セッショントークンハッシュ"
        string ip_address "IPアドレス"
        string user_agent "ユーザーエージェント"
        jsonb device_info "デバイス情報"
        timestamp login_at "ログイン日時"
        timestamp last_activity_at "最終アクティビティ"
        timestamp expires_at "有効期限"
        boolean is_active "アクティブフラグ"
        timestamp logout_at "ログアウト日時"
        string logout_reason "ログアウト理由"
    }
:::

**システム管理の特徴:**

- **SystemSetting**: メンテナンスモード、セキュリティ設定等を管理
- **SystemAnnouncement**: システムお知らせ（期間・対象ロール指定可能）
- **SystemAlert**: 監視アラート設定（閾値超過時に通知）
- **NotificationTemplate**: メール通知テンプレート
- **UserSession**: セッション管理（強制ログアウト、同時接続数制限）

---

## 4. リレーションシップ詳細

### 4.1 主要なリレーションシップ一覧

| 親テーブル | 子テーブル | カーディナリティ | 外部キー | ON DELETE | 説明 |
|-----------|-----------|----------------|---------|-----------|------|
| user_account | project_member | 1:N | user_id | CASCADE | ユーザーのプロジェクト参加 |
| user_account | analysis_session | 1:N | creator_id | SET NULL | ユーザーが作成した分析セッション |
| project | project_member | 1:N | project_id | CASCADE | プロジェクトのメンバー |
| project | project_file | 1:N | project_id | CASCADE | プロジェクトのファイル |
| project | analysis_session | 1:N | project_id | CASCADE | プロジェクトの分析セッション |
| project | driver_tree | 1:N | project_id | CASCADE | プロジェクトのドライバーツリー |
| project_file | analysis_file | 1:N | project_file_id | CASCADE | ファイルを使用した分析ファイル |
| project_file | driver_tree_file | 1:N | project_file_id | CASCADE | ファイルを使用したドライバーツリーファイル |
| analysis_issue_master | analysis_session | 1:N | issue_id | CASCADE | 課題を使用したセッション |
| analysis_session | analysis_snapshot | 1:N | session_id | CASCADE | セッションのスナップショット |
| analysis_session | analysis_file | 1:N | session_id | CASCADE | セッションのファイル |
| analysis_snapshot | analysis_chat | 1:N | snapshot_id | CASCADE | スナップショットのチャット |
| analysis_snapshot | analysis_step | 1:N | snapshot_id | CASCADE | スナップショットのステップ |
| analysis_validation_master | analysis_issue_master | 1:N | validation_id | CASCADE | 検証の課題 |
| analysis_issue_master | analysis_graph_axis_master | 1:N | issue_id | CASCADE | 課題のグラフ軸 |
| analysis_issue_master | analysis_dummy_formula_master | 1:N | issue_id | CASCADE | 課題のダミー数式 |
| analysis_issue_master | analysis_dummy_chart_master | 1:N | issue_id | CASCADE | 課題のダミーチャート |
| driver_tree | driver_tree_relationship | 1:N | driver_tree_id | CASCADE | ツリーのリレーションシップ |
| driver_tree_relationship | driver_tree_relationship_child | 1:N | relationship_id | CASCADE | リレーションシップの子 |
| driver_tree_file | driver_tree_data_frame | 1:N | driver_tree_file_id | CASCADE | ファイルのデータフレーム |
| driver_tree_node | driver_tree_policy | 1:N | node_id | CASCADE | ノードの施策 |
| user_account | audit_log | 1:N | user_id | SET NULL | ユーザーの監査ログ |
| user_account | user_activity | 1:N | user_id | SET NULL | ユーザーの操作履歴 |
| user_account | user_session | 1:N | user_id | CASCADE | ユーザーのセッション |
| user_account | system_announcement | 1:N | created_by | CASCADE | ユーザーが作成したお知らせ |
| user_account | system_alert | 1:N | created_by | CASCADE | ユーザーが作成したアラート |

### 4.2 削除動作（ON DELETE）の説明

#### CASCADE（カスケード削除）

親レコード削除時、関連する子レコードも自動削除されます。

**適用箇所:**

- プロジェクト削除 → メンバー、ファイル、分析セッション、ドライバーツリーも削除
- 分析セッション削除 → スナップショット、ファイルも削除
- スナップショット削除 → チャット、ステップも削除
- ドライバーツリー削除 → リレーションシップも削除

#### SET NULL

親レコード削除時、子レコードの外部キーがNULLに設定されます。

**適用箇所:**

- ユーザー削除 → 分析セッションの`creator_id`がNULLに
- ユーザー削除 → 監査ログの`user_id`がNULLに（履歴保持）
- ユーザー削除 → 操作履歴の`user_id`がNULLに（履歴保持）
- ドライバーツリーノード削除 → ツリーの`root_node_id`がNULLに
- ドライバーツリー数式削除 → ツリーの`formula_id`がNULLに
- データフレーム削除 → ノードの`data_frame_id`がNULLに

#### RESTRICT

親レコード削除時、子レコードが存在する場合はエラー。

**適用箇所:**

- ユーザー削除 → アップロードしたファイルが存在する場合はエラー

---

## 5. インデックス設計

### 5.1 推奨インデックス一覧

| テーブル | インデックス名 | カラム | タイプ | 目的 |
|---------|--------------|--------|--------|------|
| user_account | PRIMARY KEY | id | UNIQUE | 主キー検索 |
| user_account | idx_users_azure_oid | azure_oid | UNIQUE | Azure OID検索 |
| user_account | idx_users_email | email | UNIQUE | メール検索 |
| project | PRIMARY KEY | id | UNIQUE | 主キー検索 |
| project | idx_projects_code | code | UNIQUE | プロジェクトコード検索 |
| project_member | PRIMARY KEY | id | UNIQUE | 主キー検索 |
| project_member | uq_project_user | (project_id, user_id) | UNIQUE | 重複参加防止 |
| project_member | idx_project_members_project_id | project_id | BTREE | プロジェクト別メンバー |
| project_member | idx_project_members_user_id | user_id | BTREE | ユーザー別プロジェクト |
| project_file | PRIMARY KEY | id | UNIQUE | 主キー検索 |
| project_file | idx_project_files_project_id | project_id | BTREE | プロジェクト別ファイル |
| analysis_session | PRIMARY KEY | id | UNIQUE | 主キー検索 |
| analysis_session | idx (issue_id) | issue_id | BTREE | 課題別セッション |
| analysis_session | idx (creator_id) | creator_id | BTREE | 作成者別セッション |
| analysis_session | idx (project_id) | project_id | BTREE | プロジェクト別セッション |
| analysis_snapshot | idx (session_id) | session_id | BTREE | セッション別スナップショット |
| analysis_chat | idx (snapshot_id) | snapshot_id | BTREE | スナップショット別チャット |
| analysis_step | idx (snapshot_id) | snapshot_id | BTREE | スナップショット別ステップ |
| driver_tree | idx_driver_tree_project_id | project_id | BTREE | プロジェクト別ツリー |
| driver_tree_relationship | idx (driver_tree_id) | driver_tree_id | BTREE | ツリー別リレーションシップ |
| driver_tree_relationship | idx (parent_node_id) | parent_node_id | BTREE | 親ノード別 |
| driver_tree_relationship_child | idx (relationship_id) | relationship_id | BTREE | リレーションシップ別 |
| driver_tree_relationship_child | idx (child_node_id) | child_node_id | BTREE | 子ノード別 |
| driver_tree_policy | idx_driver_tree_policy_node_id | node_id | BTREE | ノード別施策 |
| audit_log | idx_audit_log_user_id | user_id | BTREE | ユーザー別監査ログ |
| audit_log | idx_audit_log_event_type | event_type | BTREE | イベント種別別 |
| audit_log | idx_audit_log_resource | (resource_type, resource_id) | BTREE | リソース別 |
| audit_log | idx_audit_log_created_at | created_at DESC | BTREE | 日時順 |
| user_activity | idx_user_activity_user_id | user_id | BTREE | ユーザー別操作履歴 |
| user_activity | idx_user_activity_created_at | created_at DESC | BTREE | 日時順 |
| system_setting | uq_system_setting_category_key | (category, key) | UNIQUE | 設定キー重複防止 |
| system_announcement | idx_announcement_active | (is_active, start_at, end_at) | BTREE | 有効なお知らせ取得 |
| user_session | idx_user_session_user_id | user_id | BTREE | ユーザー別セッション |
| user_session | idx_user_session_active | (is_active, expires_at) | BTREE | 有効セッション取得 |
| user_session | idx_user_session_token | session_token_hash | BTREE | トークン検索 |
| notification_template | uq_notification_template_event | event_type | UNIQUE | イベント種別重複防止 |

### 5.2 JSONB列のGINインデックス

```sql
-- JSONB列の検索性能向上
CREATE INDEX idx_analysis_file_axis_config
ON analysis_file USING GIN (axis_config);

CREATE INDEX idx_analysis_file_data
ON analysis_file USING GIN (data);

CREATE INDEX idx_analysis_step_config
ON analysis_step USING GIN (config);

CREATE INDEX idx_driver_tree_formula_formulas
ON driver_tree_formula USING GIN (formulas);
```

---

## 6. データ整合性制約

### 6.1 ユニーク制約

| テーブル | カラム | 説明 |
|---------|--------|------|
| user_account | azure_oid | Azure AD Object IDの重複防止 |
| user_account | email | メールアドレスの重複防止 |
| project | code | プロジェクトコードの重複防止 |
| project_member | (project_id, user_id) | 同じユーザーが同じプロジェクトに重複参加防止 |
| system_setting | (category, key) | 同一カテゴリ内での設定キー重複防止 |
| notification_template | event_type | イベント種別の重複防止 |

### 6.2 NOT NULL制約

すべてのテーブルで以下のカラムはNOT NULL:

- `id` (主キー)
- `created_at` (作成日時)
- `updated_at` (更新日時、該当テーブルのみ)

**その他の主要なNOT NULL:**

- `user_account.azure_oid`, `user_account.email`, `user_account.roles`, `user_account.is_active`
- `project.name`, `project.code`, `project.is_active`
- `project_member.project_id`, `project_member.user_id`, `project_member.role`
- `analysis_session.issue_id`, `analysis_session.project_id`（`creator_id`はNULLABLE - ユーザー削除時にSET NULL）
- `driver_tree_node.label`, `driver_tree_node.node_type`

---

## 7. まとめ

### 7.1 テーブル数

合計: 28テーブル

- ユーザー管理: 1テーブル
- プロジェクト管理: 3テーブル
- 個別施策分析: 10テーブル（マスタ5 + セッション系5）
- ドライバーツリー: 7テーブル
- 監査・操作履歴: 2テーブル（audit_log, user_activity）
- システム管理: 5テーブル（system_setting, system_announcement, system_alert, notification_template, user_session）

### 7.2 主要な設計思想

- **UUID主キー**: すべてのテーブルでUUID v4を使用（分散システム対応）
- **JSONB活用**: 柔軟なスキーマが必要な箇所でJSONB型を使用
- **タイムスタンプ**: すべてのレコードに作成日時・更新日時を記録（UTC）
- **論理削除**: `is_active`フラグによるソフトデリート
- **参照整合性**: 外部キー制約とON DELETE動作の適切な設定
- **インデックス最適化**: 検索頻度の高いカラムにインデックスを配置
- **非同期対応**: SQLAlchemy 2.0非同期ORMで実装
- **監査ログ**: 重要操作の追跡とセキュリティ監査
- **システム管理**: メンテナンスモード、お知らせ、アラート機能

### 7.3 関連ドキュメント

- **データベース設計書**: `01-database-design.md`
- **DBMLスキーマ**: `03-schema.dbml`
- **システムアーキテクチャ**: `../04-architecture/01-system-architecture.md`
- **セキュリティ実装**: `../05-security/03-security-implementation.md`
- **ミドルウェア設計書**: `../09-middleware/01-middleware-design.md`

---

#### ドキュメント管理情報

- **作成日**: 2025年
- **最終更新日**: 2026年1月（監査・システム管理テーブル追加）
- **対象バージョン**: 現行実装
