# テンプレート機能 統合設計書（TM-001〜TM-005）

## 1. 概要

### 1.1 目的

本ドキュメントは、CAMPシステムにおけるテンプレート機能の統合設計仕様を定義します。テンプレート機能は、分析セッションやドライバーツリーの構成を再利用可能なテンプレートとして保存・共有し、効率的な分析開始を支援します。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能名 |
|---------|-------|--------|
| **テンプレート管理** | TM-001 | テンプレート一覧表示 |
| | TM-002 | テンプレート作成（セッションから） |
| | TM-003 | テンプレート作成（ツリーから） |
| | TM-004 | テンプレート適用 |
| | TM-005 | テンプレート削除 |

### 1.3 追加コンポーネント数

| コンポーネント | 数量 | 備考 |
|--------------|------|------|
| データベーステーブル | 2 | 実装済 |
| APIエンドポイント | 7 | 実装済: 7/7 |
| Pydanticスキーマ | 10 | 実装済 |
| フロントエンド画面 | 2 | 未実装 |

---

## 2. データベース設計

### 2.1 テーブル一覧

| テーブル名 | 説明 |
|-----------|------|
| analysis_template | 分析セッションテンプレート |
| driver_tree_template | ドライバーツリーテンプレート |

### 2.2 ER図

```text
project ──1:N── analysis_template
                    │
                    └── template_config (JSONB)

project ──1:N── driver_tree_template
                    │
                    └── template_config (JSONB)
```

### 2.3 テーブル詳細

#### analysis_template（分析セッションテンプレート）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid4() | 主キー |
| project_id | UUID | YES | NULL | プロジェクトID（NULL=グローバル） |
| name | VARCHAR(255) | NO | - | テンプレート名 |
| description | TEXT | YES | NULL | 説明 |
| template_type | VARCHAR(50) | NO | - | テンプレートタイプ（session/step） |
| template_config | JSONB | NO | - | テンプレート設定 |
| source_session_id | UUID | YES | NULL | 元セッションID |
| is_public | BOOLEAN | NO | false | 公開フラグ |
| usage_count | INTEGER | NO | 0 | 使用回数 |
| created_by | UUID | YES | NULL | 作成者ID |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

**インデックス:**

- idx_analysis_template_project_id (project_id)
- idx_analysis_template_type (template_type)
- idx_analysis_template_public (is_public)

**template_config構造（session型）:**

```json
{
  "initialPrompt": "分析の初期プロンプト",
  "steps": [
    {
      "stepNumber": 1,
      "title": "データ読み込み",
      "description": "ファイルを読み込みます"
    }
  ],
  "defaultFileTypes": ["xlsx", "csv"],
  "analysisType": "売上分析"
}
```

#### driver_tree_template（ドライバーツリーテンプレート）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid4() | 主キー |
| project_id | UUID | YES | NULL | プロジェクトID（NULL=グローバル） |
| name | VARCHAR(255) | NO | - | テンプレート名 |
| description | TEXT | YES | NULL | 説明 |
| category | VARCHAR(100) | YES | NULL | カテゴリ（業種） |
| template_config | JSONB | NO | - | テンプレート設定 |
| source_tree_id | UUID | YES | NULL | 元ツリーID |
| is_public | BOOLEAN | NO | false | 公開フラグ |
| usage_count | INTEGER | NO | 0 | 使用回数 |
| created_by | UUID | YES | NULL | 作成者ID |
| created_at | TIMESTAMP | NO | now() | 作成日時 |
| updated_at | TIMESTAMP | NO | now() | 更新日時 |

**インデックス:**

- idx_driver_tree_template_project_id (project_id)
- idx_driver_tree_template_category (category)
- idx_driver_tree_template_public (is_public)

**template_config構造:**

```json
{
  "nodes": [
    {
      "label": "売上高",
      "nodeType": "calculation",
      "relativeX": 0,
      "relativeY": 0
    },
    {
      "label": "顧客数",
      "nodeType": "input",
      "relativeX": -100,
      "relativeY": 100
    }
  ],
  "relationships": [
    {
      "parentLabel": "売上高",
      "childLabels": ["顧客数", "顧客単価"],
      "operator": "*"
    }
  ],
  "formulas": [
    "売上高 = 顧客数 * 顧客単価"
  ]
}
```

---

## 3. APIエンドポイント設計

### 3.1 エンドポイント一覧

