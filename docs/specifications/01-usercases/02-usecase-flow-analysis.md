# CAMPシステム ユースケースフロー分析

本文書は、ユースケースの前後関係（依存関係・順序関係）を分析し、DB設計の妥当性を検証するものです。

---

## 1. ユーザー管理フロー

### 1.1 フロー図

::: mermaid
graph TD
    subgraph 認証フロー
        U001[U-001: Azure ADでログインする]
        U002[U-002: ユーザーアカウントを作成する]
        U006[U-006: 最終ログイン日時を記録する]

        U001 --> |初回ログイン| U002
        U001 --> |既存ユーザー| U006
        U002 --> U006
    end

    subgraph アカウント管理フロー
        U003[U-003: ユーザー情報を更新する]
        U004[U-004: ユーザーを無効化する]
        U005[U-005: ユーザーを有効化する]
        U007[U-007: ユーザー一覧を取得する]
        U008[U-008: ユーザー詳細を取得する]

        U002 --> U003
        U002 --> U004
        U004 --> U005
        U002 --> U007
        U002 --> U008
    end

    subgraph ロール管理フロー
        U009[U-009: システムロールを付与する]
        U010[U-010: システムロールを剥奪する]
        U011[U-011: ユーザーのロールを確認する]

        U002 --> U009
        U009 --> U010
        U002 --> U011
    end
:::

### 1.2 前提条件分析

| ユースケース | 前提条件（先行UC） | 後続可能UC |
|-------------|-------------------|-----------|
| U-001: Azure ADでログイン | なし（エントリーポイント） | U-002, U-006 |
| U-002: アカウント作成 | U-001（初回時） | U-003〜U-011, 全プロジェクト操作 |
| U-003: 情報更新 | U-002 | - |
| U-004: 無効化 | U-002 | U-005 |
| U-005: 有効化 | U-004 | U-003〜U-011 |
| U-006: 最終ログイン記録 | U-001 | - |
| U-009: ロール付与 | U-002 | U-010, U-011 |
| U-010: ロール剥奪 | U-009 | - |

### 1.3 DB設計への示唆

```
【現状の問題点】
1. ロール履歴が追跡できない
   - roles列がJSON配列で、いつ誰がロールを変更したか不明

2. アカウント状態の履歴がない
   - is_activeの変更履歴が追跡できない

【改善案】
Option A: 監査ログテーブルの追加
  - user_audit_log (id, user_id, action, old_value, new_value, changed_by, changed_at)

Option B: ロール履歴テーブルの追加
  - user_role_history (id, user_id, role, granted_by, granted_at, revoked_by, revoked_at)
```

---

## 2. プロジェクト管理フロー

### 2.1 フロー図

::: mermaid
graph TD
    subgraph プロジェクト作成フロー
        P001[P-001: プロジェクトを作成する]
        PM001[PM-001: メンバーを追加する]

        P001 --> |作成者は自動的にPM| PM001
    end

    subgraph メンバー管理フロー
        PM002[PM-002: メンバーを削除する]
        PM003[PM-003: ロールを変更する]
        PM004[PM-004: メンバー一覧取得]
        PM005[PM-005: 参加プロジェクト一覧]
        PM006[PM-006: 権限確認]

        PM001 --> PM002
        PM001 --> PM003
        PM001 --> PM004
        PM001 --> PM006
    end

    subgraph ファイル管理フロー
        PF001[PF-001: ファイルアップロード]
        PF002[PF-002: ファイルダウンロード]
        PF003[PF-003: ファイル削除]
        PF004[PF-004: ファイル一覧取得]

        PM001 --> |権限必要| PF001
        PF001 --> PF002
        PF001 --> PF003
        PF001 --> PF004
    end

    subgraph プロジェクト状態管理
        P002[P-002: プロジェクト更新]
        P003[P-003: プロジェクト無効化]
        P004[P-004: プロジェクト有効化]

        P001 --> P002
        P001 --> P003
        P003 --> P004
    end
:::

### 2.2 前提条件分析

