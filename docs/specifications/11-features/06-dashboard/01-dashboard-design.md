# ダッシュボード 統合設計書（D-001〜D-006）

## 1. 概要

### 1.1 目的

本ドキュメントは、CAMPシステムにおけるダッシュボード機能の統合設計仕様を定義します。ダッシュボードはユーザーのホーム画面として、参加プロジェクト・分析セッション・ドライバーツリーの統計情報、最近のアクティビティ、クイックアクセスを提供します。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能名 |
|---------|-------|--------|
| **統計表示** | D-001 | 参加プロジェクト数表示 |
| | D-002 | 進行中セッション数表示 |
| | D-003 | ドライバーツリー数表示 |
| | D-004 | アップロードファイル数表示 |
| **アクティビティ** | D-005 | 最近のアクティビティ表示 |
| **クイックアクセス** | D-006 | クイックアクセス・最近のプロジェクト表示 |

### 1.3 追加コンポーネント数

| コンポーネント | 数量 |
|--------------|------|
| データベーステーブル | 0（既存テーブル利用） |
| APIエンドポイント | 3 |
| Pydanticスキーマ | 11 |
| フロントエンド画面 | 1 |

---

## 2. データベース設計

### 2.1 利用テーブル

ダッシュボードは専用テーブルを持たず、既存テーブルから統計情報を集計します。

| テーブル名 | 用途 |
|-----------|------|
| project | プロジェクト統計 |
| project_member | ユーザー参加プロジェクト数 |
| analysis_session | セッション統計 |
| driver_tree | ドライバーツリー統計 |
| project_file | ファイル統計 |
| user_account | ユーザー統計 |
| user_activity | アクティビティログ |

### 2.2 統計クエリ例

```sql
-- 参加プロジェクト数（ユーザー別）
SELECT COUNT(DISTINCT p.id) as project_count
FROM project p
INNER JOIN project_member pm ON p.id = pm.project_id
WHERE pm.user_id = :user_id AND p.is_active = true;

-- 進行中セッション数
SELECT COUNT(*) as active_sessions
FROM analysis_session
WHERE status = 'active';

-- ドライバーツリー数
SELECT COUNT(*) as tree_count
FROM driver_tree;

-- アップロードファイル数
SELECT COUNT(*) as file_count, COALESCE(SUM(file_size), 0) as total_size
FROM project_file;
```

---

## 3. APIエンドポイント設計

### 3.1 エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/v1/dashboard/stats | 統計情報取得 |
| GET | /api/v1/dashboard/activities | アクティビティログ取得 |
| GET | /api/v1/dashboard/charts | チャートデータ取得 |

### 3.2 リクエスト/レスポンス定義

#### GET /api/v1/dashboard/stats（統計情報取得）

**レスポンス (200):**

```json
{
  "projects": {
    "total": 15,
    "active": 12,
    "archived": 3
  },
  "sessions": {
    "total": 45,
    "draft": 5,
    "active": 10,
    "completed": 30
  },
  "trees": {
    "total": 28,
    "draft": 3,
    "active": 15,
    "completed": 10
  },
  "users": {
    "total": 50,
    "active": 35
  },
  "files": {
    "total": 120,
    "totalSizeBytes": 536870912
  },
  "generatedAt": "2026-01-01T00:00:00Z"
}
```

#### GET /api/v1/dashboard/activities（アクティビティログ取得）

**クエリパラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| skip | int | - | 0 | スキップ数 |
| limit | int | - | 20 | 取得件数（最大100） |

**レスポンス (200):**

```json
{
  "activities": [
    {
      "id": "uuid",
      "userId": "uuid",
      "userName": "山田 太郎",
      "action": "created",
      "resourceType": "session",
      "resourceId": "uuid",
      "resourceName": "Q4売上分析",
      "details": {
        "projectName": "売上分析プロジェクト"
      },
      "createdAt": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 20
}
```

#### GET /api/v1/dashboard/charts（チャートデータ取得）

**クエリパラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| days | int | - | 30 | 集計対象日数（最大365） |

**レスポンス (200):**