#### 分析セッションテンプレート

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/v1/project/{project_id}/analysis/template | テンプレート一覧取得 |
| GET | /api/v1/project/{project_id}/analysis/template/{issue_id} | テンプレート詳細取得 |
| POST | /api/v1/project/{project_id}/analysis/template | テンプレート作成 |
| DELETE | /api/v1/project/{project_id}/analysis/template/{template_id} | テンプレート削除 |

#### ドライバーツリーテンプレート

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/v1/project/{project_id}/driver-tree/template | テンプレート一覧取得 |
| POST | /api/v1/project/{project_id}/driver-tree/template | テンプレート作成 |
| DELETE | /api/v1/project/{project_id}/driver-tree/template/{template_id} | テンプレート削除 |

### 3.2 リクエスト/レスポンス定義

#### GET /project/{project_id}/analysis/template（テンプレート一覧取得）

**クエリパラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| include_public | bool | - | true | 公開テンプレートを含める |
| template_type | string | - | - | フィルター（session/step） |

**レスポンス (200):**

```json
{
  "templates": [
    {
      "templateId": "uuid",
      "name": "売上分析テンプレート",
      "description": "四半期売上分析用のテンプレート",
      "templateType": "session",
      "isPublic": true,
      "usageCount": 15,
      "createdBy": "uuid",
      "createdByName": "山田 太郎",
      "createdAt": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 10
}
```

#### POST /project/{project_id}/analysis/template（テンプレート作成）

**リクエスト:**

```json
{
  "name": "売上分析テンプレート",
  "description": "四半期売上分析用のテンプレート",
  "sourceSessionId": "uuid",
  "isPublic": false
}
```

**レスポンス (201):**

```json
{
  "templateId": "uuid",
  "name": "売上分析テンプレート",
  "description": "四半期売上分析用のテンプレート",
  "templateType": "session",
  "templateConfig": {...},
  "createdAt": "2026-01-01T00:00:00Z"
}
```

#### POST /project/{project_id}/driver-tree/template（ツリーテンプレート作成）

**リクエスト:**

```json
{
  "name": "EC売上モデル",
  "description": "EC事業の売上分解テンプレート",
  "category": "小売・EC",
  "sourceTreeId": "uuid",
  "isPublic": true
}
```

**レスポンス (201):**

```json
{
  "templateId": "uuid",
  "name": "EC売上モデル",
  "description": "EC事業の売上分解テンプレート",
  "category": "小売・EC",
  "templateConfig": {...},
  "nodeCount": 8,
  "createdAt": "2026-01-01T00:00:00Z"
}
```

#### DELETE /project/{project_id}/analysis/template/{template_id}（テンプレート削除）

**レスポンス (200):**

```json
{
  "success": true,
  "deletedAt": "2026-01-01T00:00:00Z"
}
```

---

## 4. Pydanticスキーマ設計

### 4.1 分析テンプレートスキーマ

```python
class AnalysisTemplateInfo(BaseCamelCaseModel):
    """分析テンプレート情報"""
    template_id: UUID
    name: str
    description: str | None = None
    template_type: str
    is_public: bool = False
    usage_count: int = 0
    created_by: UUID | None = None
    created_by_name: str | None = None
    created_at: datetime

class AnalysisTemplateConfig(BaseCamelCaseModel):
    """分析テンプレート設定"""
    initial_prompt: str | None = None
    steps: list[dict] = []
    default_file_types: list[str] = []
    analysis_type: str | None = None

class AnalysisTemplateCreateRequest(BaseCamelCaseModel):
    """分析テンプレート作成リクエスト"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    source_session_id: UUID
    is_public: bool = False

class AnalysisTemplateListResponse(BaseCamelCaseModel):
    """分析テンプレート一覧レスポンス"""
    templates: list[AnalysisTemplateInfo] = []
    total: int
```

### 4.2 ドライバーツリーテンプレートスキーマ

```python
class DriverTreeTemplateInfo(BaseCamelCaseModel):
    """ドライバーツリーテンプレート情報"""
    template_id: UUID
    name: str
    description: str | None = None
    category: str | None = None
    node_count: int = 0
    is_public: bool = False
    usage_count: int = 0
    created_by: UUID | None = None
    created_by_name: str | None = None
    created_at: datetime

class DriverTreeTemplateConfig(BaseCamelCaseModel):
    """ドライバーツリーテンプレート設定"""
    nodes: list[dict] = []
    relationships: list[dict] = []
    formulas: list[str] = []

class DriverTreeTemplateCreateRequest(BaseCamelCaseModel):
    """ドライバーツリーテンプレート作成リクエスト"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    source_tree_id: UUID
    is_public: bool = False

class DriverTreeTemplateListResponse(BaseCamelCaseModel):
    """ドライバーツリーテンプレート一覧レスポンス"""
    templates: list[DriverTreeTemplateInfo] = []
    total: int
```

