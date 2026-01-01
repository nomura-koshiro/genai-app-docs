# ダッシュボード フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| dashboard | ダッシュボード | / | ホーム画面 |

### 1.2 コンポーネント構成

#### コンポーネントツリー

```text
features/dashboard/
├── components/
│   ├── StatsGrid/
│   │   ├── StatsGrid.tsx          # 統計カードグリッド
│   │   └── StatCard.tsx           # 統計カード
│   ├── Charts/
│   │   ├── ActivityChart.tsx      # アクティビティチャート
│   │   ├── ProjectProgressChart.tsx  # プロジェクト進捗チャート
│   │   └── ChartContainer.tsx     # チャート共通コンテナ
│   ├── ActivityList/
│   │   ├── ActivityList.tsx       # アクティビティリスト
│   │   └── ActivityItem.tsx       # アクティビティアイテム
│   └── QuickAccess/
│       ├── QuickActions.tsx       # クイックアクションボタン群
│       └── RecentProjects.tsx     # 最近のプロジェクト
├── hooks/
│   ├── useDashboardStats.ts       # 統計データフック
│   ├── useDashboardActivities.ts  # アクティビティデータフック
│   └── useDashboardCharts.ts      # チャートデータフック
├── api/
│   └── dashboardApi.ts            # API通信関数
└── types/
    └── dashboard.ts               # 型定義
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
