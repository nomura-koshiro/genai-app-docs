# ドライバーツリー 統合設計書（DTC-001〜DTP-006）

## 1. 概要

### 1.1 目的

本ドキュメントは、CAMPシステムにおけるドライバーツリー機能の統合設計仕様を定義します。ドライバーツリーは、売上やコストの構造を視覚的に分解し、各ドライバー要素の影響度分析とシミュレーションを可能にするコア機能です。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能名 |
|---------|-------|--------|
| **ツリー作成** | DTC-001 | テンプレートからツリー作成 |
| | DTC-002 | 空のツリーから作成 |
| | DTC-003 | 既存ツリーの複製 |
| **ツリー編集** | DTE-001 | ノード追加 |
| | DTE-002 | ノード削除 |
| | DTE-003 | ノード移動 |
| | DTE-004 | ノード名変更 |
| | DTE-005 | リレーション追加 |
| | DTE-006 | リレーション削除 |
| | DTE-007 | 演算子変更 |
| | DTE-008 | ノードタイプ変更 |
| | DTE-009 | ツリー保存 |
| | DTE-010 | ツリーリセット |
| | DTE-011 | ツリー削除 |
| **ファイル管理** | DTF-001 | ファイルアップロード |
| | DTF-002 | ファイル削除 |
| | DTF-003 | シート選択 |
| | DTF-004 | シート解除 |
| | DTF-005 | シートデータ更新 |
| **カラム設定** | DTA-001 | カラム役割設定 |
| | DTA-002 | データプレビュー |
| **データ紐付け** | DTB-001 | ノードにデータ紐付け |
| | DTB-002 | データ紐付け解除 |
| | DTB-003 | 集計方法設定 |
| **計算** | DTS-001 | ツリー計算実行 |
| | DTS-002 | 計算結果表示 |
| | DTS-003 | ノード別計算結果確認 |
| **シミュレーション** | DTM-001 | 施策適用シミュレーション |
| | DTM-002 | 施策効果比較 |
| | DTM-003 | 感度分析 |
| **エクスポート** | DTO-001 | シミュレーション結果エクスポート |
| | DTO-002 | ノードデータエクスポート |
| **施策管理** | DTP-001 | 施策作成 |
| | DTP-002 | 施策編集 |
| | DTP-003 | 施策削除 |
| | DTP-004 | 施策有効化/無効化 |
| | DTP-005 | 施策一覧表示 |
| | DTP-006 | 施策効果計算 |
| **マスタ参照** | DTR-001 | 業界分類取得 |
| | DTR-002 | 数式テンプレート取得 |
| | DTR-003 | KPI選択肢取得 |

### 1.3 追加コンポーネント数

| コンポーネント | 数量 |
|--------------|------|
| データベーステーブル | 10 |
| APIエンドポイント | 30 |
| Pydanticスキーマ | 50+ |
| フロントエンド画面 | 5 |

---

## 2. データベース設計

データベース設計の詳細は以下を参照してください：

