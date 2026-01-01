# ダッシュボード バックエンド設計書（D-001〜D-006）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムにおけるダッシュボード機能の統合設計仕様を定義します。ダッシュボードはユーザーのホーム画面として、参加プロジェクト・分析セッション・ドライバーツリーの統計情報、最近のアクティビティ、クイックアクセスを提供します。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|--------|
| **統計表示** | D-001 | 参加プロジェクト数表示 |
| | D-002 | 進行中セッション数表示 |
| | D-003 | ドライバーツリー数表示 |
| | D-004 | アップロードファイル数表示 |
| **アクティビティ** | D-005 | 最近のアクティビティ表示 |
| **クイックアクセス** | D-006 | クイックアクセス・最近のプロジェクト表示 |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 0（既存テーブル利用） |
| APIエンドポイント | 3 |
| Pydanticスキーマ | 11 |
| フロントエンド画面 | 1 |

---

## 2. データベース設計

### 2.1 関連テーブル一覧

ダッシュボードは専用テーブルを持たず、既存テーブルから統計情報を集計します。

| テーブル名 | 説明 |
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

### 4.1 Enum定義

```python
from enum import Enum

class ActivityActionEnum(str, Enum):
    """アクティビティアクション種別"""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ACCESSED = "accessed"

class ResourceTypeEnum(str, Enum):
    """リソース種別"""
    PROJECT = "project"
    SESSION = "session"
    TREE = "tree"
    FILE = "file"

class ChartTypeEnum(str, Enum):
    """チャート種別"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
```

### 4.2 Info/Dataスキーマ

```python
class ProjectStats(CamelCaseModel):
    """プロジェクト統計"""
    total: int
    active: int
    archived: int

class SessionStats(CamelCaseModel):
    """セッション統計"""
    total: int
    draft: int = 0
    active: int = 0
    completed: int = 0

class TreeStats(CamelCaseModel):
    """ツリー統計"""
    total: int
    draft: int = 0
    active: int = 0
    completed: int = 0

class UserStats(CamelCaseModel):
    """ユーザー統計"""
    total: int
    active: int

class FileStats(CamelCaseModel):
    """ファイル統計"""
    total: int
    total_size_bytes: int = 0

class ChartDataPoint(CamelCaseModel):
    """チャートデータポイント"""
    label: str
    value: float

class ChartDataInfo(CamelCaseModel):
    """チャートデータ情報"""
    chart_type: ChartTypeEnum
    title: str
    data: list[ChartDataPoint] = []
    x_axis_label: str | None = None
    y_axis_label: str | None = None

class ActivityLogInfo(CamelCaseModel):
    """アクティビティログ情報"""
    id: UUID
    user_id: UUID
    user_name: str
    action: ActivityActionEnum
    resource_type: ResourceTypeEnum
    resource_id: UUID
    resource_name: str
    details: dict[str, Any] | None = None
    created_at: datetime
```

### 4.3 Request/Responseスキーマ

