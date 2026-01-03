# ダッシュボード フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| dashboard | ダッシュボード | / | ホーム画面 |

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `Card` | 統計カード、チャートコンテナ、プロジェクトカード | [02-shared-ui-components.md](../01-frontend-common/02-shared-ui-components.md) |
| `Badge` | ステータスバッジ、増減表示 | 同上 |
| `Button` | クイックアクションボタン | 同上 |
| `Select` | 期間選択 | 同上 |
| `Avatar` | ユーザーアイコン | 同上 |
| `Progress` | プロジェクト進捗バー | 同上 |
| `Skeleton` | ローディング表示 | 同上 |

### 1.3 コンポーネント構成

#### コンポーネントツリー

```text
features/dashboard/
├── api/
│   ├── get-stats.ts              # GET /dashboard/stats
│   ├── get-charts.ts             # GET /dashboard/charts
│   ├── get-activities.ts         # GET /dashboard/activities
│   └── index.ts
├── components/
│   ├── stats-grid/
│   │   ├── stats-grid.tsx        # 統計カードグリッド
│   │   ├── stat-card.tsx         # 統計カード（Card使用）
│   │   └── index.ts
│   ├── activity-chart/
│   │   ├── activity-chart.tsx    # アクティビティチャート
│   │   └── index.ts
│   ├── project-progress-chart/
│   │   ├── project-progress-chart.tsx  # プロジェクト進捗チャート（Progress使用）
│   │   └── index.ts
│   ├── chart-container/
│   │   ├── chart-container.tsx   # チャート共通コンテナ（Card使用）
│   │   └── index.ts
│   ├── activity-list/
│   │   ├── activity-list.tsx     # アクティビティリスト（Card使用）
│   │   ├── activity-item.tsx     # アクティビティアイテム（Avatar使用）
│   │   └── index.ts
│   ├── quick-actions/
│   │   ├── quick-actions.tsx     # クイックアクションボタン群（Button使用）
│   │   └── index.ts
│   ├── recent-projects/
│   │   ├── recent-projects.tsx   # 最近のプロジェクト（Card使用）
│   │   └── index.ts
│   ├── period-selector/
│   │   ├── period-selector.tsx   # 期間選択（Select使用）
│   │   └── index.ts
│   └── index.ts
├── routes/
│   └── dashboard/
│       ├── dashboard.tsx         # ダッシュボードコンテナ
│       ├── dashboard.hook.ts     # ダッシュボード用hook
│       └── index.ts
├── types/
│   ├── api.ts                    # API入出力の型
│   ├── domain.ts                 # ドメインモデル（Stats, Activity等）
│   └── index.ts
└── index.ts

app/
└── page.tsx                       # ダッシュボードページ → Dashboard
```

#### レイアウト構成

```text
┌─────────────────────────────────────────────────────────┐
│  ダッシュボード                            [期間選択 ▼] │
├─────────────┬─────────────┬─────────────┬───────────────┤
│  📁         │  📊         │  🌳         │  📄           │
│  参加       │  進行中     │  ドライバー │  アップロード │
│  プロジェクト│  セッション │  ツリー     │  ファイル     │
│  12         │  5          │  8          │  47           │
│  +2 今月    │  アクティブ │  +1 今週    │  合計         │
│  [StatsGrid > StatCard × 4]                            │
├─────────────┴─────────────┼─────────────┴───────────────┤
│  分析アクティビティ       │  プロジェクト進捗           │
│  ┌───────────────────┐   │  ┌───────────────────┐     │
│  │ [バーチャート]    │   │  │ [プログレスバー]  │     │
│  └───────────────────┘   │  └───────────────────┘     │
│  [ActivityChart]          │  [ProjectProgressChart]    │
├───────────────────────────┼─────────────────────────────┤
│  最近のアクティビティ     │  クイックアクセス           │
│  ┌───────────────────┐   │  ┌───────────────────┐     │
│  │ [アクティビティ   │   │  │ [クイックアクション]│    │
│  │  リスト]          │   │  │ [最近のプロジェクト]│    │
│  └───────────────────┘   │  └───────────────────┘     │
│  [ActivityList]           │  [QuickAccess]             │
└───────────────────────────┴─────────────────────────────┘
```