- [データベース設計書 - 3.5 ドライバーツリー](../../../06-database/01-database-design.md#35-ドライバーツリー)

### 2.1 関連テーブル一覧

| テーブル名 | 説明 |
|-----------|------|
| driver_tree | ドライバーツリー本体 |
| driver_tree_node | ツリーノード |
| driver_tree_relationship | ノード間関係（親→子群） |
| driver_tree_relationship_child | 子ノードリスト |
| driver_tree_policy | 施策設定 |
| driver_tree_file | アップロードファイル情報 |
| driver_tree_data_frame | ファイルの列データキャッシュ |
| driver_tree_category | 業界分類マスタ |
| driver_tree_formula | 数式テンプレートマスタ |
| driver_tree_template | ツリーテンプレート（07-template設計書参照） |

---

## 3. APIエンドポイント設計

### 3.1 エンドポイント一覧

#### ツリー管理

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /project/{project_id}/driver-tree/tree | 新規ツリー作成 |
| GET | /project/{project_id}/driver-tree/tree | ツリー一覧取得 |
| GET | /project/{project_id}/driver-tree/tree/{tree_id} | ツリー詳細取得 |
| POST | /project/{project_id}/driver-tree/tree/{tree_id}/import | 数式インポート |
| POST | /project/{project_id}/driver-tree/tree/{tree_id}/reset | ツリーリセット |
| POST | /project/{project_id}/driver-tree/tree/{tree_id}/duplicate | ツリー複製 |
| DELETE | /project/{project_id}/driver-tree/tree/{tree_id} | ツリー削除 |
| GET | /project/{project_id}/driver-tree/tree/{tree_id}/policy | ツリー施策一覧取得 |
| GET | /project/{project_id}/driver-tree/tree/{tree_id}/data | 計算結果取得 |
| GET | /project/{project_id}/driver-tree/tree/{tree_id}/output | シミュレーション結果ダウンロード |

#### マスタデータ

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /project/{project_id}/driver-tree/category | 業界分類一覧取得 |
| GET | /project/{project_id}/driver-tree/formula | 数式取得 |

#### ノード管理

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /project/{project_id}/driver-tree/tree/{tree_id}/node | ノード作成 |
| GET | /project/{project_id}/driver-tree/node/{node_id} | ノード詳細取得 |
| PATCH | /project/{project_id}/driver-tree/node/{node_id} | ノード更新 |
| DELETE | /project/{project_id}/driver-tree/node/{node_id} | ノード削除 |
| GET | /project/{project_id}/driver-tree/node/{node_id}/preview/output | ノードデータダウンロード |

#### 施策管理

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /project/{project_id}/driver-tree/node/{node_id}/policy | 施策作成 |
| GET | /project/{project_id}/driver-tree/node/{node_id}/policy | 施策一覧取得 |
| PATCH | /project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id} | 施策更新 |
| DELETE | /project/{project_id}/driver-tree/node/{node_id}/policy/{policy_id} | 施策削除 |

#### ファイル管理

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /project/{project_id}/driver-tree/file | ファイルアップロード |
| GET | /project/{project_id}/driver-tree/file | ファイル一覧取得 |
| DELETE | /project/{project_id}/driver-tree/file/{file_id} | ファイル削除 |
| GET | /project/{project_id}/driver-tree/sheet | 選択済みシート一覧取得 |
| GET | /project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id} | シート詳細取得 |
| POST | /project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id} | シート選択 |
| POST | /project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}/refresh | シートデータ更新 |
| DELETE | /project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id} | シート選択解除 |
| PATCH | /project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}/column | カラム設定更新 |

### 3.2 リクエスト/レスポンス定義

#### POST /project/{project_id}/driver-tree/tree（新規ツリー作成）

**リクエスト:**

```json
{
  "name": "売上ドライバーツリー",
  "description": "売上構造の分析用ツリー"
}
```

**レスポンス (201):**

```json
{
  "treeId": "uuid",
  "name": "売上ドライバーツリー",
  "description": "売上構造の分析用ツリー",
  "createdAt": "2026-01-01T00:00:00Z"
}
```

#### GET /project/{project_id}/driver-tree/tree（ツリー一覧取得）

**レスポンス (200):**

