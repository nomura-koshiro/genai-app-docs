# CAMPシステム ユースケース シーケンス図

本文書は、主要なユースケースフローをUMLシーケンス図で可視化したものです。

---

## 1. ユーザー管理

### 1.1 初回ログイン〜アカウント作成

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant Azure as Azure AD
    participant API as CAMPシステム
    participant DB as Database

    User->>Azure: ログイン要求
    Azure-->>User: 認証画面表示
    User->>Azure: 資格情報入力
    Azure->>Azure: 認証処理
    Azure-->>API: IDトークン（azure_oid, email）

    API->>DB: SELECT * FROM user_account WHERE azure_oid = ?
    DB-->>API: 結果なし（初回）

    rect rgb(200, 230, 200)
        Note over API,DB: U-002: ユーザーアカウント作成
        API->>DB: INSERT INTO user_account (azure_oid, email, display_name, roles, is_active)
        DB-->>API: 作成完了
    end

    rect rgb(200, 220, 240)
        Note over API,DB: U-006: 最終ログイン日時記録
        API->>DB: UPDATE user_account SET last_login = NOW() WHERE id = ?
        DB-->>API: 更新完了
    end

    API-->>User: ログイン成功・ダッシュボード表示
:::

### 1.2 既存ユーザーログイン

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant Azure as Azure AD
    participant API as CAMPシステム
    participant DB as Database

    User->>Azure: ログイン要求
    Azure-->>User: 認証画面表示
    User->>Azure: 資格情報入力
    Azure->>Azure: 認証処理
    Azure-->>API: IDトークン（azure_oid, email）

    rect rgb(200, 220, 240)
        Note over API,DB: U-001: Azure ADでログイン
        API->>DB: SELECT * FROM user_account WHERE azure_oid = ?
        DB-->>API: ユーザー情報
    end

    alt is_active = false
        API-->>User: エラー: アカウント無効
    else is_active = true
        rect rgb(200, 220, 240)
            Note over API,DB: U-006: 最終ログイン日時記録
            API->>DB: UPDATE user_account SET last_login = NOW()
            DB-->>API: 更新完了
        end
        API-->>User: ログイン成功
    end
:::

### 1.3 システムロール管理

::: mermaid
sequenceDiagram
    autonumber
    actor Admin as システム管理者
    participant API as CAMPシステム
    participant DB as Database

    Admin->>API: ロール付与要求（user_id, role）

    rect rgb(255, 230, 200)
        Note over API,DB: 権限チェック
        API->>DB: SELECT roles FROM user_account WHERE id = {admin_id}
        DB-->>API: ["SystemAdmin"]
        API->>API: SystemAdmin権限確認
    end

    rect rgb(200, 220, 240)
        Note over API,DB: U-011: 対象ユーザーのロール確認
        API->>DB: SELECT roles FROM user_account WHERE id = {target_user_id}
        DB-->>API: ["User"]
    end

    rect rgb(200, 230, 200)
        Note over API,DB: U-009: システムロール付与
        API->>DB: UPDATE user_account SET roles = roles || '["ProjectAdmin"]'
        DB-->>API: 更新完了
    end

    API-->>Admin: ロール付与完了

    Note over Admin,DB: 【DB設計課題】ロール変更履歴が残らない
:::

---

## 2. プロジェクト管理

### 2.1 プロジェクト作成〜メンバー追加

::: mermaid
sequenceDiagram
    autonumber
    actor PM as プロジェクト作成者
    participant API as CAMPシステム
    participant DB as Database

    PM->>API: プロジェクト作成要求（name, code, description）

    rect rgb(200, 230, 200)
        Note over API,DB: P-001: プロジェクト作成
        API->>DB: INSERT INTO project (name, code, description, created_by, is_active)
        DB-->>API: project_id
    end

    rect rgb(200, 230, 200)
        Note over API,DB: PM-001: 作成者をPMとして自動追加
        API->>DB: INSERT INTO project_member (project_id, user_id, role='PROJECT_MANAGER', added_by)
        DB-->>API: 作成完了
    end

    API-->>PM: プロジェクト作成完了

    Note over PM,DB: 【DB設計課題】作成者のPM登録がアプリ層依存

    loop メンバー追加
        PM->>API: メンバー追加要求（project_id, user_id, role）

        rect rgb(255, 230, 200)
            Note over API,DB: PM-006: 権限確認
            API->>DB: SELECT role FROM project_member WHERE project_id = ? AND user_id = {pm_id}
            DB-->>API: PROJECT_MANAGER
        end

        rect rgb(200, 230, 200)
            Note over API,DB: PM-001: メンバー追加
            API->>DB: INSERT INTO project_member (project_id, user_id, role, added_by)
            DB-->>API: 作成完了
        end

        API-->>PM: メンバー追加完了
    end
:::

### 2.2 ファイルアップロード〜利用

::: mermaid
sequenceDiagram
    autonumber
    actor Member as プロジェクトメンバー
    participant API as CAMPシステム
    participant Storage as ファイルストレージ
    participant DB as Database

    Member->>API: ファイルアップロード要求（project_id, file）

    rect rgb(255, 230, 200)
        Note over API,DB: PM-006: 権限確認
        API->>DB: SELECT role FROM project_member WHERE project_id = ? AND user_id = ?
        DB-->>API: MEMBER
        API->>API: MEMBER以上の権限確認OK
    end

    API->>Storage: ファイル保存
    Storage-->>API: file_path

    rect rgb(200, 230, 200)
        Note over API,DB: PF-001: ファイル登録
        API->>DB: INSERT INTO project_file (project_id, filename, original_filename, file_path, file_size, mime_type, uploaded_by)
        DB-->>API: file_id
    end

    API-->>Member: アップロード完了（file_id）

    Note over Member,DB: このファイルは後続で以下に利用可能:
    Note over Member,DB: - AnalysisFile（個別施策分析）
    Note over Member,DB: - DriverTreeFile（ドライバーツリー）
:::

### 2.3 プロジェクト無効化とその影響

