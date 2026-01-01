# テンプレート バックエンド設計書（TM-001〜TM-005）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムにおけるテンプレート機能の統合設計仕様を定義します。テンプレート機能は、分析セッションやドライバーツリーの構成を再利用可能なテンプレートとして保存・共有し、効率的な分析開始を支援します。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|--------|
| **テンプレート管理** | TM-001 | テンプレート一覧表示 |
| | TM-002 | テンプレート作成（セッションから） |
| | TM-003 | テンプレート作成（ツリーから） |
| | TM-004 | テンプレート適用 |
| | TM-005 | テンプレート削除 |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 2 |
| APIエンドポイント | 7 |
| Pydanticスキーマ | 10 |
| フロントエンド画面 | 2 |

---

## 2. データベース設計

### 2.1 関連テーブル一覧

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

### 4.1 Enum定義

```python
from enum import Enum

class TemplateType(str, Enum):
    """テンプレートタイプ"""
    SESSION = "session"
    STEP = "step"

class TemplateCategory(str, Enum):
    """テンプレートカテゴリ（業種）"""
    RETAIL_EC = "小売・EC"
    MANUFACTURING = "製造業"
    SERVICE = "サービス業"
    SAAS = "SaaS"
    OTHER = "その他"
```

### 4.2 Info/Dataスキーマ

```python
class AnalysisTemplateInfo(CamelCaseModel):
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

class AnalysisTemplateConfig(CamelCaseModel):
    """分析テンプレート設定"""
    initial_prompt: str | None = None
    steps: list[dict] = []
    default_file_types: list[str] = []
    analysis_type: str | None = None

class DriverTreeTemplateInfo(CamelCaseModel):
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

class DriverTreeTemplateConfig(CamelCaseModel):
    """ドライバーツリーテンプレート設定"""
    nodes: list[dict] = []
    relationships: list[dict] = []
    formulas: list[str] = []
```

### 4.3 Request/Responseスキーマ

