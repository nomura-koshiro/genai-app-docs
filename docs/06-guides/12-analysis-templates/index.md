# 分析テンプレート機能ガイド

## 概要

分析テンプレート機能は、validation.ymlで定義された施策・課題の組み合わせをデータベースに格納し、API経由で取得可能にする機能です。AIエージェントによる分析時のテンプレート選択やダミーデータ表示に使用されます。

## 目次

- [概要](#概要)
- [機能説明](#機能説明)
- [データモデル](#データモデル)
- [API エンドポイント](#api-エンドポイント)
- [データシード](#データシード)
- [使用例](#使用例)
- [テスト](#テスト)
- [関連ドキュメント](#関連ドキュメント)

## 機能説明

### 主な機能

1. **テンプレートデータ管理**
   - validation.ymlの施策・課題テンプレートをデータベースに格納
   - 施策別・課題別の検索
   - アクティブ/非アクティブ管理

2. **ダミーチャートデータ管理**
   - Plotly形式のダミーチャートJSONを格納
   - テンプレートとの関連付け
   - 表示順序管理

3. **自動データシード**
   - テスト実行時の自動データロード
   - 開発環境でのCLIスクリプト
   - データベースリセット時の自動シード

### アーキテクチャ

```
validation.yml + dummy/chart/*.json
        ↓
TemplateSeeder (データパース・インポート)
        ↓
Database (PostgreSQL)
  - analysis_templates
  - analysis_template_charts
        ↓
Repository層 (データアクセス)
        ↓
API層 (REST エンドポイント)
        ↓
フロントエンド
```

## データモデル

### analysis_templates テーブル

施策・課題テンプレートを格納します。

**モデル定義**: `src/app/models/analysis_template.py`

主要なフィールド：

- `id` (UUID) - プライマリキー
- `policy` (str) - 施策名（例: "市場拡大"）
- `issue` (str) - 課題名（例: "新規参入"）
- `description` (str) - テンプレートの説明
- `agent_prompt` (str) - AIエージェント用プロンプト
- `initial_msg` (str) - 初期メッセージ
- `initial_axis` (JSONB) - 初期軸設定
- `dummy_formula` (JSONB) - ダミー計算式
- `dummy_input` (JSONB) - ダミー入力データ
- `dummy_hint` (str) - ダミーヒント
- `is_active` (bool) - アクティブフラグ
- `display_order` (int) - 表示順序

**制約:**

- `(policy, issue)` の組み合わせはユニーク
- インデックス: `policy`, `issue`, `(policy, issue)`

### analysis_template_charts テーブル

ダミーチャートデータを格納します。

**モデル定義**: `src/app/models/analysis_template_chart.py`

主要なフィールド：

- `id` (UUID) - プライマリキー
- `template_id` (UUID) - テンプレートID（外部キー）
- `chart_name` (str) - チャート名
- `chart_data` (JSONB) - Plotlyチャートデータ
- `chart_order` (int) - 表示順序
- `chart_type` (str) - チャートタイプ（scatter, bar等）

**リレーション:**

- `template_id` → `analysis_templates.id` (CASCADE DELETE)

### データソース

#### validation.yml

施策・課題テンプレートの定義ファイル：

```yaml
施策①：不採算製品の撤退:
  不採算製品から撤退した場合の利益改善効果は​？:
    description: |
      収益率がマイナスの赤字製品を撤退した場合の利益合計を算出します。
    agent_prompt: |
      現在は赤字製品を撤退した場合の利益を知りたい、その一般的な分析の流れが下記の通りです:
          - 施策前(サマリステップ): 元データから、利益合計の計算式...
    initial_msg: |
      分析にあたり、以下の選択された軸を取った散布図を作成して分析します。
    initial_axis:
      - name: 横軸 (売上高、利益など)
        option: 科目
        multiple: false
    dummy:
      formula:
        - name: 赤字商品数
          value: XXX個
      chart:
        - 不採算製品の撤退-不採算製品から撤退した場合の利益改善効果は.json
```

#### dummy/chart/*.json

Plotly形式のチャートデータ：

```json
{
    "data": [
        {
            "type": "scatter",
            "mode": "markers",
            "x": [...],
            "y": [...]
        }
    ],
    "layout": {
        "title": "利益改善効果",
        "xaxis": {"title": "売上高"},
        "yaxis": {"title": "利益率"}
    }
}
```

## API エンドポイント

### テンプレート一覧取得

アクティブなテンプレート一覧を取得します。

```http
GET /api/v1/analysis/templates?skip=0&limit=20
```

**レスポンス例:**

```json
[
    {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "policy": "施策①：不採算製品の撤退",
        "issue": "不採算製品から撤退した場合の利益改善効果は​？",
        "description": "収益率がマイナスの赤字製品を撤退した場合の利益合計を算出します。",
        "agent_prompt": "...",
        "initial_msg": "分析にあたり...",
        "initial_axis": [...],
        "dummy_formula": [...],
        "dummy_input": null,
        "dummy_hint": "対象会社の最新製品群別販売高・粗利データ",
        "is_active": true,
        "display_order": 0,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }
]
```

### テンプレート詳細取得

チャートデータを含むテンプレート詳細を取得します。

```http
GET /api/v1/analysis/templates/{template_id}
```

**レスポンス例:**

```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "policy": "施策①：不採算製品の撤退",
    "issue": "不採算製品から撤退した場合の利益改善効果は​？",
    "description": "...",
    "agent_prompt": "...",
    "initial_msg": "...",
    "initial_axis": [...],
    "dummy_formula": [...],
    "dummy_input": null,
    "dummy_hint": "...",
    "is_active": true,
    "display_order": 0,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "charts": [
        {
            "id": "223e4567-e89b-12d3-a456-426614174000",
            "template_id": "123e4567-e89b-12d3-a456-426614174000",
            "chart_name": "不採算製品の撤退-不採算製品から撤退した場合の利益改善効果は.json",
            "chart_data": {
                "data": [...],
                "layout": {...}
            },
            "chart_order": 0,
            "chart_type": "scatter",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }
    ]
}
```

### 施策別テンプレート一覧

指定された施策に紐づくテンプレート一覧を取得します。

```http
GET /api/v1/analysis/templates/policy/{policy}
```

**例:**

```http
GET /api/v1/analysis/templates/policy/施策①：不採算製品の撤退
```

### 施策・課題による検索

施策と課題の組み合わせでテンプレートを検索します。

```http
GET /api/v1/analysis/templates/search/by-policy-issue?policy={policy}&issue={issue}
```

**例:**

```http
GET /api/v1/analysis/templates/search/by-policy-issue?policy=市場拡大&issue=新規参入
```

## データシード

### CLIスクリプト（手動）

validation.ymlとチャートJSONからデータをインポートします。

```powershell
# 既存データをクリアして新規追加（デフォルト）
uv run python scripts/seed_templates.py

# 既存データを残して追加のみ
uv run python scripts/seed_templates.py --no-clear
```

**出力例:**

```
==========================================================
分析テンプレートデータシード
==========================================================
⚠️  既存データをクリアしてから新規追加します

🔄 データをインポートしています...

==========================================================
✅ インポート完了
==========================================================
📊 テンプレート作成数: 15
📈 チャート作成数: 20

💾 データベースに正常に保存されました
```

### データベースリセット時の自動シード

`scripts/reset-database.ps1` を実行すると、マイグレーション後に自動的にテンプレートデータがシードされます。

```powershell
.\scripts\reset-database.ps1
```

### テスト時の自動シード

テストで `seeded_templates` フィクスチャを使用すると、自動的にテンプレートデータがロードされます。

```python
@pytest.mark.asyncio
async def test_template_query(db_session, seeded_templates):
    # seeded_templatesフィクスチャで自動シード済み
    repo = AnalysisTemplateRepository(db_session)
    templates = await repo.list_active()
    assert len(templates) > 0
```

## 使用例

### Repository層での使用

```python
from app.repositories.analysis_template import AnalysisTemplateRepository

async def example_repository_usage(db: AsyncSession):
    """Repository層の使用例"""
    repo = AnalysisTemplateRepository(db)

    # テンプレート一覧取得
    templates = await repo.list_active(skip=0, limit=20)

    # 施策別テンプレート取得
    policy_templates = await repo.list_by_policy("市場拡大")

    # 施策・課題による検索
    template = await repo.get_by_policy_issue(
        policy="市場拡大",
        issue="新規参入"
    )

    # チャートデータを含む詳細取得
    template_with_charts = await repo.get_with_charts(template.id)
    print(f"Charts: {len(template_with_charts.charts)}")
```

### API経由での使用

```python
import httpx

async def example_api_usage():
    """API経由での使用例"""
    async with httpx.AsyncClient() as client:
        # テンプレート一覧取得
        response = await client.get(
            "http://localhost:8000/api/v1/analysis/templates?skip=0&limit=20"
        )
        templates = response.json()

        # 詳細取得
        template_id = templates[0]["id"]
        detail_response = await client.get(
            f"http://localhost:8000/api/v1/analysis/templates/{template_id}"
        )
        template_detail = detail_response.json()

        # チャートデータの取得
        charts = template_detail["charts"]
        for chart in charts:
            print(f"Chart: {chart['chart_name']}")
```

### フロントエンドでの使用

```typescript
// TypeScript/React での使用例
interface AnalysisTemplate {
  id: string;
  policy: string;
  issue: string;
  description: string;
  agent_prompt: string;
  initial_msg: string;
  initial_axis: Array<{
    name: string;
    option: string;
    multiple: boolean;
  }>;
  charts?: Array<{
    id: string;
    chart_name: string;
    chart_data: any;
    chart_type: string;
  }>;
}

async function fetchTemplates(): Promise<AnalysisTemplate[]> {
  const response = await fetch('/api/v1/analysis/templates?skip=0&limit=20');
  return response.json();
}

async function fetchTemplateDetail(id: string): Promise<AnalysisTemplate> {
  const response = await fetch(`/api/v1/analysis/templates/${id}`);
  return response.json();
}
```

## テスト

### Repository層のテスト

```python
# tests/app/repositories/test_analysis_template.py
import pytest
from app.repositories.analysis_template import AnalysisTemplateRepository

@pytest.mark.asyncio
async def test_list_by_policy(db_session, seeded_templates):
    """施策別のテンプレート一覧取得をテストします。"""
    repo = AnalysisTemplateRepository(db_session)

    templates = await repo.list_by_policy("施策①：不採算製品の撤退")

    assert len(templates) > 0
    for template in templates:
        assert template.policy == "施策①：不採算製品の撤退"
```

### API層のテスト

```python
# tests/app/api/routes/v1/test_analysis_templates.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_templates_success(client: AsyncClient, seeded_templates):
    """テンプレート一覧取得の成功ケース。"""
    response = await client.get("/api/v1/analysis/templates?skip=0&limit=20")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
```

## 関連ドキュメント

- [データベース基礎](../../01-getting-started/07-database-basics.md) - マイグレーションとシード
- [モックとフィクスチャ](../../05-testing/05-mocks-fixtures/index.md) - seeded_templatesフィクスチャ
- [レイヤードアーキテクチャ](../../02-architecture/02-layered-architecture.md) - Repository層の設計
- [データ分析機能ガイド](../09-analysis-feature/index.md) - 分析機能全体の概要

## まとめ

分析テンプレート機能により、以下が実現されました：

✅ **静的ファイルからデータベースへ** - validation.ymlとチャートJSONをDBに格納
✅ **動的なテンプレート管理** - アクティブ/非アクティブの切り替え、表示順序の管理
✅ **高速な検索** - 施策別・課題別のインデックス付き検索
✅ **自動データシード** - テスト/開発/リセット時の自動ロード
✅ **RESTful API** - 標準的なAPI経由でのアクセス
✅ **型安全なスキーマ** - Pydanticによるバリデーション
✅ **包括的なテスト** - Repository/APIレベルのテストカバレッジ

### 実装ファイル一覧

| ファイルパス | 説明 |
|-------------|------|
| `src/app/models/analysis_template.py` | テンプレートモデル |
| `src/app/models/analysis_template_chart.py` | チャートモデル |
| `src/app/repositories/analysis_template.py` | Repository層 |
| `src/app/schemas/analysis_template.py` | Pydanticスキーマ |
| `src/app/api/routes/v1/analysis_templates.py` | APIルーター |
| `src/app/utils/template_seeder.py` | データシード処理 |
| `scripts/seed_templates.py` | CLIスクリプト |
| `tests/app/repositories/test_analysis_template.py` | Repositoryテスト |
| `tests/app/api/routes/v1/test_analysis_templates.py` | APIテスト |
| `tests/conftest.py` | seeded_templatesフィクスチャ |