```json
{
  "sessionTrend": {
    "chartType": "bar",
    "title": "セッション作成トレンド",
    "data": [
      {"label": "12/19", "value": 4},
      {"label": "12/20", "value": 6},
      {"label": "12/21", "value": 3}
    ],
    "xAxisLabel": "日付",
    "yAxisLabel": "件数"
  },
  "snapshotTrend": {
    "chartType": "bar",
    "title": "スナップショット作成トレンド",
    "data": [
      {"label": "12/19", "value": 2},
      {"label": "12/20", "value": 3},
      {"label": "12/21", "value": 1}
    ],
    "xAxisLabel": "日付",
    "yAxisLabel": "件数"
  },
  "treeTrend": {
    "chartType": "bar",
    "title": "ツリー作成トレンド",
    "data": [
      {"label": "12/19", "value": 2},
      {"label": "12/20", "value": 1},
      {"label": "12/21", "value": 3}
    ],
    "xAxisLabel": "日付",
    "yAxisLabel": "件数"
  },
  "projectDistribution": {
    "chartType": "pie",
    "title": "プロジェクト状態分布",
    "data": [
      {"label": "アクティブ", "value": 12},
      {"label": "アーカイブ", "value": 3}
    ],
    "xAxisLabel": null,
    "yAxisLabel": null
  },
  "projectProgress": {
    "chartType": "bar",
    "title": "プロジェクト進捗",
    "data": [
      {"label": "売上分析プロジェクト", "value": 75},
      {"label": "市場調査プロジェクト", "value": 45},
      {"label": "製品改善プロジェクト", "value": 90}
    ],
    "xAxisLabel": null,
    "yAxisLabel": "進捗率（%）"
  },
  "userActivity": {
    "chartType": "line",
    "title": "ユーザーアクティビティ",
    "data": [
      {"label": "12/19", "value": 15},
      {"label": "12/20", "value": 22},
      {"label": "12/21", "value": 18}
    ],
    "xAxisLabel": "日付",
    "yAxisLabel": "アクション数"
  },
  "generatedAt": "2026-01-01T00:00:00Z"
}
```

---

## 4. Pydanticスキーマ設計

### 4.1 統計情報スキーマ

```python
class ProjectStats(BaseCamelCaseModel):
    """プロジェクト統計"""
    total: int
    active: int
    archived: int

class SessionStats(BaseCamelCaseModel):
    """セッション統計"""
    total: int
    draft: int = 0
    active: int = 0
    completed: int = 0

class TreeStats(BaseCamelCaseModel):
    """ツリー統計"""
    total: int
    draft: int = 0
    active: int = 0
    completed: int = 0

class UserStats(BaseCamelCaseModel):
    """ユーザー統計"""
    total: int
    active: int

class FileStats(BaseCamelCaseModel):
    """ファイル統計"""
    total: int
    total_size_bytes: int = 0

class DashboardStatsResponse(BaseCamelCaseModel):
    """ダッシュボード統計レスポンス"""
    projects: ProjectStats
    sessions: SessionStats
    trees: TreeStats
    users: UserStats
    files: FileStats
    generated_at: datetime
```

### 4.2 アクティビティスキーマ

```python
class ActivityLogResponse(BaseCamelCaseModel):
    """アクティビティログ"""
    id: UUID
    user_id: UUID
    user_name: str
    action: str  # created/updated/deleted/accessed
    resource_type: str  # project/session/tree/file
    resource_id: UUID
    resource_name: str
    details: dict[str, Any] | None = None
    created_at: datetime

class DashboardActivitiesResponse(BaseCamelCaseModel):
    """アクティビティ一覧レスポンス"""
    activities: list[ActivityLogResponse] = []
    total: int
    skip: int
    limit: int
```

### 4.3 チャートスキーマ

```python
class ChartDataPoint(BaseCamelCaseModel):
    """チャートデータポイント"""
    label: str
    value: float

class ChartDataResponse(BaseCamelCaseModel):
    """チャートデータ"""
    chart_type: str  # line/bar/pie/area
    title: str
    data: list[ChartDataPoint] = []
    x_axis_label: str | None = None
    y_axis_label: str | None = None

class DashboardChartsResponse(BaseCamelCaseModel):
    """チャート一覧レスポンス"""
    session_trend: ChartDataResponse
    snapshot_trend: ChartDataResponse
    tree_trend: ChartDataResponse
    project_distribution: ChartDataResponse
    project_progress: ChartDataResponse
    user_activity: ChartDataResponse
    generated_at: datetime
```

---

## 5. サービス層設計

### 5.1 サービスクラス