::: mermaid
sequenceDiagram
    autonumber
    actor PM as プロジェクトマネージャー
    participant API as CAMPシステム
    participant DB as Database

    PM->>API: プロジェクト無効化要求（project_id）

    rect rgb(255, 230, 200)
        Note over API,DB: 権限確認
        API->>DB: SELECT role FROM project_member WHERE project_id = ? AND user_id = ?
        DB-->>API: PROJECT_MANAGER
    end

    rect rgb(255, 200, 200)
        Note over API,DB: 影響範囲確認
        API->>DB: SELECT COUNT(*) FROM analysis_session WHERE project_id = ?
        DB-->>API: セッション数
        API->>DB: SELECT COUNT(*) FROM driver_tree WHERE project_id = ?
        DB-->>API: ツリー数
    end

    rect rgb(200, 230, 200)
        Note over API,DB: P-003: プロジェクト無効化
        API->>DB: UPDATE project SET is_active = false WHERE id = ?
        DB-->>API: 更新完了
    end

    API-->>PM: 無効化完了

    Note over PM,DB: 無効化後:
    Note over PM,DB: - 新規セッション/ツリー作成不可
    Note over PM,DB: - 既存データは参照可能
    Note over PM,DB: - P-004で再有効化可能
:::

---

## 3. 個別施策分析

### 3.1 マスタ設定フロー（管理者）

::: mermaid
sequenceDiagram
    autonumber
    actor Admin as システム管理者
    participant API as CAMPシステム
    participant DB as Database

    rect rgb(200, 230, 200)
        Note over API,DB: AVM-001: 検証マスタ作成
        Admin->>API: 検証マスタ作成（name, order）
        API->>DB: INSERT INTO analysis_validation_master (name, validation_order)
        DB-->>API: validation_id
        API-->>Admin: 作成完了
    end

    rect rgb(200, 230, 200)
        Note over API,DB: AIM-001: 課題マスタ作成
        Admin->>API: 課題マスタ作成（validation_id, name, description）
        API->>DB: INSERT INTO analysis_issue_master (validation_id, name, description, issue_order)
        DB-->>API: issue_id
        API-->>Admin: 作成完了
    end

    par 並行して設定可能
        rect rgb(200, 220, 240)
            Note over API,DB: AIM-006: プロンプト設定
            Admin->>API: プロンプト設定（issue_id, agent_prompt）
            API->>DB: UPDATE analysis_issue_master SET agent_prompt = ?
            DB-->>API: 更新完了
        end
    and
        rect rgb(200, 220, 240)
            Note over API,DB: AIM-007: 初期メッセージ設定
            Admin->>API: 初期メッセージ設定（issue_id, initial_msg）
            API->>DB: UPDATE analysis_issue_master SET initial_msg = ?
            DB-->>API: 更新完了
        end
    and
        rect rgb(200, 220, 240)
            Note over API,DB: AGM-001: グラフ軸作成
            Admin->>API: グラフ軸作成（issue_id, name, option, multiple）
            API->>DB: INSERT INTO analysis_graph_axis_master
            DB-->>API: 作成完了
        end
    end
:::

### 3.2 分析セッション開始

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: 分析セッション作成要求（project_id, issue_id）

    rect rgb(255, 230, 200)
        Note over API,DB: 前提条件確認
        API->>DB: SELECT * FROM project WHERE id = ? AND is_active = true
        DB-->>API: プロジェクト情報
        API->>DB: SELECT role FROM project_member WHERE project_id = ? AND user_id = ?
        DB-->>API: MEMBER
        API->>DB: SELECT * FROM analysis_issue_master WHERE id = ?
        DB-->>API: 課題マスタ情報
    end

    rect rgb(200, 230, 200)
        Note over API,DB: AS-001: セッション作成
        API->>DB: INSERT INTO analysis_session (project_id, issue_id, creator_id, current_snapshot=0)
        DB-->>API: session_id
    end

    rect rgb(200, 230, 200)
        Note over API,DB: ASN-001: 初期スナップショット作成
        API->>DB: INSERT INTO analysis_snapshot (session_id, snapshot_order=1)
        DB-->>API: snapshot_id
    end

    rect rgb(200, 220, 240)
        Note over API,DB: AS-007: 現在スナップショット更新
        API->>DB: UPDATE analysis_session SET current_snapshot = 1 WHERE id = ?
        DB-->>API: 更新完了
    end

    API-->>User: セッション作成完了（session_id, snapshot_id）

    Note over User,DB: 【DB設計課題】current_snapshotはINTEGER
    Note over User,DB: → snapshot_idへのFK参照がない
:::

### 3.3 ファイル選択〜分析開始

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: プロジェクトファイル一覧取得（project_id）

    rect rgb(200, 220, 240)
        Note over API,DB: PF-004: ファイル一覧取得
        API->>DB: SELECT * FROM project_file WHERE project_id = ?
        DB-->>API: ファイル一覧
    end

    API-->>User: ファイル一覧

    User->>API: 分析ファイル作成（session_id, project_file_id, sheet_name）

    rect rgb(200, 230, 200)
        Note over API,DB: AF-001: 分析ファイル作成
        API->>DB: INSERT INTO analysis_file (session_id, project_file_id, sheet_name, axis_config, data)
        DB-->>API: analysis_file_id
    end

    rect rgb(200, 220, 240)
        Note over API,DB: AS-006: 入力ファイル設定
        API->>DB: UPDATE analysis_session SET input_file_id = ? WHERE id = ?
        DB-->>API: 更新完了
    end

    API-->>User: ファイル設定完了

    Note over User,DB: この時点でセッション状態:
    Note over User,DB: - input_file_id: 設定済み
    Note over User,DB: - current_snapshot: 1
    Note over User,DB: → 分析開始可能
:::

