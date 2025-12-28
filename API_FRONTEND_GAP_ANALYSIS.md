# API - フロントエンド 差分分析レポート

**作成日**: 2025年12月29日
**目的**: フロントエンド実装とOpenAPI仕様の差分を特定し、API修正の検討資料とする

---

## 概要

フロントエンドの `*.hook.ts` ファイル内のTODOコメント（`@remarks`）で「APIには存在しない」「API拡張待ち」と記載されているフィールドを調査し、OpenAPI仕様（`openapi.json`）との差分を特定しました。

---

## 1. ツリー一覧 (DriverTreeListItem)

### フロントエンド実装
**ファイル**: `src/features/trees/routes/tree-list/tree-list.hook.ts`

```typescript
const trees: TreeListItem[] = useMemo(() => {
  return (treesData.trees ?? []).map((tree) => ({
    id: tree.treeId,
    name: tree.name,
    formulaMaster: "-",      // ❌ API拡張待ち
    nodeCount: 0,            // ❌ API拡張待ち
    policyCount: 0,          // ❌ API拡張待ち
    updatedAt: formatDateTime(tree.updatedAt),
  }));
}, [treesData.trees]);
```

### OpenAPI仕様 (DriverTreeListItem)
| フィールド | 型 | 説明 |
|-----------|-----|------|
| treeId | string (uuid) | ✅ 存在 |
| name | string | ✅ 存在 |
| description | string \| null | ✅ 存在 |
| status | TreeStatus | ✅ 存在 |
| createdAt | datetime | ✅ 存在 |
| updatedAt | datetime | ✅ 存在 |

### 差分一覧

| フィールド | フロントエンド期待値 | API現状 | 優先度 | 備考 |
|-----------|---------------------|---------|--------|------|
| `formulaMaster` | string | ❌ 未提供 | 🔴 高 | 数式マスタ名の表示に必要 |
| `nodeCount` | number | ❌ 未提供 | 🟡 中 | ツリーに含まれるノード数 |
| `policyCount` | number | ❌ 未提供 | 🟡 中 | ツリーに関連する施策数 |

---

## 2. セッション一覧 (AnalysisSessionResponse)

### フロントエンド実装
**ファイル**: `src/features/sessions/routes/session-list/session-list.hook.ts`