---

## 5. サービス層設計

### 5.1 サービスクラス

```python
class AnalysisTemplateService:
    """分析テンプレートサービス"""

    async def list_templates(
        self,
        project_id: UUID,
        include_public: bool = True,
        template_type: str | None = None
    ) -> AnalysisTemplateListResponse:
        """テンプレート一覧を取得"""
        ...

    async def create_template(
        self,
        project_id: UUID,
        name: str,
        description: str | None,
        source_session_id: UUID,
        is_public: bool,
        user_id: UUID
    ) -> AnalysisTemplateInfo:
        """セッションからテンプレートを作成"""
        # 1. 元セッションの取得
        # 2. テンプレート設定の抽出
        # 3. テンプレートの保存
        ...

    async def delete_template(
        self,
        project_id: UUID,
        template_id: UUID,
        user_id: UUID
    ) -> dict:
        """テンプレートを削除"""
        ...

    async def apply_template(
        self,
        project_id: UUID,
        template_id: UUID,
        session_name: str,
        user_id: UUID
    ) -> dict:
        """テンプレートを適用してセッション作成"""
        ...


class DriverTreeTemplateService:
    """ドライバーツリーテンプレートサービス"""

    async def list_templates(
        self,
        project_id: UUID,
        include_public: bool = True,
        category: str | None = None
    ) -> DriverTreeTemplateListResponse:
        """テンプレート一覧を取得"""
        ...

    async def create_template(
        self,
        project_id: UUID,
        name: str,
        description: str | None,
        category: str | None,
        source_tree_id: UUID,
        is_public: bool,
        user_id: UUID
    ) -> DriverTreeTemplateInfo:
        """ツリーからテンプレートを作成"""
        # 1. 元ツリーとノード・リレーションの取得
        # 2. テンプレート設定の抽出（相対座標変換）
        # 3. テンプレートの保存
        ...

    async def delete_template(
        self,
        project_id: UUID,
        template_id: UUID,
        user_id: UUID
    ) -> dict:
        """テンプレートを削除"""
        ...

    async def apply_template(
        self,
        project_id: UUID,
        template_id: UUID,
        tree_name: str,
        position_x: int,
        position_y: int,
        user_id: UUID
    ) -> dict:
        """テンプレートを適用してツリー作成"""
        ...
```

---

## 6. フロントエンド設計

### 6.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| templates | テンプレート一覧 | /projects/{id}/templates | テンプレート管理画面 |
| template-select | テンプレート選択 | - | モーダル/ドロワー |

### 6.2 コンポーネント構成

```text
features/templates/
├── components/
│   ├── TemplateList/
│   │   ├── TemplateList.tsx
│   │   ├── TemplateCard.tsx
│   │   └── TemplateFilters.tsx
│   ├── TemplateSelector/
│   │   ├── TemplateSelector.tsx
│   │   ├── TemplatePreview.tsx
│   │   └── CategoryFilter.tsx
│   └── TemplateForm/
│       ├── CreateTemplateModal.tsx
│       └── TemplateFormFields.tsx
├── hooks/
│   ├── useAnalysisTemplates.ts
│   └── useDriverTreeTemplates.ts
├── api/
│   └── templateApi.ts
└── types/
    └── template.ts
```

### 6.3 テンプレート選択UI（tree-new画面内）

既存のtree-new画面内のテンプレート選択部分は、driver_tree_templateテーブルのデータを表示します。

```text
┌────────────────────────────────────────────────────────┐
│  テンプレートから作成                                    │
├────────────────────────────────────────────────────────┤
│  業種: [すべて] [小売・EC] [製造業] [サービス業] [SaaS]  │
│  分析タイプ: [すべて] [売上分析] [コスト分析] [利益分析] │
├────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 📈       │ │ 🛒       │ │ 🔄       │ │ 🏭       │  │
│  │ 売上分解 │ │ EC売上   │ │ SaaS MRR │ │ 製造コスト│  │
│  │ モデル   │ │ モデル   │ │ 分解     │ │ 構造     │  │
│  │ ノード:8 │ │ ノード:12│ │ ノード:15│ │ ノード:18│  │
│  │ 利用:150+│ │ 利用:80+ │ │ 利用:45+ │ │ 利用:35+ │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                        │
│  ┌──────────┐                                          │
│  │ ➕       │                                          │
│  │ 空の     │                                          │
│  │ ツリー   │                                          │
│  └──────────┘                                          │
└────────────────────────────────────────────────────────┘
```

