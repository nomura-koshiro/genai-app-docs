# 複製・エクスポート フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

複製・エクスポート機能は専用の新規画面を持たず、既存画面に機能を追加します。

| 画面名 | 画面パス | 追加機能 | 実装状況 |
|-------|---------|---------|---------|
| セッション一覧 | `/projects/{id}/sessions` | セッション複製ボタン | 実装済 |
| 分析画面 | `/projects/{id}/analysis/{id}` | 分析結果エクスポートボタン | 未実装 |
| ツリー一覧 | `/projects/{id}/trees` | ツリー複製ボタン | 実装済 |
| 計算結果画面 | `/projects/{id}/trees/{id}/results` | ツリー計算結果エクスポートボタン | 実装済 |
| ノード編集パネル | `/projects/{id}/trees/{id}/edit` | ノードデータダウンロードボタン | 実装済 |

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `Button` | 複製ボタン、エクスポートボタン | [02-shared-ui-components.md](../01-frontend-common/02-shared-ui-components.md) |
| `Input` | 新しい名前入力 | 同上 |
| `Modal` | 複製確認ダイアログ、エクスポートオプションダイアログ | 同上 |
| `Alert` | 操作完了/エラー通知 | 同上 |
| `Progress` | ダウンロード進捗表示 | 同上 |

### 1.3 コンポーネント構成

```text
features/copy-export/
├── api/
│   ├── duplicate-session.ts          # POST /session/{id}/duplicate
│   ├── duplicate-tree.ts             # POST /tree/{id}/duplicate
│   ├── export-session.ts             # GET /session/{id}/export
│   ├── export-tree.ts                # GET /tree/{id}/output
│   ├── export-node-preview.ts        # GET /node/{id}/preview/output
│   └── index.ts
├── components/
│   ├── duplicate-session-modal/
│   │   ├── duplicate-session-modal.tsx  # セッション複製ダイアログ（Modal, Input使用）
│   │   └── index.ts
│   ├── duplicate-tree-modal/
│   │   ├── duplicate-tree-modal.tsx     # ツリー複製ダイアログ（Modal, Input使用）
│   │   └── index.ts
│   ├── export-session-modal/
│   │   ├── export-session-modal.tsx     # セッションエクスポートダイアログ（Modal使用）
│   │   └── index.ts
│   ├── export-tree-modal/
│   │   ├── export-tree-modal.tsx        # ツリーエクスポートダイアログ（Modal使用）
│   │   └── index.ts
│   ├── duplicate-button/
│   │   ├── duplicate-button.tsx         # 複製ボタン（Button使用）
│   │   └── index.ts
│   ├── export-button/
│   │   ├── export-button.tsx            # エクスポートボタン（Button使用）
│   │   └── index.ts
│   └── index.ts
├── types/
│   ├── api.ts                        # API入出力の型
│   ├── domain.ts                     # ドメインモデル（DuplicateOptions, ExportOptions等）
│   └── index.ts
└── index.ts
```

**注意**: copy-export機能は他機能の画面に組み込まれるコンポーネント群であり、独自のroutesディレクトリは持ちません。各モーダルコンポーネントは、使用される画面（sessions、trees等）のhookで状態管理されます。

#### ボタンコンポーネント

| コンポーネント | 配置場所 | APIエンドポイント | トリガーアクション |
|--------------|---------|------------------|------------------|
| 複製ボタン (Session) | セッション一覧の各行 | POST /session/{id}/duplicate | 複製確認ダイアログを表示 |
| 複製ボタン (Tree) | ツリー一覧の各行 | POST /tree/{id}/duplicate | 複製確認ダイアログを表示 |
| エクスポートボタン (Session) | 分析画面ヘッダー | GET /session/{id}/export | エクスポートオプションダイアログを表示 |
| エクスポートボタン (Tree) | 計算結果画面ヘッダー | GET /tree/{id}/output | ファイルダウンロード |
| データダウンロードボタン | ノード編集パネル | GET /node/{id}/preview/output | CSVファイルダウンロード |

#### ダイアログコンポーネント

##### 複製確認ダイアログ

```text
┌────────────────────────────────────────┐
│  セッションを複製                        │
├────────────────────────────────────────┤
│  新しいセッション名:                     │
│  ┌──────────────────────────────────┐  │
│  │ Q4売上分析 (コピー)              │  │
│  └──────────────────────────────────┘  │
│                                        │
│  ☑ スナップショットも複製する           │
│                                        │
├────────────────────────────────────────┤
│  [キャンセル]              [複製する]   │
└────────────────────────────────────────┘
```

