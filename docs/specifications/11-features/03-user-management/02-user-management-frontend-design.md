# ユーザー管理 フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|-------|------|------|
| users | ユーザー一覧 | `/admin/users` | ユーザー一覧表示・検索・フィルタ |
| user-detail | ユーザー詳細 | `/admin/users/{id}` | ユーザー詳細表示・編集 |
| roles | ロール管理 | `/admin/roles` | システムロール・プロジェクトロール一覧 |

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `DataTable` | ユーザー一覧テーブル | [02-shared-ui-components.md](../01-frontend-common/02-shared-ui-components.md) |
| `Pagination` | ページネーション | 同上 |
| `Badge` | ロールバッジ、ステータスバッジ | 同上 |
| `Button` | 詳細ボタン、有効化/無効化ボタン | 同上 |
| `Input` | 検索入力 | 同上 |
| `Select` | ロールフィルタ、ステータスフィルタ | 同上 |
| `Card` | ユーザー詳細カード、統計カード | 同上 |
| `Modal` | ロール変更確認ダイアログ | 同上 |
| `Alert` | 操作完了/エラー通知 | 同上 |
| `Tabs` | ユーザー詳細タブ | 同上 |
| `Avatar` | ユーザーアイコン | 同上 |

### 1.3 コンポーネント構成

```text
features/user-management/
├── api/
│   ├── get-users.ts                 # GET /api/v1/user_account
│   ├── get-user.ts                  # GET /api/v1/user_account/{id}
│   ├── update-user.ts               # PATCH /api/v1/user_account/me
│   ├── update-user-role.ts          # PUT /api/v1/user_account/{id}/role
│   ├── activate-user.ts             # PATCH /api/v1/user_account/{id}/activate
│   ├── deactivate-user.ts           # PATCH /api/v1/user_account/{id}/deactivate
│   ├── delete-user.ts               # DELETE /api/v1/user_account/{id}
│   └── index.ts
├── components/
│   ├── user-table/
│   │   ├── user-table.tsx           # ユーザー一覧テーブル（DataTable使用）
│   │   └── index.ts
│   ├── user-search-bar/
│   │   ├── user-search-bar.tsx      # 検索バー（Input, Select使用）
│   │   └── index.ts
│   ├── user-detail-card/
│   │   ├── user-detail-card.tsx     # ユーザー詳細カード（Card使用）
│   │   └── index.ts
│   ├── user-stats-grid/
│   │   ├── user-stats-grid.tsx      # 統計グリッド
│   │   └── index.ts
│   ├── role-change-modal/
│   │   ├── role-change-modal.tsx    # ロール変更モーダル（Modal使用）
│   │   └── index.ts
│   └── index.ts
├── routes/
│   ├── user-list/
│   │   ├── user-list.tsx            # ユーザー一覧コンテナ
│   │   ├── user-list.hook.ts        # ユーザー一覧用hook
│   │   └── index.ts
│   ├── user-detail/
│   │   ├── user-detail.tsx          # ユーザー詳細コンテナ
│   │   ├── user-detail.hook.ts      # ユーザー詳細用hook
│   │   └── index.ts
│   └── roles/
│       ├── roles.tsx                # ロール管理コンテナ
│       ├── roles.hook.ts            # ロール管理用hook
│       └── index.ts
├── types/
│   ├── api.ts                       # API入出力の型
│   ├── domain.ts                    # ドメインモデル（User, Role等）
│   └── index.ts
└── index.ts

app/admin/
├── users/
│   ├── page.tsx             # ユーザー一覧ページ → UserList
│   └── [id]/
│       └── page.tsx         # ユーザー詳細ページ → UserDetail
└── roles/
    └── page.tsx             # ロール管理ページ → Roles
```

---

## 2. 画面詳細設計

### 2.1 ユーザー一覧画面（users）

#### 検索・フィルタ項目

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 備考 |
|---------|---------|------------------|-----------------|------|
| 名前/メール検索 | テキスト | `GET /api/v1/user_account` | `email` | 完全一致 |
| ロールフィルタ | セレクト | 同上 | - | フロントでフィルタ |
| ステータスフィルタ | セレクト | 同上 | - | フロントでフィルタ |

