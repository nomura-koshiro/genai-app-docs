# 共通UI フロントエンド設計書（UI-001〜UI-011）

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| header | ヘッダー | 全ページ共通 | グローバルナビゲーション（検索、通知、ユーザーメニュー） |
| sidebar | サイドバー | 全ページ共通 | サイドナビゲーション（権限ベース表示） |
| notifications | 通知一覧 | /notifications | 全通知一覧ページ（オプション） |

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `Badge` | 通知件数バッジ、管理者バッジ | [02-shared-ui-components.md](../00-frontend-common/02-shared-ui-components.md) |
| `Button` | ユーザーメニュー、検索ボタン | 同上 |
| `Input` | 検索入力フィールド | 同上 |
| `DropdownMenu` | ユーザーメニュー、通知ドロップダウン | 同上 |
| `Avatar` | ユーザーアバター表示 | 同上 |
| `Skeleton` | 読み込み中表示 | 同上 |

### 1.3 コンポーネント構成

```text
features/common/
├── components/
│   ├── Header/
│   │   ├── Header.tsx                 # ヘッダー本体
│   │   ├── UserMenu.tsx               # ユーザーメニュー（DropdownMenu使用）
│   │   ├── NotificationBell.tsx       # 通知ベルアイコン
│   │   ├── NotificationDropdown.tsx   # 通知ドロップダウン（DropdownMenu使用）
│   │   ├── GlobalSearch.tsx           # グローバル検索（Input使用）
│   │   ├── SearchDropdown.tsx         # 検索結果ドロップダウン
│   │   ├── SearchResultItem.tsx       # 検索結果項目
│   │   └── ThemeToggle.tsx            # テーマ切り替え（Button, DropdownMenu使用）
│   ├── Sidebar/
│   │   ├── Sidebar.tsx                # サイドバー本体
│   │   ├── SidebarSection.tsx         # サイドバーセクション
│   │   ├── SidebarItem.tsx            # サイドバー項目
│   │   └── ProjectNavigator.tsx       # プロジェクトナビゲーター
│   └── Layout/
│       └── AppLayout.tsx              # アプリケーションレイアウト
├── hooks/
│   ├── useUserContext.ts
│   ├── usePermissions.ts
│   ├── useNavigation.ts
│   ├── useGlobalSearch.ts
│   ├── useSearchDebounce.ts
│   ├── useNotifications.ts
│   ├── useUnreadCount.ts
│   └── useNotificationPolling.ts
├── contexts/
│   └── UserContextProvider.tsx
├── api/
│   ├── userContextApi.ts
│   ├── searchApi.ts
│   └── notificationApi.ts
└── types/
    ├── userContext.ts
    ├── search.ts
    └── notification.ts
```

---

## 2. 画面詳細設計

### 2.1 サイドバー（sidebar）

#### セクション構成

| セクションID | セクション名 | 必要権限 | メニュー項目 |
|-------------|-------------|---------|------------|
| dashboard | ダッシュボード | user | ホーム |
| project | プロジェクト管理 | user | プロジェクト、プロジェクト作成 |
| analysis | 個別施策分析 | user | 分析セッション一覧、新規セッション作成 |
| driver-tree | ドライバーツリー | user | ツリー一覧、新規ツリー作成、カテゴリマスタ |
| file | ファイル管理 | user | ファイル一覧、アップロード |
| system-admin | システム管理 | system_admin | ユーザー管理、ロール管理、検証カテゴリ、課題マスタ |
| monitoring | 監視・運用 | system_admin | システム統計、操作履歴、監査ログ、全プロジェクト |
| operations | システム運用 | system_admin | システム設定、通知管理、セキュリティ、一括操作 |

#### 表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 表示セクション | セクション群 | `GET /api/v1/user_account/me/context` | `sidebar.visibleSections` | 配列→セクション表示判定 |
| プロジェクトリンク | ナビゲーション | 同上 | `navigation.projectNavigationType` | `detail`→詳細直接遷移, `list`→一覧遷移 |
| プロジェクト名 | テキスト | 同上 | `navigation.defaultProjectName` | 1件時のみ表示 |

#### 動的遷移ルール

| 条件 | 遷移先 | URL |
|-----|-------|-----|
| プロジェクト数 = 0 | プロジェクト一覧（空状態） | `/projects` |
| プロジェクト数 = 1 | プロジェクト詳細 | `/projects/{projectId}` |
| プロジェクト数 > 1 | プロジェクト一覧 | `/projects` |

### 2.2 ヘッダー（header）

#### 表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザー名 | テキスト | `GET /api/v1/user_account/me/context` | `user.displayName` | - |
| ユーザーアバター | イニシャル | 同上 | `user.displayName` | 先頭2文字 |
| 通知バッジ | バッジ | 同上 | `notifications.unreadCount` | 0の場合非表示、99+表示 |
| 管理者バッジ | バッジ | 同上 | `permissions.isSystemAdmin` | `true`の場合のみ表示 |

