# 複製・エクスポート機能 統合設計書（CP-001〜EX-003）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムにおける複製・エクスポート機能の統合設計仕様を定義します。本機能は、分析セッション・ドライバーツリー・プロジェクトの複製、および分析結果・ツリーデータのエクスポートを提供します。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|--------|
| **複製機能** | CP-001 | 分析セッション複製 |
| | CP-002 | ドライバーツリー複製 |
| **エクスポート機能** | EX-001 | 分析結果エクスポート |
| | EX-002 | ツリー計算結果エクスポート |
| | EX-003 | ノードデータエクスポート |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 0 |
| APIエンドポイント | 5 |
| Pydanticスキーマ | 6 |
| フロントエンド画面 | 0 |

---

## 2. データベース設計

### 2.1 関連テーブル一覧

複製・エクスポート機能は専用テーブルを持たず、既存テーブルを利用します。

| テーブル名 | 説明 |
|-----------|------|
| analysis_session | セッション複製元/先 |
| analysis_step | ステップ複製 |
| analysis_snapshot | スナップショット複製 |
| driver_tree | ツリー複製元/先 |
| driver_tree_node | ノード複製 |
| driver_tree_relationship | リレーション複製 |
| driver_tree_relationship_child | 子ノード関係複製 |

### 2.2 複製ロジック

#### 分析セッション複製

```sql
-- 1. セッション複製（新規UUID生成）
INSERT INTO analysis_session (id, project_id, name, status, ...)
SELECT uuid_generate_v4(), project_id, name || ' (コピー)', 'draft', ...
FROM analysis_session WHERE id = :source_id;

-- 2. ステップ複製（親セッションIDを新規に紐付け）
INSERT INTO analysis_step (id, session_id, step_number, ...)
SELECT uuid_generate_v4(), :new_session_id, step_number, ...
FROM analysis_step WHERE session_id = :source_id;
```

#### ドライバーツリー複製

```sql
-- 1. ツリー複製
INSERT INTO driver_tree (id, project_id, name, ...)
SELECT uuid_generate_v4(), project_id, name || ' (コピー)', ...
FROM driver_tree WHERE id = :source_id;

-- 2. ノード複製（ID対応マップ作成）
-- 3. リレーション複製（ノードIDを新IDに置換）
-- 4. 子ノード関係複製
```

---

## 3. APIエンドポイント設計

### 3.1 エンドポイント一覧

#### 複製機能

| メソッド | パス | 説明 | 備考 |
|---------|------|------|------|
| POST | /api/v1/project/{project_id}/analysis/session/{session_id}/duplicate | セッション複製 | 実装済 |
| POST | /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/duplicate | ツリー複製 | 実装済 |

#### エクスポート機能

| メソッド | パス | 説明 | 備考 |
|---------|------|------|------|
| GET | /api/v1/project/{project_id}/analysis/session/{session_id}/export | 分析結果エクスポート | 未実装 |
| GET | /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/output | ツリー計算結果エクスポート | 実装済 |
| GET | /api/v1/project/{project_id}/driver-tree/node/{node_id}/preview/output | ノードデータエクスポート | 実装済 |

### 3.2 リクエスト/レスポンス定義

#### POST /project/{project_id}/analysis/session/{session_id}/duplicate（セッション複製）

**リクエスト:**

```json
{
  "name": "Q4売上分析 (コピー)",
  "includeSnapshots": true
}
```

**レスポンス (201):**

```json
{
  "sessionId": "uuid",
  "name": "Q4売上分析 (コピー)",
  "sourceSessionId": "uuid",
  "stepCount": 5,
  "snapshotCount": 3,
  "createdAt": "2026-01-01T00:00:00Z"
}
```

#### POST /project/{project_id}/driver-tree/tree/{tree_id}/duplicate（ツリー複製）

**リクエスト:**

```json
{
  "name": "売上ドライバーツリー (コピー)"
}
```

**レスポンス (201):**

```json
{
  "tree": {
    "treeId": "uuid",
    "name": "売上ドライバーツリー (コピー)",
    "nodes": [...],
    "relationships": [...]
  }
}
```

#### GET /project/{project_id}/analysis/session/{session_id}/export（分析結果エクスポート）

**クエリパラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| format | string | - | xlsx | 出力形式（xlsx/csv/pdf） |
| include_steps | bool | - | true | ステップを含める |
| include_chat | bool | - | true | チャット履歴を含める |