#### 一覧表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザー（アイコン+名前） | アイコン+テキスト | `GET /api/v1/user_account` | `users[].displayName` | アイコンは固定表示 |
| メールアドレス | テキスト | 同上 | `users[].email` | - |
| システムロール | バッジ | 同上 | `users[].roles` | `system_admin`→"ADMIN"(danger), `user`→"SYSTEM_USER"(info) |
| ステータス | バッジ | 同上 | `users[].isActive` | `true`→"有効"(success), `false`→"無効"(danger) |
| 最終ログイン | 日時 | 同上 | `users[].lastLogin` | ISO8601→YYYY/MM/DD HH:mm |
| 詳細ボタン | ボタン | - | - | user-detail画面へ遷移 |
| 無効化/有効化ボタン | ボタン | `PATCH .../activate` or `deactivate` | - | isActiveにより切替 |

#### ページネーション

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ページ番号 | ボタン群 | `GET /api/v1/user_account` | `total`, `skip`, `limit` | `Math.ceil(total / limit)` でページ数計算 |

### 2.2 ユーザー詳細画面（user-detail）

#### アカウント情報

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザーID | テキスト | `GET /api/v1/user_account/{id}` | `id` | UUID表示 |
| Azure ID | テキスト | 同上 | `azureId` | - |
| メールアドレス | テキスト | 同上 | `email` | - |
| 表示名 | テキスト | 同上 | `displayName` | - |
| システムロール | バッジ群 | 同上 | `roles` | 配列をバッジ群として表示 |
| ステータス | バッジ | 同上 | `isActive` | boolean→バッジ変換 |
| 作成日時 | 日時 | 同上 | `createdAt` | ISO8601→YYYY/MM/DD HH:mm:ss |
| 更新日時 | 日時 | 同上 | `updatedAt` | ISO8601→YYYY/MM/DD HH:mm:ss |
| 最終ログイン | 日時 | 同上 | `lastLogin` | ISO8601→YYYY/MM/DD HH:mm:ss |
| ログイン回数 | 数値 | 同上 | `loginCount` | 数値表示 |

#### 統計情報

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 参加プロジェクト数 | 数値 | `GET /api/v1/user_account/{id}` | `stats.projectCount` | 数値表示 |
| 作成セッション数 | 数値 | 同上 | `stats.sessionCount` | 数値表示 |
| 作成ツリー数 | 数値 | 同上 | `stats.treeCount` | 数値表示 |

#### 参加プロジェクト一覧

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| プロジェクト名 | リンク | `GET /api/v1/user_account/{id}` | `projects[].projectName` | プロジェクト詳細画面へのリンク |
| プロジェクトロール | バッジ | 同上 | `projects[].projectRole` | ロールに応じたバッジ表示 |
| 参加日 | 日時 | 同上 | `projects[].joinedAt` | ISO8601→YYYY/MM/DD |
| ステータス | バッジ | 同上 | `projects[].status` | `active`→"アクティブ"(success) |

#### 最近のアクティビティ

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| アクティビティ内容 | テキスト | `GET /api/v1/user_account/{id}` | `recentActivities[].activityType` + `activityDetail` | "セッション作成: セッション名" など |
| 時刻 | 日時 | 同上 | `recentActivities[].activityAt` | ISO8601→YYYY/MM/DD HH:mm |
| プロジェクト名 | テキスト | 同上 | `recentActivities[].projectName` | プロジェクト名表示 |

#### 編集項目

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 表示名 | テキスト | - | `PATCH /api/v1/user_account/me` | `displayName` | 最大255文字 |
| システムロール | セレクト（単一選択） | ✓ | `PUT /api/v1/user_account/{id}/role` | `roles` | system_admin または user を選択 |

#### アクション

| 画面項目 | 操作 | APIエンドポイント | 備考 |
|---------|-----|------------------|------|
| 有効化ボタン | クリック | `PATCH /api/v1/user_account/{id}/activate` | 無効ユーザーのみ表示 |
| 無効化ボタン | クリック | `PATCH /api/v1/user_account/{id}/deactivate` | 有効ユーザーかつ自分以外 |
| 削除ボタン | クリック | `DELETE /api/v1/user_account/{id}` | 確認ダイアログ表示 |