#### ユーザーメニュー

| メニュー項目 | 表示条件 | 遷移先 |
|------------|---------|-------|
| プロフィール | 常時 | `/settings/profile` |
| 設定 | 常時 | `/settings` |
| 管理パネル | isSystemAdmin = true | `/admin` |
| ログアウト | 常時 | Azure AD logout |

### 2.3 グローバル検索（GlobalSearch）

#### 検索入力

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 検索ボックス | テキスト入力 | - | `GET /api/v1/search` | `q` | 2文字以上で検索実行 |
| タイプフィルタ | セレクト | - | 同上 | `type` | project/session/file/tree |

#### 検索結果表示

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 検索結果件数 | テキスト | `GET /api/v1/search` | `total` | "n件" 形式 |
| 結果アイテム（アイコン） | アイコン | 同上 | `results[].type` | type→絵文字マッピング |
| 結果アイテム（名前） | テキスト | 同上 | `results[].highlightedText` | HTMLとしてレンダリング |
| 結果アイテム（説明） | テキスト | 同上 | `results[].description` | 50文字で切り詰め |
| 結果アイテム（プロジェクト名） | テキスト | 同上 | `results[].projectName` | 親プロジェクト表示 |
| 結果アイテム（更新日時） | テキスト | 同上 | `results[].updatedAt` | 相対時間表示 |
| 空状態 | アイコン+テキスト | - | - | "検索結果がありません" |

#### タイプアイコンマッピング

| type | アイコン | 説明 |
|------|---------|------|
| project | 📁 | プロジェクト |
| session | 📊 | 分析セッション |
| file | 📄 | ファイル |
| tree | 🌳 | ドライバーツリー |

#### キーボードショートカット

| キー | 動作 |
|------|------|
| Ctrl+K / Cmd+K | 検索ボックスにフォーカス |
| ↑ | 前の結果を選択 |
| ↓ | 次の結果を選択 |
| Enter | 選択中の結果に遷移 |
| Esc | ドロップダウンを閉じる |

### 2.4 通知ベル（NotificationBell）

#### 通知ベルコンポーネント

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 通知ベルアイコン | アイコンボタン | - | - | 🔔 |
| 未読バッジ | バッジ | `GET /api/v1/user_account/me/context` | `notifications.unreadCount` | 0の場合非表示、99+表示 |

#### 通知ドロップダウン表示

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ヘッダータイトル | テキスト | - | - | "通知" |
| すべて既読ボタン | リンクボタン | `PATCH /api/v1/notifications/read-all` | - | 未読がある場合のみ表示 |
| 通知アイテム（アイコン） | アイコン | `GET /api/v1/notifications` | `items[].icon` | 絵文字表示 |
| 通知アイテム（タイトル） | テキスト | 同上 | `items[].title` | 1行表示 |
| 通知アイテム（メッセージ） | テキスト | 同上 | `items[].message` | 100文字切り詰め |
| 通知アイテム（時間） | テキスト | 同上 | `items[].createdAt` | 相対時間表示 |
| 通知アイテム（未読マーク） | スタイル | 同上 | `items[].isRead` | 未読時に背景色変更 |
| 空状態 | アイコン+テキスト | - | - | "通知はありません" |
| フッターリンク | リンク | - | - | "すべての通知を見る" |

#### 通知タイプアイコンマッピング

| type | icon | 説明 |
|------|------|------|
| member_added | 👥 | メンバー追加 |
| member_removed | 👤 | メンバー削除 |
| session_complete | ✅ | セッション完了 |
| file_uploaded | 📄 | ファイルアップロード |
| tree_updated | 🌳 | ツリー更新 |
| project_invitation | 📨 | プロジェクト招待 |
| system_announcement | 📢 | システムお知らせ |

#### アクション

| 画面項目 | 操作 | APIエンドポイント | 備考 |
|---------|-----|------------------|------|
| 通知アイテムクリック | 既読化+遷移 | `PATCH /api/v1/notifications/{id}/read` | 関連画面へ遷移 |
| すべて既読ボタン | クリック | `PATCH /api/v1/notifications/read-all` | 確認なしで実行 |
| 削除ボタン | クリック | `DELETE /api/v1/notifications/{id}` | 確認ダイアログ表示 |

### 2.5 通知一覧ページ（notifications）

#### 一覧表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 通知アイコン | アイコン | `GET /api/v1/notifications` | `items[].icon` | 絵文字表示 |
| 通知タイトル | テキスト | 同上 | `items[].title` | - |
| 通知メッセージ | テキスト | 同上 | `items[].message` | - |
| 通知日時 | 日時 | 同上 | `items[].createdAt` | YYYY/MM/DD HH:mm |
| 既読状態 | バッジ | 同上 | `items[].isRead` | `true`→"既読", `false`→"未読" |
| 関連リソース | リンク | 同上 | `items[].linkUrl` | 遷移リンク表示 |