**コンポーネント責務:**

| コンポーネント | 責務 | 使用API |
|--------------|------|---------|
| StatsGrid | 統計カードのグリッドレイアウト表示 | - |
| StatCard | 各統計項目（プロジェクト数、セッション数等）の表示 | GET /dashboard/stats |
| ActivityChart | 分析アクティビティのバーチャート表示 | GET /dashboard/charts |
| ProjectProgressChart | プロジェクト進捗のプログレスバー表示 | GET /dashboard/charts |
| ChartContainer | チャートの共通ラッパー（タイトル、凡例等） | - |
| ActivityList | 最近のアクティビティリスト表示 | GET /dashboard/activities |
| ActivityItem | 個別のアクティビティアイテム表示 | - |
| QuickActions | クイックアクションボタン群 | - |
| RecentProjects | 最近のプロジェクト一覧表示 | GET /api/v1/projects |

---

---

## 2. 画面詳細設計

### 2.1 統計カード

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

### 2.2 分析アクティビティチャート

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| セッションバー | 棒グラフ | GET /dashboard/charts | sessionTrend.data[] | label→X軸, value→幅 |
| スナップショットバー | 棒グラフ | GET /dashboard/charts | snapshotTrend.data[] | label→X軸, value→幅 |
| 日付ラベル | テキスト | GET /dashboard/charts | sessionTrend.data[].label | MM/DD形式 |
| 値表示 | テキスト | GET /dashboard/charts | sessionTrend.data[].value | n / m 形式 |
| 凡例 | テキスト | - | - | 固定値 |

### 2.3 プロジェクト進捗

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| プロジェクト名 | テキスト | GET /dashboard/charts | projectProgress.data[].label | - |
| 進捗率 | 数値+% | GET /dashboard/charts | projectProgress.data[].value | n% 表示 |
| プログレスバー | バー | GET /dashboard/charts | projectProgress.data[].value | width: n% |
| バー色 | 色 | - | - | 進捗率に応じて変更 |

### 2.4 最近のアクティビティ

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| アイコン | アイコン | GET /dashboard/activities | activities[].resourceType | type→アイコン変換 |
| ユーザー名 | テキスト（太字） | GET /dashboard/activities | activities[].userName | - |
| アクション | テキスト | GET /dashboard/activities | activities[].action | created→作成しました等 |
| リソース名 | テキスト（太字） | GET /dashboard/activities | activities[].resourceName | - |
| 時間 | テキスト | GET /dashboard/activities | activities[].createdAt | 相対時間表示（n分前） |
| プロジェクト名 | テキスト | GET /dashboard/activities | activities[].details.projectName | - |
| すべて見るリンク | リンク | - | - | アクティビティ一覧へ遷移 |

### 2.5 クイックアクセス

| 画面項目 | 表示形式 | APIエンドポイント | フィールド | 遷移先 |
|---------|---------|------------------|-----------|--------|
| 新規プロジェクト | ボタン | - | - | /projects/new |
| 分析開始 | ボタン | - | - | /sessions/new |
| ツリー作成 | ボタン | - | - | /trees/new |
| ファイルアップロード | ボタン | - | - | /upload |

### 2.6 最近のプロジェクト

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| プロジェクト名 | テキスト | GET /api/v1/projects?sort=updated_at&order=desc&limit=5 | projects[].name | - |
| メンバー数 | テキスト | GET /api/v1/projects | projects[].member_count | n人のメンバー |
| 更新時間 | テキスト | GET /api/v1/projects | projects[].updated_at | 更新: n分前 |
| プロジェクトアイコン | アイコン | - | - | 固定 📁 |

