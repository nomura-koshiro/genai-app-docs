# API - フロントエンド ギャップ解決策

**作成日**: 2025年12月28日
**目的**: API_FRONTEND_GAP_ANALYSIS.md で特定された全ての問題に対する解決策を策定

---

## 概要

本ドキュメントでは、フロントエンドUIで必要とされているがAPIで提供されていないフィールドについて、DB設計・バックエンドモデル・APIスキーマ・エンドポイントの各レイヤーでの修正計画を策定します。

---

## 修正対象レイヤー

```
┌─────────────────────────────────────────────────────────────────┐
│  1. DB設計ドキュメント (docs/specifications/05-database/)       │
│     └── 01-database-design.md, 03-schema.dbml                  │
├─────────────────────────────────────────────────────────────────┤
│  2. SQLAlchemyモデル (src/app/models/)                          │
│     └── 各テーブル定義ファイル                                   │
├─────────────────────────────────────────────────────────────────┤
│  3. Pydanticスキーマ (src/app/schemas/)                         │
│     └── APIリクエスト/レスポンス定義                             │
├─────────────────────────────────────────────────────────────────┤
│  4. APIエンドポイント (src/app/api/routes/)                      │
│     └── クエリ・レスポンス構築ロジック                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. セッション一覧 (AnalysisSession)

### 問題
| フィールド | 状態 | 影響度 |
|-----------|------|--------|
| `name` | DB・APIに存在しない | 🔴 高 |
| `issueName` | IDのみ（名前なし） | 🔴 高 |
| `creatorName` | IDのみ（名前なし） | 🔴 高 |
| `inputFileName` | IDのみ（名前なし） | 🟡 中 |

### 解決策

#### 1.1 DB設計変更

**対象テーブル**: `analysis_session`

| 変更種別 | カラム名 | 型 | 制約 | 説明 |
|---------|---------|-----|------|------|
| **追加** | `name` | VARCHAR(255) | NOT NULL, DEFAULT '' | セッション名 |

```sql
-- マイグレーション
ALTER TABLE analysis_session
ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT '';

-- 既存データの更新（スナップショット番号からデフォルト名生成）
UPDATE analysis_session
SET name = CONCAT('セッション #', current_snapshot)
WHERE name = '';
```

#### 1.2 SQLAlchemyモデル変更

**ファイル**: `src/app/models/analysis/analysis_session.py`

```python
# 追加
name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
```

#### 1.3 Pydanticスキーマ変更

**ファイル**: `src/app/schemas/analysis/analysis_session.py`

```python
# 新規追加: ネストされたリレーション情報
class IssueInfo(BaseCamelCaseModel):
    id: UUID
    name: str

class CreatorInfo(BaseCamelCaseModel):
    id: UUID
    display_name: str

class InputFileInfo(BaseCamelCaseModel):
    id: UUID
    original_filename: str

# AnalysisSessionResponse を拡張
class AnalysisSessionResponse(BaseCamelCaseORMModel):
    id: UUID
    name: str  # 新規追加
    project_id: UUID
    issue_id: UUID
    issue: IssueInfo | None = None  # 新規追加
    creator_id: UUID
    creator: CreatorInfo | None = None  # 新規追加
    input_file_id: UUID | None = None
    input_file: InputFileInfo | None = None  # 新規追加
    current_snapshot: int
    status: str
    created_at: datetime
    updated_at: datetime
```

#### 1.4 APIエンドポイント変更

**ファイル**: `src/app/api/routes/v1/analysis/analysis_session.py`

```python
# セッション一覧取得時にリレーションをeager loadする
async def get_sessions(...):
    query = (
        select(AnalysisSession)
        .options(
            selectinload(AnalysisSession.issue),
            selectinload(AnalysisSession.creator),
            selectinload(AnalysisSession.input_file)
            .selectinload(AnalysisFile.project_file)
        )
        .where(AnalysisSession.project_id == project_id)
    )
    # ...
```

---

## 2. ツリー一覧 (DriverTree)

### 問題
| フィールド | 状態 | 影響度 |
|-----------|------|--------|
| `formulaMaster` | 数式マスタ名がない | 🔴 高 |
| `nodeCount` | ノード数がない | 🟡 中 |
| `policyCount` | 施策数がない | 🟡 中 |

### 解決策

#### 2.1 DB設計変更

**変更不要** - 必要なリレーションは既に存在
- `driver_tree.formula_id` → `driver_tree_formula`
- `driver_tree_node.driver_tree_id` でノード数計算可能
- `driver_tree_policy.node_id` で施策数計算可能

#### 2.2 Pydanticスキーマ変更

**ファイル**: `src/app/schemas/driver_tree/driver_tree.py`

```python
class DriverTreeListItem(BaseCamelCaseORMModel):
    tree_id: UUID
    name: str
    description: str | None = None
    status: str
    formula_master_name: str | None = None  # 新規追加
    node_count: int = 0  # 新規追加
    policy_count: int = 0  # 新規追加
    created_at: datetime
    updated_at: datetime