### 3.4 チャット分析〜ステップ生成

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant AI as AIエージェント
    participant DB as Database

    User->>API: チャットメッセージ送信（snapshot_id, message）

    rect rgb(200, 230, 200)
        Note over API,DB: AC-001: ユーザーメッセージ保存
        API->>DB: INSERT INTO analysis_chat (snapshot_id, chat_order, role='user', message)
        DB-->>API: chat_id
    end

    API->>AI: メッセージ + コンテキスト送信
    AI->>AI: 分析処理

    alt 分析ステップが必要な場合
        AI-->>API: 分析結果 + ステップ情報

        rect rgb(200, 230, 200)
            Note over API,DB: AST-001: ステップ作成
            API->>DB: INSERT INTO analysis_step (snapshot_id, name, type, config, step_order)
            DB-->>API: step_id
        end

        Note over API,DB: 【DB設計課題】チャットとステップの関連がない
        Note over API,DB: → triggered_by_chat_id があれば因果関係が明確
    end

    rect rgb(200, 230, 200)
        Note over API,DB: AC-001: AI応答保存
        API->>DB: INSERT INTO analysis_chat (snapshot_id, chat_order, role='assistant', message)
        DB-->>API: chat_id
    end

    API-->>User: 分析結果表示
:::

### 3.5 スナップショット分岐（過去に戻る）

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: スナップショット一覧取得（session_id）

    rect rgb(200, 220, 240)
        Note over API,DB: ASN-003: スナップショット一覧
        API->>DB: SELECT * FROM analysis_snapshot WHERE session_id = ? ORDER BY snapshot_order
        DB-->>API: スナップショット一覧
    end

    API-->>User: スナップショット一覧（1, 2, 3, 4, 5）

    User->>API: スナップショット3に戻る（session_id, snapshot_order=3）

    rect rgb(255, 200, 200)
        Note over API,DB: 【現状】単純に現在位置を変更
        API->>DB: UPDATE analysis_session SET current_snapshot = 3
        DB-->>API: 更新完了
    end

    API-->>User: スナップショット3の状態を表示

    User->>API: 新しい分析を開始（チャット送信）

    rect rgb(200, 230, 200)
        Note over API,DB: ASN-001: 新スナップショット作成（分岐）
        API->>DB: INSERT INTO analysis_snapshot (session_id, snapshot_order=6)
        DB-->>API: snapshot_id
    end

    Note over User,DB: 【DB設計課題】
    Note over User,DB: snapshot_order=6 は snapshot_order=3 から分岐
    Note over User,DB: しかし parent_snapshot_id がないため分岐元が不明
    Note over User,DB:
    Note over User,DB: 【理想的な構造】
    Note over User,DB: snapshot_order=6, parent_snapshot_id = {snapshot_3_id}
:::

### 3.6 スナップショット分岐の可視化（問題点）

::: mermaid
sequenceDiagram
    autonumber
    participant S1 as Snapshot 1
    participant S2 as Snapshot 2
    participant S3 as Snapshot 3
    participant S4 as Snapshot 4
    participant S5 as Snapshot 5
    participant S6 as Snapshot 6 (分岐)
    participant S7 as Snapshot 7

    Note over S1,S5: 【現状のDB構造】順序のみ保持
    S1->>S2: snapshot_order: 1→2
    S2->>S3: snapshot_order: 2→3
    S3->>S4: snapshot_order: 3→4
    S4->>S5: snapshot_order: 4→5

    Note over S3,S6: ユーザーがS3に戻って分岐
    S3-->>S6: snapshot_order: 6（分岐元不明）
    S6->>S7: snapshot_order: 6→7

    Note over S1,S7: 【問題】S6がS3から分岐したことがDBから読み取れない
:::

### 3.7 スナップショット分岐の可視化（改善案）

::: mermaid
sequenceDiagram
    autonumber
    participant S1 as Snapshot 1<br/>parent: NULL
    participant S2 as Snapshot 2<br/>parent: S1
    participant S3 as Snapshot 3<br/>parent: S2
    participant S4 as Snapshot 4<br/>parent: S3
    participant S5 as Snapshot 5<br/>parent: S4
    participant S6 as Snapshot 6<br/>parent: S3
    participant S7 as Snapshot 7<br/>parent: S6

    Note over S1,S5: 【改善後】parent_snapshot_id で履歴追跡
    S1->>S2: 線形進行
    S2->>S3: 線形進行
    S3->>S4: 線形進行
    S4->>S5: 線形進行

    Note over S3,S6: S3から分岐（parent_snapshot_id = S3.id）
    S3-->>S6: 分岐
    S6->>S7: 線形進行

    Note over S1,S7: 【効果】ツリー構造として履歴を完全に再現可能
:::

---

## 4. ドライバーツリー

### 4.1 カテゴリ・数式マスタ設定

::: mermaid
sequenceDiagram
    autonumber
    actor Admin as システム管理者
    participant API as CAMPシステム
    participant DB as Database

    rect rgb(200, 230, 200)
        Note over API,DB: DTC-001: カテゴリマスタ作成
        Admin->>API: カテゴリ作成（category_id, category_name, industry_id, industry_name, driver_type_id, driver_type_name）
        API->>DB: INSERT INTO driver_tree_category
        DB-->>API: id
        API-->>Admin: 作成完了
    end

    rect rgb(200, 230, 200)
        Note over API,DB: DTF-001: 数式マスタ作成
        Admin->>API: 数式作成（driver_type_id, driver_type, kpi, formulas）
        API->>DB: INSERT INTO driver_tree_formula (driver_type_id, driver_type, kpi, formulas)
        DB-->>API: formula_id
        API-->>Admin: 作成完了
    end

    Note over Admin,DB: 【DB設計課題】
    Note over Admin,DB: CategoryとFormulaの関係が driver_type_id で暗黙的に紐付き
    Note over Admin,DB: → FKではないため参照整合性なし
    Note over Admin,DB: → Categoryのdriver_type_idを変更してもFormulaは追従しない
:::

### 4.2 ドライバーツリー作成〜ノード構築

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: ツリー作成要求（project_id, name, description）

    rect rgb(255, 230, 200)
        Note over API,DB: 前提条件確認
        API->>DB: SELECT role FROM project_member WHERE project_id = ? AND user_id = ?
        DB-->>API: MEMBER
    end

    rect rgb(200, 230, 200)
        Note over API,DB: DT-001: ツリー作成
        API->>DB: INSERT INTO driver_tree (project_id, name, description, root_node_id=NULL, formula_id=NULL)
        DB-->>API: tree_id
    end

    API-->>User: ツリー作成完了（tree_id）

    Note over User,DB: この時点: root_node_id = NULL（ドラフト状態）

    User->>API: ルートノード作成（label, position_x, position_y, node_type）

    rect rgb(200, 230, 200)
        Note over API,DB: DTN-001: ノード作成
        API->>DB: INSERT INTO driver_tree_node (label, position_x, position_y, node_type)
        DB-->>API: node_id
    end

    Note over User,DB: 【DB設計課題】ノードがどのツリーに属するか不明
    Note over User,DB: → driver_tree_id FK がない

    rect rgb(200, 220, 240)
        Note over API,DB: DT-006: ルートノード設定
        API->>DB: UPDATE driver_tree SET root_node_id = ? WHERE id = ?
        DB-->>API: 更新完了
    end

    API-->>User: ルートノード設定完了