#### ページネーション

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ページ番号 | ボタン群 | `GET /api/v1/notifications` | `total`, `skip`, `limit` | `Math.ceil(total / limit)` でページ数計算 |

---

## 3. 画面項目・APIマッピング

### 3.1 コンテキスト取得

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザーID | - | `GET /api/v1/user_account/me/context` | `user.id` | 内部使用 |
| ユーザー名 | テキスト | 同上 | `user.displayName` | - |
| メール | テキスト | 同上 | `user.email` | - |
| ロール | 配列 | 同上 | `user.roles` | - |
| システム管理者フラグ | boolean | 同上 | `permissions.isSystemAdmin` | - |
| 表示セクション | 配列 | 同上 | `sidebar.visibleSections` | - |
| プロジェクト数 | 数値 | 同上 | `navigation.projectCount` | - |
| 遷移タイプ | enum | 同上 | `navigation.projectNavigationType` | `list` or `detail` |
| デフォルトプロジェクトID | UUID | 同上 | `navigation.defaultProjectId` | 1件時のみ |
| 未読通知数 | 数値 | 同上 | `notifications.unreadCount` | - |

### 3.2 グローバル検索

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 検索キーワード | テキスト | ✓ | `GET /api/v1/search` | `q` | 2文字以上 |
| タイプフィルタ | セレクト | - | 同上 | `type` | project/session/file/tree |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト10 |

### 3.3 通知管理

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 既読フィルタ | セレクト | - | `GET /api/v1/notifications` | `is_read` | true/false |
| スキップ | 数値 | - | 同上 | `skip` | ≥0 |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト20、最大100 |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| アプリ初期化 | `GET /api/v1/user_account/me/context` | 1回のみ |
| ページリロード | `GET /api/v1/user_account/me/context` | キャッシュ無効時 |
| ログイン成功後 | `GET /api/v1/user_account/me/context` | 強制リフレッシュ |
| プロジェクト参加/離脱後 | refetch() | ナビゲーション更新 |
| 検索入力変更 | `GET /api/v1/search` | 300msデバウンス、2文字以上 |
| ベルクリック | `GET /api/v1/notifications?limit=10` | ドロップダウン用 |
| 通知クリック | `PATCH /api/v1/notifications/{id}/read` | 既読化 |
| すべて既読クリック | `PATCH /api/v1/notifications/read-all` | 一括既読 |
| 60秒ごと | `GET /api/v1/user_account/me/context` | ポーリング（未読件数更新） |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス拒否画面を表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |
| Network Error | オフライン表示、リトライボタン |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 初期ロード | コンテキストAPIは軽量（1KB未満） |
| キャッシュ | React Query で5分間キャッシュ |
| 再レンダリング | useMemo でセクション表示を最適化 |
| バンドルサイズ | セクションコンポーネントは遅延ロード |
| 検索 | 300msデバウンスでAPI呼び出しを最適化 |
| 通知 | 60秒ポーリングで負荷軽減 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| UI-001 | 権限に応じたメニューを表示する | `GET /user_account/me/context` | Sidebar | 設計済 |
| UI-002 | 参画プロジェクト数に応じて遷移先を切り替える | `GET /user_account/me/context` | ProjectNavigator | 設計済 |
| UI-003 | ユーザーコンテキスト情報を取得する | `GET /user_account/me/context` | UserContextProvider | 設計済 |
| UI-004 | プロジェクト・セッション・ファイル・ツリーを横断検索する | `GET /search` | GlobalSearch | 設計済 |
| UI-005 | 検索結果をフィルタリングする | `GET /search?type=` | SearchDropdown | 設計済 |
| UI-006 | 未読通知一覧を取得する | `GET /notifications` | NotificationDropdown | 設計済 |
| UI-007 | 通知詳細を取得する | `GET /notifications/{id}` | NotificationDropdown | 設計済 |
| UI-008 | 通知を既読にする | `PATCH /notifications/{id}/read` | NotificationDropdown | 設計済 |
| UI-009 | すべての通知を既読にする | `PATCH /notifications/read-all` | NotificationDropdown | 設計済 |
| UI-010 | 通知を削除する | `DELETE /notifications/{id}` | NotificationDropdown | 設計済 |
| UI-011 | 未読通知バッジを表示する | `GET /user_account/me/context` | NotificationBadge | 設計済 |