```

#### 2.3 APIエンドポイント変更

**ファイル**: `src/app/api/routes/v1/driver_tree/driver_tree.py`

```python
from sqlalchemy import func, select

async def get_trees(...):
    # サブクエリでノード数を計算
    node_count_subq = (
        select(
            DriverTreeNode.driver_tree_id,
            func.count(DriverTreeNode.id).label('node_count')
        )
        .group_by(DriverTreeNode.driver_tree_id)
        .subquery()
    )

    # サブクエリで施策数を計算
    policy_count_subq = (
        select(
            DriverTreeNode.driver_tree_id,
            func.count(DriverTreePolicy.id).label('policy_count')
        )
        .join(DriverTreePolicy, DriverTreePolicy.node_id == DriverTreeNode.id)
        .group_by(DriverTreeNode.driver_tree_id)
        .subquery()
    )

    query = (
        select(
            DriverTree,
            DriverTreeFormula.driver_type.label('formula_master_name'),
            func.coalesce(node_count_subq.c.node_count, 0).label('node_count'),
            func.coalesce(policy_count_subq.c.policy_count, 0).label('policy_count')
        )
        .outerjoin(DriverTreeFormula, DriverTree.formula_id == DriverTreeFormula.id)
        .outerjoin(node_count_subq, DriverTree.id == node_count_subq.c.driver_tree_id)
        .outerjoin(policy_count_subq, DriverTree.id == policy_count_subq.c.driver_tree_id)
        .where(DriverTree.project_id == project_id)
    )
```

---

## 3. カテゴリ編集 (DriverTreeCategory)

### 問題
| フィールド | 状態 | 影響度 |
|-----------|------|--------|
| `description` | DBに存在しない | 🟡 中 |
| `formulaCount` | 集計情報がない | 🟡 中 |
| `creatorName` | DBに存在しない | 🟡 中 |
| `usageTreeCount` | 集計情報がない | 🟡 中 |

### 解決策

#### 3.1 DB設計変更

**対象テーブル**: `driver_tree_category`

| 変更種別 | カラム名 | 型 | 制約 | 説明 |
|---------|---------|-----|------|------|
| **追加** | `description` | TEXT | NULLABLE | カテゴリ説明 |
| **追加** | `created_by` | UUID | FK(user_account.id), NULLABLE | 作成者ID |

```sql
-- マイグレーション
ALTER TABLE driver_tree_category
ADD COLUMN description TEXT;

ALTER TABLE driver_tree_category
ADD COLUMN created_by UUID REFERENCES user_account(id) ON DELETE SET NULL;
```

#### 3.2 SQLAlchemyモデル変更

**ファイル**: `src/app/models/driver_tree/driver_tree_category.py`

```python
# 追加
description: Mapped[str | None] = mapped_column(Text, nullable=True)
created_by: Mapped[UUID | None] = mapped_column(
    ForeignKey("user_account.id", ondelete="SET NULL"),
    nullable=True
)

# リレーション追加
creator: Mapped["UserAccount | None"] = relationship(
    "UserAccount",
    foreign_keys=[created_by]
)
```

#### 3.3 Pydanticスキーマ変更

**ファイル**: `src/app/schemas/driver_tree/category.py`

```python
class DriverTreeCategoryDetailResponse(BaseCamelCaseORMModel):
    id: int
    category_id: int
    category_name: str
    industry_id: int
    industry_name: str
    driver_type_id: int
    driver_type: str
    description: str | None = None  # 新規追加
    created_by: UUID | None = None  # 新規追加
    creator_name: str | None = None  # 新規追加（JOINで取得）
    formula_count: int = 0  # 新規追加（集計）
    usage_tree_count: int = 0  # 新規追加（集計）
    created_at: datetime
    updated_at: datetime
```

#### 3.4 APIエンドポイント変更

**ファイル**: `src/app/api/routes/v1/admin/category.py`

```python
async def get_category(category_id: int, ...):
    # カテゴリ取得
    category = await db.get(DriverTreeCategory, category_id)

    # 数式数を集計
    formula_count = await db.scalar(
        select(func.count(DriverTreeFormula.id))
        .where(DriverTreeFormula.category_id == category_id)
    )

    # 使用ツリー数を集計（数式経由）
    usage_tree_count = await db.scalar(
        select(func.count(distinct(DriverTree.id)))
        .join(DriverTreeFormula, DriverTree.formula_id == DriverTreeFormula.id)
        .where(DriverTreeFormula.category_id == category_id)
    )

    # 作成者名を取得
    creator_name = None
    if category.created_by:
        creator = await db.get(UserAccount, category.created_by)
        creator_name = creator.display_name if creator else None