:::

### 4.3 ノード階層構築（リレーションシップ）

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    Note over User,DB: 前提: ルートノード（売上）が作成済み

    loop 子ノード作成
        User->>API: 子ノード作成（label, position）

        rect rgb(200, 230, 200)
            Note over API,DB: DTN-001: ノード作成
            API->>DB: INSERT INTO driver_tree_node (label, position_x, position_y, node_type)
            DB-->>API: child_node_id
        end

        API-->>User: ノード作成完了
    end

    Note over User,DB: 作成されたノード: 単価, 数量

    User->>API: リレーションシップ作成（tree_id, parent_node_id=売上, operator='*'）

    rect rgb(200, 230, 200)
        Note over API,DB: DTR-001: リレーションシップ作成
        API->>DB: INSERT INTO driver_tree_relationship (driver_tree_id, parent_node_id, operator)
        DB-->>API: relationship_id
    end

    API-->>User: リレーションシップ作成完了

    User->>API: 子ノード追加（relationship_id, child_node_id=単価, order_index=1）

    rect rgb(200, 230, 200)
        Note over API,DB: DTRC-001: 子ノード追加
        API->>DB: INSERT INTO driver_tree_relationship_child (relationship_id, child_node_id, order_index=1)
        DB-->>API: 作成完了
    end

    User->>API: 子ノード追加（relationship_id, child_node_id=数量, order_index=2）

    rect rgb(200, 230, 200)
        Note over API,DB: DTRC-001: 子ノード追加
        API->>DB: INSERT INTO driver_tree_relationship_child (relationship_id, child_node_id, order_index=2)
        DB-->>API: 作成完了
    end

    API-->>User: 子ノード追加完了

    Note over User,DB: 結果: 売上 = 単価 * 数量
:::

### 4.4 ノード階層の可視化

::: mermaid
sequenceDiagram
    autonumber
    participant Root as 売上<br/>(root_node)
    participant R1 as Relationship<br/>operator: *
    participant C1 as 単価<br/>order: 1
    participant C2 as 数量<br/>order: 2
    participant R2 as Relationship<br/>operator: +
    participant C3 as 新規顧客<br/>order: 1
    participant C4 as 既存顧客<br/>order: 2

    Note over Root,C4: ツリー構造: 売上 = 単価 * 数量, 数量 = 新規 + 既存

    Root->>R1: parent_node_id
    R1->>C1: child (order=1)
    R1->>C2: child (order=2)

    C2->>R2: parent_node_id
    R2->>C3: child (order=1)
    R2->>C4: child (order=2)

    Note over Root,C4: 【DB設計課題】
    Note over Root,C4: 1. ノードにdriver_tree_idがないため孤立ノード検出困難
    Note over Root,C4: 2. order_indexにUNIQUE制約がなく重複可能
    Note over Root,C4: 3. 循環参照（売上→単価→売上）を防ぐ制約がない
:::

### 4.5 データ紐付けフロー

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    Note over User,DB: 前提: ProjectFileにExcelファイルがアップロード済み

    User->>API: ドライバーツリーファイル作成（project_file_id, sheet_name, axis_config）

    rect rgb(200, 230, 200)
        Note over API,DB: DTFL-001: ファイル作成
        API->>DB: INSERT INTO driver_tree_file (project_file_id, sheet_name, axis_config)
        DB-->>API: file_id
    end

    API-->>User: ファイル作成完了

    loop 各列のデータフレーム作成
        User->>API: データフレーム作成（file_id, column_name, data）

        rect rgb(200, 230, 200)
            Note over API,DB: DTDF-001: データフレーム作成
            API->>DB: INSERT INTO driver_tree_data_frame (driver_tree_file_id, column_name, data)
            DB-->>API: data_frame_id
        end

        API-->>User: データフレーム作成完了
    end

    User->>API: ノードにデータ紐付け（node_id, data_frame_id）

    rect rgb(200, 220, 240)
        Note over API,DB: DTN-007: データフレーム紐付け
        API->>DB: UPDATE driver_tree_node SET data_frame_id = ? WHERE id = ?
        DB-->>API: 更新完了
    end

    API-->>User: データ紐付け完了

    Note over User,DB: これによりノードに実データが紐付く
    Note over User,DB: → ツリー計算が可能になる
:::

### 4.6 施策設定フロー

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    Note over User,DB: 前提: ドライバーツリーのノードが構築済み

    User->>API: 施策追加（node_id, label, value）

    rect rgb(200, 230, 200)
        Note over API,DB: DTP-001: 施策作成
        API->>DB: INSERT INTO driver_tree_policy (node_id, label, value)
        DB-->>API: policy_id
    end

    API-->>User: 施策追加完了

    User->>API: 施策値変更（policy_id, new_value）

    rect rgb(200, 220, 240)
        Note over API,DB: DTP-005: 施策値変更
        API->>DB: UPDATE driver_tree_policy SET value = ? WHERE id = ?
        DB-->>API: 更新完了
    end

    API-->>User: 施策値変更完了

    Note over User,DB: 施策適用後、ツリー全体の再計算が必要
    Note over User,DB: → アプリケーション層で計算処理
:::

---

## 5. クロスモジュールフロー