---

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| Header | Default | 標準状態のヘッダー | 未読通知あり/なし、管理者バッジあり/なし |
| Header | WithSearchOpen | 検索パネルが開いた状態 | 検索結果あり/なし/ローディング |
| UserMenu | Default | ユーザーメニュー（閉じた状態） | 通常ユーザー/管理者 |
| UserMenu | Open | ユーザーメニュー（開いた状態） | 全メニュー項目表示 |
| NotificationBell | Default | 通知ベル（未読なし） | バッジなし |
| NotificationBell | WithUnread | 通知ベル（未読あり） | バッジ表示（1-99, 99+） |
| NotificationDropdown | Default | 通知ドロップダウン | 通知一覧表示 |
| NotificationDropdown | Empty | 通知なし状態 | 空状態メッセージ |
| NotificationDropdown | Loading | ローディング状態 | Skeleton表示 |
| GlobalSearch | Default | 検索ボックス（フォーカスなし） | プレースホルダー表示 |
| GlobalSearch | Focused | 検索ボックス（フォーカスあり） | ショートカットヒント非表示 |
| SearchDropdown | WithResults | 検索結果表示 | 各タイプの結果を表示 |
| SearchDropdown | NoResults | 結果なし | 空状態メッセージ |
| SearchDropdown | Loading | ローディング状態 | Skeleton表示 |
| SearchResultItem | Project | プロジェクト結果 | 📁アイコン |
| SearchResultItem | Session | セッション結果 | 📊アイコン |
| SearchResultItem | File | ファイル結果 | 📄アイコン |
| SearchResultItem | Tree | ツリー結果 | 🌳アイコン |
| Sidebar | Default | 通常ユーザー向け | 基本メニュー表示 |
| Sidebar | Admin | 管理者向け | 全メニュー表示 |
| Sidebar | Collapsed | 折りたたみ状態 | アイコンのみ表示 |
| SidebarItem | Default | 通常状態 | 非アクティブ |
| SidebarItem | Active | アクティブ状態 | ハイライト表示 |
| ThemeToggle | Light | ライトモード選択中 | ☀️アイコン |
| ThemeToggle | Dark | ダークモード選択中 | 🌙アイコン |
| ThemeToggle | System | システム設定 | 💻アイコン |
| AppLayout | Default | アプリケーションレイアウト | ヘッダー+サイドバー+コンテンツ |

### 8.2 ストーリー実装例

```tsx
// features/common/components/Header/Header.stories.tsx
import type { Meta, StoryObj } from "@storybook/react";
import { Header } from "./Header";
import { UserContextProvider } from "../../contexts/UserContextProvider";

const meta: Meta<typeof Header> = {
  title: "Features/Common/Header",
  component: Header,
  tags: ["autodocs"],
  decorators: [
    (Story) => (
      <UserContextProvider>
        <Story />
      </UserContextProvider>
    ),
  ],
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;
type Story = StoryObj<typeof Header>;

export const Default: Story = {};

export const WithUnreadNotifications: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get("/api/v1/user_account/me/context", () => {
          return HttpResponse.json({
            user: { id: "1", displayName: "テストユーザー", email: "test@example.com" },
            notifications: { unreadCount: 5 },
            permissions: { isSystemAdmin: false },
          });
        }),
      ],
    },
  },
};

export const AdminUser: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get("/api/v1/user_account/me/context", () => {
          return HttpResponse.json({
            user: { id: "1", displayName: "管理者", email: "admin@example.com" },
            notifications: { unreadCount: 0 },
            permissions: { isSystemAdmin: true },
          });
        }),
      ],
    },
  },
};
```

```tsx
// features/common/components/Header/NotificationBell.stories.tsx
import type { Meta, StoryObj } from "@storybook/react";
import { NotificationBell } from "./NotificationBell";

const meta: Meta<typeof NotificationBell> = {
  title: "Features/Common/NotificationBell",
  component: NotificationBell,
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof NotificationBell>;

export const Default: Story = {
  args: {
    unreadCount: 0,
  },
};

export const WithUnread: Story = {
  args: {
    unreadCount: 5,
  },
};

export const ManyUnread: Story = {
  args: {
    unreadCount: 99,
  },
};

export const OverflowUnread: Story = {
  args: {
    unreadCount: 150,
  },
};
```

```tsx
// features/common/components/Sidebar/Sidebar.stories.tsx
import type { Meta, StoryObj } from "@storybook/react";
import { Sidebar } from "./Sidebar";
import { MemoryRouter } from "react-router-dom";

const meta: Meta<typeof Sidebar> = {
  title: "Features/Common/Sidebar",
  component: Sidebar,
  tags: ["autodocs"],
  decorators: [
    (Story) => (
      <MemoryRouter>
        <Story />
      </MemoryRouter>
    ),
  ],
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;
type Story = StoryObj<typeof Sidebar>;

export const Default: Story = {
  args: {
    visibleSections: ["dashboard", "project", "analysis", "driver-tree", "file"],
    isCollapsed: false,
  },
};

export const Admin: Story = {
  args: {
    visibleSections: [
      "dashboard",
      "project",
      "analysis",
      "driver-tree",
      "file",
      "system-admin",
      "monitoring",
      "operations",
    ],
    isCollapsed: false,
  },
};

export const Collapsed: Story = {
  args: {
    visibleSections: ["dashboard", "project", "analysis", "driver-tree", "file"],
    isCollapsed: true,
  },
};
```