```

---

## 4. ダッシュボード統計

### 問題
| フィールド | 状態 | 影響度 |
|-----------|------|--------|
| `fileCount` | ファイル統計がない | 🟡 中 |

### 解決策

#### 4.1 DB設計変更

**変更不要** - `project_file`テーブルは既に存在

#### 4.2 Pydanticスキーマ変更

**ファイル**: `src/app/schemas/dashboard/dashboard.py`

```python
class FileStats(BaseCamelCaseModel):
    total: int
    by_mime_type: dict[str, int] | None = None  # オプション: MIMEタイプ別集計

class DashboardStatsResponse(BaseCamelCaseModel):
    projects: ProjectStats
    sessions: SessionStats
    trees: TreeStats
    users: UserStats
    files: FileStats  # 新規追加
    generated_at: datetime
```

#### 4.3 APIエンドポイント変更

**ファイル**: `src/app/api/routes/v1/dashboard/dashboard.py`

```python
async def get_stats(...):
    # 既存の統計情報...

    # ファイル統計を追加
    file_count = await db.scalar(
        select(func.count(ProjectFile.id))
    )

    return DashboardStatsResponse(
        # ...既存フィールド
        files=FileStats(total=file_count),
        generated_at=datetime.utcnow()
    )
```

---

## 5. プロジェクトメンバー

### 問題
| フィールド | 状態 | 影響度 |
|-----------|------|--------|
| `joinedAt` | DBに存在（実装確認済み） | ✅ 解決済み |
| `lastActivityAt` | DBに存在しない | 🟢 低 |

### 解決策

#### 5.1 DB設計変更

**対象テーブル**: `project_member`

| 変更種別 | カラム名 | 型 | 制約 | 説明 |
|---------|---------|-----|------|------|
| **追加** | `last_activity_at` | DATETIME | NULLABLE | プロジェクト内最終活動日時 |

```sql
-- マイグレーション
ALTER TABLE project_member
ADD COLUMN last_activity_at TIMESTAMP;

-- 初期値として参加日時を設定
UPDATE project_member
SET last_activity_at = joined_at;
```

#### 5.2 SQLAlchemyモデル変更

**ファイル**: `src/app/models/project/project_member.py`

```python
# 追加
last_activity_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

#### 5.3 活動追跡の実装

プロジェクト内でのアクション時に`last_activity_at`を更新するミドルウェアまたはサービス層の実装が必要:

```python
# src/app/services/activity_tracker.py
async def update_member_activity(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID
) -> None:
    """プロジェクトメンバーの最終活動日時を更新"""
    await db.execute(
        update(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
        .values(last_activity_at=datetime.utcnow())
    )
```

---

## 6. プロジェクト作成

### 問題
| フィールド | 状態 | 影響度 |
|-----------|------|--------|
| `startDate` | ✅ APIに存在 | - (FE実装待ち) |
| `endDate` | ✅ APIに存在 | - (FE実装待ち) |
| `budget` | DBに存在しない | 🟢 低 |

### 解決策

#### 6.1 DB設計変更

**対象テーブル**: `project`

| 変更種別 | カラム名 | 型 | 制約 | 説明 |
|---------|---------|-----|------|------|
| **追加** | `budget` | DECIMAL(15,2) | NULLABLE | プロジェクト予算 |

```sql
-- マイグレーション
ALTER TABLE project
ADD COLUMN budget DECIMAL(15,2);
```

#### 6.2 SQLAlchemyモデル変更

**ファイル**: `src/app/models/project/project.py`

```python
from decimal import Decimal

# 追加
budget: Mapped[Decimal | None] = mapped_column(
    Numeric(15, 2),
    nullable=True
)
```

#### 6.3 Pydanticスキーマ変更

**ファイル**: `src/app/schemas/project/project.py`

```python
from decimal import Decimal

class ProjectCreate(BaseCamelCaseModel):
    name: str
    code: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal | None = None  # 新規追加

class ProjectResponse(BaseCamelCaseORMModel):
    # ...既存フィールド
    budget: Decimal | None = None  # 新規追加
```

#### 6.4 フロントエンド対応（参考）

`startDate`/`endDate`はAPIに既に存在するため、フロントエンド側の実装を更新:

```typescript
// src/features/projects/routes/project-new/project-new.hook.ts
// @remarks コメントを削除し、APIフィールドを活用
const projectData: ProjectCreate = {
  name: formData.name,
  code: formData.code,
  startDate: formData.startDate,  // API対応済み
  endDate: formData.endDate,      // API対応済み
  budget: formData.budget,        // API拡張後に対応
};
```

---

## 7. セッション作成（将来機能）

### 問題
| フィールド | 状態 | 影響度 |
|-----------|------|--------|
| `templateId` | 将来機能 | 🟢 低 |
| `parameters` | 将来機能 | 🟢 低 |

### 解決策

**優先度: 低** - 将来のテンプレート機能実装時に対応

#### 7.1 将来のDB設計案

```sql
-- セッションテンプレートテーブル（将来追加）
CREATE TABLE analysis_session_template (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    default_parameters JSONB,
    created_by UUID REFERENCES user_account(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- analysis_session に外部キー追加（将来）
ALTER TABLE analysis_session
ADD COLUMN template_id UUID REFERENCES analysis_session_template(id),
ADD COLUMN parameters JSONB;
```

---

## 修正ファイル一覧

### DB設計ドキュメント

| ファイル | 変更内容 |
|---------|---------|
| `docs/specifications/05-database/01-database-design.md` | テーブル定義更新 |
| `docs/specifications/05-database/03-schema.dbml` | DBML更新 |

### SQLAlchemyモデル

| ファイル | 変更内容 |
|---------|---------|
| `src/app/models/analysis/analysis_session.py` | `name`カラム追加 |
| `src/app/models/driver_tree/driver_tree_category.py` | `description`, `created_by`追加 |
| `src/app/models/project/project_member.py` | `last_activity_at`追加 |
| `src/app/models/project/project.py` | `budget`追加 |

### Pydanticスキーマ

| ファイル | 変更内容 |
|---------|---------|
| `src/app/schemas/analysis/analysis_session.py` | リレーション情報追加 |
| `src/app/schemas/driver_tree/driver_tree.py` | 集計フィールド追加 |
| `src/app/schemas/driver_tree/category.py` | 詳細フィールド追加 |
| `src/app/schemas/dashboard/dashboard.py` | ファイル統計追加 |
| `src/app/schemas/project/project.py` | `budget`追加 |
| `src/app/schemas/project/project_member.py` | `last_activity_at`追加 |

### APIエンドポイント

| ファイル | 変更内容 |
|---------|---------|
| `src/app/api/routes/v1/analysis/analysis_session.py` | リレーション展開 |
| `src/app/api/routes/v1/driver_tree/driver_tree.py` | 集計クエリ追加 |
| `src/app/api/routes/v1/admin/category.py` | 詳細情報取得 |
| `src/app/api/routes/v1/dashboard/dashboard.py` | ファイル統計追加 |

---

## 実装優先度

### Phase 1: 高優先度（ユーザー体験に直接影響）

1. **セッション一覧のリレーション展開**
   - DB: `analysis_session.name`追加
   - API: `issue`, `creator`, `inputFile`のネスト情報

2. **ツリー一覧の集計情報**
   - API: `formulaMasterName`, `nodeCount`, `policyCount`

### Phase 2: 中優先度（機能改善）

3. **カテゴリ詳細の拡充**
   - DB: `description`, `created_by`追加
   - API: 集計情報追加

4. **ダッシュボード統計**
   - API: ファイル統計追加

### Phase 3: 低優先度（将来機能）

5. **プロジェクトメンバー活動情報**
   - DB: `last_activity_at`追加
   - サービス: 活動追跡実装

6. **プロジェクト予算**
   - DB: `budget`追加

7. **セッションテンプレート**
   - 将来実装

---

## マイグレーション計画

### マイグレーションファイル作成

```bash
# Phase 1
alembic revision --autogenerate -m "add_session_name_column"

# Phase 2
alembic revision --autogenerate -m "add_category_description_and_creator"

# Phase 3
alembic revision --autogenerate -m "add_project_member_activity_and_project_budget"
```

### ロールバック戦略

各マイグレーションは独立して実行・ロールバック可能に設計:

```python
def downgrade():
    op.drop_column('analysis_session', 'name')
```

---

## 備考

- 本ドキュメントはAPI_FRONTEND_GAP_ANALYSIS.mdの分析結果に基づいて作成
- 各変更はバックエンドチームとの協議後に実装を開始
- フロントエンド側の対応は別途計画が必要
- OpenAPI仕様（openapi.json）は実装後に自動生成で更新

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2025-12-28 | 初版作成 |