### 5.1 プロジェクトファイルの共有利用

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    Note over User,DB: 1つのProjectFileが複数機能で利用されるケース

    User->>API: ファイルアップロード
    rect rgb(200, 230, 200)
        API->>DB: INSERT INTO project_file
        DB-->>API: file_id = "FILE-001"
    end

    par 個別施策分析で利用
        User->>API: 分析セッション作成
        rect rgb(200, 230, 200)
            API->>DB: INSERT INTO analysis_file (project_file_id = "FILE-001")
            DB-->>API: analysis_file_id
        end
    and ドライバーツリーで利用
        User->>API: ドライバーツリーファイル作成
        rect rgb(200, 230, 200)
            API->>DB: INSERT INTO driver_tree_file (project_file_id = "FILE-001")
            DB-->>API: driver_tree_file_id
        end
    end

    Note over User,DB: 【DB設計課題】
    Note over User,DB: FILE-001を削除すると両方に影響
    Note over User,DB: → CASCADE削除で予期せぬデータ損失の可能性
    Note over User,DB:
    Note over User,DB: 【改善案】
    Note over User,DB: - 参照がある間は削除不可（RESTRICT）
    Note over User,DB: - または論理削除のみ許可
:::

### 5.2 ファイル削除時の影響確認

::: mermaid
sequenceDiagram
    autonumber
    actor PM as プロジェクトマネージャー
    participant API as CAMPシステム
    participant DB as Database

    PM->>API: ファイル削除要求（file_id）

    rect rgb(255, 230, 200)
        Note over API,DB: 権限確認
        API->>DB: SELECT uploaded_by FROM project_file WHERE id = ?
        DB-->>API: uploaded_by
        API->>DB: SELECT role FROM project_member WHERE project_id = ? AND user_id = ?
        DB-->>API: PROJECT_MANAGER
        API->>API: PM権限またはアップロード者 → OK
    end

    rect rgb(255, 200, 200)
        Note over API,DB: 影響範囲確認（改善案）
        API->>DB: SELECT COUNT(*) FROM analysis_file WHERE project_file_id = ?
        DB-->>API: 3件
        API->>DB: SELECT COUNT(*) FROM driver_tree_file WHERE project_file_id = ?
        DB-->>API: 2件
    end

    alt 参照あり
        API-->>PM: 警告: このファイルは5つの分析で使用中です。削除しますか？
        PM->>API: 削除確認

        rect rgb(255, 200, 200)
            Note over API,DB: カスケード削除
            API->>DB: DELETE FROM project_file WHERE id = ?
            Note over DB: CASCADE: analysis_file 3件削除
            Note over DB: CASCADE: driver_tree_file 2件削除
            Note over DB: CASCADE: driver_tree_data_frame N件削除
            DB-->>API: 削除完了
        end
    else 参照なし
        rect rgb(200, 230, 200)
            API->>DB: DELETE FROM project_file WHERE id = ?
            DB-->>API: 削除完了
        end
    end

    API-->>PM: ファイル削除完了
:::

---

## 6. ダッシュボード・統計

### 6.1 ダッシュボード統計情報取得

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: ダッシュボード表示要求

    rect rgb(200, 220, 240)
        Note over API,DB: D-001: 統計情報取得
        par 並列クエリ
            API->>DB: SELECT COUNT(*) FROM project
            API->>DB: SELECT COUNT(*) FROM analysis_session
            API->>DB: SELECT COUNT(*) FROM driver_tree
            API->>DB: SELECT COUNT(*) FROM user_account
        end
        DB-->>API: 各種カウント
    end

    rect rgb(200, 220, 240)
        Note over API,DB: D-005: プロジェクト分布
        API->>DB: SELECT is_active, COUNT(*) FROM project GROUP BY is_active
        DB-->>API: アクティブ/アーカイブ分布
    end

    rect rgb(200, 220, 240)
        Note over API,DB: D-006: ユーザーアクティビティ
        API->>DB: SELECT is_active, COUNT(*) FROM user_account GROUP BY is_active
        DB-->>API: アクティブ/非アクティブ分布
    end

    API-->>User: ダッシュボード表示
:::

### 6.2 アクティビティ一覧取得

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: アクティビティ一覧要求（skip, limit）

    rect rgb(200, 220, 240)
        Note over API,DB: D-002: アクティビティ集約
        par 複数ソースから取得
            API->>DB: SELECT 'role' as type, * FROM role_history
            API->>DB: SELECT 'project' as type, * FROM project
            API->>DB: SELECT 'session' as type, * FROM analysis_session
            API->>DB: SELECT 'tree' as type, * FROM driver_tree
            API->>DB: SELECT 'file' as type, * FROM project_file
        end
        DB-->>API: 各種アクティビティデータ
    end

    API->>API: created_at順でソート・統合
    API->>API: ページネーション適用

    API-->>User: アクティビティ一覧（activities, total, skip, limit）

    Note over User,DB: 【実装】RoleHistory, Project, AnalysisSession,
    Note over User,DB: DriverTree, ProjectFileから集約
:::

### 6.3 チャートデータ取得

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: チャートデータ要求（days=30）

    rect rgb(200, 220, 240)
        Note over API,DB: D-003: セッショントレンド
        API->>DB: SELECT DATE(created_at), COUNT(*)<br/>FROM analysis_session<br/>WHERE created_at >= NOW() - INTERVAL '{days} days'<br/>GROUP BY DATE(created_at)
        DB-->>API: 日別セッション数
    end

    rect rgb(200, 220, 240)
        Note over API,DB: D-003: ツリートレンド
        API->>DB: SELECT DATE(created_at), COUNT(*)<br/>FROM driver_tree<br/>WHERE created_at >= NOW() - INTERVAL '{days} days'<br/>GROUP BY DATE(created_at)
        DB-->>API: 日別ツリー数
    end

    API->>API: チャートデータ構築

    API-->>User: チャートデータ（sessionTrend, treeTrend, projectDistribution, userActivity）
:::

---

## 7. 複製・エクスポート機能