```typescript
const sessions: SessionListItem[] = useMemo(() => {
  return sessionsData.sessions.map((session) => ({
    id: session.id,
    name: `セッション #${session.currentSnapshot}`,  // ❌ 名前がないため番号で代用
    issue: session.issueId,                          // ❌ 課題名がないためIDで代用
    inputFile: "",                                   // ❌ API拡張待ち
    snapshotCount: session.currentSnapshot,
    creatorName: session.creatorId,                  // ❌ ユーザー名がないためIDで代用
    updatedAt: formatDateTime(session.updatedAt),
    status: mapStatus(session.status),
  }));
}, [sessionsData.sessions]);
```

### OpenAPI仕様 (AnalysisSessionResponse)
| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | string (uuid) | ✅ 存在 |
| projectId | string (uuid) | ✅ 存在 |
| issueId | string (uuid) | ✅ 存在（IDのみ） |
| creatorId | string (uuid) | ✅ 存在（IDのみ） |
| status | SessionStatus | ✅ 存在 |
| currentSnapshot | integer | ✅ 存在 |
| createdAt | datetime | ✅ 存在 |
| updatedAt | datetime | ✅ 存在 |
| snapshotHistory | array | ✅ 存在 |

### 差分一覧

| フィールド | フロントエンド期待値 | API現状 | 優先度 | 備考 |
|-----------|---------------------|---------|--------|------|
| `name` | string | ❌ 未提供 | 🔴 高 | セッション名（現在は番号で代用） |
| `issueName` | string | ❌ 未提供 | 🔴 高 | 課題名（issueIdのみ提供） |
| `inputFile` | string | ❌ 未提供 | 🟡 中 | 入力ファイル名 |
| `creatorName` | string | ❌ 未提供 | 🔴 高 | 作成者名（creatorIdのみ提供） |

### 提案
- **オプションA**: `AnalysisSessionResponse`にリレーション情報を含める
  - `issue: { id, name }` 形式でネスト
  - `creator: { id, displayName }` 形式でネスト
- **オプションB**: フロントエンドで別途API呼び出しを行う（非推奨：N+1問題）

---

## 3. カテゴリ編集 (DriverTreeCategoryResponse)

### フロントエンド実装
**ファイル**: `src/features/masters/routes/category-edit/category-edit.hook.ts`

```typescript
const initialCategory: CategoryDetail = useMemo(() => {
  return {
    id: String(data.id),
    name: data.categoryName,
    industry: mapIndustryFromId(data.industryId),
    driverType: mapDriverType(data.driverType),
    formulaCount: 0,           // ❌ API拡張待ち
    updatedAt: formatDate(data.updatedAt),
    description: "",           // ❌ API拡張待ち
    formulas: [],              // ❌ 別APIから取得予定
    createdAt: formatDate(data.createdAt),
    creatorName: "-",          // ❌ API拡張待ち
    usageTreeCount: 0,         // ❌ API拡張待ち
  };
}, [categoryData]);
```

### OpenAPI仕様 (DriverTreeCategoryResponse)
| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | integer | ✅ 存在 |
| categoryName | string | ✅ 存在 |
| industryId | integer | ✅ 存在 |
| driverType | string | ✅ 存在 |
| createdAt | datetime | ✅ 存在 |
| updatedAt | datetime | ✅ 存在 |

### 差分一覧

| フィールド | フロントエンド期待値 | API現状 | 優先度 | 備考 |
|-----------|---------------------|---------|--------|------|
| `description` | string | ❌ 未提供 | 🟡 中 | カテゴリの説明文 |
| `formulaCount` | number | ❌ 未提供 | 🟡 中 | 紐づく数式の数 |
| `formulas` | Formula[] | ❌ 未提供 | 🟢 低 | 別APIで取得可能 |
| `creatorName` | string | ❌ 未提供 | 🟡 中 | 作成者名 |
| `usageTreeCount` | number | ❌ 未提供 | 🟡 中 | このカテゴリを使用しているツリー数 |

---

## 4. ダッシュボード統計

### フロントエンド実装
**ファイル**: `src/features/dashboard/routes/dashboard/dashboard.hook.ts`

```typescript
const stats = useMemo(() => ({
  projectCount: statsData.projects.total,
  projectChange: statsData.projects.active - statsData.projects.archived,
  activeSessionCount: statsData.sessions.active,
  treeCount: statsData.trees.total,
  treeChange: statsData.trees.active,
  fileCount: 47,  // ❌ ファイル統計はAPIにないためモック値
}), [statsData]);
```

### 差分一覧

| フィールド | フロントエンド期待値 | API現状 | 優先度 | 備考 |
|-----------|---------------------|---------|--------|------|
| `fileCount` | number | ❌ 未提供 | 🟡 中 | ファイル総数の統計 |

---

## 5. プロジェクトメンバー

### フロントエンド実装
**ファイル**: `src/features/projects/routes/project-members/project-members.hook.ts`

```typescript
// @remarks
// 以下のフィールドはAPI拡張待ち:
// - joinedAt: 参加日
// - lastActivityAt: 最終活動日時
```

### 差分一覧

| フィールド | フロントエンド期待値 | API現状 | 優先度 | 備考 |
|-----------|---------------------|---------|--------|------|
| `joinedAt` | datetime | ❌ 未提供 | 🟢 低 | メンバーの参加日 |
| `lastActivityAt` | datetime | ❌ 未提供 | 🟢 低 | 最終活動日時 |

---

## 6. プロジェクト作成

### フロントエンド実装
**ファイル**: `src/features/projects/routes/project-new/project-new.hook.ts`

```typescript
// @remarks
// 以下のフィールドはAPI拡張待ち:
// - startDate: 開始日
// - endDate: 終了日
// - budget: 予算
```

### OpenAPI仕様確認
`ProjectResponse`には`startDate`と`endDate`が**存在**しています。

### 差分一覧

| フィールド | フロントエンド期待値 | API現状 | 優先度 | 備考 |
|-----------|---------------------|---------|--------|------|
| `startDate` | date | ✅ 存在 | - | **API側に存在確認** |
| `endDate` | date | ✅ 存在 | - | **API側に存在確認** |
| `budget` | number | ❌ 未提供 | 🟢 低 | プロジェクト予算 |

> **注意**: `startDate`と`endDate`はAPIに存在するため、フロントエンド側の実装が追いついていない可能性があります。

---

## 7. セッション作成

### フロントエンド実装
**ファイル**: `src/features/sessions/routes/session-new/session-new.hook.ts`

```typescript
// @remarks
// 以下のフィールドはAPI拡張待ち:
// - templateId: テンプレートID
// - parameters: セッションパラメータ
```

### 差分一覧

| フィールド | フロントエンド期待値 | API現状 | 優先度 | 備考 |
|-----------|---------------------|---------|--------|------|
| `templateId` | string | ❌ 未提供 | 🟢 低 | セッションテンプレート機能 |
| `parameters` | object | ❌ 未提供 | 🟢 低 | セッション設定パラメータ |

---

## 優先度サマリー

### 🔴 高優先度（ユーザー体験に直接影響）

| 対象 | フィールド | 理由 |
|------|-----------|------|
| ツリー一覧 | `formulaMaster` | 一覧画面で重要な情報 |
| セッション一覧 | `name` | 識別に必須 |
| セッション一覧 | `issueName` | IDでは認識困難 |
| セッション一覧 | `creatorName` | IDでは認識困難 |

### 🟡 中優先度（機能改善に寄与）

| 対象 | フィールド |
|------|-----------|
| ツリー一覧 | `nodeCount`, `policyCount` |
| カテゴリ編集 | `description`, `formulaCount`, `creatorName`, `usageTreeCount` |
| セッション一覧 | `inputFile` |
| ダッシュボード | `fileCount` |

### 🟢 低優先度（将来的な機能拡張）

| 対象 | フィールド |
|------|-----------|
| プロジェクトメンバー | `joinedAt`, `lastActivityAt` |
| プロジェクト作成 | `budget` |
| セッション作成 | `templateId`, `parameters` |
| カテゴリ編集 | `formulas`（別API可） |

---

## 推奨アクション

### 即座対応推奨
1. **セッション一覧のリレーション展開**: `issue`, `creator`のネスト情報を含める
2. **ツリー一覧の集計情報追加**: `formulaMaster`, `nodeCount`, `policyCount`

### 中期対応
1. **カテゴリ詳細の拡充**: 統計情報と説明フィールドの追加
2. **ダッシュボード統計**: ファイル統計の追加

### フロントエンド側対応
1. **プロジェクト作成**: `startDate`/`endDate`はAPIに存在するため、フロントエンド実装を更新

---

---

## 8. スキーマ定義の分析

### 調査対象
フロントエンドの型定義ファイル（`types/api.ts`, `types/domain.ts`）とOpenAPI仕様を比較

### 分析結果

#### ✅ OpenAPI準拠済みのスキーマ

以下のスキーマはOpenAPIに完全準拠しており、差分なし:

| Feature | スキーマ | 状態 |
|---------|----------|------|
| sessions | `apiAnalysisSessionResponseSchema` | ✅ 準拠 |
| sessions | `apiAnalysisSnapshotResponseSchema` | ✅ 準拠 |
| sessions | `apiAnalysisChatResponseSchema` | ✅ 準拠 |
| sessions | `apiAnalysisStepResponseSchema` | ✅ 準拠 |
| trees | `apiDriverTreeListItemSchema` | ✅ 準拠 |
| trees | `apiDriverTreeInfoSchema` | ✅ 準拠 |
| trees | `apiDriverTreeNodePolicyInfoSchema` | ✅ 準拠 |
| projects | `apiProjectSchema` | ✅ 準拠 |
| projects | `apiProjectMemberSchema` | ✅ 準拠 |
| projects | `apiProjectStatsSchema` | ✅ 準拠 |
| files | `apiProjectFileSchema` | ✅ 準拠 |
| dashboard | `apiDashboardStatsResponseSchema` | ✅ 準拠 |
| dashboard | `apiActivityLogSchema` | ✅ 準拠 |
| admin | `apiCategorySchema` | ✅ 準拠 |
| admin | `apiIssueSchema` | ✅ 準拠 |
| admin | `apiValidationSchema` | ✅ 準拠 |

#### ⚠️ UI用スキーマ（後方互換性）

フロントエンドには「API用スキーマ」と「UI用スキーマ」の2層が存在:

```
API Response → api*Schema → hook変換処理 → UI用スキーマ → コンポーネント
```

**UI用スキーマで追加されているフィールド（API未提供）:**

| Feature | UI用スキーマ | 追加フィールド |
|---------|-------------|---------------|
| sessions | `sessionListItemSchema` | `name`, `issue`, `inputFile`, `creatorName` |
| trees | `treeListItemSchema` | `formulaMaster`, `nodeCount`, `policyCount` |
| projects | `projectDetailSchema` | `creatorName`, `goals` |
| projects | `projectMemberSchema` | `isCreator` |

---

## 9. API-フロントエンド統合パターン

### 現在の実装パターン

```typescript
// 1. API型（OpenAPI準拠）
export const apiAnalysisSessionResponseSchema = z.object({
  id: z.string().uuid(),
  issueId: z.string().uuid(),        // IDのみ
  creatorId: z.string().uuid(),      // IDのみ
  // ...
});