| ユースケース | 前提条件（先行UC） | 後続可能UC | 必要権限 |
|-------------|-------------------|-----------|---------|
| P-001: プロジェクト作成 | U-002（ユーザー存在） | PM-001〜PM-006, PF-001〜PF-006, P-002〜P-007 | SystemUser以上 |
| PM-001: メンバー追加 | P-001 | PM-002, PM-003, PF-001 | PM/MODERATOR |
| PM-002: メンバー削除 | PM-001 | - | PM/MODERATOR |
| PM-003: ロール変更 | PM-001 | - | PM |
| PF-001: ファイルアップロード | PM-001（メンバーである） | PF-002〜PF-006, AF-001, DTFL-001 | MEMBER以上 |
| PF-003: ファイル削除 | PF-001 | - | PM/MODERATOR/アップロード者 |
| P-003: プロジェクト無効化 | P-001 | P-004 | PM |

### 2.3 DB設計への示唆

```
【現状の問題点】
1. プロジェクト作成者とPROJECT_MANAGERの関係が暗黙的
   - created_byとProjectMemberの整合性保証がない

2. ファイル削除権限の判定が複雑
   - uploaded_by または PM/MODERATOR の判定がアプリケーション層依存

3. メンバー追加者（added_by）の制約がない
   - 権限のないユーザーがadded_byになる可能性

【改善案】
Option A: トリガーによる整合性保証
  - プロジェクト作成時、自動的にProjectMemberにPMとして追加

Option B: ファイル削除権限の明示化
  - ProjectFileに can_delete_by カラム追加、または削除ポリシーテーブル追加

Option C: 制約の追加
  - added_byはそのプロジェクトのPM/MODERATORであることをチェック制約
```

---

## 3. 個別施策分析フロー

### 3.1 マスタ設定フロー（管理者操作）

::: mermaid
graph TD
    subgraph 検証マスタ設定
        AVM001[AVM-001: 検証マスタ作成]
        AVM002[AVM-002: 検証マスタ更新]
        AVM003[AVM-003: 検証マスタ削除]

        AVM001 --> AVM002
        AVM001 --> AVM003
    end

    subgraph 課題マスタ設定
        AIM001[AIM-001: 課題マスタ作成]
        AIM002[AIM-002: 課題マスタ更新]
        AIM006[AIM-006: プロンプト設定]
        AIM007[AIM-007: 初期メッセージ設定]
        AIM008[AIM-008: ダミーデータ設定]

        AVM001 --> |検証が必要| AIM001
        AIM001 --> AIM002
        AIM001 --> AIM006
        AIM001 --> AIM007
        AIM001 --> AIM008
    end

    subgraph 軸・数式・チャート設定
        AGM001[AGM-001: グラフ軸作成]
        ADM001[ADM-001: ダミー数式作成]
        ADM005[ADM-005: ダミーチャート作成]

        AIM001 --> |課題が必要| AGM001
        AIM001 --> |課題が必要| ADM001
        AIM001 --> |課題が必要| ADM005
    end
:::

### 3.2 分析セッションフロー（ユーザー操作）

::: mermaid
graph TD
    subgraph セッション開始
        AS001[AS-001: セッション作成]
        AF001[AF-001: 分析ファイル作成]
        AS006[AS-006: 入力ファイル設定]

        AS001 --> AF001
        AF001 --> AS006
    end

    subgraph スナップショット操作
        ASN001[ASN-001: スナップショット作成]
        ASN005[ASN-005: 過去に戻る]

        AS001 --> |初期スナップショット| ASN001
        ASN001 --> ASN005
        ASN005 --> |新しいブランチ| ASN001
    end

    subgraph チャット・ステップ操作
        AC001[AC-001: チャット送信]
        AST001[AST-001: ステップ作成]
        AST002[AST-002: ステップ更新]

        ASN001 --> AC001
        ASN001 --> AST001
        AC001 --> |AI応答で| AST001
        AST001 --> AST002
    end

    subgraph 分岐フロー
        AS007[AS-007: 現在スナップショット更新]

        ASN005 --> AS007
        ASN001 --> AS007
    end
:::

### 3.3 前提条件分析（セッション系）