**レスポンス:**

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Content-Disposition: attachment; filename="session_export_YYYYMMDD.xlsx"

**Excelファイル構成:**

```text
Sheet1: サマリー
  - セッション名、作成日、ステータス
  - プロジェクト情報
  - ステップ概要

Sheet2: ステップ詳細
  - ステップ番号、タイトル、説明
  - 実行日時、結果

Sheet3: チャット履歴
  - メッセージ一覧（ユーザー/AI）
  - タイムスタンプ

Sheet4: データ
  - アップロードファイルのデータ（任意）
```

#### GET /project/{project_id}/driver-tree/tree/{tree_id}/output（ツリー計算結果エクスポート）

**クエリパラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| format | string | - | xlsx | 出力形式（xlsx/csv） |

**レスポンス:**

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Content-Disposition: attachment; filename="tree_simulation_YYYYMMDD.xlsx"

**Excelファイル構成:**

```text
Sheet1: サマリー
  - ツリー名、計算日時
  - 施策一覧と効果

Sheet2: ノード別計算結果
  - ノード名、現在値、施策後、変化率
  - 適用施策

Sheet3: 施策効果比較
  - 施策名、影響額、コスト、ROI
```

#### GET /project/{project_id}/driver-tree/node/{node_id}/preview/output（ノードデータエクスポート）

**レスポンス:**

- Content-Type: text/csv
- Content-Disposition: attachment; filename="node_data_{node_id}.csv"

---

## 4. Pydanticスキーマ設計

### 4.1 Enum定義

```python
class ExportFormatEnum(str, Enum):
    """エクスポート形式"""
    xlsx = "xlsx"
    csv = "csv"
    pdf = "pdf"
```

### 4.2 Info/Dataスキーマ

複製・エクスポート機能では専用のInfo/Dataスキーマは使用せず、既存のドメインモデル（Session, Tree, Node等）を利用します。

### 4.3 Request/Responseスキーマ

#### 複製関連スキーマ

```python
class SessionDuplicateRequest(CamelCaseModel):
    """セッション複製リクエスト"""
    name: str | None = None
    include_snapshots: bool = True

class SessionDuplicateResponse(CamelCaseModel):
    """セッション複製レスポンス"""
    session_id: UUID
    name: str
    source_session_id: UUID
    step_count: int
    snapshot_count: int
    created_at: datetime

class TreeDuplicateRequest(CamelCaseModel):
    """ツリー複製リクエスト"""
    name: str | None = None

# TreeDuplicateResponse は既存の DriverTreeGetTreeResponse を使用
```

#### エクスポート関連スキーマ

```python
class SessionExportRequest(CamelCaseModel):
    """セッションエクスポートリクエスト"""
    format: ExportFormatEnum = ExportFormatEnum.xlsx
    include_steps: bool = True
    include_chat: bool = True

class TreeExportRequest(CamelCaseModel):
    """ツリーエクスポートリクエスト"""
    format: ExportFormatEnum = ExportFormatEnum.xlsx
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| DuplicationService | セッション・ツリーの複製処理 |
| ExportService | 分析結果・ツリーデータのエクスポート処理 |

### 5.2 主要メソッド

#### DuplicationService - セッション複製

```python
class DuplicationService:
    """複製サービス"""

    async def duplicate_session(
        self,
        project_id: UUID,
        session_id: UUID,
        name: str | None,
        include_snapshots: bool,
        user_id: UUID
    ) -> SessionDuplicateResponse:
        """セッションを複製"""
        # 1. 元セッションの取得と権限確認
        source = await self._get_session(session_id)

        # 2. 新規セッションの作成
        new_name = name or f"{source.name} (コピー)"
        new_session = await self._create_session(project_id, new_name, user_id)

        # 3. ステップの複製
        steps = await self._duplicate_steps(session_id, new_session.id)

        # 4. スナップショットの複製（オプション）
        snapshots = []
        if include_snapshots:
            snapshots = await self._duplicate_snapshots(session_id, new_session.id)

        return SessionDuplicateResponse(
            session_id=new_session.id,
            name=new_name,
            source_session_id=session_id,
            step_count=len(steps),
            snapshot_count=len(snapshots),
            created_at=new_session.created_at
        )

    async def duplicate_tree(
        self,
        project_id: UUID,
        tree_id: UUID,
        name: str | None,
        user_id: UUID
    ) -> dict:
        """ツリーを複製"""
        # 1. 元ツリーの取得
        source = await self._get_tree(tree_id)

        # 2. 新規ツリーの作成
        new_name = name or f"{source.name} (コピー)"
        new_tree = await self._create_tree(project_id, new_name, user_id)

        # 3. ノードの複製（IDマッピング作成）
        node_id_map = await self._duplicate_nodes(tree_id, new_tree.id)

        # 4. リレーションの複製（IDを置換）
        await self._duplicate_relationships(tree_id, new_tree.id, node_id_map)

        # 5. ルートノードIDの更新
        if source.root_node_id:
            new_tree.root_node_id = node_id_map[source.root_node_id]
            await self._update_tree(new_tree)

        return await self._get_full_tree(new_tree.id)