// 2. UI型（追加フィールド含む）
export const sessionListItemSchema = z.object({
  id: z.string(),
  name: z.string(),                  // API未提供
  issue: z.string(),                 // 課題名（API未提供）
  creatorName: z.string(),           // 作成者名（API未提供）
  // ...
});

// 3. Hook内で変換（差分発生箇所）
const sessions = sessionsData.sessions.map((session) => ({
  id: session.id,
  name: `セッション #${session.currentSnapshot}`,  // 代替値
  issue: session.issueId,                          // ID代用
  creatorName: session.creatorId,                  // ID代用
}));
```

### 推奨パターン（API拡張時）

```typescript
// Option A: リレーション展開
export const apiAnalysisSessionResponseSchema = z.object({
  id: z.string().uuid(),
  issueId: z.string().uuid(),
  issue: z.object({                  // 新規追加
    id: z.string().uuid(),
    name: z.string(),
  }).nullable().optional(),
  creatorId: z.string().uuid(),
  creator: z.object({                // 新規追加
    id: z.string().uuid(),
    displayName: z.string(),
  }).nullable().optional(),
});

// Option B: 専用エンドポイント（N+1回避）
// GET /api/v1/sessions?expand=issue,creator
```

---

## 10. 対応優先度マトリックス

| 優先度 | API修正 | FE修正 | 項目 |
|--------|---------|--------|------|
| 🔴 高 | 必要 | - | セッション一覧: リレーション展開 |
| 🔴 高 | 必要 | - | ツリー一覧: 集計情報追加 |
| 🟡 中 | 必要 | - | カテゴリ詳細: 統計・説明追加 |
| 🟡 中 | 必要 | - | ダッシュボード: ファイル統計追加 |
| 🟢 低 | - | 必要 | プロジェクト: startDate/endDate活用 |
| 🟢 低 | 検討 | - | プロジェクトメンバー: 活動情報 |
| 🟢 低 | 検討 | - | セッション: テンプレート機能 |

---

## 備考

- 本レポートは`*.hook.ts`ファイル内の`@remarks`コメント、`types/*.ts`のスキーマ定義、およびOpenAPI仕様を基に作成
- フロントエンドのAPI型定義は概ねOpenAPIに準拠済み
- 差分は主にUI用スキーマとhook変換処理で発生
- 優先度はユーザー体験への影響度を基準に設定
- 各APIエンドポイントの詳細な変更については、バックエンドチームとの協議が必要

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2025-12-29 | 初版作成（hook.tsの@remarks調査） |
| 2025-12-29 | スキーマ定義の詳細分析追加（types/*.ts調査） |