```python
class AnalysisTemplateCreateRequest(CamelCaseModel):
    """分析テンプレート作成リクエスト"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    source_session_id: UUID
    is_public: bool = False

class AnalysisTemplateListResponse(CamelCaseModel):
    """分析テンプレート一覧レスポンス"""
    templates: list[AnalysisTemplateInfo] = []
    total: int

class DriverTreeTemplateCreateRequest(CamelCaseModel):
    """ドライバーツリーテンプレート作成リクエスト"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    source_tree_id: UUID
    is_public: bool = False

class DriverTreeTemplateListResponse(CamelCaseModel):
    """ドライバーツリーテンプレート一覧レスポンス"""
    templates: list[DriverTreeTemplateInfo] = []
    total: int
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| AnalysisTemplateService | 分析テンプレートの管理 |
| DriverTreeTemplateService | ドライバーツリーテンプレートの管理 |

### 5.2 主要メソッド

#### AnalysisTemplateService

```python
class AnalysisTemplateService:
    """分析テンプレートサービス"""

    async def list_templates(
        self,
        project_id: UUID,
        include_public: bool = True,
        template_type: str | None = None
    ) -> AnalysisTemplateListResponse:
        """
        テンプレート一覧を取得

        Args:
            project_id: プロジェクトID
            include_public: 公開テンプレートを含めるか
            template_type: テンプレートタイプでフィルター

        Returns:
            テンプレート一覧
        """
        query = select(AnalysisTemplate).where(
            or_(
                AnalysisTemplate.project_id == project_id,
                AnalysisTemplate.is_public == True if include_public else False
            )
        )

        if template_type:
            query = query.where(AnalysisTemplate.template_type == template_type)

        result = await self.db.execute(query)
        templates = result.scalars().all()

        return AnalysisTemplateListResponse(
            templates=[AnalysisTemplateInfo.from_orm(t) for t in templates],
            total=len(templates)
        )

    async def create_template(
        self,
        project_id: UUID,
        name: str,
        description: str | None,
        source_session_id: UUID,
        is_public: bool,
        user_id: UUID
    ) -> AnalysisTemplateInfo:
        """
        セッションからテンプレートを作成

        処理フロー:
        1. 元セッションの取得と検証
        2. テンプレート設定の抽出（steps, prompt等）
        3. テンプレートの保存

        Args:
            project_id: プロジェクトID
            name: テンプレート名
            description: 説明
            source_session_id: 元セッションID
            is_public: 公開フラグ
            user_id: 作成者ID

        Returns:
            作成されたテンプレート情報
        """
        # 1. 元セッションの取得
        session = await self.session_service.get_session(project_id, source_session_id)
        if not session:
            raise SessionNotFoundError()

        # 2. テンプレート設定の抽出
        template_config = AnalysisTemplateConfig(
            initial_prompt=session.initial_prompt,
            steps=[step.to_dict() for step in session.steps],
            default_file_types=session.file_types,
            analysis_type=session.analysis_type
        )

        # 3. テンプレートの保存
        template = AnalysisTemplate(
            project_id=project_id,
            name=name,
            description=description,
            template_type=session.session_type,
            template_config=template_config.model_dump(),
            source_session_id=source_session_id,
            is_public=is_public,
            created_by=user_id
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        return AnalysisTemplateInfo.from_orm(template)

    async def apply_template(
        self,
        project_id: UUID,
        template_id: UUID,
        session_name: str,
        user_id: UUID
    ) -> dict:
        """
        テンプレートを適用してセッション作成

        Args:
            project_id: プロジェクトID
            template_id: テンプレートID
            session_name: 新セッション名
            user_id: ユーザーID

        Returns:
            作成されたセッション情報
        """
        template = await self.get_template(project_id, template_id)
        if not template:
            raise TemplateNotFoundError()

        # テンプレート設定を使用してセッション作成
        session_data = {
            "name": session_name,
            "initial_prompt": template.template_config.get("initial_prompt"),
            "steps": template.template_config.get("steps", []),
            "analysis_type": template.template_config.get("analysis_type")
        }

        new_session = await self.session_service.create_session(
            project_id, session_data, user_id
        )

        # 使用回数をインクリメント
        template.usage_count += 1
        await self.db.commit()

        return new_session
```

#### DriverTreeTemplateService

```python
class DriverTreeTemplateService:
    """ドライバーツリーテンプレートサービス"""

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
        """
        ツリーからテンプレートを作成

        処理フロー:
        1. 元ツリーとノード・リレーションの取得
        2. テンプレート設定の抽出（相対座標変換）
        3. テンプレートの保存

        Args:
            project_id: プロジェクトID
            name: テンプレート名
            description: 説明
            category: カテゴリ（業種）
            source_tree_id: 元ツリーID
            is_public: 公開フラグ
            user_id: 作成者ID

        Returns:
            作成されたテンプレート情報
        """
        # 1. 元ツリーとノード・リレーションの取得
        tree = await self.tree_service.get_tree(project_id, source_tree_id)
        if not tree:
            raise TreeNotFoundError()

        nodes = await self.tree_service.get_tree_nodes(source_tree_id)
        relationships = await self.tree_service.get_tree_relationships(source_tree_id)

        # 2. テンプレート設定の抽出（絶対座標→相対座標変換）
        # 基準ノード（ルート）を中心に相対座標化
        root_node = next((n for n in nodes if n.is_root), nodes[0])
        base_x, base_y = root_node.position_x, root_node.position_y

        template_nodes = [
            {
                "label": node.label,
                "nodeType": node.node_type,
                "relativeX": node.position_x - base_x,
                "relativeY": node.position_y - base_y
            }
            for node in nodes
        ]

        template_relationships = [
            {
                "parentLabel": rel.parent_node.label,
                "childLabels": [child.label for child in rel.child_nodes],
                "operator": rel.operator
            }
            for rel in relationships
        ]

        template_config = DriverTreeTemplateConfig(
            nodes=template_nodes,
            relationships=template_relationships,
            formulas=tree.formulas
        )

        # 3. テンプレートの保存
        template = DriverTreeTemplate(
            project_id=project_id,
            name=name,
            description=description,
            category=category,
            template_config=template_config.model_dump(),
            source_tree_id=source_tree_id,
            is_public=is_public,
            created_by=user_id
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        return DriverTreeTemplateInfo.from_orm(template)

    async def apply_template(
        self,
        project_id: UUID,
        template_id: UUID,
        tree_name: str,
        position_x: int,
        position_y: int,
        user_id: UUID
    ) -> dict:
        """
        テンプレートを適用してツリー作成

        処理フロー:
        1. テンプレート取得
        2. 相対座標→絶対座標変換
        3. ノードとリレーションの作成

        Args:
            project_id: プロジェクトID
            template_id: テンプレートID
            tree_name: 新ツリー名
            position_x: 配置位置X
            position_y: 配置位置Y
            user_id: ユーザーID

        Returns:
            作成されたツリー情報
        """
        template = await self.get_template(project_id, template_id)
        if not template:
            raise TemplateNotFoundError()

        # 相対座標→絶対座標変換
        nodes_data = [
            {
                "label": node["label"],
                "node_type": node["nodeType"],
                "position_x": position_x + node["relativeX"],
                "position_y": position_y + node["relativeY"]
            }
            for node in template.template_config["nodes"]
        ]

        # ツリー作成
        new_tree = await self.tree_service.create_tree_with_nodes(
            project_id=project_id,
            tree_name=tree_name,
            nodes=nodes_data,
            relationships=template.template_config["relationships"],
            user_id=user_id
        )

        # 使用回数をインクリメント
        template.usage_count += 1
        await self.db.commit()

        return new_tree
```

---

## 6. フロントエンド設計

フロントエンド設計の詳細は以下を参照してください：

- [テンプレート フロントエンド設計書](./02-template-frontend-design.md)

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|--------|-----|------|-----------|
| TM-001 | テンプレート一覧表示 | GET /template | templates, tree-new | 設計済 |
| TM-002 | テンプレート作成（セッションから） | POST /analysis/template | session-detail | 設計済 |
| TM-003 | テンプレート作成（ツリーから） | POST /driver-tree/template | tree-edit | 設計済 |
| TM-004 | テンプレート適用 | POST /session + config, POST /tree/import | session-new, tree-new | 設計済 |
| TM-005 | テンプレート削除 | DELETE /template/{id} | templates | 設計済 |

カバレッジ: 5/5 = 100%

---

## 8. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **分析機能設計書**: [../05-analysis/01-analysis-design.md](../05-analysis/01-analysis-design.md)
- **ドライバーツリー設計書**: [../06-driver-tree/01-driver-tree-design.md](../06-driver-tree/01-driver-tree-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | TM-DESIGN-001 |
| 対象ユースケース | TM-001〜TM-005 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/models/analysis/analysis_template.py` |
|  | `src/app/models/driver_tree/driver_tree_template.py` |
|  | `src/app/schemas/analysis/template.py` |
|  | `src/app/schemas/driver_tree/template.py` |
|  | `src/app/api/routes/v1/analysis/template.py` |
|  | `src/app/api/routes/v1/driver_tree/template.py` |