### 7.1 セッション複製

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: セッション複製要求（session_id）

    rect rgb(255, 230, 200)
        Note over API,DB: 権限確認
        API->>DB: SELECT role FROM project_member WHERE project_id = ? AND user_id = ?
        DB-->>API: MEMBER
    end

    rect rgb(200, 220, 240)
        Note over API,DB: 元セッション取得
        API->>DB: SELECT * FROM analysis_session WHERE id = ?
        DB-->>API: セッションデータ
        API->>DB: SELECT * FROM analysis_snapshot WHERE session_id = ?
        DB-->>API: スナップショット一覧
        API->>DB: SELECT * FROM analysis_step WHERE snapshot_id IN (...)
        DB-->>API: ステップ一覧
        API->>DB: SELECT * FROM analysis_chat WHERE snapshot_id IN (...)
        DB-->>API: チャット一覧
    end

    rect rgb(200, 230, 200)
        Note over API,DB: CP-001: セッション複製
        API->>DB: INSERT INTO analysis_session (新規ID, 複製データ)
        DB-->>API: new_session_id
        loop 各スナップショット
            API->>DB: INSERT INTO analysis_snapshot (新規ID, session_id=new_session_id)
            DB-->>API: new_snapshot_id
            API->>DB: INSERT INTO analysis_step (新規ID, snapshot_id=new_snapshot_id)
            API->>DB: INSERT INTO analysis_chat (新規ID, snapshot_id=new_snapshot_id)
        end
    end

    API-->>User: 複製完了（new_session_id）
:::

### 7.2 ツリー複製（施策込み）

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: ツリー複製要求（tree_id）

    rect rgb(200, 220, 240)
        Note over API,DB: 元ツリー取得
        API->>DB: SELECT * FROM driver_tree WHERE id = ?
        DB-->>API: ツリーデータ
        API->>DB: SELECT * FROM driver_tree_node WHERE driver_tree_id = ?
        DB-->>API: ノード一覧
        API->>DB: SELECT * FROM driver_tree_relationship WHERE driver_tree_id = ?
        DB-->>API: リレーション一覧
        API->>DB: SELECT * FROM driver_tree_policy WHERE node_id IN (...)
        DB-->>API: 施策一覧
    end

    rect rgb(200, 230, 200)
        Note over API,DB: CP-002: ツリー複製
        API->>DB: INSERT INTO driver_tree (新規ID, 複製データ)
        DB-->>API: new_tree_id
        API->>API: ノードIDマッピング作成

        loop 各ノード
            API->>DB: INSERT INTO driver_tree_node (新規ID, driver_tree_id=new_tree_id)
            DB-->>API: new_node_id
            API->>API: old_node_id → new_node_id マッピング更新
        end

        loop 各リレーション
            API->>DB: INSERT INTO driver_tree_relationship<br/>(新規ID, parent_node_id=mapped_id)
            DB-->>API: new_relationship_id
            API->>DB: INSERT INTO driver_tree_relationship_child<br/>(relationship_id, child_node_id=mapped_id)
        end

        loop 各施策
            API->>DB: INSERT INTO driver_tree_policy<br/>(新規ID, node_id=mapped_id)
        end
    end

    API-->>User: 複製完了（new_tree_id）

    Note over User,DB: 【実装済み】ノードIDマッピングにより
    Note over User,DB: 関係性を維持したまま完全複製
:::

### 7.3 エクスポート機能（将来実装予定）

> **注記**: 以下のシーケンスは将来実装予定のフロントエンド機能です。

```text
EX-001: セッション結果をレポート出力する
  - フロントエンドでPDF/Excel形式のレポートを生成
  - セッション、スナップショット、ステップ情報を含む

EX-002: ツリー計算結果をエクスポートする
  - フロントエンドでExcel/CSV形式でエクスポート
  - ノード値、施策効果、計算結果を含む

EX-003: セッション結果を共有する
  - 共有リンクの生成と管理
  - 閲覧権限の設定
```

---

## 8. テンプレート機能

### 8.1 テンプレート一覧・絞込

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: テンプレート一覧要求（industry?, analysis_type?）

    rect rgb(200, 220, 240)
        Note over API,DB: TM-001〜003: テンプレート取得
        alt フィルタなし
            API->>DB: SELECT * FROM analysis_template WHERE is_active = true
        else 業種フィルタ
            API->>DB: SELECT * FROM analysis_template<br/>WHERE is_active = true AND industry = ?
        else 分析タイプフィルタ
            API->>DB: SELECT * FROM analysis_template<br/>WHERE is_active = true AND analysis_type = ?
        else 複合フィルタ
            API->>DB: SELECT * FROM analysis_template<br/>WHERE is_active = true AND industry = ? AND analysis_type = ?
        end
        DB-->>API: テンプレート一覧
    end

    API-->>User: テンプレート一覧
:::

### 8.2 テンプレートからツリー作成

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: テンプレートからツリー作成（template_id, project_id）

    rect rgb(255, 230, 200)
        Note over API,DB: 権限確認
        API->>DB: SELECT role FROM project_member WHERE project_id = ? AND user_id = ?
        DB-->>API: MEMBER
    end

    rect rgb(200, 220, 240)
        Note over API,DB: TM-004: テンプレート取得
        API->>DB: SELECT * FROM analysis_template WHERE id = ?
        DB-->>API: テンプレートデータ（config含む）
    end

    rect rgb(200, 230, 200)
        Note over API,DB: TM-005: ツリー作成
        API->>DB: INSERT INTO driver_tree (project_id, name, description)
        DB-->>API: tree_id

        Note over API,DB: テンプレートconfigに基づいてノード作成
        loop configのノード定義
            API->>DB: INSERT INTO driver_tree_node<br/>(driver_tree_id, label, node_type, position)
            DB-->>API: node_id
        end

        API->>DB: UPDATE driver_tree SET root_node_id = ?
        DB-->>API: 更新完了
    end

    API-->>User: ツリー作成完了（tree_id）
:::

---

## 9. ファイルバージョン管理