##### エクスポートオプションダイアログ

```text
┌────────────────────────────────────────┐
│  分析結果をエクスポート                  │
├────────────────────────────────────────┤
│  ファイル形式:                          │
│  ○ Excel (.xlsx)                       │
│  ○ CSV (.csv)                          │
│  ○ PDF (.pdf)                          │
│                                        │
│  含めるデータ:                          │
│  ☑ ステップ詳細                        │
│  ☑ チャット履歴                        │
│                                        │
├────────────────────────────────────────┤
│  [キャンセル]           [エクスポート]   │
└────────────────────────────────────────┘
```

---

## 2. 画面詳細設計

### 2.1 セッション複製

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| セッション名 | テキスト | - | POST /session/{id}/duplicate | name | 省略時は自動生成 |
| スナップショット複製 | チェックボックス | - | POST /session/{id}/duplicate | includeSnapshots | デフォルトtrue |
| 複製ボタン | ボタン | - | POST /session/{id}/duplicate | - | - |

### 2.2 ツリー複製

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| ツリー名 | テキスト | - | POST /tree/{id}/duplicate | name | 省略時は自動生成 |
| 複製ボタン | ボタン | - | POST /tree/{id}/duplicate | - | - |

### 2.3 セッションエクスポート

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 値 |
|---------|---------|------------------|-----------------|-----|
| Excel形式 | ラジオ | GET /session/{id}/export | format | xlsx |
| CSV形式 | ラジオ | GET /session/{id}/export | format | csv |
| PDF形式 | ラジオ | GET /session/{id}/export | format | pdf |
| ステップ詳細 | チェックボックス | GET /session/{id}/export | include_steps | true/false |
| チャット履歴 | チェックボックス | GET /session/{id}/export | include_chat | true/false |

### 2.4 ツリーエクスポート

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 値 |
|---------|---------|------------------|-----------------|-----|
| Excel形式 | ラジオ | GET /tree/{id}/output | format | xlsx |
| CSV形式 | ラジオ | GET /tree/{id}/output | format | csv |
| エクスポートボタン | ボタン | GET /tree/{id}/output | - | - |

---

## 3. 画面項目・APIマッピング

### 3.1 セッション複製

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| セッション名 | テキスト | - | `POST /session/{id}/duplicate` | `name` | 省略時は自動生成 |
| スナップショット複製 | チェックボックス | - | 同上 | `includeSnapshots` | デフォルトtrue |

### 3.2 ツリー複製

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ツリー名 | テキスト | - | `POST /tree/{id}/duplicate` | `name` | 省略時は自動生成 |

### 3.3 エクスポート

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| ファイル形式 | ラジオ | ✓ | `GET /session/{id}/export` | `format` | xlsx/csv/pdf |
| ステップ詳細含む | チェックボックス | - | 同上 | `include_steps` | true/false |
| チャット履歴含む | チェックボックス | - | 同上 | `include_chat` | true/false |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| 複製ボタンクリック | - | 確認ダイアログ表示 |
| 複製確認 | `POST /session/{id}/duplicate` | ダイアログ送信時 |
| ツリー複製確認 | `POST /tree/{id}/duplicate` | ダイアログ送信時 |
| エクスポートボタンクリック | - | オプションダイアログ表示 |
| エクスポート実行 | `GET /session/{id}/export` | ファイルダウンロード |
| ツリーエクスポート | `GET /tree/{id}/output` | ファイルダウンロード |
| ノードデータダウンロード | `GET /node/{id}/preview/output` | CSVダウンロード |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス権限がありませんメッセージ表示 |
| 404 Not Found | 対象が見つかりませんメッセージ表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |
| ダウンロードエラー | "ファイルのダウンロードに失敗しました"メッセージ表示 |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 複製処理 | 非同期処理で大きなセッションも対応 |
| エクスポート | ストリーミングダウンロードで大容量ファイル対応 |
| UI応答性 | 処理中はローディング表示、キャンセル可能 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| CP-001 | 分析セッション複製 | `POST /session/{id}/duplicate` | sessions | 実装済 |
| CP-002 | ドライバーツリー複製 | `POST /tree/{id}/duplicate` | trees | 実装済 |
| EX-001 | 分析結果エクスポート | `GET /session/{id}/export` | analysis | 未実装 |
| EX-002 | ツリー計算結果エクスポート | `GET /tree/{id}/output` | tree-results | 実装済 |
| EX-003 | ノードデータエクスポート | `GET /node/{id}/preview/output` | tree-edit | 実装済 |

