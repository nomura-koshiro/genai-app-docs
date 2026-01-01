# 個別施策分析 統合設計書（AVM-001〜AST-006）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムの個別施策分析機能（ユースケースAVM-001〜AST-006）の実装に必要なフロントエンド・バックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | ユースケースID | 機能概要 |
|---------|---------------|---------|
| 検証マスタ管理 | AVM-001〜AVM-005 | 検証カテゴリの作成・更新・削除・一覧・並べ替え |
| 課題マスタ管理 | AIM-001〜AIM-008 | 分析課題の作成・更新・削除・一覧・プロンプト設定 |
| グラフ軸マスタ管理 | AGM-001〜AGM-004 | グラフ軸の作成・更新・削除・一覧 |
| ダミー数式・チャート管理 | ADM-001〜ADM-008 | ダミー数式・チャートの作成・更新・削除・一覧 |
| 分析セッション管理 | AS-001〜AS-007 | セッションの作成・削除・一覧・詳細・入力ファイル設定 |
| 分析ファイル管理 | AF-001〜AF-006 | 分析ファイルの作成・更新・削除・一覧・軸設定 |
| スナップショット管理 | ASN-001〜ASN-005 | スナップショットの作成・削除・一覧・復元 |
| チャット管理 | AC-001〜AC-003 | チャットメッセージ送信・履歴取得・削除 |
| 分析ステップ管理 | AST-001〜AST-006 | ステップの作成・更新・削除・一覧・並べ替え |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 10テーブル |
| APIエンドポイント | 20エンドポイント |
| Pydanticスキーマ | 35スキーマ |
| サービス | 5サービス |
| フロントエンド画面 | 6画面 |

---

## 2. データベース設計

### 2.1 analysis_validation_master（検証マスタ）

**対応ユースケース**: AVM-001〜AVM-005

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| name | VARCHAR(255) | NO | 検証名 |
| description | TEXT | YES | 説明 |
| validation_order | INTEGER | NO | 表示順序 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

### 2.2 analysis_issue_master（課題マスタ）

**対応ユースケース**: AIM-001〜AIM-008

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| validation_id | UUID | NO | 検証マスタID（FK） |
| name | VARCHAR(255) | NO | 課題名 |
| description | TEXT | YES | 説明 |
| agent_prompt | TEXT | YES | エージェントプロンプト |
| initial_msg | TEXT | YES | 初期メッセージ |
| dummy_hint | TEXT | YES | ダミーヒント |
| dummy_input | BYTEA | YES | ダミー入力データ |
| issue_order | INTEGER | NO | 表示順序 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

### 2.3 analysis_graph_axis_master（グラフ軸マスタ）

**対応ユースケース**: AGM-001〜AGM-004

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| issue_id | UUID | NO | 課題マスタID（FK） |
| axis_name | VARCHAR(100) | NO | 軸名 |
| axis_type | VARCHAR(50) | NO | 軸タイプ（time/value/group） |
| description | TEXT | YES | 説明 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

### 2.4 analysis_dummy_formula_master（ダミー数式マスタ）

**対応ユースケース**: ADM-001〜ADM-004

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| issue_id | UUID | NO | 課題マスタID（FK） |
| formula_name | VARCHAR(100) | NO | 数式名 |
| formula | TEXT | NO | 数式 |
| description | TEXT | YES | 説明 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

### 2.5 analysis_dummy_chart_master（ダミーチャートマスタ）

**対応ユースケース**: ADM-005〜ADM-008

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| issue_id | UUID | NO | 課題マスタID（FK） |
| chart_name | VARCHAR(100) | NO | チャート名 |
| chart_type | VARCHAR(50) | NO | チャートタイプ |
| chart_config | JSONB | NO | チャート設定 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

### 2.6 analysis_session（分析セッション）

**対応ユースケース**: AS-001〜AS-007

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| name | VARCHAR(255) | NO | セッション名 |
| project_id | UUID | NO | プロジェクトID（FK） |
| issue_id | UUID | NO | 課題マスタID（FK） |
| creator_id | UUID | NO | 作成者ID（FK） |
| input_file_id | UUID | YES | 入力ファイルID（FK） |
| current_snapshot_id | UUID | YES | 現在のスナップショットID（FK） |
| status | VARCHAR(20) | NO | 状態（draft/active/completed/archived） |
| custom_system_prompt | TEXT | YES | カスタムシステムプロンプト |
| initial_message | TEXT | YES | 初期メッセージ |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