```tsx
// features/common/components/Header/GlobalSearch.stories.tsx
import type { Meta, StoryObj } from "@storybook/react";
import { GlobalSearch } from "./GlobalSearch";
import { http, HttpResponse } from "msw";

const meta: Meta<typeof GlobalSearch> = {
  title: "Features/Common/GlobalSearch",
  component: GlobalSearch,
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof GlobalSearch>;

export const Default: Story = {};

export const WithResults: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get("/api/v1/search", () => {
          return HttpResponse.json({
            total: 4,
            results: [
              {
                id: "1",
                type: "project",
                highlightedText: "<mark>テスト</mark>プロジェクト",
                description: "プロジェクトの説明",
                updatedAt: "2025-12-01T10:00:00Z",
              },
              {
                id: "2",
                type: "session",
                highlightedText: "<mark>テスト</mark>セッション",
                description: "セッションの説明",
                projectName: "サンプルプロジェクト",
                updatedAt: "2025-12-01T09:00:00Z",
              },
            ],
          });
        }),
      ],
    },
  },
};

export const NoResults: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get("/api/v1/search", () => {
          return HttpResponse.json({
            total: 0,
            results: [],
          });
        }),
      ],
    },
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| ユーティリティ関数 | ユニットテスト | 100% | getTypeIcon, formatUnreadCount, truncateText |
| カスタムフック | ユニットテスト | 90% | useUserContext, useGlobalSearch, useNotifications |
| UIコンポーネント | コンポーネントテスト | 85% | Header, Sidebar, NotificationBell, GlobalSearch |
| 統合フロー | E2Eテスト | 主要パス | 検索フロー、通知フロー、ナビゲーション |

### 9.2 ユニットテスト例

```typescript
// features/common/utils/__tests__/formatters.test.ts
import { describe, it, expect } from "vitest";
import { formatUnreadCount, truncateText, getTypeIcon } from "../formatters";

describe("formatUnreadCount", () => {
  it("0の場合は空文字を返す", () => {
    expect(formatUnreadCount(0)).toBe("");
  });

  it("99以下の場合はそのまま返す", () => {
    expect(formatUnreadCount(5)).toBe("5");
    expect(formatUnreadCount(99)).toBe("99");
  });

  it("100以上の場合は99+を返す", () => {
    expect(formatUnreadCount(100)).toBe("99+");
    expect(formatUnreadCount(150)).toBe("99+");
  });
});

describe("truncateText", () => {
  it("指定文字数以下の場合はそのまま返す", () => {
    expect(truncateText("短いテキスト", 50)).toBe("短いテキスト");
  });

  it("指定文字数を超える場合は省略記号を付ける", () => {
    const longText = "これは50文字を超える非常に長いテキストで切り詰められるべきものです。";
    const result = truncateText(longText, 20);
    expect(result).toBe("これは50文字を超える非常に長いテ...");
    expect(result.length).toBe(23); // 20 + "..."
  });
});

describe("getTypeIcon", () => {
  it("各タイプに対応するアイコンを返す", () => {
    expect(getTypeIcon("project")).toBe("📁");
    expect(getTypeIcon("session")).toBe("📊");
    expect(getTypeIcon("file")).toBe("📄");
    expect(getTypeIcon("tree")).toBe("🌳");
  });

  it("未知のタイプの場合はデフォルトアイコンを返す", () => {
    expect(getTypeIcon("unknown")).toBe("📋");
  });
});
```

```typescript
// features/common/utils/__tests__/navigation.test.ts
import { describe, it, expect } from "vitest";
import { getProjectNavigationUrl } from "../navigation";