| ユースケース | 前提条件（先行UC） | 後続可能UC | 状態遷移 |
|-------------|-------------------|-----------|---------|
| AS-001: セッション作成 | P-001, PM-001, AIM-001 | AF-001, ASN-001 | 初期状態 |
| AF-001: 分析ファイル作成 | AS-001, PF-001 | AS-006 | ファイル紐付け |
| AS-006: 入力ファイル設定 | AF-001 | - | 入力確定 |
| ASN-001: スナップショット作成 | AS-001 | AC-001, AST-001, AS-007 | 新スナップショット |
| AC-001: チャット送信 | ASN-001 | AST-001（AI処理時） | チャット追加 |
| AST-001: ステップ作成 | ASN-001 | AST-002〜AST-006 | ステップ追加 |
| ASN-005: 過去に戻る | ASN-001（複数） | ASN-001, AS-007 | ブランチ発生 |

### 3.4 DB設計への示唆

```
【現状の問題点】
1. スナップショットの分岐履歴が追跡できない
   - snapshot_orderは連番だが、分岐元が不明
   - 過去に戻って新しいスナップショットを作った場合の親子関係が不明

2. current_snapshotの整合性
   - AnalysisSession.current_snapshotとAnalysisSnapshot.snapshot_orderの整合性保証がない

3. チャットとステップの関連が不明確
   - どのチャットがどのステップを生成したか追跡できない

4. 入力ファイルの状態管理
   - input_file_idがNULL許容だが、セッション開始後は必須という業務ルールが表現できない

【改善案】
Option A: スナップショットに親参照追加
  - AnalysisSnapshot.parent_snapshot_id FK (自己参照)
  - これにより分岐履歴がツリー構造で表現可能

Option B: チャットとステップの関連付け
  - AnalysisStep.triggered_by_chat_id FK
  - またはAnalysisChat.generated_step_id FK

Option C: セッション状態の明示化
  - AnalysisSession.status ENUM('draft', 'file_selected', 'analyzing', 'completed')
  - 状態によってNULL許容を制御

Option D: current_snapshotを外部キー化
  - current_snapshot INTEGER → current_snapshot_id UUID FK
  - 整合性をDB制約で保証
```

---

## 4. ドライバーツリーフロー

### 4.1 マスタ設定フロー

::: mermaid
graph TD
    subgraph カテゴリマスタ設定
        DTC001[DTC-001: カテゴリ作成]
        DTC002[DTC-002: カテゴリ更新]
        DTC005[DTC-005: 業界分類で絞込]
        DTC006[DTC-006: 業界名で絞込]
        DTC007[DTC-007: ドライバー型で絞込]

        DTC001 --> DTC002
        DTC001 --> DTC005
        DTC001 --> DTC006
        DTC001 --> DTC007
    end

    subgraph 数式マスタ設定
        DTF001[DTF-001: 数式マスタ作成]
        DTF002[DTF-002: 数式マスタ更新]
        DTF004[DTF-004: ドライバー型別一覧]
        DTF005[DTF-005: KPIで検索]

        DTC001 --> |カテゴリが必要| DTF001
        DTF001 --> DTF002
        DTF001 --> DTF004
        DTF001 --> DTF005
    end
:::

### 4.2 ツリー構築フロー

::: mermaid
graph TD
    subgraph ツリー作成
        DT001[DT-001: ツリー作成]
        DT007[DT-007: 数式マスタ紐付け]

        DT001 --> DT007
    end

    subgraph ファイル準備
        DTFL001[DTFL-001: ファイル作成]
        DTDF001[DTDF-001: データフレーム作成]

        DTFL001 --> DTDF001
    end

    subgraph ノード構築
        DTN001[DTN-001: ノード作成]
        DTN007[DTN-007: データフレーム紐付け]
        DT006[DT-006: ルートノード設定]

        DT001 --> DTN001
        DTDF001 --> DTN007
        DTN001 --> DTN007
        DTN001 --> DT006
    end

    subgraph リレーション構築
        DTR001[DTR-001: リレーション作成]
        DTRC001[DTRC-001: 子ノード追加]

        DTN001 --> |親ノード| DTR001
        DTN001 --> |子ノード| DTRC001
        DTR001 --> DTRC001
    end

    subgraph 施策設定
        DTP001[DTP-001: 施策作成]
        DTP005[DTP-005: 施策値変更]

        DTN001 --> DTP001
        DTP001 --> DTP005
    end