### 2.7 analysis_file（分析ファイル）

**対応ユースケース**: AF-001〜AF-006

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| session_id | UUID | NO | セッションID（FK） |
| project_file_id | UUID | YES | プロジェクトファイルID（FK） |
| filename | VARCHAR(255) | NO | ファイル名 |
| axis_config | JSONB | YES | 軸設定 |
| data | JSONB | YES | 解析済みデータ |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

### 2.8 analysis_snapshot（分析スナップショット）

**対応ユースケース**: ASN-001〜ASN-005

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| session_id | UUID | NO | セッションID（FK） |
| parent_snapshot_id | UUID | YES | 親スナップショットID（FK） |
| snapshot_order | INTEGER | NO | スナップショット順序 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

### 2.9 analysis_chat（分析チャット）

**対応ユースケース**: AC-001〜AC-003

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| snapshot_id | UUID | NO | スナップショットID（FK） |
| role | VARCHAR(20) | NO | ロール（user/assistant/system） |
| content | TEXT | NO | メッセージ内容 |
| chat_order | INTEGER | NO | チャット順序 |
| created_at | TIMESTAMP | NO | 作成日時 |

### 2.10 analysis_step（分析ステップ）

**対応ユースケース**: AST-001〜AST-006

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | UUID | NO | 主キー |
| snapshot_id | UUID | NO | スナップショットID（FK） |
| step_type | VARCHAR(50) | NO | ステップタイプ |
| step_config | JSONB | NO | ステップ設定 |
| step_order | INTEGER | NO | ステップ順序 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

---

## 3. APIエンドポイント設計

### 3.1 分析セッション管理

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/project/{project_id}/analysis/session` | セッション一覧取得 | メンバー | AS-003, AS-004 |
| GET | `/api/v1/project/{project_id}/analysis/session/{session_id}` | セッション詳細取得 | メンバー | AS-005 |
| GET | `/api/v1/project/{project_id}/analysis/session/{session_id}/result` | セッション結果取得 | メンバー | AS-005 |
| POST | `/api/v1/project/{project_id}/analysis/session` | セッション作成 | メンバー | AS-001 |
| POST | `/api/v1/project/{project_id}/analysis/session/{session_id}/duplicate` | セッション複製 | メンバー | - |
| PUT | `/api/v1/project/{project_id}/analysis/session/{session_id}` | セッション更新 | メンバー | AS-006, AS-007, ASN-005 |
| DELETE | `/api/v1/project/{project_id}/analysis/session/{session_id}` | セッション削除 | PM/Mod | AS-002 |

### 3.2 分析ファイル管理

| メソッド | エンドポイント | 説明 | 権限 | 対応UC | 備考 |
|---------|---------------|------|------|--------|------|
| GET | `/api/v1/project/{project_id}/analysis/session/{session_id}/file` | ファイル一覧取得 | メンバー | AF-004 | - |
| POST | `/api/v1/project/{project_id}/analysis/session/{session_id}/file` | ファイル追加 | メンバー | AF-001 | - |
| PATCH | `/api/v1/project/{project_id}/analysis/session/{session_id}/file/{file_id}` | ファイル設定更新 | メンバー | AF-002, AF-005, AF-006 | - |
| DELETE | `/api/v1/project/{project_id}/analysis/session/{session_id}/file/{file_id}` | ファイル削除 | メンバー | AF-003 | 未実装 |

### 3.3 チャット・ステップ管理

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/project/{project_id}/analysis/session/{session_id}/messages` | チャット履歴取得 | メンバー | AC-002 |
| POST | `/api/v1/project/{project_id}/analysis/session/{session_id}/chat` | チャット実行 | メンバー | AC-001 |
| DELETE | `/api/v1/project/{project_id}/analysis/session/{session_id}/messages/{chat_id}` | チャットメッセージ削除 | メンバー | AC-003 |
| POST | `/api/v1/project/{project_id}/analysis/session/{session_id}/step` | ステップ作成 | メンバー | AST-001 |
| PUT | `/api/v1/project/{project_id}/analysis/session/{session_id}/step/{step_id}` | ステップ更新 | メンバー | AST-002, AST-005, AST-006 |
| DELETE | `/api/v1/project/{project_id}/analysis/session/{session_id}/step/{step_id}` | ステップ削除 | メンバー | AST-003 |