describe("getProjectNavigationUrl", () => {
  it("プロジェクト数が0の場合は一覧ページを返す", () => {
    expect(getProjectNavigationUrl(0, null)).toBe("/projects");
  });

  it("プロジェクト数が1の場合は詳細ページを返す", () => {
    expect(getProjectNavigationUrl(1, "project-123")).toBe("/projects/project-123");
  });

  it("プロジェクト数が2以上の場合は一覧ページを返す", () => {
    expect(getProjectNavigationUrl(5, "project-123")).toBe("/projects");
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
// features/common/components/Header/__tests__/NotificationBell.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { NotificationBell } from "../NotificationBell";

describe("NotificationBell", () => {
  it("未読数0の場合はバッジを表示しない", () => {
    render(<NotificationBell unreadCount={0} onClick={vi.fn()} />);

    expect(screen.queryByTestId("notification-badge")).not.toBeInTheDocument();
  });

  it("未読数がある場合はバッジを表示する", () => {
    render(<NotificationBell unreadCount={5} onClick={vi.fn()} />);

    expect(screen.getByTestId("notification-badge")).toHaveTextContent("5");
  });

  it("未読数が99を超える場合は99+を表示する", () => {
    render(<NotificationBell unreadCount={150} onClick={vi.fn()} />);

    expect(screen.getByTestId("notification-badge")).toHaveTextContent("99+");
  });

  it("クリックでonClickが呼ばれる", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<NotificationBell unreadCount={5} onClick={onClick} />);

    await user.click(screen.getByRole("button"));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("アクセシビリティ属性が正しく設定されている", () => {
    render(<NotificationBell unreadCount={5} onClick={vi.fn()} />);

    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-label", "通知 5件の未読");
  });
});
```

```tsx
// features/common/components/Sidebar/__tests__/Sidebar.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Sidebar } from "../Sidebar";

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe("Sidebar", () => {
  it("表示セクションに応じたメニューを表示する", () => {
    renderWithRouter(
      <Sidebar
        visibleSections={["dashboard", "project", "analysis"]}
        isCollapsed={false}
      />
    );

    expect(screen.getByText("ダッシュボード")).toBeInTheDocument();
    expect(screen.getByText("プロジェクト管理")).toBeInTheDocument();
    expect(screen.getByText("個別施策分析")).toBeInTheDocument();
    expect(screen.queryByText("システム管理")).not.toBeInTheDocument();
  });

  it("管理者セクションを含める場合は管理メニューを表示する", () => {
    renderWithRouter(
      <Sidebar
        visibleSections={["dashboard", "system-admin", "monitoring"]}
        isCollapsed={false}
      />
    );

    expect(screen.getByText("システム管理")).toBeInTheDocument();
    expect(screen.getByText("監視・運用")).toBeInTheDocument();
  });

  it("折りたたみ状態ではアイコンのみ表示する", () => {
    renderWithRouter(
      <Sidebar
        visibleSections={["dashboard", "project"]}
        isCollapsed={true}
      />
    );

    expect(screen.queryByText("ダッシュボード")).not.toBeInTheDocument();
    expect(screen.getByTestId("sidebar")).toHaveClass("collapsed");
  });
});
```

```tsx
// features/common/components/Header/__tests__/GlobalSearch.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GlobalSearch } from "../GlobalSearch";
import { server } from "@/mocks/server";
import { http, HttpResponse } from "msw";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
};

describe("GlobalSearch", () => {
  it("2文字未満では検索を実行しない", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GlobalSearch />);

    await user.type(screen.getByPlaceholderText("検索..."), "a");

    await waitFor(() => {
      expect(screen.queryByTestId("search-dropdown")).not.toBeInTheDocument();
    });
  });

  it("2文字以上で検索を実行する", async () => {
    server.use(
      http.get("/api/v1/search", () => {
        return HttpResponse.json({
          total: 1,
          results: [
            { id: "1", type: "project", highlightedText: "テスト", description: "説明" },
          ],
        });
      })
    );

    const user = userEvent.setup();
    renderWithProviders(<GlobalSearch />);

    await user.type(screen.getByPlaceholderText("検索..."), "テスト");

    await waitFor(() => {
      expect(screen.getByTestId("search-dropdown")).toBeInTheDocument();
    });
  });

  it("Ctrl+Kで検索ボックスにフォーカスする", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GlobalSearch />);

    await user.keyboard("{Control>}k{/Control}");

    expect(screen.getByPlaceholderText("検索...")).toHaveFocus();
  });

  it("検索結果をキーボードでナビゲートできる", async () => {
    server.use(
      http.get("/api/v1/search", () => {
        return HttpResponse.json({
          total: 2,
          results: [
            { id: "1", type: "project", highlightedText: "結果1", description: "説明1" },
            { id: "2", type: "session", highlightedText: "結果2", description: "説明2" },
          ],
        });
      })
    );

    const user = userEvent.setup();
    renderWithProviders(<GlobalSearch />);

    await user.type(screen.getByPlaceholderText("検索..."), "テスト");

    await waitFor(() => {
      expect(screen.getByTestId("search-dropdown")).toBeInTheDocument();
    });

    await user.keyboard("{ArrowDown}");
    expect(screen.getByText("結果1").closest("li")).toHaveClass("selected");

    await user.keyboard("{ArrowDown}");
    expect(screen.getByText("結果2").closest("li")).toHaveClass("selected");
  });
});
```

### 9.4 E2Eテスト例

```typescript
// e2e/common-ui.spec.ts
import { test, expect } from "@playwright/test";