### 2.3 ロール管理画面（roles）

#### システムロール一覧

| 画面項目 | 表示形式 | データソース | 備考 |
|---------|---------|-------------|------|
| ロール名 | バッジ | 固定値 | ADMIN, SYSTEM_USER |
| 説明 | テキスト | 固定値 | 定義済み説明文 |
| 権限 | テキスト | 固定値 | 権限説明文 |

#### プロジェクトロール一覧

| 画面項目 | 表示形式 | データソース | 備考 |
|---------|---------|-------------|------|
| ロール名 | バッジ | 固定値 | PROJECT_MANAGER, MODERATOR, MEMBER, VIEWER |
| 説明 | テキスト | 固定値 | 定義済み説明文 |
| 権限 | テキスト | 固定値 | 権限説明文 |

---

## 3. 画面項目・APIマッピング

### 3.1 ユーザー一覧取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| メール検索 | テキスト | - | `GET /api/v1/user_account` | `email` | 完全一致 |
| スキップ | 数値 | - | 同上 | `skip` | ≥0 |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト20、最大100 |

### 3.2 ユーザー更新

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 表示名 | テキスト | - | `PATCH /api/v1/user_account/me` | `displayName` | 最大255文字 |
| システムロール | セレクト | ✓ | `PUT /api/v1/user_account/{id}/role` | `roles` | system_admin/user |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| ユーザー一覧ページ表示 | `GET /api/v1/user_account` | 初期ロード |
| 検索実行 | `GET /api/v1/user_account?email=` | デバウンス300ms |
| ユーザー詳細表示 | `GET /api/v1/user_account/{id}` | - |
| 有効化ボタンクリック | `PATCH /api/v1/user_account/{id}/activate` | 確認後実行 |
| 無効化ボタンクリック | `PATCH /api/v1/user_account/{id}/deactivate` | 確認後実行 |
| ロール変更保存 | `PUT /api/v1/user_account/{id}/role` | - |
| 削除ボタンクリック | `DELETE /api/v1/user_account/{id}` | 確認ダイアログ後 |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス拒否メッセージ表示 |
| 404 Not Found | ユーザーが見つかりませんメッセージ表示 |
| 409 Conflict | 自分自身は無効化できませんメッセージ表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 一覧取得 | ページネーションで件数制限（デフォルト20件） |
| 検索 | 300msデバウンスでAPI呼び出しを最適化 |
| キャッシュ | React Query で一覧データを5分間キャッシュ |
| 再レンダリング | useMemo でフィルタ結果を最適化 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| U-003 | ユーザー情報を更新する | `PATCH /user_account/me` | user-detail | 実装済 |
| U-004 | ユーザーを無効化する | `PATCH /user_account/{id}/deactivate` | users, user-detail | 実装済 |
| U-005 | ユーザーを有効化する | `PATCH /user_account/{id}/activate` | users, user-detail | 実装済 |
| U-007 | ユーザー一覧を取得する | `GET /user_account` | users | 実装済 |
| U-008 | ユーザー詳細を取得する | `GET /user_account/{id}` | user-detail | 実装済 |
| U-009 | システムロールを付与する | `PUT /user_account/{id}/role` | user-detail | 実装済 |
| U-010 | システムロールを剥奪する | `PUT /user_account/{id}/role` | user-detail | 実装済 |
| U-011 | ユーザーのロールを確認する | `GET /user_account/{id}/role_history` | user-detail | 実装済 |

---

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| UserTable | Default | ユーザー一覧テーブル表示 | 通常表示、ローディング、空状態、エラー |
| UserSearchBar | Default | ユーザー検索バー | 通常、フィルタ適用済み |
| UserDetailCard | Default | ユーザー詳細カード | 通常、編集可能、ローディング |
| UserStatsGrid | Default | ユーザー統計グリッド | 通常、ローディング |
| RoleChangeModal | Open | ロール変更モーダル | 開いた状態、送信中 |

### 8.2 ストーリー実装例