```python
class DashboardStatsResponse(CamelCaseModel):
    """ダッシュボード統計レスポンス"""
    projects: ProjectStats
    sessions: SessionStats
    trees: TreeStats
    users: UserStats
    files: FileStats
    generated_at: datetime

class DashboardActivitiesResponse(CamelCaseModel):
    """アクティビティ一覧レスポンス"""
    activities: list[ActivityLogInfo] = []
    total: int
    skip: int
    limit: int

class DashboardChartsResponse(CamelCaseModel):
    """チャート一覧レスポンス"""
    session_trend: ChartDataInfo
    snapshot_trend: ChartDataInfo
    tree_trend: ChartDataInfo
    project_distribution: ChartDataInfo
    project_progress: ChartDataInfo
    user_activity: ChartDataInfo
    generated_at: datetime
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| DashboardService | ダッシュボード統計・チャート・アクティビティ管理 |

**DashboardServiceメソッド一覧:**

| メソッド名 | 戻り値型 | 説明 |
|-----------|---------|------|
| get_stats() | DashboardStatsResponse | 統計情報を集計して取得 |
| get_activities(skip, limit) | DashboardActivitiesResponse | アクティビティログを取得 |
| get_charts(days) | DashboardChartsResponse | チャートデータを取得 |
| _get_project_stats() | ProjectStats | プロジェクト統計を取得 |
| _get_session_stats() | SessionStats | セッション統計を取得 |
| _get_tree_stats() | TreeStats | ツリー統計を取得 |
| _get_user_stats() | UserStats | ユーザー統計を取得 |
| _get_file_stats() | FileStats | ファイル統計を取得 |
| _get_session_trend(days) | ChartDataInfo | セッション作成トレンドを取得 |
| _get_snapshot_trend(days) | ChartDataInfo | スナップショット作成トレンドを取得 |
| _get_tree_trend(days) | ChartDataInfo | ツリー作成トレンドを取得 |
| _get_project_distribution() | ChartDataInfo | プロジェクト状態分布を取得 |
| _get_project_progress() | ChartDataInfo | プロジェクト進捗を取得 |
| _get_user_activity_trend(days) | ChartDataInfo | ユーザーアクティビティトレンドを取得 |

### 5.2 主要メソッド

#### get_stats() - 統計情報取得

```python
class DashboardService:
    """ダッシュボードサービス"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> DashboardStatsResponse:
        """
        統計情報を取得

        Returns:
            DashboardStatsResponse: プロジェクト、セッション、ツリー、ユーザー、ファイルの統計情報
        """
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
```

#### get_activities() - アクティビティログ取得

```python
    async def get_activities(
        self, skip: int = 0, limit: int = 20
    ) -> DashboardActivitiesResponse:
        """
        アクティビティログを取得

        Args:
            skip: スキップ数
            limit: 取得件数（最大100）

        Returns:
            DashboardActivitiesResponse: アクティビティログ一覧
        """
        # 取得件数の上限チェック
        limit = min(limit, 100)

        # user_activityテーブルから取得
        query = (
            select(UserActivity)
            .order_by(UserActivity.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        activities = result.scalars().all()

        # 総件数取得
        count_query = select(func.count(UserActivity.id))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # レスポンス変換
        activity_list = [
            ActivityLogInfo(
                id=activity.id,
                user_id=activity.user_id,
                user_name=activity.user_name,
                action=ActivityActionEnum(activity.action),
                resource_type=ResourceTypeEnum(activity.resource_type),
                resource_id=activity.resource_id,
                resource_name=activity.resource_name,
                details=activity.details,
                created_at=activity.created_at
            )
            for activity in activities
        ]

        return DashboardActivitiesResponse(
            activities=activity_list,
            total=total,
            skip=skip,
            limit=limit
        )
```

#### get_charts() - チャートデータ取得

```python
    async def get_charts(self, days: int = 30) -> DashboardChartsResponse:
        """
        チャートデータを取得

        Args:
            days: 集計対象日数（最大365）

        Returns:
            DashboardChartsResponse: 各種チャートデータ
        """
        # 日数の上限チェック
        days = min(days, 365)

        # 各チャートデータを並行取得
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
```

#### _get_project_stats() - プロジェクト統計取得

```python
    async def _get_project_stats(self) -> ProjectStats:
        """
        プロジェクト統計を取得

        Returns:
            ProjectStats: 総数、アクティブ数、アーカイブ数
        """
        # 総数
        total_query = select(func.count(Project.id))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()

        # アクティブ数
        active_query = select(func.count(Project.id)).where(Project.is_active == True)
        active_result = await self.db.execute(active_query)
        active = active_result.scalar()

        # アーカイブ数
        archived = total - active

        return ProjectStats(
            total=total,
            active=active,
            archived=archived
        )
```

#### _get_session_trend() - セッション作成トレンド取得

```python
    async def _get_session_trend(self, days: int) -> ChartDataInfo:
        """
        セッション作成トレンドを取得

        Args:
            days: 集計対象日数

        Returns:
            ChartDataInfo: セッション作成トレンドチャート
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        # 日付ごとにグループ化して集計
        query = (
            select(
                func.date(AnalysisSession.created_at).label('date'),
                func.count(AnalysisSession.id).label('count')
            )
            .where(AnalysisSession.created_at >= start_date)
            .group_by(func.date(AnalysisSession.created_at))
            .order_by(func.date(AnalysisSession.created_at))
        )
        result = await self.db.execute(query)
        rows = result.all()

        # チャートデータポイント作成
        data_points = [
            ChartDataPoint(
                label=row.date.strftime('%m/%d'),
                value=float(row.count)
            )
            for row in rows
        ]

        return ChartDataInfo(
            chart_type=ChartTypeEnum.BAR,
            title="セッション作成トレンド",
            data=data_points,
            x_axis_label="日付",
            y_axis_label="件数"
        )
```

---

## 6. フロントエンド設計

フロントエンド設計の詳細は以下を参照してください：

- [ダッシュボード フロントエンド設計書](./02-dashboard-frontend-design.md)

---

## 7. ユースケースカバレッジ表

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

## 8. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/pages/index.js](../../03-mockup/pages/index.js)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | DB-DESIGN-001 |
| 対象ユースケース | D-001〜D-006 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/services/dashboard/` |
|  | `src/app/schemas/dashboard/` |
|  | `src/app/api/routes/v1/dashboard/` |