```json
{
  "trees": [
    {
      "treeId": "uuid",
      "name": "売上ドライバーツリー",
      "description": "売上構造の分析用ツリー",
      "nodeCount": 12,
      "policyCount": 3,
      "status": "active",
      "createdAt": "2026-01-01T00:00:00Z",
      "updatedAt": "2026-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /project/{project_id}/driver-tree/tree/{tree_id}（ツリー詳細取得）

**レスポンス (200):**

```json
{
  "tree": {
    "treeId": "uuid",
    "name": "売上ドライバーツリー",
    "description": "説明",
    "status": "active",
    "rootNodeId": "uuid",
    "nodes": [
      {
        "nodeId": "uuid",
        "label": "売上高",
        "nodeType": "calculation",
        "positionX": 400,
        "positionY": 50
      }
    ],
    "relationships": [
      {
        "relationshipId": "uuid",
        "parentNodeId": "uuid",
        "childNodeIds": ["uuid", "uuid"],
        "operator": "*"
      }
    ]
  }
}
```

#### POST /project/{project_id}/driver-tree/tree/{tree_id}/import（数式インポート）

**リクエスト:**

```json
{
  "positionX": 400,
  "positionY": 50,
  "formulas": [
    "売上 = 顧客数 * 顧客単価",
    "顧客数 = 新規顧客 + 既存顧客",
    "顧客単価 = 購入頻度 * 平均購入額"
  ],
  "sheetId": "uuid"
}
```

**レスポンス (201):**

```json
{
  "tree": {
    "treeId": "uuid",
    "nodes": [...],
    "relationships": [...]
  }
}
```

#### POST /project/{project_id}/driver-tree/tree/{tree_id}/node（ノード作成）

**リクエスト:**

```json
{
  "label": "新規顧客",
  "nodeType": "input",
  "positionX": 200,
  "positionY": 200
}
```

**レスポンス (201):**

```json
{
  "tree": {...},
  "createdNodeId": "uuid"
}
```

#### POST /project/{project_id}/driver-tree/node/{node_id}/policy（施策作成）

**リクエスト:**

```json
{
  "name": "新規顧客獲得キャンペーン",
  "value": 15.0
}
```

**レスポンス (201):**

```json
{
  "nodeId": "uuid",
  "policies": [
    {
      "policyId": "uuid",
      "name": "新規顧客獲得キャンペーン",
      "value": 15.0
    }
  ]
}
```

#### GET /project/{project_id}/driver-tree/tree/{tree_id}/data（計算結果取得）

**レスポンス (200):**

```json
{
  "calculatedDataList": [
    {
      "nodeId": "uuid",
      "label": "売上高",
      "columns": ["月", "値"],
      "records": [
        {"月": "2025-01", "値": 10000000},
        {"月": "2025-02", "値": 12000000}
      ]
    }
  ]
}
```

#### GET /project/{project_id}/driver-tree/category（業界分類一覧取得）

**レスポンス (200):**

```json
{
  "categories": [
    {
      "categoryId": 1,
      "categoryName": "小売・EC",
      "industries": [
        {
          "industryId": 1,
          "industryName": "EC（総合）",
          "driverTypes": [
            {
              "driverTypeId": 1,
              "driverType": "売上分解モデル（基本）"
            }
          ]
        }
      ]
    }
  ]
}
```

#### GET /project/{project_id}/driver-tree/formula（数式取得）

**クエリパラメータ:**

- driver_type_id: int（必須）
- kpi: string（必須、売上|原価|販管費|粗利|営業利益|EBITDA）

**レスポンス (200):**

```json
{
  "formula": {
    "formulaId": "uuid",
    "driverTypeId": 1,
    "driverType": "売上分解モデル（基本）",
    "kpi": "売上",
    "formulas": [
      "売上 = 顧客数 * 顧客単価",
      "顧客数 = 新規顧客 + 既存顧客"
    ]
  }
}
```

---

## 4. Pydanticスキーマ設計

### 4.1 Enum定義

```python
class DriverTreeNodeTypeEnum(str, Enum):
    """ノードタイプ"""
    calculation = "calculation"  # 計算
    input = "input"              # 入力
    constant = "constant"        # 定数

class DriverTreeColumnRoleEnum(str, Enum):
    """カラム役割"""
    transition = "推移"   # 時系列軸
    axis = "軸"           # 分類軸
    value = "値"          # 値
    unused = "利用しない"  # 使用しない

class DriverTreeKpiEnum(str, Enum):
    """KPI種別"""
    sales = "売上"
    cost = "原価"
    sg_and_a = "販管費"
    gross_profit = "粗利"
    operating_income = "営業利益"
    ebitda = "EBITDA"
```

### 4.2 Info/Dataスキーマ

```python
class DriverTreeInfo(CamelCaseModel):
    """ツリー情報"""
    tree_id: UUID
    name: str
    description: str = ""
    status: str = "draft"
    root_node_id: UUID | None = None
    nodes: list[DriverTreeNodeInfo] = []
    relationships: list[DriverTreeRelationshipInfo] = []

class DriverTreeNodeInfo(CamelCaseModel):
    """ノード情報"""
    node_id: UUID
    label: str
    node_type: DriverTreeNodeTypeEnum
    position_x: int = 0
    position_y: int = 0
    data: DriverTreeNodeData | None = None

class DriverTreeNodeData(CamelCaseModel):
    """ノードデータ"""
    columns: list[str]
    records: list[dict[str, Any]]

class DriverTreeRelationshipInfo(CamelCaseModel):
    """リレーション情報"""
    relationship_id: UUID
    parent_node_id: UUID
    child_node_ids: list[UUID]
    operator: str | None = None

class DriverTreeNodePolicyInfo(CamelCaseModel):
    """施策情報"""
    policy_id: UUID
    name: str
    value: float
    description: str | None = None
    cost: float | None = None
    duration_months: int | None = None
    status: str = "planned"