```

#### ExportService - セッションエクスポート

```python
class ExportService:
    """エクスポートサービス"""

    async def export_session(
        self,
        project_id: UUID,
        session_id: UUID,
        format: str,
        include_steps: bool,
        include_chat: bool,
        user_id: UUID
    ) -> StreamingResponse:
        """セッションをエクスポート"""
        # 1. セッションデータの取得
        session = await self._get_session(session_id)

        # 2. ステップデータの取得
        steps = []
        if include_steps:
            steps = await self._get_steps(session_id)

        # 3. チャット履歴の取得
        chat_history = []
        if include_chat:
            chat_history = await self._get_chat_history(session_id)

        # 4. ファイル生成
        if format == "xlsx":
            file_stream = await self._generate_xlsx(session, steps, chat_history)
        elif format == "csv":
            file_stream = await self._generate_csv(session, steps)
        elif format == "pdf":
            file_stream = await self._generate_pdf(session, steps, chat_history)

        return file_stream

    async def export_tree_results(
        self,
        project_id: UUID,
        tree_id: UUID,
        format: str,
        user_id: UUID
    ) -> StreamingResponse:
        """ツリー計算結果をエクスポート"""
        # 1. ツリーと計算結果の取得
        tree = await self._get_tree(tree_id)
        calculated_data = await self._get_calculated_data(tree_id)
        policies = await self._get_policies(tree_id)

        # 2. ファイル生成
        if format == "xlsx":
            file_stream = await self._generate_tree_xlsx(tree, calculated_data, policies)
        else:
            file_stream = await self._generate_tree_csv(tree, calculated_data)

        return file_stream

    async def export_node_data(
        self,
        project_id: UUID,
        node_id: UUID,
        user_id: UUID
    ) -> StreamingResponse:
        """ノードデータをCSVエクスポート"""
        # 1. ノードとデータフレームの取得
        node = await self._get_node(node_id)
        data_frame = await self._get_data_frame(node.data_frame_id)

        # 2. CSV生成
        file_stream = await self._generate_node_csv(node, data_frame)

        return file_stream