### 3.4 スナップショット管理

| メソッド | エンドポイント | 説明 | 権限 | 対応UC | 備考 |
|---------|---------------|------|------|--------|------|
| GET | `/api/v1/project/{project_id}/analysis/session/{session_id}/snapshot` | スナップショット一覧 | メンバー | ASN-003 | - |
| POST | `/api/v1/project/{project_id}/analysis/session/{session_id}/snapshot` | スナップショット作成 | メンバー | ASN-001 | - |
| DELETE | `/api/v1/project/{project_id}/analysis/session/{session_id}/snapshot/{snapshot_id}` | スナップショット削除 | メンバー | ASN-002 | 未実装 |

---

## 4. Pydanticスキーマ設計

### 4.1 セッションスキーマ

| スキーマ名 | 用途 |
|-----------|------|
| AnalysisSessionCreate | セッション作成リクエスト |
| AnalysisSessionUpdate | セッション更新リクエスト |
| AnalysisSessionResponse | セッションレスポンス |
| AnalysisSessionDetailResponse | セッション詳細レスポンス |
| AnalysisSessionListResponse | セッション一覧レスポンス |
| AnalysisSessionResultListResponse | セッション結果一覧 |

### 4.2 ファイル・スナップショットスキーマ

| スキーマ名 | 用途 |
|-----------|------|
| AnalysisFileCreate | ファイル追加リクエスト |
| AnalysisFileUpdate | ファイル更新リクエスト |
| AnalysisFileResponse | ファイルレスポンス |
| AnalysisFileListResponse | ファイル一覧レスポンス |
| AnalysisSnapshotCreate | スナップショット作成リクエスト |
| AnalysisSnapshotResponse | スナップショットレスポンス |
| AnalysisSnapshotListResponse | スナップショット一覧レスポンス |

### 4.3 チャット・ステップスキーマ

| スキーマ名 | 用途 |
|-----------|------|
| AnalysisChatCreate | チャット送信リクエスト |
| AnalysisChatListResponse | チャット履歴レスポンス |
| AnalysisStepCreate | ステップ作成リクエスト |
| AnalysisStepUpdate | ステップ更新リクエスト |
| AnalysisStepResponse | ステップレスポンス |

---

## 5. サービス層設計

### 5.1 AnalysisSessionService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `create_session(project_id, issue_id, creator_id, name)` | セッション作成 | AS-001 |
| `delete_session(session_id)` | セッション削除 | AS-002 |
| `list_sessions(project_id, skip, limit, is_active)` | セッション一覧 | AS-003, AS-004 |
| `get_session(session_id)` | セッション詳細 | AS-005 |
| `update_session(session_id, update_data)` | セッション更新 | AS-006, AS-007 |
| `set_input_file(session_id, file_id)` | 入力ファイル設定 | AS-006 |
| `restore_snapshot(session_id, snapshot_id)` | スナップショット復元 | ASN-005 |

### 5.2 AnalysisFileService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `add_file(session_id, project_file_id)` | ファイル追加 | AF-001 |
| `update_file(file_id, update_data)` | ファイル更新 | AF-002 |
| `delete_file(file_id)` | ファイル削除 | AF-003 |
| `list_files(session_id)` | ファイル一覧 | AF-004 |
| `update_axis_config(file_id, axis_config)` | 軸設定更新 | AF-005 |

### 5.3 AnalysisSnapshotService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `create_snapshot(session_id, parent_snapshot_id)` | スナップショット作成 | ASN-001 |
| `delete_snapshot(snapshot_id)` | スナップショット削除 | ASN-002 |
| `list_snapshots(session_id)` | スナップショット一覧 | ASN-003 |
| `get_snapshot(snapshot_id)` | スナップショット詳細 | ASN-004 |