---

## 7. 画面項目・APIマッピング

### 7.1 テンプレート選択画面（tree-new内）

| 画面項目 | 表示/入力形式 | APIエンドポイント | フィールド | 変換処理 |
|---------|-------------|------------------|-----------|---------|
| 業種フィルター | チップ選択 | GET /driver-tree/template | query: category | - |
| テンプレートカード | カードグリッド | GET /driver-tree/template | templates[] | - |
| テンプレート名 | テキスト | GET /driver-tree/template | templates[].name | - |
| テンプレートアイコン | アイコン | - | - | カテゴリ→アイコン変換 |
| ノード数 | テキスト | GET /driver-tree/template | templates[].nodeCount | "ノード: n" |
| 利用実績 | テキスト | GET /driver-tree/template | templates[].usageCount | "利用実績: n+" |
| 人気バッジ | バッジ | GET /driver-tree/template | templates[].usageCount | >100で表示 |

### 7.2 テンプレート作成モーダル

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| テンプレート名 | テキスト | ○ | POST /driver-tree/template | name | 1-255文字 |
| 説明 | テキストエリア | - | POST /driver-tree/template | description | 任意 |
| カテゴリ | セレクト | - | POST /driver-tree/template | category | 業種選択 |
| 公開設定 | トグル | - | POST /driver-tree/template | isPublic | true/false |
| 元ツリー | 非表示 | ○ | POST /driver-tree/template | sourceTreeId | 現在のツリーID |

### 7.3 テンプレート一覧画面

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| テンプレート名 | テキスト | GET /template | templates[].name | - |
| 説明 | テキスト | GET /template | templates[].description | - |
| タイプ | バッジ | GET /template | templates[].templateType | session/tree |
| 公開状態 | アイコン | GET /template | templates[].isPublic | 公開/非公開アイコン |
| 使用回数 | 数値 | GET /template | templates[].usageCount | - |
| 作成者 | テキスト | GET /template | templates[].createdByName | - |
| 作成日時 | 日時 | GET /template | templates[].createdAt | YYYY/MM/DD形式 |
| 削除ボタン | ボタン | DELETE /template/{id} | - | 確認ダイアログ |

---

## 8. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|--------|-----|------|-----------|
| TM-001 | テンプレート一覧表示 | GET /template | templates, tree-new | 設計済 |
| TM-002 | テンプレート作成（セッションから） | POST /analysis/template | session-detail | 設計済 |
| TM-003 | テンプレート作成（ツリーから） | POST /driver-tree/template | tree-edit | 設計済 |
| TM-004 | テンプレート適用 | POST /session + config, POST /tree/import | session-new, tree-new | 設計済 |
| TM-005 | テンプレート削除 | DELETE /template/{id} | templates | 設計済 |

カバレッジ: 5/5 = 100%

---

## 9. 備考

### 9.1 既存機能との統合

- **ドライバーツリー作成画面（tree-new）**: 既存のテンプレート選択UIは、driver_tree_templateテーブルのデータを表示するように拡張
- **数式マスタ（driver_tree_formula）**: 業界分類マスタと連携してテンプレートのカテゴリフィルタリングに使用
- **セッション作成画面（session-new）**: テンプレート選択オプションを追加

### 9.2 将来拡張

- テンプレートのバージョン管理
- テンプレートのフォーク/派生
- テンプレートマーケットプレイス（組織間共有）
- テンプレートの評価・レビュー機能

---

## 10. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **分析機能設計書**: [../04-analysis/01-analysis-design.md](../04-analysis/01-analysis-design.md)
- **ドライバーツリー設計書**: [../05-driver-tree/01-driver-tree-design.md](../05-driver-tree/01-driver-tree-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

### ドキュメント管理情報

- **作成日**: 2026年1月1日
- **更新日**: 2026年1月1日
- **対象ソースコード**:
  - モデル: `src/app/models/analysis/analysis_template.py`, `src/app/models/driver_tree/driver_tree_template.py`
  - スキーマ: `src/app/schemas/analysis/template.py`, `src/app/schemas/driver_tree/template.py`
  - API: `src/app/api/routes/v1/analysis/template.py`, `src/app/api/routes/v1/driver_tree/template.py`