:::

### 4.3 ツリー構築の詳細シーケンス

::: mermaid
sequenceDiagram
    participant User
    participant System
    participant DB

    User->>System: ツリー作成開始
    System->>DB: DriverTree INSERT (root_node_id=NULL, formula_id=NULL)

    User->>System: 数式マスタ選択
    System->>DB: DriverTree UPDATE (formula_id)

    User->>System: ルートノード作成
    System->>DB: DriverTreeNode INSERT
    System->>DB: DriverTree UPDATE (root_node_id)

    User->>System: 子ノード作成
    System->>DB: DriverTreeNode INSERT (×N)

    User->>System: リレーション定義
    System->>DB: DriverTreeRelationship INSERT
    System->>DB: DriverTreeRelationshipChild INSERT (×N)

    User->>System: ファイルからデータ取込
    System->>DB: DriverTreeFile INSERT
    System->>DB: DriverTreeDataFrame INSERT (×N)

    User->>System: ノードにデータ紐付け
    System->>DB: DriverTreeNode UPDATE (data_frame_id)

    User->>System: 施策追加
    System->>DB: DriverTreePolicy INSERT
:::

### 4.4 前提条件分析

| ユースケース | 前提条件（先行UC） | 後続可能UC | 必須/任意 |
|-------------|-------------------|-----------|----------|
| DT-001: ツリー作成 | P-001, PM-001 | DTN-001, DT-006, DT-007 | 必須 |
| DTN-001: ノード作成 | DT-001 | DTN-002〜008, DTR-001, DTP-001, DT-006 | 必須 |
| DT-006: ルートノード設定 | DTN-001 | - | 必須 |
| DT-007: 数式マスタ紐付け | DT-001, DTF-001 | - | 任意 |
| DTR-001: リレーション作成 | DTN-001（親） | DTRC-001 | 必須（ノード2つ以上時） |
| DTRC-001: 子ノード追加 | DTR-001, DTN-001（子） | DTRC-002, DTRC-003 | 必須（リレーション時） |
| DTFL-001: ファイル作成 | PF-001 | DTDF-001 | 任意 |
| DTDF-001: データフレーム作成 | DTFL-001 | DTN-007 | 任意 |
| DTN-007: データフレーム紐付け | DTN-001, DTDF-001 | - | 任意 |
| DTP-001: 施策作成 | DTN-001 | DTP-002〜006 | 任意 |

### 4.5 DB設計への示唆

```
【現状の問題点】
1. DriverTreeCategoryとDriverTreeFormulaの関係が不明確
   - ER図ではDriverTreeCategory ||--o{ DriverTreeFormula
   - しかしDriverTreeFormulaにcategory_id FKがない
   - driver_type_idで紐付いているが、これはFKではない

2. ノードがどのツリーに属するか不明
   - DriverTreeNodeにdriver_tree_id FKがない
   - リレーションシップ経由でしかツリーとの関連が分からない
   - 孤立ノードの検出が困難

3. ルートノード設定の整合性
   - root_node_idがNULL許容だが、ツリーとして成立するには必須
   - root_nodeが削除された時の動作が不明確

4. リレーションシップの循環検出ができない
   - 親→子→孫→親 のような循環が発生する可能性
   - DBレベルでの制約がない

5. order_indexの一意性制約がない
   - DriverTreeRelationshipChildのorder_indexが重複する可能性

【改善案】
Option A: カテゴリと数式の関係明確化
  - DriverTreeFormulaにcategory_id FK追加
  - または、driver_type_idをDriverTreeCategoryのPKとして整理

Option B: ノードにツリー参照追加
  - DriverTreeNode.driver_tree_id FK（NOT NULL）
  - これによりノードの所属が明確になり、カスケード削除も容易

Option C: ツリー状態の明示化
  - DriverTree.status ENUM('draft', 'building', 'complete', 'archived')
  - status='complete'時はroot_node_id NOT NULL制約

Option D: 順序の一意性保証
  - (relationship_id, order_index) に UNIQUE制約
  - アプリケーション層でのギャップ管理

Option E: ノードの階層情報追加（非正規化）
  - DriverTreeNode.path TEXT (例: '/root/child1/grandchild')
  - 循環検出と階層クエリの高速化
```