**補足**: 最近のプロジェクトは、既存のプロジェクト一覧API（GET /api/v1/projects）を利用し、更新日時で降順ソート、上位5件を取得します。

### 2.7 期間選択

| 画面項目 | 入力形式 | APIエンドポイント | パラメータ | 値 |
|---------|---------|------------------|-----------|-----|
| 過去7日間 | 選択肢 | GET /dashboard/charts | days | 7 |
| 過去30日間 | 選択肢 | GET /dashboard/charts | days | 30 |
| 過去90日間 | 選択肢 | GET /dashboard/charts | days | 90 |

---

## 3. 画面項目・APIマッピング

### 3.1 統計データ取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 期間 | セレクト | - | `GET /dashboard/stats` | `days` | 7/30/90 |

### 3.2 チャートデータ取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 期間 | セレクト | - | `GET /dashboard/charts` | `days` | 7/30/90 |

### 3.3 アクティビティ取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 取得件数 | 数値 | - | `GET /dashboard/activities` | `limit` | デフォルト10、最大50 |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| ダッシュボードページ表示 | `GET /dashboard/stats` | 初期ロード |
| ダッシュボードページ表示 | `GET /dashboard/charts` | 並列取得 |
| ダッシュボードページ表示 | `GET /dashboard/activities` | 並列取得 |
| ダッシュボードページ表示 | `GET /api/v1/projects?sort=updated_at&limit=5` | 最近のプロジェクト |
| 期間選択変更 | `GET /dashboard/stats`, `GET /dashboard/charts` | 再取得 |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス権限がありませんメッセージ表示 |
| 500 Server Error | 各カードに"データ取得エラー"を表示 |
| Network Error | オフライン表示、リトライボタン |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 初期ロード | 複数APIを並列取得で高速化 |
| キャッシュ | React Query で統計データを5分間キャッシュ |
| チャート描画 | recharts でレンダリング最適化 |
| 再レンダリング | useMemo で統計カード表示を最適化 |
| スケルトン | 読み込み中はスケルトンUIを表示 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| D-001 | 参加プロジェクト数表示 | `GET /dashboard/stats` | StatisticsCards | 実装済 |
| D-002 | 進行中セッション数表示 | `GET /dashboard/stats` | StatisticsCards | 実装済 |
| D-003 | ドライバーツリー数表示 | `GET /dashboard/stats` | StatisticsCards | 実装済 |
| D-004 | アップロードファイル数表示 | `GET /dashboard/stats` | StatisticsCards | 実装済 |
| D-005 | 最近のアクティビティ表示 | `GET /dashboard/activities` | RecentActivities | 実装済 |
| D-006 | クイックアクセス・最近のプロジェクト表示 | `GET /projects` | QuickAccess, RecentProjects | 実装済 |

---

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| StatsGrid | Default | 統計グリッド表示 | 通常、ローディング |
| StatCard | Default | 統計カード表示 | 通常、増加、減少、変化なし |
| ActivityChart | Default | アクティビティチャート表示 | 通常、ローディング、空 |
| ProjectProgressChart | Default | プロジェクト進捗チャート | 通常、ローディング、空 |
| ActivityList | Default | アクティビティ一覧表示 | 通常、ローディング、空 |
| ActivityItem | Session | アクティビティ項目表示 | セッション、スナップショット、ツリー、ファイル |
| QuickActions | Default | クイックアクション表示 | 通常 |
| RecentProjects | Default | 最近のプロジェクト表示 | 通常、ローディング、空 |
| PeriodSelector | Default | 期間選択表示 | 通常、週、月、四半期 |

### 8.2 ストーリー実装例