```python
class DashboardService:
    """ダッシュボードサービス"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> DashboardStatsResponse:
        """統計情報を取得"""
        projects = await self._get_project_stats()
        sessions = await self._get_session_stats()
        trees = await self._get_tree_stats()
        users = await self._get_user_stats()
        files = await self._get_file_stats()

        return DashboardStatsResponse(
            projects=projects,
            sessions=sessions,
            trees=trees,
            users=users,
            files=files,
            generated_at=datetime.utcnow()
        )

    async def get_activities(
        self, skip: int = 0, limit: int = 20
    ) -> DashboardActivitiesResponse:
        """アクティビティログを取得"""
        # user_activityテーブルから取得
        ...

    async def get_charts(self, days: int = 30) -> DashboardChartsResponse:
        """チャートデータを取得"""
        session_trend = await self._get_session_trend(days)
        snapshot_trend = await self._get_snapshot_trend(days)
        tree_trend = await self._get_tree_trend(days)
        project_distribution = await self._get_project_distribution()
        project_progress = await self._get_project_progress()
        user_activity = await self._get_user_activity_trend(days)

        return DashboardChartsResponse(
            session_trend=session_trend,
            snapshot_trend=snapshot_trend,
            tree_trend=tree_trend,
            project_distribution=project_distribution,
            project_progress=project_progress,
            user_activity=user_activity,
            generated_at=datetime.utcnow()
        )

    async def _get_project_stats(self) -> ProjectStats:
        """プロジェクト統計を取得"""
        ...

    async def _get_session_stats(self) -> SessionStats:
        """セッション統計を取得"""
        ...

    async def _get_tree_stats(self) -> TreeStats:
        """ツリー統計を取得"""
        ...

    async def _get_user_stats(self) -> UserStats:
        """ユーザー統計を取得"""
        ...

    async def _get_file_stats(self) -> FileStats:
        """ファイル統計を取得"""
        ...

    async def _get_session_trend(self, days: int) -> ChartDataResponse:
        """セッション作成トレンドを取得"""
        ...

    async def _get_snapshot_trend(self, days: int) -> ChartDataResponse:
        """スナップショット作成トレンドを取得"""
        ...

    async def _get_tree_trend(self, days: int) -> ChartDataResponse:
        """ツリー作成トレンドを取得"""
        ...

    async def _get_project_distribution(self) -> ChartDataResponse:
        """プロジェクト状態分布を取得"""
        ...

    async def _get_project_progress(self) -> ChartDataResponse:
        """プロジェクト進捗を取得"""
        ...

    async def _get_user_activity_trend(self, days: int) -> ChartDataResponse:
        """ユーザーアクティビティトレンドを取得"""
        ...
```

---

## 6. フロントエンド設計

### 6.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| dashboard | ダッシュボード | / | ホーム画面 |

### 6.2 コンポーネント構成

```text
features/dashboard/
├── components/
│   ├── StatsGrid/
│   │   ├── StatsGrid.tsx
│   │   └── StatCard.tsx
│   ├── Charts/
│   │   ├── ActivityChart.tsx
│   │   ├── ProjectProgressChart.tsx
│   │   └── ChartContainer.tsx
│   ├── ActivityList/
│   │   ├── ActivityList.tsx
│   │   └── ActivityItem.tsx
│   └── QuickAccess/
│       ├── QuickActions.tsx
│       └── RecentProjects.tsx
├── hooks/
│   ├── useDashboardStats.ts
│   ├── useDashboardActivities.ts
│   └── useDashboardCharts.ts
├── api/
│   └── dashboardApi.ts
└── types/
    └── dashboard.ts
```

### 6.3 レイアウト構成

```text
┌─────────────────────────────────────────────────────────┐
│  ダッシュボード                            [期間選択 ▼] │
├─────────────┬─────────────┬─────────────┬───────────────┤
│  📁         │  📊         │  🌳         │  📄           │
│  参加       │  進行中     │  ドライバー │  アップロード │
│  プロジェクト│  セッション │  ツリー     │  ファイル     │
│  12         │  5          │  8          │  47           │
│  +2 今月    │  アクティブ │  +1 今週    │  合計         │
├─────────────┴─────────────┼─────────────┴───────────────┤
│  分析アクティビティ       │  プロジェクト進捗           │
│  ┌───────────────────┐   │  ┌───────────────────┐     │
│  │ [バーチャート]    │   │  │ [プログレスバー]  │     │
│  └───────────────────┘   │  └───────────────────┘     │
├───────────────────────────┼─────────────────────────────┤
│  最近のアクティビティ     │  クイックアクセス           │
│  ┌───────────────────┐   │  ┌───────────────────┐     │
│  │ [アクティビティ   │   │  │ [クイックアクション]│    │
│  │  リスト]          │   │  │ [最近のプロジェクト]│    │
│  └───────────────────┘   │  └───────────────────┘     │
└───────────────────────────┴─────────────────────────────┘
```

---

## 7. 画面項目・APIマッピング

### 7.1 統計カード

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 参加プロジェクト | 数値 | GET /dashboard/stats | projects.active | - |
| 増減表示 | テキスト | GET /dashboard/stats | （前期間比較） | +n 今月 |
| 進行中セッション | 数値 | GET /dashboard/stats | sessions.active | - |
| ステータス | テキスト | - | - | 固定値"アクティブ" |
| ドライバーツリー | 数値 | GET /dashboard/stats | trees.total | - |
| 増減表示 | テキスト | GET /dashboard/stats | （前期間比較） | +n 今週 |
| アップロードファイル | 数値 | GET /dashboard/stats | files.total | - |
| 合計表示 | テキスト | - | - | 固定値"合計" |