### 9.1 新バージョンアップロード

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant Storage as ファイルストレージ
    participant DB as Database

    User->>API: 新バージョンアップロード（file_id, new_file）

    rect rgb(255, 230, 200)
        Note over API,DB: 権限確認
        API->>DB: SELECT role FROM project_member WHERE project_id = ? AND user_id = ?
        DB-->>API: MEMBER
    end

    rect rgb(200, 220, 240)
        Note over API,DB: FV-004: 現在バージョン確認
        API->>DB: SELECT * FROM project_file WHERE id = ?
        DB-->>API: current_file（version, is_latest）
    end

    API->>Storage: 新ファイル保存
    Storage-->>API: new_file_path

    rect rgb(200, 230, 200)
        Note over API,DB: FV-001: 新バージョン作成
        API->>DB: UPDATE project_file SET is_latest = false WHERE id = ?
        DB-->>API: 更新完了

        API->>DB: INSERT INTO project_file<br/>(parent_file_id=?, version=current+1, is_latest=true, ...)
        DB-->>API: new_file_id
    end

    API-->>User: 新バージョン作成完了（new_file_id, version）

    Note over User,DB: 【実装】parent_file_idでバージョンチェーン構築
    Note over User,DB: is_latestフラグで最新版を識別
:::

### 9.2 バージョン履歴取得

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: バージョン履歴要求（file_id）

    rect rgb(200, 220, 240)
        Note over API,DB: FV-002: バージョン履歴取得

        API->>DB: SELECT * FROM project_file WHERE id = ?
        DB-->>API: 指定ファイル

        Note over API,DB: 親ファイルを辿って履歴取得
        loop parent_file_id != NULL
            API->>DB: SELECT * FROM project_file WHERE id = {parent_file_id}
            DB-->>API: 親ファイル
        end

        Note over API,DB: 子ファイルを辿って履歴取得
        API->>DB: WITH RECURSIVE を使用して子ファイル取得
        DB-->>API: 子ファイル一覧
    end

    API->>API: バージョン順でソート

    API-->>User: バージョン履歴（versions[]）

    Note over User,DB: 各バージョンにはversion, created_at,
    Note over User,DB: uploaded_by, is_latestが含まれる
:::

---

## 10. システム管理

> **注記**: 以下のシーケンスはシステム管理者（SystemAdmin）ロールを持つユーザーのみが実行可能です。すべて将来実装予定の機能です。

### 10.1 ユーザー操作履歴追跡

::: mermaid
sequenceDiagram
    autonumber
    actor Admin as システム管理者
    participant API as CAMPシステム
    participant DB as Database

    Admin->>API: 操作履歴検索要求（user_id, date_range, action_type）

    rect rgb(255, 230, 200)
        Note over API,DB: 権限確認
        API->>DB: SELECT roles FROM user_account WHERE id = {admin_id}
        DB-->>API: ["SystemAdmin"]
        API->>API: SystemAdmin権限確認OK
    end

    rect rgb(200, 220, 240)
        Note over API,DB: SA-001: 操作履歴検索
        API->>DB: SELECT * FROM user_activity<br/>WHERE user_id = ? AND created_at BETWEEN ? AND ?<br/>ORDER BY created_at DESC
        DB-->>API: 操作履歴一覧
    end

    API-->>Admin: 操作履歴一覧

    Admin->>API: 詳細確認要求（activity_id）

    rect rgb(200, 220, 240)
        Note over API,DB: SA-004: 詳細確認
        API->>DB: SELECT * FROM user_activity WHERE id = ?
        DB-->>API: 操作詳細（リクエスト内容、レスポンス、エラー情報）
    end

    API-->>Admin: 操作詳細
:::

### 10.2 通知・アラート管理

::: mermaid
sequenceDiagram
    autonumber
    actor Admin as システム管理者
    participant API as CAMPシステム
    participant DB as Database
    participant Notify as 通知サービス

    Admin->>API: システムお知らせ作成（title, content, target_users, scheduled_at）

    rect rgb(255, 230, 200)
        Note over API,DB: 権限確認
        API->>DB: SELECT roles FROM user_account WHERE id = {admin_id}
        DB-->>API: ["SystemAdmin"]
    end

    rect rgb(200, 230, 200)
        Note over API,DB: SA-033: システムお知らせ配信
        API->>DB: INSERT INTO system_announcement<br/>(title, content, target_users, scheduled_at, created_by)
        DB-->>API: announcement_id
    end

    alt 即時配信
        API->>Notify: 通知送信要求
        Notify-->>API: 送信完了
        API->>DB: UPDATE system_announcement SET status = 'sent'
    else 予約配信
        Note over API: スケジューラに登録
    end

    API-->>Admin: お知らせ登録完了

    Note over Admin,DB: メンテナンス予告も同様のフローで登録（SA-034）
:::

### 10.3 セキュリティ管理（セッション管理）

::: mermaid
sequenceDiagram
    autonumber
    actor Admin as システム管理者
    participant API as CAMPシステム
    participant DB as Database
    participant Auth as 認証サービス

    Admin->>API: アクティブセッション一覧要求

    rect rgb(255, 230, 200)
        Note over API,DB: 権限確認
        API->>DB: SELECT roles FROM user_account WHERE id = {admin_id}
        DB-->>API: ["SystemAdmin"]
    end

    rect rgb(200, 220, 240)
        Note over API,DB: SA-035: アクティブセッション一覧
        API->>DB: SELECT us.*, ua.email, ua.display_name<br/>FROM user_session us<br/>JOIN user_account ua ON us.user_id = ua.id<br/>WHERE us.expires_at > NOW()
        DB-->>API: アクティブセッション一覧
    end

    API-->>Admin: セッション一覧（user_id, login_time, ip_address, user_agent）

    Admin->>API: 強制ログアウト要求（user_id）

    rect rgb(255, 200, 200)
        Note over API,DB: SA-036: 強制ログアウト
        API->>DB: DELETE FROM user_session WHERE user_id = ?
        DB-->>API: 削除完了
        API->>Auth: トークン無効化要求
        Auth-->>API: 無効化完了
    end

    API-->>Admin: 強制ログアウト完了

    Note over Admin,DB: 【補足】IP制限・認証ポリシーはAzure ADで管理
:::

### 10.4 データ管理・クリーンアップ

