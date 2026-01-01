# 個別施策分析 統合設計書（AVM-001〜AST-006）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムの個別施策分析機能（ユースケースAVM-001〜AST-006）の実装に必要なフロントエンド・バックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|---------|
| **検証マスタ管理** | AVM-001〜AVM-005 | 検証カテゴリの作成・更新・削除・一覧・並べ替え |
| **課題マスタ管理** | AIM-001〜AIM-008 | 分析課題の作成・更新・削除・一覧・プロンプト設定 |
| **グラフ軸マスタ管理** | AGM-001〜AGM-004 | グラフ軸の作成・更新・削除・一覧 |
| **ダミー数式・チャート管理** | ADM-001〜ADM-008 | ダミー数式・チャートの作成・更新・削除・一覧 |
| **分析セッション管理** | AS-001〜AS-007 | セッションの作成・削除・一覧・詳細・入力ファイル設定 |
| **分析ファイル管理** | AF-001〜AF-006 | 分析ファイルの作成・更新・削除・一覧・軸設定 |
| **スナップショット管理** | ASN-001〜ASN-005 | スナップショットの作成・削除・一覧・復元 |
| **チャット管理** | AC-001〜AC-003 | チャットメッセージ送信・履歴取得・削除 |
| **分析ステップ管理** | AST-001〜AST-006 | ステップの作成・更新・削除・一覧・並べ替え |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 11テーブル |
| APIエンドポイント | 20エンドポイント |
| Pydanticスキーマ | 35スキーマ |
| サービス | 5サービス |
| フロントエンド画面 | 8画面 |

---

## 2. データベース設計

データベース設計の詳細は以下を参照してください：