```tsx
// features/dashboard/components/stat-card/stat-card.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { StatCard } from "./stat-card";
import type { StatCardProps } from "../../types";

const meta = {
  title: "features/dashboard/components/stat-card",
  component: StatCard,
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: "統計カードコンポーネント。ダッシュボードで数値を表示。",
      },
    },
  },
  tags: ["autodocs"],
  argTypes: {
    trend: {
      control: "select",
      options: ["up", "down", "neutral"],
    },
  },
} satisfies Meta<typeof StatCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    icon: "📁",
    title: "参加プロジェクト",
    value: 12,
    subtext: "+2 今月",
    trend: "up",
  },
};

export const Increase: Story = {
  args: {
    icon: "🌳",
    title: "ドライバーツリー",
    value: 8,
    subtext: "+1 今週",
    trend: "up",
  },
};

export const Decrease: Story = {
  args: {
    icon: "📊",
    title: "進行中セッション",
    value: 3,
    subtext: "-2 先週比",
    trend: "down",
  },
};

export const Neutral: Story = {
  args: {
    icon: "📄",
    title: "アップロードファイル",
    value: 47,
    subtext: "合計",
    trend: "neutral",
  },
};
```

```tsx
// features/dashboard/components/activity-list/activity-list.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { ActivityList } from "./activity-list";
import type { Activity } from "../../types";

const mockActivities: Activity[] = [
  {
    id: "1",
    userName: "山田太郎",
    action: "created",
    resourceType: "session",
    resourceName: "売上分析セッション",
    createdAt: "2024-01-15T10:30:00Z",
    details: { projectName: "2024年度売上分析" },
  },
  {
    id: "2",
    userName: "鈴木花子",
    action: "updated",
    resourceType: "tree",
    resourceName: "売上ドライバーツリー",
    createdAt: "2024-01-15T09:15:00Z",
    details: { projectName: "新規事業計画" },
  },
];

const meta = {
  title: "features/dashboard/components/activity-list",
  component: ActivityList,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: "アクティビティ一覧コンポーネント。最近の活動を表示。",
      },
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof ActivityList>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    activities: mockActivities,
  },
};

export const Loading: Story = {
  args: {
    activities: [],
    isLoading: true,
  },
};

export const Empty: Story = {
  args: {
    activities: [],
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| コンポーネント | ユニットテスト | 80%以上 | 統計カード、チャート、アクティビティ一覧 |
| ユーティリティ | ユニットテスト | 90%以上 | hooks, utils, 日付変換 |
| API連携 | 統合テスト | 70%以上 | API呼び出し、状態管理、エラーハンドリング |
| E2E | E2Eテスト | 主要フロー100% | ダッシュボード表示、期間切替、クイックアクション |

### 9.2 ユニットテスト例

```typescript
// features/dashboard/utils/__tests__/format-relative-time.test.ts
import { formatRelativeTime } from "../format-relative-time";