### 5.4 AnalysisChatService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `send_message(snapshot_id, content)` | メッセージ送信 | AC-001 |
| `get_chat_history(snapshot_id)` | 履歴取得 | AC-002 |
| `delete_message(chat_id)` | メッセージ削除 | AC-003 |

### 5.5 AnalysisStepService

| メソッド | 説明 | 対応UC |
|---------|------|--------|
| `create_step(snapshot_id, step_type, step_config)` | ステップ作成 | AST-001 |
| `update_step(step_id, update_data)` | ステップ更新 | AST-002 |
| `delete_step(step_id)` | ステップ削除 | AST-003 |
| `list_steps(snapshot_id)` | ステップ一覧 | AST-004 |
| `update_step_config(step_id, config)` | ステップ設定更新 | AST-005 |
| `reorder_steps(snapshot_id, step_ids)` | ステップ順序変更 | AST-006 |

---

## 6. フロントエンド設計

### 6.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|-------|------|------|
| sessions | セッション一覧 | `/projects/{id}/sessions` | セッション一覧表示・検索 |
| session-new | セッション作成 | `/projects/{id}/sessions/new` | 新規セッション作成ウィザード |
| analysis | 分析画面 | `/projects/{id}/sessions/{id}/analysis` | チャット・ステップ・結果表示 |
| verifications | 検証マスタ管理 | `/admin/verifications` | 検証カテゴリ管理（管理者） |
| issues | 課題マスタ管理 | `/admin/issues` | 分析課題管理（管理者） |
| issue-edit | 課題編集 | `/admin/issues/{id}` | 課題詳細・プロンプト編集 |

### 6.2 コンポーネント構成

```text
pages/projects/[id]/sessions/
├── index.tsx              # セッション一覧
├── new.tsx                # セッション作成ウィザード
└── [sessionId]/
    └── analysis.tsx       # 分析画面

pages/admin/
├── verifications.tsx      # 検証マスタ管理
├── issues.tsx             # 課題マスタ管理
└── issues/[id].tsx        # 課題編集
```

---

## 7. 画面項目・APIマッピング

### 7.1 セッション一覧画面（sessions）

#### 検索・フィルタ項目

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 備考 |
|---------|---------|------------------|-----------------|------|
| セッション名検索 | テキスト | `GET .../analysis/session` | - | フロントでフィルタ |
| 課題フィルタ | セレクト | 同上 | - | フロントでフィルタ |

#### 一覧表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| セッション名 | テキスト(strong) | `GET .../analysis/session` | `sessions[].name` | - |
| 課題 | テキスト | 同上 | `sessions[].issue.name` | - |
| 入力ファイル | テキスト | 同上 | `sessions[].inputFile.filename` | null→"-" |
| スナップショット | 数値 | 同上 | `sessions[].snapshotCount` | - |
| 作成者 | テキスト | 同上 | `sessions[].creator.displayName` | - |
| 更新日時 | 日時 | 同上 | `sessions[].updatedAt` | ISO8601→YYYY/MM/DD HH:mm |
| 開くボタン | ボタン | - | - | analysis画面へ遷移 |
| 複製ボタン | ボタン | `POST .../analysis/session` | - | セッション複製 |

### 7.2 セッション作成画面（session-new）

#### STEP 1: 分析テーマ選択

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | 備考 |
|---------|---------|-----|------------------|---------------------|------|
| 検証カテゴリ | カード選択 | ✓ | `GET /api/v1/analysis/template` | - | カテゴリ一覧から選択 |
| 分析課題 | セレクト | ✓ | `POST .../analysis/session` | `issueId` | カテゴリにより絞り込み |

#### STEP 2: データ準備

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | 備考 |
|---------|---------|-----|------------------|---------------------|------|
| 入力ファイル | セレクト | ✓ | `PUT .../session/{id}` | `inputFileId` | プロジェクトファイルから選択 |
| 対象シート | セレクト | ✓ | 同上 | - | Excelファイルの場合 |
| 時間軸 | セレクト | ✓ | `PATCH .../file/{id}` | `axisConfig.timeAxis` | 列選択 |
| 分析対象値 | セレクト | ✓ | 同上 | `axisConfig.valueAxis` | 列選択 |
| グループ化 | セレクト | - | 同上 | `axisConfig.groupAxis` | 列選択（任意） |

