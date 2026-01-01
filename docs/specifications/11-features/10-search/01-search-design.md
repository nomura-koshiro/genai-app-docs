# グローバル検索 バックエンド設計書（S-001〜S-002）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムのグローバル検索機能（ユースケースS-001〜S-002）の実装に必要なバックエンドの設計を定義する。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|---------|
| **検索** | S-001 | プロジェクト・セッション・ファイル・ツリーを横断検索する |
| | S-002 | 検索結果をフィルタリングする |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| APIエンドポイント | 1エンドポイント |
| Pydanticスキーマ | 6スキーマ |
| サービス | 1サービス |
| フロントエンド画面 | 0画面（ヘッダー内コンポーネント） |

---

## 2. データベース設計

グローバル検索は既存のテーブルを参照するため、追加のテーブルは不要です。

### 2.1 検索対象テーブル

| テーブル名 | 検索対象フィールド |
|-----------|-------------------|
| project | name, description |
| session | name, description |
| file | filename, description |
| driver_tree | name, description |

---

## 3. APIエンドポイント設計

### 3.1 エンドポイント一覧

| メソッド | エンドポイント | 説明 | 権限 | 対応UC |
|---------|---------------|------|------|--------|
| GET | `/api/v1/search` | グローバル検索 | 認証済 | S-001, S-002 |

### 3.2 リクエスト/レスポンス定義

#### GET /api/v1/search（グローバル検索）

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| q | string | ○ | 検索クエリ（2文字以上） |
| type | string | - | 検索対象タイプ（project/session/file/tree）、カンマ区切りで複数指定可 |
| project_id | UUID | - | プロジェクトIDで絞り込み |
| limit | int | - | 取得件数（デフォルト: 20、最大: 100） |

**レスポンス**: `SearchResponse`

```json
{
  "results": [
    {
      "type": "project",
      "id": "uuid",
      "name": "売上分析プロジェクト",
      "description": "Q4売上の分析...",
      "matchedField": "name",
      "highlightedText": "<mark>売上</mark>分析プロジェクト",
      "projectId": null,
      "projectName": null,
      "updatedAt": "datetime",
      "url": "/projects/uuid"
    },
    {
      "type": "session",
      "id": "uuid",
      "name": "Q4売上分析セッション",
      "description": "四半期売上の詳細分析",
      "matchedField": "name",
      "highlightedText": "Q4<mark>売上</mark>分析セッション",
      "projectId": "uuid",
      "projectName": "売上分析プロジェクト",
      "updatedAt": "datetime",
      "url": "/projects/uuid/sessions/uuid"
    }
  ],
  "total": 15,
  "query": "売上",
  "types": ["project", "session", "file", "tree"]
}
```

---

## 4. Pydanticスキーマ設計

### 4.1 Enum定義

```python
class SearchTypeEnum(str, Enum):
    """検索対象タイプ"""
    project = "project"
    session = "session"
    file = "file"
    tree = "tree"
```

### 4.2 Info/Dataスキーマ

```python
class SearchResultInfo(CamelCaseModel):
    """検索結果情報"""
    type: SearchTypeEnum
    id: UUID
    name: str
    description: str | None = None
    matched_field: str
    highlighted_text: str
    project_id: UUID | None = None
    project_name: str | None = None
    updated_at: datetime
    url: str
```

### 4.3 Request/Responseスキーマ

```python
class SearchQuery(CamelCaseModel):
    """検索クエリ"""
    q: str = Field(..., min_length=2, max_length=100)
    type: list[SearchTypeEnum] | None = None
    project_id: UUID | None = None
    limit: int = Field(default=20, ge=1, le=100)

class SearchResponse(CamelCaseModel):
    """検索レスポンス"""
    results: list[SearchResultInfo]
    total: int
    query: str
    types: list[SearchTypeEnum]
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| GlobalSearchService | 横断検索、結果マージ、ハイライト生成 |

### 5.2 主要メソッド

#### GlobalSearchService

```python
class GlobalSearchService:
    # 検索実行
    async def search(
        query: str,
        types: list[SearchTypeEnum] | None,
        project_id: UUID | None,
        user_id: UUID,
        limit: int = 20
    ) -> SearchResponse

    # 個別検索（内部メソッド）
    async def _search_projects(query: str, user_id: UUID, limit: int) -> list[SearchResultInfo]
    async def _search_sessions(query: str, user_id: UUID, project_id: UUID | None, limit: int) -> list[SearchResultInfo]
    async def _search_files(query: str, user_id: UUID, project_id: UUID | None, limit: int) -> list[SearchResultInfo]
    async def _search_trees(query: str, user_id: UUID, project_id: UUID | None, limit: int) -> list[SearchResultInfo]

    # ハイライト生成
    def _highlight_text(text: str, query: str) -> str

    # 結果マージ・ソート
    def _merge_results(results: list[list[SearchResultInfo]], limit: int) -> list[SearchResultInfo]
```

---

## 6. フロントエンド設計

フロントエンド設計の詳細は以下を参照してください：

- [グローバル検索 フロントエンド設計書](./02-search-frontend-design.md)

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|-------|-----|------|-----------|
| S-001 | プロジェクト・セッション・ファイル・ツリーを横断検索する | `GET /search` | header-search | 設計済 |
| S-002 | 検索結果をフィルタリングする | `GET /search?type=` | header-search | 設計済 |

---

## 8. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/index.html](../../03-mockup/index.html)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | SEARCH-DESIGN-001 |
| 対象ユースケース | S-001〜S-002 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/schemas/search/search.py` |
|  | `src/app/api/routes/v1/search/search.py` |
|  | `src/app/services/search/global_search.py` |