- [データベース設計書 - 3.4 個別施策分析機能](../../../06-database/01-database-design.md#34-個別施策分析機能)

### 2.1 関連テーブル一覧

| テーブル名 | 説明 |
|-----------|------|
| analysis_validation_master | 検証マスタ |
| analysis_issue_master | 課題マスタ |
| analysis_graph_axis_master | グラフ軸マスタ |
| analysis_dummy_formula_master | ダミー数式マスタ |
| analysis_dummy_chart_master | ダミーチャートマスタ |
| analysis_session | 分析セッション |
| analysis_file | 分析ファイル |
| analysis_snapshot | 分析スナップショット |
| analysis_chat | 分析チャット |
| analysis_step | 分析ステップ |
| analysis_template | 分析テンプレート |

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

### 4.1 Enum定義

```python
class AnalysisSessionStatusEnum(str, Enum):
    """セッション状態"""
    draft = "draft"          # 下書き
    active = "active"        # アクティブ
    completed = "completed"  # 完了
    archived = "archived"    # アーカイブ

class AnalysisChatRoleEnum(str, Enum):
    """チャットロール"""
    user = "user"            # ユーザー
    assistant = "assistant"  # アシスタント

class AnalysisAxisTypeEnum(str, Enum):
    """軸タイプ"""
    time = "time"    # 時間軸
    value = "value"  # 値軸
    group = "group"  # グループ軸
```

### 4.2 Info/Dataスキーマ

```python
class AnalysisSessionInfo(CamelCaseModel):
    """分析セッション情報"""
    id: UUID
    name: str
    project_id: UUID
    issue_id: UUID
    creator_id: UUID
    input_file_id: UUID | None = None
    current_snapshot_id: UUID | None = None
    status: AnalysisSessionStatusEnum
    custom_system_prompt: str | None = None
    initial_message: str | None = None
    created_at: datetime
    updated_at: datetime
    snapshot_count: int = 0

class AnalysisFileInfo(CamelCaseModel):
    """分析ファイル情報"""
    id: UUID
    session_id: UUID
    project_file_id: UUID | None = None
    filename: str
    axis_config: dict | None = None
    data: dict | None = None
    created_at: datetime
    updated_at: datetime

class AnalysisSnapshotInfo(CamelCaseModel):
    """スナップショット情報"""
    id: UUID
    session_id: UUID
    parent_snapshot_id: UUID | None = None
    snapshot_order: int
    created_at: datetime
    updated_at: datetime

class AnalysisChatInfo(CamelCaseModel):
    """チャット情報"""
    id: UUID
    snapshot_id: UUID
    chat_order: int
    role: AnalysisChatRoleEnum
    message: str | None = None
    created_at: datetime

class AnalysisStepInfo(CamelCaseModel):
    """ステップ情報"""
    id: UUID
    snapshot_id: UUID
    step_type: str
    step_config: dict
    step_order: int
    created_at: datetime
    updated_at: datetime
```

### 4.3 Request/Responseスキーマ

```python
# セッション作成
class AnalysisSessionCreate(CamelCaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    issue_id: UUID
    input_file_id: UUID | None = None
    custom_system_prompt: str | None = None

# セッション更新
class AnalysisSessionUpdate(CamelCaseModel):
    name: str | None = Field(None, max_length=255)
    input_file_id: UUID | None = None
    current_snapshot_id: UUID | None = None
    status: AnalysisSessionStatusEnum | None = None
    custom_system_prompt: str | None = None

# セッション一覧レスポンス
class AnalysisSessionListResponse(CamelCaseModel):
    sessions: list[AnalysisSessionInfo]
    total: int
    skip: int
    limit: int

# セッション詳細レスポンス
class AnalysisSessionDetailResponse(CamelCaseModel):
    session: AnalysisSessionInfo
    input_file: AnalysisFileInfo | None = None
    current_snapshot: AnalysisSnapshotInfo | None = None
    issue: dict  # 課題マスタ情報

# ファイル追加
class AnalysisFileCreate(CamelCaseModel):
    project_file_id: UUID

# ファイル更新
class AnalysisFileUpdate(CamelCaseModel):
    axis_config: dict | None = None

# スナップショット一覧レスポンス
class AnalysisSnapshotListResponse(CamelCaseModel):
    snapshots: list[AnalysisSnapshotInfo]
    total: int

# チャット送信
class AnalysisChatCreate(CamelCaseModel):
    content: str = Field(..., min_length=1)

# チャット履歴レスポンス
class AnalysisChatListResponse(CamelCaseModel):
    chats: list[AnalysisChatInfo]
    total: int

# ステップ作成
class AnalysisStepCreate(CamelCaseModel):
    step_type: str = Field(..., min_length=1, max_length=50)
    step_config: dict

# ステップ更新
class AnalysisStepUpdate(CamelCaseModel):
    step_type: str | None = None
    step_config: dict | None = None
    step_order: int | None = None
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| AnalysisSessionService | セッションCRUD、複製、ファイル設定 |
| AnalysisFileService | 分析ファイル管理、軸設定 |
| AnalysisSnapshotService | スナップショットCRUD、復元 |
| AnalysisChatService | チャットメッセージ送受信 |
| AnalysisStepService | ステップCRUD、並べ替え |

### 5.2 主要メソッド

#### AnalysisSessionService

```python
class AnalysisSessionService:
    # セッションCRUD
    async def create_session(
        project_id: UUID,
        issue_id: UUID,
        creator_id: UUID,
        name: str,
        custom_system_prompt: str | None = None
    ) -> AnalysisSession
    async def delete_session(session_id: UUID) -> None
    async def update_session(session_id: UUID, update_data: AnalysisSessionUpdate) -> AnalysisSession
    async def duplicate_session(session_id: UUID, user_id: UUID) -> AnalysisSession

    # セッション取得
    async def list_sessions(
        project_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: AnalysisSessionStatusEnum | None = None
    ) -> list[AnalysisSession]
    async def count_sessions(project_id: UUID, status: AnalysisSessionStatusEnum | None = None) -> int
    async def get_session(session_id: UUID) -> AnalysisSession | None
    async def get_session_result(session_id: UUID) -> dict

    # ファイル・スナップショット設定
    async def set_input_file(session_id: UUID, file_id: UUID) -> AnalysisSession
    async def restore_snapshot(session_id: UUID, snapshot_id: UUID) -> AnalysisSession
```

#### AnalysisFileService

```python
class AnalysisFileService:
    # ファイルCRUD
    async def add_file(session_id: UUID, project_file_id: UUID) -> AnalysisFile
    async def update_file(file_id: UUID, update_data: AnalysisFileUpdate) -> AnalysisFile
    async def delete_file(file_id: UUID) -> None
    async def list_files(session_id: UUID) -> list[AnalysisFile]
    async def get_file(file_id: UUID) -> AnalysisFile | None

    # 軸設定
    async def update_axis_config(file_id: UUID, axis_config: dict) -> AnalysisFile
    async def parse_file_data(file_id: UUID) -> dict
```

#### AnalysisSnapshotService

```python
class AnalysisSnapshotService:
    # スナップショットCRUD
    async def create_snapshot(
        session_id: UUID,
        parent_snapshot_id: UUID | None = None
    ) -> AnalysisSnapshot
    async def delete_snapshot(snapshot_id: UUID) -> None
    async def list_snapshots(session_id: UUID) -> list[AnalysisSnapshot]
    async def get_snapshot(snapshot_id: UUID) -> AnalysisSnapshot | None
```

#### AnalysisChatService

```python
class AnalysisChatService:
    # チャット操作
    async def send_message(snapshot_id: UUID, content: str) -> AnalysisChat
    async def get_chat_history(snapshot_id: UUID) -> list[AnalysisChat]
    async def delete_message(chat_id: UUID) -> None
    async def count_messages(snapshot_id: UUID) -> int
```

#### AnalysisStepService

```python
class AnalysisStepService:
    # ステップCRUD
    async def create_step(
        snapshot_id: UUID,
        step_type: str,
        step_config: dict
    ) -> AnalysisStep
    async def update_step(step_id: UUID, update_data: AnalysisStepUpdate) -> AnalysisStep
    async def delete_step(step_id: UUID) -> None
    async def list_steps(snapshot_id: UUID) -> list[AnalysisStep]

    # ステップ設定
    async def update_step_config(step_id: UUID, config: dict) -> AnalysisStep
    async def reorder_steps(snapshot_id: UUID, step_ids: list[UUID]) -> list[AnalysisStep]
```

---

## 6. フロントエンド設計

### 6.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|-------|------|------|
| sessions | セッション一覧 | `/projects/{id}/sessions` | セッション一覧表示・検索 |
| session-new | セッション作成 | `/projects/{id}/sessions/new` | 新規セッション作成ウィザード |
| analysis | 分析画面 | `/projects/{id}/sessions/{id}/analysis` | チャット・ステップ・結果表示 |
| snapshots | スナップショット履歴 | `/projects/{id}/sessions/{id}/snapshots` | スナップショットタイムライン・復元 |
| session-detail | セッション詳細 | `/projects/{id}/sessions/{id}` | 完了セッションの結果閲覧 |
| verifications | 検証マスタ管理 | `/admin/verifications` | 検証カテゴリ管理（管理者） |
| issues | 課題マスタ管理 | `/admin/issues` | 分析課題管理（管理者） |
| issue-edit | 課題編集 | `/admin/issues/{id}` | 課題詳細・プロンプト編集 |

### 6.2 コンポーネント構成

```text
pages/projects/[id]/sessions/
├── index.tsx              # セッション一覧
├── new.tsx                # セッション作成ウィザード
└── [sessionId]/
    ├── index.tsx          # セッション詳細（結果閲覧）
    ├── analysis.tsx       # 分析画面
    └── snapshots.tsx      # スナップショット履歴

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

#### ページヘッダー

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | アクション | 備考 |
|---------|---------|------------------|---------------------|-----------|------|
| セッション名 | テキスト(large) | `GET .../session/{id}` | `name` | - | - |
| スナップショット履歴ボタン | ボタン | - | - | スナップショット履歴画面へ遷移 | - |
| 保存ボタン | ボタン | `POST .../snapshot` | - | 現在のスナップショット保存 | ASN-001 |

#### 情報アラート

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| 現在のスナップショット番号 | バッジ | `GET .../session/{id}` | `currentSnapshot.snapshotOrder` | "スナップショット #N" |
| 入力ファイル名 | テキスト | 同上 | `inputFile.filename` | - |
| 課題名 | テキスト | 同上 | `issue.name` | - |

#### メインエリア（チャット）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| チャット履歴 | メッセージリスト | `GET .../session/{id}/result` | `chats` | role別スタイル |
| ユーザーメッセージ | 右寄せ | 同上 | `chats[].content` (role=user) | - |
| アシスタント返答 | 左寄せ | 同上 | `chats[].content` (role=assistant) | Markdown対応 |
| メッセージ入力 | テキストエリア | `POST .../session/{id}/chat` | `content` | - |

#### 右サイドバー（ファイル情報・ステップ）

**ファイル情報カード**

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ファイル名 | テキスト | `GET .../session/{id}` | `inputFile.filename` | - |
| ファイルサイズ | テキスト | 同上 | `inputFile.size` | バイト→KB/MB変換 |
| 行数 | テキスト | 同上 | `inputFile.rows` | - |
| 列数 | テキスト | 同上 | `inputFile.columns` | - |

**ステップリスト**

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ステップリスト | カードリスト | `GET .../session/{id}/result` | `steps` | ドラッグ並替え可 |
| ステップタイプ | バッジ | 同上 | `steps[].stepType` | - |
| ステップ設定 | 展開パネル | 同上 | `steps[].stepConfig` | JSON表示 |

### 7.4 スナップショット履歴画面（snapshots）

#### ページヘッダー

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | アクション | 備考 |
|---------|---------|------------------|---------------------|-----------|------|
| タイトル | テキスト | - | - | - | "スナップショット履歴" |
| 戻るボタン | ボタン | - | - | 分析画面へ戻る | - |

#### 警告アラート

| 画面項目 | 表示形式 | 備考 |
|---------|---------|------|
| 警告メッセージ | アラート | "スナップショットを復元すると、現在の変更が失われます。" |

#### スナップショットタイムライン

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | アクション | 備考 |
|---------|---------|------------------|---------------------|-----------|------|
| スナップショット番号 | バッジ | `GET .../session/{id}/snapshot` | `snapshots[].snapshotOrder` | - | "#1", "#2", ... |
| 作成日時 | テキスト | 同上 | `snapshots[].createdAt` | - | ISO8601→YYYY/MM/DD HH:mm |
| 説明 | テキスト | 同上 | `snapshots[].description` | - | 自動生成またはユーザー入力 |
| 現在地バッジ | バッジ | 同上 | `snapshots[].id === currentSnapshotId` | - | "現在ここ" |
| 復元ボタン | ボタン | `PUT .../session/{id}` | - | スナップショット復元 | ASN-005 |
| 削除ボタン | アイコンボタン | `DELETE .../snapshot/{id}` | - | スナップショット削除 | ASN-002 |

### 7.5 セッション詳細画面（session-detail）

#### ステータスバナー

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ステータス | バッジ | `GET .../session/{id}` | `status` | "完了", "進行中", "アーカイブ" |
| 完了日時 | テキスト | 同上 | `completedAt` | status=completedの場合のみ |
| スナップショット数 | テキスト | 同上 | `snapshotCount` | - |

#### 分析結果サマリー

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| 課題名 | テキスト | `GET .../session/{id}/result` | `issue.name` | - |
| 入力ファイル | テキスト | 同上 | `inputFile.filename` | - |
| チャット数 | 数値 | 同上 | `chatCount` | - |
| ステップ数 | 数値 | 同上 | `stepCount` | - |

#### キーインサイト

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| インサイトリスト | リスト | `GET .../session/{id}/result` | `insights` | AIが抽出した主要な発見 |
| インサイトテキスト | テキスト | 同上 | `insights[].text` | Markdown対応 |

#### AI対話履歴（折り畳み可能）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| チャット履歴 | メッセージリスト | `GET .../session/{id}/messages` | `chats` | 読み取り専用 |
| ユーザーメッセージ | 右寄せ | 同上 | `chats[].content` (role=user) | - |
| アシスタント返答 | 左寄せ | 同上 | `chats[].content` (role=assistant) | Markdown対応 |

#### サイドバー（セッション情報）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| セッション名 | テキスト | `GET .../session/{id}` | `name` | - |
| 作成者 | テキスト | 同上 | `creator.displayName` | - |
| 作成日時 | テキスト | 同上 | `createdAt` | ISO8601→YYYY/MM/DD HH:mm |
| 最終更新日時 | テキスト | 同上 | `updatedAt` | ISO8601→YYYY/MM/DD HH:mm |

#### サイドバー（アクション）

| 画面項目 | 表示形式 | APIエンドポイント | アクション | 備考 |
|---------|---------|------------------|-----------|------|
| 複製ボタン | ボタン | `POST .../session/{id}/duplicate` | セッション複製 | - |
| エクスポートボタン | ボタン | `GET .../session/{id}/export` | 結果をPDF/CSV出力 | - |
| アーカイブボタン | ボタン | `PUT .../session/{id}` | status=archivedに変更 | - |

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

## 10. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | AN-DESIGN-001 |
| 対象ユースケース | AS-001〜AS-007, AF-001〜AF-006, ASN-001〜ASN-005, AC-001〜AC-003, AST-001〜AST-006 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/models/analysis/` |
|  | `src/app/schemas/analysis/` |
|  | `src/app/api/routes/v1/analysis/` |