```tsx
// user-table/user-table.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { UserTable } from "./user-table";
import { mockUsers } from "@/test/mocks/users";

const meta = {
  title: "features/user-management/components/user-table",
  component: UserTable,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: "ユーザー一覧テーブルコンポーネント。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onEdit: fn(),
    onDeactivate: fn(),
  },
} satisfies Meta<typeof UserTable>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    users: mockUsers,
  },
};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const Empty: Story = {
  args: {
    users: [],
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| コンポーネント | ユニットテスト | 80%以上 | テーブル表示、フィルタ動作、モーダル操作 |
| ユーティリティ | ユニットテスト | 90%以上 | hooks, utils, バリデーション |
| API連携 | 統合テスト | 70%以上 | API呼び出し、状態管理、エラーハンドリング |
| E2E | E2Eテスト | 主要フロー100% | ユーザー検索、ロール変更、詳細表示 |

### 9.2 ユニットテスト例

```typescript
// hooks/use-user-list.test.ts
import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { useUserList } from "./use-user-list";
import { QueryClientProvider } from "@tanstack/react-query";

describe("useUserList", () => {
  it("ユーザー一覧を取得できる", async () => {
    const { result } = renderHook(() => useUserList(), {
      wrapper: QueryClientProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(10);
  });

  it("フィルタ条件でユーザーを絞り込める", async () => {
    const { result } = renderHook(() => useUserList({ role: "admin" }), {
      wrapper: QueryClientProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.every(u => u.role === "admin")).toBe(true);
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
// components/user-table/user-table.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { UserTable } from "./user-table";
import { mockUsers } from "@/test/mocks/users";

describe("UserTable", () => {
  it("ユーザー一覧を表示する", () => {
    render(<UserTable users={mockUsers} />);

    expect(screen.getByText(mockUsers[0].displayName)).toBeInTheDocument();
    expect(screen.getByText(mockUsers[0].email)).toBeInTheDocument();
  });

  it("詳細ボタンクリックでonEditが呼ばれる", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    render(<UserTable users={mockUsers} onEdit={onEdit} />);

    await user.click(screen.getAllByRole("button", { name: "詳細" })[0]);
    expect(onEdit).toHaveBeenCalledWith(mockUsers[0].id);
  });

  it("ローディング中はスケルトンを表示する", () => {
    render(<UserTable isLoading />);

    expect(screen.getByTestId("user-table-skeleton")).toBeInTheDocument();
  });
});
```

### 9.4 E2Eテスト例

```typescript
// e2e/user-management.spec.ts
import { test, expect } from "@playwright/test";

test.describe("ユーザー管理", () => {
  test("UC-007: ユーザー一覧を取得・表示できる", async ({ page }) => {
    await page.goto("/admin/users");

    await expect(page.getByRole("table")).toBeVisible();
    await expect(page.getByRole("row")).toHaveCount.greaterThan(1);
  });

  test("UC-008: ユーザー詳細を表示できる", async ({ page }) => {
    await page.goto("/admin/users");
    await page.getByRole("button", { name: "詳細" }).first().click();

    await expect(page).toHaveURL(/\/admin\/users\/[a-z0-9-]+/);
    await expect(page.getByTestId("user-detail-card")).toBeVisible();
  });

  test("UC-004: ユーザーを無効化できる", async ({ page }) => {
    await page.goto("/admin/users");
    await page.getByRole("button", { name: "無効化" }).first().click();
    await page.getByRole("button", { name: "確認" }).click();

    await expect(page.getByText("ユーザーを無効化しました")).toBeVisible();
  });
});
```

### 9.5 モックデータ

```typescript
// test/mocks/users.ts
export const mockUsers: User[] = [
  {
    id: "user-001",
    azureId: "azure-001",
    email: "admin@example.com",
    displayName: "管理者ユーザー",
    roles: ["system_admin"],
    isActive: true,
    lastLogin: "2026-01-01T10:00:00Z",
    loginCount: 50,
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2026-01-01T10:00:00Z",
  },
  // ... 追加のモックデータ
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計書**: [01-user-management-design.md](./01-user-management-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **モックアップ**: [../../03-mockup/pages/admin.js](../../03-mockup/pages/admin.js)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | UM-FRONTEND-001 |
| 対象ユースケース | U-003〜U-011 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `app/admin/users/` |