test.describe("共通UI機能", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("グローバル検索で結果を表示し、選択できる", async ({ page }) => {
    // 検索ボックスをクリック
    await page.getByPlaceholder("検索...").click();

    // 検索キーワードを入力
    await page.getByPlaceholder("検索...").fill("テストプロジェクト");

    // 検索結果が表示されるまで待機
    await expect(page.getByTestId("search-dropdown")).toBeVisible();

    // 検索結果をクリック
    await page.getByTestId("search-result-0").click();

    // 詳細ページに遷移
    await expect(page).toHaveURL(/\/projects\/.+/);
  });

  test("Ctrl+Kで検索にフォーカスできる", async ({ page }) => {
    await page.keyboard.press("Control+k");

    await expect(page.getByPlaceholder("検索...")).toBeFocused();
  });

  test("通知ベルをクリックして通知一覧を表示できる", async ({ page }) => {
    // 通知ベルをクリック
    await page.getByTestId("notification-bell").click();

    // ドロップダウンが表示される
    await expect(page.getByTestId("notification-dropdown")).toBeVisible();

    // 通知が表示される
    await expect(page.getByTestId("notification-item-0")).toBeVisible();
  });

  test("通知をクリックして既読にできる", async ({ page }) => {
    await page.getByTestId("notification-bell").click();
    await expect(page.getByTestId("notification-dropdown")).toBeVisible();

    // 未読通知をクリック
    const notification = page.getByTestId("notification-item-0");
    await expect(notification).toHaveClass(/unread/);
    await notification.click();

    // 関連ページに遷移
    await expect(page).not.toHaveURL("/");
  });

  test("すべて既読ボタンで一括既読にできる", async ({ page }) => {
    await page.getByTestId("notification-bell").click();

    // すべて既読ボタンをクリック
    await page.getByRole("button", { name: "すべて既読" }).click();

    // バッジが消える
    await expect(page.getByTestId("notification-badge")).not.toBeVisible();
  });

  test("サイドバーの折りたたみができる", async ({ page }) => {
    const sidebar = page.getByTestId("sidebar");

    // 初期状態は展開
    await expect(sidebar).not.toHaveClass(/collapsed/);

    // 折りたたみボタンをクリック
    await page.getByTestId("sidebar-toggle").click();

    // 折りたたみ状態になる
    await expect(sidebar).toHaveClass(/collapsed/);

    // 再度クリックで展開
    await page.getByTestId("sidebar-toggle").click();
    await expect(sidebar).not.toHaveClass(/collapsed/);
  });

  test("権限に応じたサイドバーメニューを表示する", async ({ page }) => {
    // 通常ユーザーとしてログイン
    await page.goto("/");

    // 管理メニューが表示されない
    await expect(page.getByText("システム管理")).not.toBeVisible();

    // 管理者としてログイン
    await page.evaluate(() => {
      localStorage.setItem("test-user-role", "system_admin");
    });
    await page.reload();

    // 管理メニューが表示される
    await expect(page.getByText("システム管理")).toBeVisible();
  });

  test("ユーザーメニューからプロフィールに遷移できる", async ({ page }) => {
    // ユーザーアバターをクリック
    await page.getByTestId("user-avatar").click();

    // メニューが表示される
    await expect(page.getByTestId("user-menu")).toBeVisible();

    // プロフィールをクリック
    await page.getByRole("menuitem", { name: "プロフィール" }).click();

    // プロフィールページに遷移
    await expect(page).toHaveURL("/settings/profile");
  });
});
```

### 9.5 モックデータ

```typescript
// mocks/handlers/common.ts
import { http, HttpResponse } from "msw";

// ユーザーコンテキスト
const mockUserContext = {
  user: {
    id: "user-001",
    displayName: "テストユーザー",
    email: "test@example.com",
    roles: ["user"],
  },
  permissions: {
    isSystemAdmin: false,
  },
  sidebar: {
    visibleSections: ["dashboard", "project", "analysis", "driver-tree", "file"],
  },
  navigation: {
    projectCount: 3,
    projectNavigationType: "list" as const,
    defaultProjectId: null,
    defaultProjectName: null,
  },
  notifications: {
    unreadCount: 5,
  },
};

const mockAdminContext = {
  ...mockUserContext,
  user: {
    ...mockUserContext.user,
    displayName: "管理者ユーザー",
    email: "admin@example.com",
    roles: ["user", "system_admin"],
  },
  permissions: {
    isSystemAdmin: true,
  },
  sidebar: {
    visibleSections: [
      "dashboard",
      "project",
      "analysis",
      "driver-tree",
      "file",
      "system-admin",
      "monitoring",
      "operations",
    ],
  },
};