```

---

## 6. フロントエンド設計

### 6.1 画面一覧

複製・エクスポート機能は専用の新規画面を持たず、既存画面に機能を追加します。

| 画面名 | 画面パス | 追加機能 | 実装状況 |
|-------|---------|---------|---------|
| セッション一覧 | `/projects/{id}/sessions` | セッション複製ボタン | 実装済 |
| 分析画面 | `/projects/{id}/analysis/{id}` | 分析結果エクスポートボタン | 未実装 |
| ツリー一覧 | `/projects/{id}/trees` | ツリー複製ボタン | 実装済 |
| 計算結果画面 | `/projects/{id}/trees/{id}/results` | ツリー計算結果エクスポートボタン | 実装済 |
| ノード編集パネル | `/projects/{id}/trees/{id}/edit` | ノードデータダウンロードボタン | 実装済 |

### 6.2 コンポーネント構成

#### ボタンコンポーネント

| コンポーネント | 配置場所 | APIエンドポイント | トリガーアクション |
|--------------|---------|------------------|------------------|
| 複製ボタン (Session) | セッション一覧の各行 | POST /session/{id}/duplicate | 複製確認ダイアログを表示 |
| 複製ボタン (Tree) | ツリー一覧の各行 | POST /tree/{id}/duplicate | 複製確認ダイアログを表示 |
| エクスポートボタン (Session) | 分析画面ヘッダー | GET /session/{id}/export | エクスポートオプションダイアログを表示 |
| エクスポートボタン (Tree) | 計算結果画面ヘッダー | GET /tree/{id}/output | ファイルダウンロード |
| データダウンロードボタン | ノード編集パネル | GET /node/{id}/preview/output | CSVファイルダウンロード |

#### ダイアログコンポーネント

**複製確認ダイアログ**

```text
┌────────────────────────────────────────┐
│  セッションを複製                        │
├────────────────────────────────────────┤
│  新しいセッション名:                     │
│  ┌──────────────────────────────────┐  │
│  │ Q4売上分析 (コピー)              │  │
│  └──────────────────────────────────┘  │
│                                        │
│  ☑ スナップショットも複製する           │
│                                        │
├────────────────────────────────────────┤
│  [キャンセル]              [複製する]   │
└────────────────────────────────────────┘
```

**エクスポートオプションダイアログ**

```text
┌────────────────────────────────────────┐
│  分析結果をエクスポート                  │
├────────────────────────────────────────┤
│  ファイル形式:                          │
│  ○ Excel (.xlsx)                       │
│  ○ CSV (.csv)                          │
│  ○ PDF (.pdf)                          │
│                                        │
│  含めるデータ:                          │
│  ☑ ステップ詳細                        │
│  ☑ チャット履歴                        │
│                                        │
├────────────────────────────────────────┤
│  [キャンセル]           [エクスポート]   │
└────────────────────────────────────────┘
```

---

## 7. 画面項目・APIマッピング

### 7.1 セッション複製

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| セッション名 | テキスト | - | POST /session/{id}/duplicate | name | 省略時は自動生成 |
| スナップショット複製 | チェックボックス | - | POST /session/{id}/duplicate | includeSnapshots | デフォルトtrue |
| 複製ボタン | ボタン | - | POST /session/{id}/duplicate | - | - |

### 7.2 ツリー複製

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| ツリー名 | テキスト | - | POST /tree/{id}/duplicate | name | 省略時は自動生成 |
| 複製ボタン | ボタン | - | POST /tree/{id}/duplicate | - | - |

### 7.3 セッションエクスポート

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 値 |
|---------|---------|------------------|-----------------|-----|
| Excel形式 | ラジオ | GET /session/{id}/export | format | xlsx |
| CSV形式 | ラジオ | GET /session/{id}/export | format | csv |
| PDF形式 | ラジオ | GET /session/{id}/export | format | pdf |
| ステップ詳細 | チェックボックス | GET /session/{id}/export | include_steps | true/false |
| チャット履歴 | チェックボックス | GET /session/{id}/export | include_chat | true/false |

### 7.4 ツリーエクスポート

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 値 |
|---------|---------|------------------|-----------------|-----|
| Excel形式 | ラジオ | GET /tree/{id}/output | format | xlsx |
| CSV形式 | ラジオ | GET /tree/{id}/output | format | csv |
| エクスポートボタン | ボタン | GET /tree/{id}/output | - | - |

---

## 8. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|--------|-----|------|-----------|
| CP-001 | 分析セッション複製 | POST /session/{id}/duplicate | sessions | 実装済 |
| CP-002 | ドライバーツリー複製 | POST /tree/{id}/duplicate | trees | 実装済 |
| EX-001 | 分析結果エクスポート | GET /session/{id}/export | analysis | 未実装 |
| EX-002 | ツリー計算結果エクスポート | GET /tree/{id}/output | tree-results | 実装済 |
| EX-003 | ノードデータエクスポート | GET /node/{id}/preview/output | tree-edit | 実装済 |

カバレッジ: 4/5 = 80%（実装済のみ）

---

## 9. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **分析機能設計書**: [../04-analysis/01-analysis-design.md](../04-analysis/01-analysis-design.md)
- **ドライバーツリー設計書**: [../05-driver-tree/01-driver-tree-design.md](../05-driver-tree/01-driver-tree-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 10. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | CE-DESIGN-001 |
| 対象ユースケース | CP-001〜CP-002, EX-001〜EX-003 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/services/analysis/` |
|  | `src/app/services/driver_tree/` |
|  | `src/app/api/routes/v1/analysis/` |
|  | `src/app/api/routes/v1/driver_tree/` |