#### STEP 3: 確認

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | 備考 |
|---------|---------|-----|------------------|---------------------|------|
| セッション名 | テキスト | - | `POST .../analysis/session` | `name` | 空白時は自動生成 |

### 7.3 分析画面（analysis）

#### 左サイドバー（スナップショット履歴）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| スナップショットリスト | リスト | `GET .../session/{id}` | `snapshotList` | 順序でソート |
| 現在のスナップショット | ハイライト | 同上 | `currentSnapshotId` | - |
| スナップショット番号 | バッジ | 同上 | `snapshotList[].snapshotOrder` | - |

#### メインエリア（チャット）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| チャット履歴 | メッセージリスト | `GET .../session/{id}/result` | `chats` | role別スタイル |
| ユーザーメッセージ | 右寄せ | 同上 | `chats[].content` (role=user) | - |
| アシスタント返答 | 左寄せ | 同上 | `chats[].content` (role=assistant) | Markdown対応 |
| メッセージ入力 | テキストエリア | `POST .../session/{id}/chat` | `content` | - |

#### 右サイドバー（ステップ・結果）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ステップリスト | カードリスト | `GET .../session/{id}/result` | `steps` | ドラッグ並替え可 |
| ステップタイプ | バッジ | 同上 | `steps[].stepType` | - |
| ステップ設定 | 展開パネル | 同上 | `steps[].stepConfig` | JSON表示 |

---

## 8. ユースケースカバレッジ表

### 8.1 マスタ管理（AVM, AIM, AGM, ADM）

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| AVM-001 | 検証マスタを作成する | `POST /admin/validation` | verifications | 実装済 |
| AVM-002 | 検証マスタを更新する | `PATCH /admin/validation/{id}` | verifications | 実装済 |
| AVM-003 | 検証マスタを削除する | `DELETE /admin/validation/{id}` | verifications | 実装済 |
| AVM-004 | 検証マスタ一覧を取得する | `GET /admin/validation` | verifications | 実装済 |
| AVM-005 | 検証マスタの表示順を変更する | `PATCH /admin/validation/{id}` | verifications | 実装済 |
| AIM-001〜AIM-008 | 課題マスタ管理 | `/admin/issue/*` | issues, issue-edit | 実装済 |
| AGM-001〜AGM-004 | グラフ軸マスタ管理 | `/admin/graph-axis/*` | issue-edit | 実装済 |
| ADM-001〜ADM-008 | ダミー数式・チャート管理 | `/admin/dummy-*/*` | issue-edit | 実装済 |

### 8.2 セッション管理（AS, AF, ASN, AC, AST）

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| AS-001 | セッションを作成する | `POST .../session` | session-new | 実装済 |
| AS-002 | セッションを削除する | `DELETE .../session/{id}` | sessions | 実装済 |
| AS-003 | プロジェクト別セッション一覧 | `GET .../session` | sessions | 実装済 |
| AS-004 | ユーザー別セッション一覧 | `GET .../session` | sessions | 実装済 |
| AS-005 | セッション詳細を取得する | `GET .../session/{id}` | analysis | 実装済 |
| AS-006 | 入力ファイルを設定する | `PUT .../session/{id}` | session-new | 実装済 |
| AS-007 | スナップショット番号を更新する | `PUT .../session/{id}` | analysis | 実装済 |
| AF-001〜AF-006 | 分析ファイル管理 | `.../file/*` | analysis | 実装済 |
| ASN-001〜ASN-005 | スナップショット管理 | `.../snapshot/*` | analysis | 実装済 |
| AC-001〜AC-003 | チャット管理 | `.../chat` | analysis | 実装済 |
| AST-001〜AST-006 | ステップ管理 | `.../step/*` | analysis | 実装済 |

---

## 9. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/pages/sessions.js](../../03-mockup/pages/sessions.js)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

### ドキュメント管理情報

- **作成日**: 2026年1月1日
- **更新日**: 2026年1月1日
- **対象ソースコード**:
  - モデル: `src/app/models/analysis/`
  - スキーマ: `src/app/schemas/analysis/`
  - API: `src/app/api/routes/v1/analysis/`