class CategoryInfo(CamelCaseModel):
    """業界分類情報"""
    category_id: int
    category_name: str
    industries: list[IndustryInfo]

class IndustryInfo(CamelCaseModel):
    """業界情報"""
    industry_id: int
    industry_name: str
    driver_types: list[DriverTypeInfo]

class DriverTypeInfo(CamelCaseModel):
    """ドライバー型情報"""
    driver_type_id: int
    driver_type: str

class FormulaInfo(CamelCaseModel):
    """数式情報"""
    formula_id: UUID
    driver_type_id: int
    driver_type: str
    kpi: str
    formulas: list[str]
```

### 4.3 Request/Responseスキーマ

```python
# ツリー
class DriverTreeCreateTreeRequest(CamelCaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""

class DriverTreeCreateTreeResponse(CamelCaseModel):
    tree_id: UUID
    name: str
    description: str
    created_at: datetime

class DriverTreeListResponse(CamelCaseModel):
    trees: list[DriverTreeListItem]

class DriverTreeGetTreeResponse(CamelCaseModel):
    tree: DriverTreeInfo

class DriverTreeImportFormulaRequest(CamelCaseModel):
    position_x: int = 0
    position_y: int = 0
    formulas: list[str]
    sheet_id: UUID | None = None

# ノード
class DriverTreeCreateNodeRequest(CamelCaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    node_type: DriverTreeNodeTypeEnum
    position_x: int = 0
    position_y: int = 0

class DriverTreeNodeUpdateRequest(CamelCaseModel):
    label: str | None = None
    node_type: DriverTreeNodeTypeEnum | None = None
    position_x: int | None = None
    position_y: int | None = None
    operator: str | None = None
    children_id_list: list[UUID] | None = None

# 施策
class DriverTreeNodePolicyCreateRequest(CamelCaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    value: float

class DriverTreeNodePolicyUpdateRequest(CamelCaseModel):
    name: str | None = None
    value: float | None = None

# ファイル
class DriverTreeColumnSetupItem(CamelCaseModel):
    column_id: UUID
    role: DriverTreeColumnRoleEnum

class DriverTreeColumnSetupRequest(CamelCaseModel):
    columns: list[DriverTreeColumnSetupItem]
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| DriverTreeService | ツリーCRUD、計算、エクスポート |
| DriverTreeNodeService | ノードCRUD、施策管理 |
| DriverTreeFileService | ファイル/シート管理、カラム設定 |

### 5.2 主要メソッド

#### DriverTreeService

```python
class DriverTreeService:
    # ツリーCRUD
    async def create_tree(project_id, name, description, user_id) -> dict
    async def list_trees(project_id, user_id) -> dict
    async def get_tree(project_id, tree_id, user_id) -> dict
    async def reset_tree(project_id, tree_id, user_id) -> dict
    async def delete_tree(project_id, tree_id, user_id) -> dict
    async def duplicate_tree(project_id, tree_id, user_id) -> dict

    # 数式インポート
    async def import_formula(project_id, tree_id, position_x, position_y, formulas, sheet_id, user_id) -> dict

    # マスタ
    async def get_categories(project_id, user_id) -> dict
    async def get_formulas(project_id, driver_type_id, kpi, user_id) -> dict

    # 計算・エクスポート
    async def get_tree_data(project_id, tree_id, user_id) -> dict
    async def get_tree_policies(project_id, tree_id, user_id) -> dict
    async def download_simulation_output(project_id, tree_id, format, user_id) -> StreamingResponse
```

#### DriverTreeNodeService

```python
class DriverTreeNodeService:
    # ノードCRUD
    async def create_node(project_id, tree_id, label, node_type, position_x, position_y, user_id) -> dict
    async def get_node(project_id, node_id, user_id) -> dict
    async def update_node(project_id, node_id, label, node_type, position_x, position_y, operator, children_id_list, user_id) -> dict
    async def delete_node(project_id, node_id, user_id) -> dict
    async def download_node_preview(project_id, node_id, user_id) -> StreamingResponse

    # 施策管理
    async def create_policy(project_id, node_id, name, value, user_id) -> dict
    async def list_policies(project_id, node_id, user_id) -> dict
    async def update_policy(project_id, node_id, policy_id, name, value, user_id) -> dict
    async def delete_policy(project_id, node_id, policy_id, user_id) -> dict
```

#### DriverTreeFileService

```python
class DriverTreeFileService:
    # ファイル管理
    async def upload_file(project_id, file, user_id) -> dict
    async def list_uploaded_files(project_id, user_id) -> dict
    async def delete_file(project_id, file_id, user_id) -> dict

    # シート管理
    async def list_selected_sheets(project_id, user_id) -> dict
    async def get_sheet_detail(project_id, file_id, sheet_id, user_id) -> dict
    async def select_sheet(project_id, file_id, sheet_id, user_id) -> dict
    async def refresh_sheet(project_id, file_id, sheet_id, user_id) -> dict
    async def delete_sheet(project_id, file_id, sheet_id, user_id) -> dict

    # カラム設定
    async def update_column_config(project_id, file_id, sheet_id, columns, user_id) -> dict
```

---

## 6. フロントエンド設計

### 6.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| trees | ドライバーツリー一覧 | /projects/{id}/trees | ツリー一覧表示 |
| tree-new | ツリー作成 | /projects/{id}/trees/new | テンプレート選択・新規作成 |
| tree-edit | ツリー編集 | /projects/{id}/trees/{treeId} | ツリー編集画面 |
| tree-policies | 施策設定 | /projects/{id}/trees/{treeId}/policies | 施策一覧・編集 |
| tree-data-binding | データ紐付け | /projects/{id}/trees/{treeId}/data-binding | データ紐付け設定 |
| tree-results | 計算結果 | /projects/{id}/trees/{treeId}/results | 計算結果・シミュレーション |

### 6.2 コンポーネント構成

```text
features/driver-tree/
├── components/
│   ├── TreeList/
│   │   ├── TreeList.tsx
│   │   └── TreeListItem.tsx
│   ├── TreeCanvas/
│   │   ├── TreeCanvas.tsx
│   │   ├── TreeNode.tsx
│   │   ├── TreeConnection.tsx
│   │   └── TreeToolbar.tsx
│   ├── NodeEditor/
│   │   ├── NodeEditor.tsx
│   │   └── NodeTypeSelector.tsx
│   ├── PolicyEditor/
│   │   ├── PolicyList.tsx
│   │   ├── PolicyCard.tsx
│   │   └── PolicyModal.tsx
│   ├── DataBinding/
│   │   ├── DataSourceSelector.tsx
│   │   ├── NodeBindingTable.tsx
│   │   └── ColumnRoleSelector.tsx
│   ├── Results/
│   │   ├── ResultsSummary.tsx
│   │   ├── NodeCalculationTable.tsx
│   │   └── PolicyEffectChart.tsx
│   └── TemplateSelector/
│       ├── TemplateGrid.tsx
│       ├── TemplateCard.tsx
│       └── TemplatePreview.tsx
├── hooks/
│   ├── useDriverTree.ts
│   ├── useDriverTreeNodes.ts
│   ├── useDriverTreePolicies.ts
│   ├── useDriverTreeFiles.ts
│   └── useTreeCalculation.ts
├── api/
│   ├── driverTreeApi.ts
│   ├── driverTreeNodeApi.ts
│   └── driverTreeFileApi.ts
└── types/
    └── driverTree.ts
```

---

## 7. 画面項目・APIマッピング

### 7.1 ドライバーツリー一覧画面（trees）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ツリー名 | テキスト（リンク） | GET /driver-tree/tree | trees[].name | - |
| 数式マスタ | テキスト | GET /driver-tree/tree | trees[].formulaName | formulaId→名前解決 |
| ノード数 | 数値 | GET /driver-tree/tree | trees[].nodeCount | - |
| 施策数 | 数値 | GET /driver-tree/tree | trees[].policyCount | - |
| 更新日時 | 日時 | GET /driver-tree/tree | trees[].updatedAt | ISO8601→YYYY/MM/DD HH:mm |
| 編集ボタン | ボタン | - | - | tree-edit画面へ遷移 |
| 複製ボタン | ボタン | POST /driver-tree/tree/{id}/duplicate | - | 確認ダイアログ後実行 |
| 新規作成ボタン | ボタン | - | - | tree-new画面へ遷移 |

### 7.2 ツリー作成画面（tree-new）

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| 業種フィルター | チップ選択 | - | GET /driver-tree/category | （クエリ用） | - |
| 分析タイプフィルター | チップ選択 | - | GET /driver-tree/category | （クエリ用） | - |
| テンプレートカード | 選択カード | - | GET /driver-tree/category | - | - |
| テンプレート人気バッジ | バッジ | - | - | - | 人気テンプレートに表示 |
| テンプレート利用実績 | テキスト | - | - | - | "利用実績: n+" 形式 |
| ツリー名 | テキスト入力 | ○ | POST /driver-tree/tree | name | 1-255文字 |
| 説明 | テキストエリア | - | POST /driver-tree/tree | description | 任意 |
| 選択中のテンプレート | 表示 | - | - | - | テンプレート名とアイコン |
| 構造プレビュー | ツリービュー | - | - | - | テンプレートのノード構造 |
| キャンセルボタン | ボタン | - | - | - | ツリー一覧に戻る |
| 作成して編集ボタン | ボタン | - | POST /driver-tree/tree + POST /import | - | - |

### 7.3 ツリー編集画面（tree-edit）

#### 共通タブナビゲーション

| タブ名 | 遷移先 | 説明 |
|--------|--------|------|
| ツリー編集 | tree-edit | ツリー構造の編集（アクティブ） |
| 施策設定 | tree-policies | 施策の追加・編集 |
| データ紐付け | tree-data-binding | ノードへのデータ紐付け |
| 計算結果 | tree-results | 計算結果とシミュレーション |

#### 画面項目

| 画面項目 | 入力/表示形式 | APIエンドポイント | フィールド | 変換処理/バリデーション |
|---------|-------------|------------------|-----------|----------------------|
| ツリー名 | 表示 | GET /driver-tree/tree/{id} | tree.name | - |
| ツールバー（ノード追加） | ボタン | POST /driver-tree/tree/{id}/node | label, nodeType, positionX, positionY | - |
| ツールバー（リレーション追加） | ボタン | - | - | リレーション作成モード |
| ツールバー（整列） | ボタン | - | - | ノード自動配置 |
| ツールバー（ズームイン） | ボタン | - | - | キャンバス拡大 |
| ツールバー（ズームアウト） | ボタン | - | - | キャンバス縮小 |
| ノード（ビジュアル） | キャンバス | GET /driver-tree/tree/{id} | tree.nodes[] | position_x/y→座標 |
| 接続線 | SVG | GET /driver-tree/tree/{id} | tree.relationships[] | 親子座標から算出 |
| ノードラベル | テキスト入力 | PATCH /driver-tree/node/{id} | label | 1-255文字 |
| ノードタイプ | セレクト | PATCH /driver-tree/node/{id} | nodeType | driver/kpi/metric |
| データフレーム紐付け | セレクト | PATCH /driver-tree/node/{id} | dataFrameId | - |
| 保存ボタン | ボタン | PATCH /driver-tree/node/{id} | - | - |
| データ取込ボタン | ボタン | - | - | tree-data-binding画面へ |

### 7.4 施策設定画面（tree-policies）

#### 共通タブナビゲーション

| タブ名 | 遷移先 | 説明 |
|--------|--------|------|
| ツリー編集 | tree-edit | ツリー構造の編集 |
| 施策設定 | tree-policies | 施策の追加・編集（アクティブ） |
| データ紐付け | tree-data-binding | ノードへのデータ紐付け |
| 計算結果 | tree-results | 計算結果とシミュレーション |

#### 画面項目

| 画面項目 | 表示/入力形式 | APIエンドポイント | フィールド | 変換処理/バリデーション |
|---------|-------------|------------------|-----------|----------------------|
| 施策カード一覧 | カードリスト | GET /driver-tree/tree/{id}/policy | policies[] | - |
| 施策アイコン | アイコン | - | - | 施策タイプに応じた絵文字 |
| 施策名 | テキスト | GET/PATCH | policies[].label | - |
| 対象ノード | テキスト | GET | policies[].nodeLabel | nodeId→ラベル解決 |
| 影響値 | 数値+% | GET/PATCH | policies[].value | 正負で色分け |
| コスト | 通貨表示 | GET/PATCH | policies[].cost | ¥フォーマット |
| 期間 | テキスト | GET/PATCH | policies[].durationMonths | n + "ヶ月" |
| ステータス | バッジ | GET/PATCH | policies[].status | planned/in_progress/completed |
| 編集ボタン | ボタン | - | - | モーダル表示 |
| 削除ボタン | ボタン | DELETE /driver-tree/node/{id}/policy/{id} | - | 確認ダイアログ |
| 新規施策ボタン | ボタン | POST /driver-tree/node/{id}/policy | name, value | モーダルフォーム |

#### 施策追加モーダル

| 画面項目 | 入力形式 | 必須 | リクエストフィールド | バリデーション |
|---------|---------|------|---------------------|---------------|
| 施策名 | テキスト | ○ | name | 1-255文字 |
| 対象ノード | セレクト | ○ | nodeId（パス） | ノード一覧から選択 |
| 影響値 | 数値 | ○ | value | 数値（正負可） |
| コスト | 数値 | - | cost | 正の数値 |
| 実施期間 | セレクト | - | durationMonths | 1/3/6/12 |
| 説明 | テキストエリア | - | description | 任意 |

### 7.5 データ紐付け画面（tree-data-binding）

#### 共通タブナビゲーション

| タブ名 | 遷移先 | 説明 |
|--------|--------|------|
| ツリー編集 | tree-edit | ツリー構造の編集 |
| 施策設定 | tree-policies | 施策の追加・編集 |
| データ紐付け | tree-data-binding | ノードへのデータ紐付け（アクティブ） |
| 計算結果 | tree-results | 計算結果とシミュレーション |

#### 画面項目

| 画面項目 | 表示/入力形式 | APIエンドポイント | フィールド | 変換処理/バリデーション |
|---------|-------------|------------------|-----------|----------------------|
| ファイル選択 | セレクト | GET /driver-tree/file | files[] | - |
| シート選択 | セレクト | GET /driver-tree/file | files[].sheets[] | - |
| 期間選択 | セレクト | - | - | フロントエンドフィルター |
| ノード一覧テーブル | テーブル | GET /driver-tree/tree/{id} | tree.nodes[] | - |
| ノード名 | テキスト | - | nodes[].label | 階層インデント |
| タイプ | バッジ | - | nodes[].nodeType | root/計算/データ/未設定 |
| データ列 | セレクト | GET /driver-tree/sheet | columns[] | シートのカラム一覧 |
| 集計方法 | セレクト | PATCH | - | 合計/平均/最新 |
| 現在値 | 数値 | GET /driver-tree/tree/{id}/data | - | 計算結果表示 |
| ステータス | バッジ | - | - | 紐付済/計算済/未紐付 |
| データ更新ボタン | ボタン | POST /sheet/{id}/refresh | - | - |
| 保存ボタン | ボタン | PATCH /driver-tree/file/{id}/sheet/{id}/column | columns[] | - |

### 7.6 計算結果画面（tree-results）

#### 共通タブナビゲーション

| タブ名 | 遷移先 | 説明 |
|--------|--------|------|
| ツリー編集 | tree-edit | ツリー構造の編集 |
| 施策設定 | tree-policies | 施策の追加・編集 |
| データ紐付け | tree-data-binding | ノードへのデータ紐付け |
| 計算結果 | tree-results | 計算結果とシミュレーション（アクティブ） |

#### 画面項目

| 画面項目 | 表示形式 | APIエンドポイント | フィールド | 変換処理 |
|---------|---------|------------------|-----------|---------|
| 現在の売上高 | サマリカード | GET /driver-tree/tree/{id}/data | calculatedDataList[0] | ルートノード値 |
| 施策適用後 | サマリカード | GET /driver-tree/tree/{id}/data | （計算値） | シミュレーション結果 |
| 増加額 | サマリカード | - | - | 施策後 - 現在 |
| 施策コスト合計 | サマリカード | GET /driver-tree/tree/{id}/policy | sum(policies[].cost) | ¥フォーマット |
| ノード別計算結果テーブル | テーブル | GET /driver-tree/tree/{id}/data | calculatedDataList[] | - |
| 施策効果比較 | 棒グラフ | GET /driver-tree/tree/{id}/policy | policies[] + 計算 | ROI算出 |
| エクスポートボタン | ボタン | GET /driver-tree/tree/{id}/output | - | ファイルダウンロード |
| 再計算ボタン | ボタン | GET /driver-tree/tree/{id}/data | - | 最新データで再計算 |

---

## 8. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|--------|-----|------|-----------|
| DTC-001 | テンプレートからツリー作成 | POST /tree + POST /import | tree-new | 実装済 |
| DTC-002 | 空のツリーから作成 | POST /tree | tree-new | 実装済 |
| DTC-003 | 既存ツリーの複製 | POST /tree/{id}/duplicate | trees | 実装済 |
| DTE-001 | ノード追加 | POST /tree/{id}/node | tree-edit | 実装済 |
| DTE-002 | ノード削除 | DELETE /node/{id} | tree-edit | 実装済 |
| DTE-003 | ノード移動 | PATCH /node/{id} | tree-edit | 実装済 |
| DTE-004 | ノード名変更 | PATCH /node/{id} | tree-edit | 実装済 |
| DTE-005 | リレーション追加 | PATCH /node/{id} | tree-edit | 実装済 |
| DTE-006 | リレーション削除 | PATCH /node/{id} | tree-edit | 実装済 |
| DTE-007 | 演算子変更 | PATCH /node/{id} | tree-edit | 実装済 |
| DTE-008 | ノードタイプ変更 | PATCH /node/{id} | tree-edit | 実装済 |
| DTE-009 | ツリー保存 | PATCH /node/{id} | tree-edit | 実装済 |
| DTE-010 | ツリーリセット | POST /tree/{id}/reset | tree-edit | 実装済 |
| DTE-011 | ツリー削除 | DELETE /tree/{id} | trees | 実装済 |
| DTF-001 | ファイルアップロード | POST /file | tree-data-binding | 実装済 |
| DTF-002 | ファイル削除 | DELETE /file/{id} | tree-data-binding | 実装済 |
| DTF-003 | シート選択 | POST /file/{id}/sheet/{id} | tree-data-binding | 実装済 |
| DTF-004 | シート解除 | DELETE /file/{id}/sheet/{id} | tree-data-binding | 実装済 |
| DTF-005 | シートデータ更新 | POST /sheet/{id}/refresh | tree-data-binding | 実装済 |
| DTA-001 | カラム役割設定 | PATCH /sheet/{id}/column | tree-data-binding | 実装済 |
| DTA-002 | データプレビュー | GET /sheet/{id} | tree-data-binding | 実装済 |
| DTB-001 | ノードにデータ紐付け | PATCH /node/{id} | tree-data-binding | 実装済 |
| DTB-002 | データ紐付け解除 | PATCH /node/{id} | tree-data-binding | 実装済 |
| DTB-003 | 集計方法設定 | PATCH /node/{id} | tree-data-binding | 実装予定 |
| DTS-001 | ツリー計算実行 | GET /tree/{id}/data | tree-results | 実装済 |
| DTS-002 | 計算結果表示 | GET /tree/{id}/data | tree-results | 実装済 |
| DTS-003 | ノード別計算結果確認 | GET /tree/{id}/data | tree-results | 実装済 |
| DTM-001 | 施策適用シミュレーション | GET /tree/{id}/data + policies | tree-results | 実装済 |
| DTM-002 | 施策効果比較 | GET /tree/{id}/policy | tree-results | 実装済 |
| DTM-003 | 感度分析 | - | - | 実装予定 |
| DTO-001 | シミュレーション結果エクスポート | GET /tree/{id}/output | tree-results | 実装済 |
| DTO-002 | ノードデータエクスポート | GET /node/{id}/preview/output | tree-edit | 実装済 |
| DTP-001 | 施策作成 | POST /node/{id}/policy | tree-policies | 実装済 |
| DTP-002 | 施策編集 | PATCH /node/{id}/policy/{id} | tree-policies | 実装済 |
| DTP-003 | 施策削除 | DELETE /node/{id}/policy/{id} | tree-policies | 実装済 |
| DTP-004 | 施策有効化/無効化 | PATCH /node/{id}/policy/{id} | tree-policies | 実装済 |
| DTP-005 | 施策一覧表示 | GET /tree/{id}/policy | tree-policies | 実装済 |
| DTP-006 | 施策効果計算 | GET /tree/{id}/data | tree-results | 実装済 |
| DTR-001 | 業界分類取得 | GET /category | tree-new | 実装済 |
| DTR-002 | 数式テンプレート取得 | GET /formula | tree-new | 実装済 |
| DTR-003 | KPI選択肢取得 | GET /formula (query) | tree-new | 実装済 |

カバレッジ: 41/41 = 100%

---

## 9. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/pages/projects.js](../../03-mockup/pages/projects.js)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

### ドキュメント管理情報

- **作成日**: 2026年1月1日
- **更新日**: 2026年1月1日
- **対象ソースコード**:
  - モデル: `src/app/models/driver_tree/`
  - スキーマ: `src/app/schemas/driver_tree/`
  - API: `src/app/api/routes/v1/driver_tree/`