describe("formatRelativeTime", () => {
  it("1分未満は「たった今」と表示", () => {
    const now = new Date();
    const thirtySecondsAgo = new Date(now.getTime() - 30 * 1000);

    expect(formatRelativeTime(thirtySecondsAgo.toISOString())).toBe("たった今");
  });

  it("1時間未満は「n分前」と表示", () => {
    const now = new Date();
    const tenMinutesAgo = new Date(now.getTime() - 10 * 60 * 1000);

    expect(formatRelativeTime(tenMinutesAgo.toISOString())).toBe("10分前");
  });

  it("24時間未満は「n時間前」と表示", () => {
    const now = new Date();
    const threeHoursAgo = new Date(now.getTime() - 3 * 60 * 60 * 1000);

    expect(formatRelativeTime(threeHoursAgo.toISOString())).toBe("3時間前");
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
// features/dashboard/components/stat-card/__tests__/stat-card.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { StatCard } from "../stat-card";

describe("StatCard", () => {
  it("統計情報を正しく表示する", () => {
    render(
      <StatCard
        icon="📁"
        title="参加プロジェクト"
        value={12}
        subtext="+2 今月"
        trend="up"
      />
    );

    expect(screen.getByText("📁")).toBeInTheDocument();
    expect(screen.getByText("参加プロジェクト")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("+2 今月")).toBeInTheDocument();
  });

  it("上昇トレンドで緑色のスタイルを適用", () => {
    render(<StatCard title="テスト" value={10} subtext="+5" trend="up" />);

    const subtext = screen.getByText("+5");
    expect(subtext).toHaveClass("text-green-600");
  });

  it("下降トレンドで赤色のスタイルを適用", () => {
    render(<StatCard title="テスト" value={10} subtext="-3" trend="down" />);

    const subtext = screen.getByText("-3");
    expect(subtext).toHaveClass("text-red-600");
  });
});
```

### 9.4 E2Eテスト例

```typescript
// e2e/dashboard.spec.ts
import { test, expect } from "@playwright/test";

test.describe("ダッシュボード", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("ダッシュボードが表示される", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "ダッシュボード" })
    ).toBeVisible();
  });

  test("統計カードが4つ表示される", async ({ page }) => {
    await expect(page.getByTestId("stat-card")).toHaveCount(4);
  });

  test("期間を変更するとデータが更新される", async ({ page }) => {
    await page.getByLabel("期間").selectOption("30");

    // ローディング状態を確認
    await expect(page.getByTestId("stats-loading")).toBeVisible();

    // データが更新されたことを確認
    await expect(page.getByTestId("stat-card")).toHaveCount(4);
  });

  test("クイックアクションボタンが機能する", async ({ page }) => {
    await page.getByRole("button", { name: "新規プロジェクト" }).click();

    await expect(page).toHaveURL("/projects/new");
  });

  test("最近のプロジェクトをクリックして詳細に遷移", async ({ page }) => {
    await page.getByTestId("recent-project").first().click();

    await expect(page).toHaveURL(/\/projects\/\w+/);
  });
});
```

### 9.5 モックデータ

```typescript
// features/dashboard/__mocks__/handlers.ts
import { http, HttpResponse } from "msw";

export const dashboardHandlers = [
  http.get("/api/v1/dashboard/stats", ({ request }) => {
    const url = new URL(request.url);
    const days = url.searchParams.get("days") || "7";

    return HttpResponse.json({
      projects: { active: 12, change: 2 },
      sessions: { active: 5, change: 0 },
      trees: { total: 8, change: 1 },
      files: { total: 47, change: 5 },
      period: `${days}days`,
    });
  }),

  http.get("/api/v1/dashboard/charts", () => {
    return HttpResponse.json({
      sessionTrend: {
        data: [
          { label: "01/10", value: 3 },
          { label: "01/11", value: 5 },
          { label: "01/12", value: 2 },
          { label: "01/13", value: 7 },
          { label: "01/14", value: 4 },
        ],
      },
      projectProgress: {
        data: [
          { label: "売上分析プロジェクト", value: 75 },
          { label: "新規事業計画", value: 45 },
          { label: "コスト削減施策", value: 90 },
        ],
      },
    });
  }),

  http.get("/api/v1/dashboard/activities", () => {
    return HttpResponse.json({
      activities: [
        {
          id: "1",
          userName: "山田太郎",
          action: "created",
          resourceType: "session",
          resourceName: "売上分析セッション",
          createdAt: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
          details: { projectName: "2024年度売上分析" },
        },
        {
          id: "2",
          userName: "鈴木花子",
          action: "updated",
          resourceType: "tree",
          resourceName: "売上ドライバーツリー",
          createdAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
          details: { projectName: "新規事業計画" },
        },
      ],
    });
  }),
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計書**: [01-dashboard-design.md](./01-dashboard-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **モックアップ**: [../../03-mockup/pages/dashboard.js](../../03-mockup/pages/dashboard.js)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | DB-FRONTEND-001 |
| 対象ユースケース | D-001〜D-006 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `app/` |

---