### 7.2 分析アクティビティチャート

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| セッションバー | 棒グラフ | GET /dashboard/charts | sessionTrend.data[] | label→X軸, value→幅 |
| スナップショットバー | 棒グラフ | GET /dashboard/charts | snapshotTrend.data[] | label→X軸, value→幅 |
| 日付ラベル | テキスト | GET /dashboard/charts | sessionTrend.data[].label | MM/DD形式 |
| 値表示 | テキスト | GET /dashboard/charts | sessionTrend.data[].value | n / m 形式 |
| 凡例 | テキスト | - | - | 固定値 |

### 7.3 プロジェクト進捗

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| プロジェクト名 | テキスト | GET /dashboard/charts | projectProgress.data[].label | - |
| 進捗率 | 数値+% | GET /dashboard/charts | projectProgress.data[].value | n% 表示 |
| プログレスバー | バー | GET /dashboard/charts | projectProgress.data[].value | width: n% |
| バー色 | 色 | - | - | 進捗率に応じて変更 |

### 7.4 最近のアクティビティ

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| アイコン | アイコン | GET /dashboard/activities | activities[].resourceType | type→アイコン変換 |
| ユーザー名 | テキスト（太字） | GET /dashboard/activities | activities[].userName | - |
| アクション | テキスト | GET /dashboard/activities | activities[].action | created→作成しました等 |
| リソース名 | テキスト（太字） | GET /dashboard/activities | activities[].resourceName | - |
| 時間 | テキスト | GET /dashboard/activities | activities[].createdAt | 相対時間表示（n分前） |
| プロジェクト名 | テキスト | GET /dashboard/activities | activities[].details.projectName | - |
| すべて見るリンク | リンク | - | - | アクティビティ一覧へ遷移 |

### 7.5 クイックアクセス

| 画面項目 | 表示形式 | APIエンドポイント | フィールド | 遷移先 |
|---------|---------|------------------|-----------|--------|
| 新規プロジェクト | ボタン | - | - | /projects/new |
| 分析開始 | ボタン | - | - | /sessions/new |
| ツリー作成 | ボタン | - | - | /trees/new |
| ファイルアップロード | ボタン | - | - | /upload |

### 7.6 最近のプロジェクト

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| プロジェクト名 | テキスト | GET /api/v1/projects?sort=updated_at&order=desc&limit=5 | projects[].name | - |
| メンバー数 | テキスト | GET /api/v1/projects | projects[].member_count | n人のメンバー |
| 更新時間 | テキスト | GET /api/v1/projects | projects[].updated_at | 更新: n分前 |
| プロジェクトアイコン | アイコン | - | - | 固定 📁 |

**補足**: 最近のプロジェクトは、既存のプロジェクト一覧API（GET /api/v1/projects）を利用し、更新日時で降順ソート、上位5件を取得します。

### 7.7 期間選択

| 画面項目 | 入力形式 | APIエンドポイント | パラメータ | 値 |
|---------|---------|------------------|-----------|-----|
| 過去7日間 | 選択肢 | GET /dashboard/charts | days | 7 |
| 過去30日間 | 選択肢 | GET /dashboard/charts | days | 30 |
| 過去90日間 | 選択肢 | GET /dashboard/charts | days | 90 |

---

## 8. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|--------|-----|------|-----------|
| D-001 | 参加プロジェクト数表示 | GET /dashboard/stats | dashboard | 実装済 |
| D-002 | 進行中セッション数表示 | GET /dashboard/stats | dashboard | 実装済 |
| D-003 | ドライバーツリー数表示 | GET /dashboard/stats | dashboard | 実装済 |
| D-004 | アップロードファイル数表示 | GET /dashboard/stats | dashboard | 実装済 |
| D-005 | 最近のアクティビティ表示 | GET /dashboard/activities | dashboard | 実装済 |
| D-006 | クイックアクセス・最近のプロジェクト表示 | - | dashboard | 実装済 |

カバレッジ: 6/6 = 100%

---

### ドキュメント管理情報

- **作成日**: 2026年1月1日
- **更新日**: 2026年1月1日
- **バージョン**: 1.1
- **変更履歴**:
  - v1.1 (2026-01-01): snapshotTrend、projectProgressのAPI定義追加、最近のプロジェクト取得方法を明確化
  - v1.0 (2026-01-01): 初版作成
