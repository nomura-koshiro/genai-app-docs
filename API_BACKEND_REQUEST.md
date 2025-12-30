# バックエンドAPI拡張リクエスト

フロントエンドUIが必要とするが、現在のOpenAPIに含まれていないフィールド・エンドポイントの一覧です。

---

## 1. 分析セッション（Analysis Session）

### 1.1 カテゴリ情報の追加

**対象エンドポイント:**

- `GET /api/v1/project/{project_id}/analysis/session/{session_id}`
- `GET /api/v1/project/{project_id}/analysis/session`

**リクエスト内容:**
セッションレスポンスに検証カテゴリ（Validation）情報のリレーション展開を追加してほしい。

```json
{
  "id": "...",
  "issueId": "...",
  "issue": { "id": "...", "name": "課題名" },
  "validation": {  // 追加希望
    "id": "...",
    "name": "検証カテゴリ名"
  },
  ...
}
```

**フロントエンド使用箇所:**

- [session-detail.hook.ts:86](src/features/sessions/routes/session-detail/session-detail.hook.ts#L86)

---

### 1.2 インサイト情報

**対象エンドポイント:**

- `GET /api/v1/project/{project_id}/analysis/session/{session_id}`

**リクエスト内容:**
分析結果から抽出されたインサイト情報を返すフィールドまたは専用エンドポイントが必要。

```json
{
  "insights": [
    {
      "id": "...",
      "title": "売上トレンド",
      "description": "前年比15%増加",
      "type": "trend"
    }
  ],
  "insightCards": [
    {
      "icon": "TrendingUp",
      "label": "売上成長率",
      "value": "+15%",
      "change": "+3%",
      "isPositive": true
    }
  ]
}
```

**フロントエンド使用箇所:**

- [session-detail.hook.ts:103-107](src/features/sessions/routes/session-detail/session-detail.hook.ts#L103-L107)

---

### 1.3 関連セッション

**対象エンドポイント:**

- 新規エンドポイント: `GET /api/v1/project/{project_id}/analysis/session/{session_id}/related`

**リクエスト内容:**
同じ課題や同じデータを使用している関連セッションを取得するエンドポイント。

```json
{
  "relatedSessions": [
    {
      "id": "...",
      "name": "セッション名",
      "date": "2025-01-15",
      "status": "completed"
    }
  ]
}
```

**フロントエンド使用箇所:**

- [session-detail.hook.ts:109-110](src/features/sessions/routes/session-detail/session-detail.hook.ts#L109-L110)

---

### 1.4 スナップショット説明文

**対象エンドポイント:**

- `GET /api/v1/project/{project_id}/analysis/session/{session_id}/snapshots`
- `POST /api/v1/project/{project_id}/analysis/session/{session_id}/snapshots`

**リクエスト内容:**
スナップショットレスポンスに `description` フィールドを追加。

```json
{
  "id": "...",
  "snapshotOrder": 1,
  "description": "初期分析結果",  // 追加希望
  ...
}
```

**フロントエンド使用箇所:**

- [snapshots.hook.ts:40](src/features/sessions/routes/snapshots/snapshots.hook.ts#L40)

---

### 1.5 スナップショット復元API

**対象エンドポイント:**

- 新規エンドポイント: `POST /api/v1/project/{project_id}/analysis/session/{session_id}/snapshots/{snapshot_id}/restore`

**リクエスト内容:**
指定したスナップショットの状態にセッションを復元するエンドポイント。

```json
// Request: POST /api/v1/project/{project_id}/analysis/session/{session_id}/snapshots/{snapshot_id}/restore
// Response:
{
  "success": true,
  "restoredSnapshot": { ... },
  "session": { ... }
}
```

**フロントエンド使用箇所:**

- [snapshots.hook.ts:51](src/features/sessions/routes/snapshots/snapshots.hook.ts#L51)

---

## 2. 検証マスタ（Validation）

### 2.1 フィールド追加

**対象エンドポイント:**

- `GET /api/v1/admin/validation`
- `GET /api/v1/admin/validation/{validation_id}`

**リクエスト内容:**
ValidationResponseに以下のフィールドを追加。

```json
{
  "id": "...",
  "name": "検証名",
  "validationOrder": 1,
  "description": "検証の説明文",  // 追加希望
  "issueCount": 5,                // 追加希望（関連課題数）
  "status": "active",             // 追加希望（active/inactive）
  "createdAt": "...",
  "updatedAt": "..."
}
```

**フロントエンド使用箇所:**

- [verifications.hook.ts:17-22](src/features/admin/routes/verifications/verifications.hook.ts#L17-L22)

---

## 3. ドライバーツリー（Driver Tree）

### 3.1 テンプレート情報の拡張

**対象エンドポイント:**

- `GET /api/v1/project/{project_id}/driver-tree/category`

**リクエスト内容:**
カテゴリ（テンプレート）レスポンスに以下のフィールドを追加。

```json
{
  "categoryId": 1,
  "industryName": "製造業",
  "driverType": "売上分析",
  "nodeCount": 15,    // 追加希望（テンプレートのノード数）
  "usageCount": 42    // 追加希望（使用回数）
}
```

**フロントエンド使用箇所:**

- [tree-new.hook.ts:84-85](src/features/trees/routes/tree-new/tree-new.hook.ts#L84-L85)

---

### 3.2 ツリー全体の施策一覧

**対象エンドポイント:**

- 新規エンドポイント: `GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/policy`

**リクエスト内容:**
ツリー全体に紐づく全ノードの施策を一括取得するエンドポイント。
（現在はノード単位 `/node/{node_id}/policy` のみ）

```json
{
  "treeId": "...",
  "policies": [
    {
      "nodeId": "...",
      "nodeName": "売上",
      "policyId": "...",
      "name": "新規顧客獲得",
      "value": 1000000,
      "status": "planned"
    }
  ],
  "total": 10
}
```

**フロントエンド使用箇所:**

- [tree-policies.hook.ts:10](src/features/trees/routes/tree-policies/tree-policies.hook.ts#L10)

---

### 3.3 計算結果の詳細データ

**対象エンドポイント:**

- `GET /api/v1/project/{project_id}/driver-tree/tree/{tree_id}/data`

**リクエスト内容:**
計算結果に詳細なメタデータを追加。

```json
{
  "calculatedDataList": [...],
  "summary": {           // 追加希望
    "totalNodes": 15,
    "calculatedNodes": 15,
    "errorNodes": 0,
    "lastCalculatedAt": "2025-01-15T10:00:00Z"
  },
  "kpiSummary": {        // 追加希望
    "targetKpi": "売上",
    "baseValue": 1000000,
    "simulatedValue": 1150000,
    "changeRate": 0.15
  }
}
```

**フロントエンド使用箇所:**

- [tree-results.hook.ts:9](src/features/trees/routes/tree-results/tree-results.hook.ts#L9)

---

### 3.4 カラム情報取得

**対象エンドポイント:**

- `GET /api/v1/project/{project_id}/driver-tree/file/{file_id}/sheet/{sheet_id}`
- または既存のシート選択APIのレスポンス拡張

**リクエスト内容:**
シートのカラム情報を取得。

```json
{
  "sheetId": "...",
  "sheetName": "Sheet1",
  "columns": [
    {
      "name": "date",
      "displayName": "日付",
      "dataType": "datetime",
      "role": "推移"
    },
    {
      "name": "sales",
      "displayName": "売上",
      "dataType": "number",
      "role": "値"
    }
  ],
  "rowCount": 1000,
  "sampleData": [...]
}
```

**フロントエンド使用箇所:**

- [tree-edit.hook.ts:30](src/features/trees/routes/tree-edit/tree-edit.hook.ts#L30)
- [tree-data-binding.hook.ts:53](src/features/trees/routes/tree-data-binding/tree-data-binding.hook.ts#L53)

---

## 4. ファイル管理（Files）

### 4.1 ファイル使用状況

**対象エンドポイント:**

- `GET /api/v1/project/{project_id}/file/{file_id}/usage`

**リクエスト内容:**
現在のレスポンスに `sessionCount` を追加。

```json
{
  "fileId": "...",
  "usedInSessions": [...],
  "sessionCount": 3,  // 追加希望（使用セッション数のサマリー）
  "usedInTrees": [...],
  "treeCount": 2      // 追加希望（使用ツリー数のサマリー）
}
```

**フロントエンド使用箇所:**

- [file-list.hook.ts:43](src/features/files/routes/file-list/file-list.hook.ts#L43)

---

## 5. カテゴリマスタ（Category）

### 5.1 関連数式数

**対象エンドポイント:**

- `GET /api/v1/admin/category`
- `GET /api/v1/admin/category/{category_id}`

**リクエスト内容:**
カテゴリレスポンスに関連数式数を追加。

```json
{
  "categoryId": 1,
  "industryName": "製造業",
  "driverType": "売上分析",
  "formulaCount": 10,  // 追加希望
  ...
}
```

**フロントエンド使用箇所:**

- [categories.hook.ts:37](src/features/masters/routes/categories/categories.hook.ts#L37)

---

## 6. ダッシュボード

### 6.1 プロジェクト進捗

**対象エンドポイント:**

- 新規エンドポイント: `GET /api/v1/dashboard/progress`
- または既存の `GET /api/v1/dashboard/stats` の拡張

**リクエスト内容:**
プロジェクトごとの進捗情報を取得。

```json
{
  "projectProgress": [
    {
      "id": "...",
      "name": "プロジェクトA",
      "progress": 75,
      "totalSessions": 10,
      "completedSessions": 7
    }
  ]
}
```

**フロントエンド使用箇所:**

- [dashboard.hook.ts:147-150](src/features/dashboard/routes/dashboard/dashboard.hook.ts#L147-L150)

---

## 優先度

| 優先度 | 項目 | 理由 |
|--------|------|------|
| 高 | 1.1 カテゴリ情報 | セッション詳細の基本情報 |
| 高 | 2.1 Validationフィールド | マスタ管理の基本機能 |
| 高 | 3.4 カラム情報 | ツリー編集の必須機能 |
| 中 | 1.4 スナップショット説明 | UX向上 |
| 中 | 3.2 ツリー施策一覧 | 施策管理画面に必要 |
| 中 | 4.1 ファイル使用状況 | ファイル管理のUX向上 |
| 低 | 1.2 インサイト情報 | 将来的な分析機能 |
| 低 | 1.3 関連セッション | 将来的な機能 |
| 低 | 6.1 プロジェクト進捗 | ダッシュボード拡張 |

---

## 備考

- 現在フロントエンドでは、上記の不足フィールドに対してプレースホルダー値（`"-"`, `0`, `[]`など）を使用しています
- API実装後、フロントエンドのremarksコメントを削除し、実際のAPIデータを使用するよう更新します
- 型定義（Zodスキーマ）は、OpenAPI更新後に同期します

---

**作成日:** 2025-12-30
**フロントエンドバージョン:** main branch (commit: 55401dd)