::: mermaid
sequenceDiagram
    autonumber
    actor Admin as システム管理者
    participant API as CAMPシステム
    participant DB as Database
    participant Storage as ファイルストレージ

    Admin->>API: 孤立ファイルクリーンアップ要求

    rect rgb(255, 230, 200)
        Note over API,DB: 権限確認
        API->>DB: SELECT roles FROM user_account WHERE id = {admin_id}
        DB-->>API: ["SystemAdmin"]
    end

    rect rgb(200, 220, 240)
        Note over API,DB: SA-038: 孤立ファイル検出
        API->>DB: SELECT pf.* FROM project_file pf<br/>LEFT JOIN analysis_file af ON pf.id = af.project_file_id<br/>LEFT JOIN driver_tree_file dtf ON pf.id = dtf.project_file_id<br/>WHERE af.id IS NULL AND dtf.id IS NULL<br/>AND pf.created_at < NOW() - INTERVAL '90 days'
        DB-->>API: 孤立ファイル一覧
    end

    API-->>Admin: 孤立ファイル一覧（確認用）

    Admin->>API: クリーンアップ実行（file_ids[]）

    rect rgb(255, 200, 200)
        Note over API,DB: 削除実行
        loop 各ファイル
            API->>Storage: ファイル削除（file_path）
            Storage-->>API: 削除完了
            API->>DB: DELETE FROM project_file WHERE id = ?
            DB-->>API: 削除完了
        end
    end

    API-->>Admin: クリーンアップ完了（削除件数）
:::

### 10.5 サポートツール

::: mermaid
sequenceDiagram
    autonumber
    actor Admin as システム管理者
    participant API as CAMPシステム
    participant DB as Database

    Admin->>API: システムヘルスチェック要求

    rect rgb(200, 220, 240)
        Note over API,DB: SA-043: ヘルスチェック実行
        par 並列チェック
            API->>DB: SELECT 1（DB接続確認）
            API->>API: メモリ使用率確認
            API->>API: ディスク使用率確認
            API->>API: 外部サービス接続確認
        end
        DB-->>API: OK
    end

    API-->>Admin: ヘルスチェック結果

    Note over Admin,DB: 結果には以下を含む:
    Note over Admin,DB: - DB接続状態
    Note over Admin,DB: - メモリ/ディスク使用率
    Note over Admin,DB: - Azure AD接続状態
    Note over Admin,DB: - ストレージ接続状態
:::

---

## 11. DB設計課題まとめ（シーケンス図から抽出）

### 11.1 課題一覧

::: mermaid
sequenceDiagram
    participant Issue as 課題
    participant Current as 現状
    participant Solution as 改善案

    rect rgb(255, 200, 200)
        Note over Issue,Solution: 【高優先度】データ整合性
    end

    Issue->>Current: スナップショット分岐履歴
    Current->>Solution: snapshot_orderのみ
    Solution-->>Issue: parent_snapshot_id FK追加

    Issue->>Current: ノードのツリー所属
    Current->>Solution: driver_tree_id なし
    Solution-->>Issue: driver_tree_id FK追加

    Issue->>Current: current_snapshot整合性
    Current->>Solution: INTEGER（参照なし）
    Solution-->>Issue: UUID FK化

    Issue->>Current: Category↔Formula関係
    Current->>Solution: driver_type_idで暗黙紐付
    Solution-->>Issue: category_id FK追加

    rect rgb(255, 230, 200)
        Note over Issue,Solution: 【中優先度】業務ルール
    end

    Issue->>Current: セッション状態管理
    Current->>Solution: 状態カラムなし
    Solution-->>Issue: status ENUM追加

    Issue->>Current: チャット→ステップ関連
    Current->>Solution: 関連なし
    Solution-->>Issue: triggered_by_chat_id FK

    Issue->>Current: order_index重複
    Current->>Solution: 制約なし
    Solution-->>Issue: UNIQUE制約追加

    rect rgb(200, 220, 240)
        Note over Issue,Solution: 【低優先度】拡張性
    end

    Issue->>Current: ロール変更履歴
    Current->>Solution: JSON配列のみ
    Solution-->>Issue: 履歴テーブル追加

    Issue->>Current: ファイル削除保護
    Current->>Solution: CASCADE削除
    Solution-->>Issue: 参照確認＋警告
:::

---

## 12. 改善後の理想的なシーケンス

### 12.1 スナップショット分岐（改善後）

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: スナップショット3に戻る

    rect rgb(200, 220, 240)
        API->>DB: SELECT id FROM analysis_snapshot WHERE session_id = ? AND snapshot_order = 3
        DB-->>API: snapshot_3_id
    end

    rect rgb(200, 220, 240)
        API->>DB: UPDATE analysis_session SET current_snapshot_id = {snapshot_3_id}
        DB-->>API: 更新完了
    end

    User->>API: 新しい分析開始

    rect rgb(200, 230, 200)
        Note over API,DB: 【改善後】parent_snapshot_idを設定
        API->>DB: INSERT INTO analysis_snapshot (session_id, snapshot_order=6, parent_snapshot_id={snapshot_3_id})
        DB-->>API: snapshot_6_id
    end

    rect rgb(200, 220, 240)
        API->>DB: UPDATE analysis_session SET current_snapshot_id = {snapshot_6_id}
        DB-->>API: 更新完了
    end

    Note over User,DB: 【効果】
    Note over User,DB: - 分岐元が明確（parent_snapshot_id）
    Note over User,DB: - current_snapshot_idはFK参照で整合性保証
    Note over User,DB: - ツリー構造の履歴を完全に再現可能
:::

### 12.2 ノード作成（改善後）

::: mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant API as CAMPシステム
    participant DB as Database

    User->>API: ノード作成（tree_id, label, position）

    rect rgb(200, 230, 200)
        Note over API,DB: 【改善後】driver_tree_idを必須で設定
        API->>DB: INSERT INTO driver_tree_node (driver_tree_id, label, position_x, position_y, node_type)
        DB-->>API: node_id
    end

    Note over User,DB: 【効果】
    Note over User,DB: - ノードの所属ツリーが明確
    Note over User,DB: - 孤立ノードの検出が容易
    Note over User,DB: - ツリー削除時のカスケード削除が確実
:::

---

#### ドキュメント管理情報

- **作成日**: 2025年12月24日
- **更新日**: 2025年12月29日
- **目的**: ユースケースフローの可視化とDB設計課題の抽出
- **関連**: 02-usecase-flow-analysis.md, ../03-database/02-er-diagram.md
- **更新内容**: システム管理のシーケンス図（操作履歴追跡、通知・アラート、セキュリティ、データ管理、サポートツール）を追加