---

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| DuplicateButton | Default | 複製ボタン表示 | 通常、無効、処理中 |
| DuplicateSessionModal | Default | セッション複製モーダル | 通常、オプション選択、送信中 |
| DuplicateTreeModal | Default | ツリー複製モーダル | 通常、送信中 |
| ExportButton | Default | エクスポートボタン表示 | 通常、ダウンロード中 |
| ExportSessionModal | Default | セッションエクスポートモーダル | 通常、オプション選択 |
| ExportTreeModal | Default | ツリーエクスポートモーダル | 通常、フォーマット選択 |

### 8.2 ストーリー実装例

```tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { DuplicateSessionModal } from "./duplicate-session-modal";
import type { DuplicateSession } from "../../types";

const mockSession: DuplicateSession = {
  id: "1",
  name: "Q4売上分析",
};

const meta = {
  title: "features/copy-export/components/duplicate-session-modal",
  component: DuplicateSessionModal,
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: "セッション複製モーダルコンポーネント。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onClose: fn(),
    onDuplicate: fn(),
  },
  argTypes: {
    isOpen: { control: "boolean" },
    isSubmitting: { control: "boolean" },
  },
} satisfies Meta<typeof DuplicateSessionModal>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    isOpen: true,
    session: mockSession,
    defaultName: "Q4売上分析 (コピー)",
  },
};

export const WithOptions: Story = {
  args: {
    isOpen: true,
    session: mockSession,
    defaultName: "Q4売上分析 (コピー)",
    includeSnapshots: true,
  },
};

export const Submitting: Story = {
  args: {
    isOpen: true,
    session: mockSession,
    isSubmitting: true,
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| コンポーネント | ユニットテスト | 80%以上 | モーダル表示、フォーム操作、ボタン状態 |
| API関数 | ユニットテスト | 90%以上 | リクエスト構築、レスポンス処理 |
| 統合 | コンポーネントテスト | 70%以上 | 複製フロー、エクスポートフロー |
| E2E | E2Eテスト | 主要フロー | 複製完了、ファイルダウンロード |

### 9.2 ユニットテスト例

```typescript
import { describe, it, expect } from "vitest";
import { generateDuplicateName, buildExportUrl } from "./copy-export-utils";

describe("generateDuplicateName", () => {
  it("名前にコピーを追加する", () => {
    expect(generateDuplicateName("Q4売上分析")).toBe("Q4売上分析 (コピー)");
  });

  it("既にコピーがある場合は番号を付ける", () => {
    expect(generateDuplicateName("Q4売上分析 (コピー)")).toBe("Q4売上分析 (コピー 2)");
  });
});