---

## 5. 全体フロー（ユーザージャーニー）

### 5.1 新規プロジェクト〜分析完了までのフロー

::: mermaid
graph TD
    subgraph 1_初期設定
        U001[ログイン] --> P001[プロジェクト作成]
        P001 --> PM001[メンバー追加]
    end

    subgraph 2_データ準備
        PM001 --> PF001[ファイルアップロード]
    end

    subgraph 3_個別施策分析
        PF001 --> AS001[分析セッション作成]
        AS001 --> AF001[分析ファイル作成]
        AF001 --> ASN001[スナップショット作成]
        ASN001 --> AC001[チャット分析]
        AC001 --> AST001[ステップ実行]
    end

    subgraph 4_ドライバーツリー分析
        PF001 --> DT001[ツリー作成]
        DT001 --> DTN001[ノード構築]
        DTN001 --> DTR001[リレーション定義]
        PF001 --> DTFL001[ファイル取込]
        DTFL001 --> DTDF001[データフレーム作成]
        DTDF001 --> DTN007[ノードにデータ紐付け]
        DTN001 --> DTP001[施策設定]
    end
:::

### 5.2 共有リソースの依存関係

::: mermaid
graph LR
    subgraph 共有リソース
        PF[ProjectFile]
    end

    subgraph 個別施策分析
        AF[AnalysisFile]
    end

    subgraph ドライバーツリー
        DTF[DriverTreeFile]
    end

    PF --> |project_file_id| AF
    PF --> |project_file_id| DTF
:::

### 5.3 DB設計への示唆（全体）

```
【現状の問題点】
1. ProjectFileの削除時の影響が広範囲
   - AnalysisFileとDriverTreeFileの両方に影響
   - カスケード削除で予期せぬデータ損失の可能性

2. プロジェクト横断の参照がない
   - 例：別プロジェクトのドライバーツリーテンプレートを参照したい場合
   - 現状は不可能

3. バージョニングの概念がない
   - ファイル更新時、過去の分析結果との整合性が崩れる

【改善案】
Option A: ファイル削除の保護
  - ProjectFile.is_deletable フラグ
  - 参照がある場合は論理削除のみ

Option B: テンプレート機能
  - DriverTreeTemplate テーブル追加
  - プロジェクト横断で再利用可能

Option C: ファイルバージョニング
  - ProjectFile.version INT
  - 同じoriginal_filenameで複数バージョン保持
```

---

## 6. 状態遷移図

### 6.1 プロジェクトの状態

::: mermaid
stateDiagram-v2
    [*] --> Active: P-001 作成
    Active --> Inactive: P-003 無効化
    Inactive --> Active: P-004 有効化
    Active --> Active: P-002 更新

    note right of Active
        メンバー追加可能
        ファイルアップロード可能
        分析セッション作成可能
        ドライバーツリー作成可能
    end note

    note right of Inactive
        参照のみ可能
        新規作成・変更不可
    end note
:::

### 6.2 分析セッションの状態（提案）

::: mermaid
stateDiagram-v2
    [*] --> Created: AS-001 作成
    Created --> FileSelected: AS-006 入力ファイル設定
    FileSelected --> Analyzing: AC-001 チャット開始
    Analyzing --> Analyzing: AC-001 チャット継続
    Analyzing --> Branched: ASN-005 過去に戻る
    Branched --> Analyzing: ASN-001 新スナップショット
    Analyzing --> Completed: 分析完了

    note right of Created
        input_file_id = NULL
    end note

    note right of FileSelected
        input_file_id ≠ NULL
        スナップショット = 1
    end note
:::

### 6.3 ドライバーツリーの状態（提案）

::: mermaid
stateDiagram-v2
    [*] --> Draft: DT-001 作成
    Draft --> Building: DT-006 ルートノード設定
    Building --> Building: DTN-001 ノード追加
    Building --> Building: DTR-001 リレーション定義
    Building --> Complete: 構造完成
    Complete --> Complete: DTP-001 施策追加/変更
    Complete --> Archived: アーカイブ

    note right of Draft
        root_node_id = NULL
    end note

    note right of Building
        root_node_id ≠ NULL
        ノード追加中
    end note

    note right of Complete
        計算可能な状態
    end note