// 検索結果
const mockSearchResults = {
  total: 4,
  results: [
    {
      id: "project-001",
      type: "project",
      highlightedText: "<mark>テスト</mark>プロジェクト",
      description: "テスト用のプロジェクトです",
      projectName: null,
      updatedAt: "2025-12-15T10:00:00Z",
      linkUrl: "/projects/project-001",
    },
    {
      id: "session-001",
      type: "session",
      highlightedText: "<mark>テスト</mark>セッション",
      description: "分析セッションの説明",
      projectName: "サンプルプロジェクト",
      updatedAt: "2025-12-14T09:00:00Z",
      linkUrl: "/projects/project-001/sessions/session-001",
    },
    {
      id: "file-001",
      type: "file",
      highlightedText: "<mark>テスト</mark>ドキュメント.pdf",
      description: "アップロードされたPDFファイル",
      projectName: "サンプルプロジェクト",
      updatedAt: "2025-12-13T08:00:00Z",
      linkUrl: "/projects/project-001/files/file-001",
    },
    {
      id: "tree-001",
      type: "tree",
      highlightedText: "売上<mark>テスト</mark>ツリー",
      description: "売上分析用ドライバーツリー",
      projectName: "サンプルプロジェクト",
      updatedAt: "2025-12-12T07:00:00Z",
      linkUrl: "/projects/project-001/trees/tree-001",
    },
  ],
};

// 通知一覧
const mockNotifications = {
  total: 10,
  items: [
    {
      id: "notif-001",
      type: "project_invitation",
      icon: "📨",
      title: "プロジェクトへの招待",
      message: "新規プロジェクト「マーケティング分析」に招待されました。",
      isRead: false,
      createdAt: "2025-12-15T10:30:00Z",
      linkUrl: "/projects/project-002",
    },
    {
      id: "notif-002",
      type: "session_complete",
      icon: "✅",
      title: "分析完了",
      message: "セッション「Q4売上分析」の分析が完了しました。",
      isRead: false,
      createdAt: "2025-12-15T09:00:00Z",
      linkUrl: "/projects/project-001/sessions/session-002",
    },
    {
      id: "notif-003",
      type: "member_added",
      icon: "👥",
      title: "メンバー追加",
      message: "山田太郎さんがプロジェクト「売上分析」に参加しました。",
      isRead: true,
      createdAt: "2025-12-14T15:00:00Z",
      linkUrl: "/projects/project-001/members",
    },
    {
      id: "notif-004",
      type: "file_uploaded",
      icon: "📄",
      title: "ファイルアップロード",
      message: "新しいファイル「報告書.pdf」がアップロードされました。",
      isRead: true,
      createdAt: "2025-12-14T12:00:00Z",
      linkUrl: "/projects/project-001/files/file-002",
    },
    {
      id: "notif-005",
      type: "system_announcement",
      icon: "📢",
      title: "システムメンテナンス",
      message: "12/20 02:00-04:00にシステムメンテナンスを実施します。",
      isRead: true,
      createdAt: "2025-12-13T10:00:00Z",
      linkUrl: null,
    },
  ],
};

export const commonHandlers = [
  // ユーザーコンテキスト取得
  http.get("/api/v1/user_account/me/context", ({ request }) => {
    const url = new URL(request.url);
    const isAdmin = url.searchParams.get("admin") === "true";
    return HttpResponse.json(isAdmin ? mockAdminContext : mockUserContext);
  }),

  // グローバル検索
  http.get("/api/v1/search", ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get("q");
    const type = url.searchParams.get("type");

    if (!query || query.length < 2) {
      return HttpResponse.json({ total: 0, results: [] });
    }

    let results = mockSearchResults.results;
    if (type) {
      results = results.filter((r) => r.type === type);
    }

    return HttpResponse.json({
      total: results.length,
      results,
    });
  }),

  // 通知一覧取得
  http.get("/api/v1/notifications", ({ request }) => {
    const url = new URL(request.url);
    const isRead = url.searchParams.get("is_read");
    const skip = parseInt(url.searchParams.get("skip") || "0");
    const limit = parseInt(url.searchParams.get("limit") || "20");

    let items = mockNotifications.items;
    if (isRead === "true") {
      items = items.filter((n) => n.isRead);
    } else if (isRead === "false") {
      items = items.filter((n) => !n.isRead);
    }

    return HttpResponse.json({
      total: items.length,
      items: items.slice(skip, skip + limit),
    });
  }),

  // 通知既読化
  http.patch("/api/v1/notifications/:id/read", ({ params }) => {
    const { id } = params;
    const notification = mockNotifications.items.find((n) => n.id === id);
    if (!notification) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json({ ...notification, isRead: true });
  }),

  // すべて既読化
  http.patch("/api/v1/notifications/read-all", () => {
    return HttpResponse.json({ success: true, updatedCount: 5 });
  }),

  // 通知削除
  http.delete("/api/v1/notifications/:id", ({ params }) => {
    const { id } = params;
    const notification = mockNotifications.items.find((n) => n.id === id);
    if (!notification) {
      return new HttpResponse(null, { status: 404 });
    }
    return new HttpResponse(null, { status: 204 });
  }),
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計書**: [01-common-ui-design.md](./01-common-ui-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **ユーザー管理設計書**: [../03-user-management/01-user-management-design.md](../03-user-management/01-user-management-design.md)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | CU-FRONTEND-001 |
| 対象ユースケース | UI-001〜UI-011 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `features/common/` |