describe("buildExportUrl", () => {
  it("オプションなしでURLを構築する", () => {
    const url = buildExportUrl("session-1", { format: "xlsx" });
    expect(url).toBe("/api/session/session-1/export?format=xlsx");
  });

  it("オプション付きでURLを構築する", () => {
    const url = buildExportUrl("session-1", {
      format: "xlsx",
      includeSteps: true,
      includeChat: false,
    });
    expect(url).toBe(
      "/api/session/session-1/export?format=xlsx&include_steps=true&include_chat=false"
    );
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { DuplicateSessionModal } from "./duplicate-session-modal";
import type { DuplicateSession } from "../../types";

describe("DuplicateSessionModal", () => {
  const mockSession: DuplicateSession = { id: "1", name: "Q4売上分析" };

  it("モーダルを表示する", () => {
    render(
      <DuplicateSessionModal
        isOpen={true}
        session={mockSession}
        onClose={vi.fn()}
        onDuplicate={vi.fn()}
      />
    );

    expect(screen.getByText("セッションを複製")).toBeInTheDocument();
    expect(screen.getByLabelText("新しいセッション名")).toBeInTheDocument();
  });

  it("デフォルト名を表示する", () => {
    render(
      <DuplicateSessionModal
        isOpen={true}
        session={mockSession}
        defaultName="Q4売上分析 (コピー)"
        onClose={vi.fn()}
        onDuplicate={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue("Q4売上分析 (コピー)")).toBeInTheDocument();
  });

  it("複製ボタンクリックでonDuplicateを呼び出す", async () => {
    const user = userEvent.setup();
    const onDuplicate = vi.fn();
    render(
      <DuplicateSessionModal
        isOpen={true}
        session={mockSession}
        onClose={vi.fn()}
        onDuplicate={onDuplicate}
      />
    );

    await user.click(screen.getByRole("button", { name: "複製する" }));

    await waitFor(() => {
      expect(onDuplicate).toHaveBeenCalledWith({
        name: expect.any(String),
        includeSnapshots: true,
      });
    });
  });

  it("送信中は複製ボタンを無効化する", () => {
    render(
      <DuplicateSessionModal
        isOpen={true}
        session={mockSession}
        isSubmitting={true}
        onClose={vi.fn()}
        onDuplicate={vi.fn()}
      />
    );

    expect(screen.getByRole("button", { name: /複製/ })).toBeDisabled();
  });
});
```

### 9.4 E2Eテスト例

```typescript
import { test, expect } from "@playwright/test";

test.describe("複製・エクスポート機能", () => {
  test("セッションを複製できる", async ({ page }) => {
    await page.goto("/projects/1/sessions");

    // 複製ボタンクリック
    await page.getByTestId("session-row-1").getByRole("button", { name: "複製" }).click();

    // モーダルで名前を入力
    await expect(page.getByText("セッションを複製")).toBeVisible();
    await page.getByLabel("新しいセッション名").fill("Q4売上分析 (コピー)");

    // 複製実行
    await page.getByRole("button", { name: "複製する" }).click();

    // 成功メッセージ
    await expect(page.getByText("セッションを複製しました")).toBeVisible();

    // 一覧に表示される
    await expect(page.getByText("Q4売上分析 (コピー)")).toBeVisible();
  });

  test("ツリーを複製できる", async ({ page }) => {
    await page.goto("/projects/1/trees");

    // 複製ボタンクリック
    await page.getByTestId("tree-row-1").getByRole("button", { name: "複製" }).click();

    // モーダルで名前を入力
    await page.getByLabel("新しいツリー名").fill("売上分析ツリー (コピー)");

    // 複製実行
    await page.getByRole("button", { name: "複製する" }).click();

    // 成功メッセージ
    await expect(page.getByText("ツリーを複製しました")).toBeVisible();
  });

  test("セッション結果をエクスポートできる", async ({ page }) => {
    await page.goto("/projects/1/analysis/1");

    // エクスポートボタンクリック
    await page.getByRole("button", { name: "エクスポート" }).click();

    // オプション選択
    await page.getByLabel("Excel (.xlsx)").check();
    await page.getByLabel("ステップ詳細").check();

    // ダウンロード開始
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "エクスポート" }).click();

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
  });

  test("ツリー計算結果をエクスポートできる", async ({ page }) => {
    await page.goto("/projects/1/trees/1/results");

    // ダウンロード開始
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "エクスポート" }).click();
    await page.getByRole("menuitem", { name: "Excel" }).click();

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
  });
});
```

### 9.5 モックデータ

```typescript
// src/testing/mocks/handlers/copy-export.ts
import { http, HttpResponse } from "msw";

export const copyExportHandlers = [
  http.post("/api/session/:id/duplicate", async ({ request, params }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: "new-session-id",
      name: body.name || `Session ${params.id} (コピー)`,
      createdAt: new Date().toISOString(),
    });
  }),

  http.post("/api/tree/:id/duplicate", async ({ request, params }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: "new-tree-id",
      name: body.name || `Tree ${params.id} (コピー)`,
      createdAt: new Date().toISOString(),
    });
  }),

  http.get("/api/session/:id/export", ({ request }) => {
    const url = new URL(request.url);
    const format = url.searchParams.get("format") || "xlsx";

    // ファイルダウンロードレスポンス
    return new HttpResponse(new Blob(["mock data"]), {
      headers: {
        "Content-Type": format === "xlsx"
          ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          : format === "csv"
          ? "text/csv"
          : "application/pdf",
        "Content-Disposition": `attachment; filename="export.${format}"`,
      },
    });
  }),

  http.get("/api/tree/:id/output", ({ request }) => {
    const url = new URL(request.url);
    const format = url.searchParams.get("format") || "xlsx";

    return new HttpResponse(new Blob(["mock tree data"]), {
      headers: {
        "Content-Type": format === "xlsx"
          ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          : "text/csv",
        "Content-Disposition": `attachment; filename="tree-output.${format}"`,
      },
    });
  }),

  http.get("/api/node/:id/preview/output", () => {
    return new HttpResponse(new Blob(["col1,col2\nval1,val2"]), {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": 'attachment; filename="node-data.csv"',
      },
    });
  }),
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計書**: [01-copy-export-design.md](./01-copy-export-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | CE-FRONTEND-001 |
| 対象ユースケース | CP-001〜CP-002, EX-001〜EX-003 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `features/copy-export/` |