:::

---

## 7. DB設計改善提案まとめ

### 7.1 高優先度（データ整合性に直結）

| # | 問題 | 改善案 | 影響範囲 |
|---|------|-------|---------|
| 1 | スナップショットの分岐履歴が追跡できない | AnalysisSnapshot.parent_snapshot_id FK追加 | AnalysisSnapshot |
| 2 | DriverTreeNodeがどのツリーに属するか不明 | DriverTreeNode.driver_tree_id FK追加 | DriverTreeNode |
| 3 | current_snapshotの整合性保証がない | current_snapshot_id UUID FK化 | AnalysisSession |
| 4 | DriverTreeCategoryとFormulaの関係不明確 | DriverTreeFormula.category_id FK追加、またはスキーマ整理 | DriverTreeCategory, DriverTreeFormula |

### 7.2 中優先度（業務ルールの明示化）

| # | 問題 | 改善案 | 影響範囲 |
|---|------|-------|---------|
| 5 | セッション/ツリーの状態が不明確 | statusカラム追加 | AnalysisSession, DriverTree |
| 6 | チャットとステップの関連が不明確 | AnalysisStep.triggered_by_chat_id FK追加 | AnalysisStep |
| 7 | order_indexの一意性制約がない | (relationship_id, order_index) UNIQUE制約 | DriverTreeRelationshipChild |
| 8 | プロジェクト作成者とPMの整合性 | トリガーまたはアプリ層での保証 | Project, ProjectMember |

### 7.3 低優先度（将来の拡張性）

| # | 問題 | 改善案 | 影響範囲 |
|---|------|-------|---------|
| 9 | ロール変更履歴がない | user_role_history テーブル追加 | 新規テーブル |
| 10 | ファイルバージョニングがない | version カラム追加 | ProjectFile |
| 11 | テンプレート機能がない | DriverTreeTemplate テーブル追加 | 新規テーブル |
| 12 | 循環参照の検出 | path カラム追加またはアプリ層チェック | DriverTreeNode |

---

## 8. 改善後ER図（提案）

### 8.1 AnalysisSnapshot（改善案）

::: mermaid
erDiagram
    AnalysisSnapshot {
        uuid id PK
        uuid session_id FK
        uuid parent_snapshot_id FK "NEW: 親スナップショット（分岐元）"
        integer snapshot_order
        timestamp created_at
        timestamp updated_at
    }
:::

### 8.2 DriverTreeNode（改善案）

::: mermaid
erDiagram
    DriverTreeNode {
        uuid id PK
        uuid driver_tree_id FK "NEW: 所属ツリー"
        string label
        integer position_x
        integer position_y
        string node_type
        uuid data_frame_id FK
        timestamp created_at
        timestamp updated_at
    }
:::

### 8.3 AnalysisSession（改善案）

::: mermaid
erDiagram
    AnalysisSession {
        uuid id PK
        uuid issue_id FK
        uuid creator_id FK
        uuid project_id FK
        uuid input_file_id FK
        uuid current_snapshot_id FK "CHANGED: UUIDに変更"
        string status "NEW: draft/file_selected/analyzing/completed"
        timestamp created_at
        timestamp updated_at
    }
:::

### 8.4 DriverTreeFormula（改善案）

::: mermaid
erDiagram
    DriverTreeFormula {
        uuid id PK
        integer category_id FK "NEW: カテゴリへのFK"
        integer driver_type_id
        string driver_type
        string kpi
        jsonb formulas
        timestamp created_at
        timestamp updated_at
    }
:::

---

## 9. 次のステップ

1. **レビュー**: 本分析結果をチームでレビュー
2. **優先度決定**: 高優先度の改善から着手
3. **マイグレーション計画**: 既存データの移行計画策定
4. **実装**: スキーマ変更とアプリケーション層の対応
5. **テスト**: 回帰テストの実施

---

##### ドキュメント管理情報

- **作成日**: 2025年12月24日
- **分析元**: 01-usecases.md, ../03-database/02-er-diagram.md
- **目的**: ユースケースフロー分析によるDB設計検証
