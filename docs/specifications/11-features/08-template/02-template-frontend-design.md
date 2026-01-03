# テンプレート フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| templates | テンプレート一覧 | /projects/{id}/templates | テンプレート管理画面 |
| template-select | テンプレート選択 | - | モーダル/ドロワー（tree-new内） |

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `Card` | テンプレートカード | [02-shared-ui-components.md](../01-frontend-common/02-shared-ui-components.md) |
| `DataTable` | テンプレート一覧テーブル | 同上 |
| `Badge` | タイプバッジ、人気バッジ | 同上 |
| `Button` | 削除ボタン、作成ボタン | 同上 |
| `Input` | テンプレート名入力 | 同上 |
| `Textarea` | 説明入力 | 同上 |
| `Select` | カテゴリ選択 | 同上 |
| `Modal` | テンプレート作成モーダル | 同上 |
| `Alert` | 操作完了/エラー通知 | 同上 |
| `Skeleton` | ローディング表示 | 同上 |
| `EmptyState` | テンプレートなし状態 | 同上 |

### 1.3 コンポーネント構成

```text
features/templates/
├── api/
│   ├── get-templates.ts              # GET /template, GET /driver-tree/template
│   ├── get-template.ts               # GET /template/{id}
│   ├── create-template.ts            # POST /driver-tree/template
│   ├── delete-template.ts            # DELETE /template/{id}
│   └── index.ts
├── components/
│   ├── template-table/
│   │   ├── template-table.tsx        # テンプレート一覧表示（DataTable使用）
│   │   └── index.ts
│   ├── template-card/
│   │   ├── template-card.tsx         # テンプレートカード（Card, Badge使用）
│   │   └── index.ts
│   ├── template-filters/
│   │   ├── template-filters.tsx      # フィルター機能（Select使用）
│   │   └── index.ts
│   ├── template-selector/
│   │   ├── template-selector.tsx     # テンプレート選択UI（Card使用）
│   │   ├── template-preview.tsx      # プレビュー表示
│   │   ├── category-filter.tsx       # 業種・分析タイプフィルター（Select使用）
│   │   └── index.ts
│   ├── create-template-modal/
│   │   ├── create-template-modal.tsx # テンプレート作成モーダル（Modal使用）
│   │   ├── template-form-fields.tsx  # フォームフィールド（Input, Textarea, Select使用）
│   │   └── index.ts
│   └── index.ts
├── routes/
│   └── template-list/
│       ├── template-list.tsx         # テンプレート一覧コンテナ
│       ├── template-list.hook.ts     # テンプレート一覧用hook
│       └── index.ts
├── types/
│   ├── api.ts                        # API入出力の型
│   ├── domain.ts                     # ドメインモデル（Template等）
│   └── index.ts
└── index.ts

app/projects/[id]/templates/
└── page.tsx                          # テンプレート一覧ページ → TemplateList
```

#### テンプレート選択UI（tree-new画面内）

既存のtree-new画面内のテンプレート選択部分は、`TemplateSelector`コンポーネントを使用してdriver_tree_templateテーブルのデータを表示します。

```text
┌────────────────────────────────────────────────────────┐
│  テンプレートから作成                                    │
├────────────────────────────────────────────────────────┤
│  業種: [すべて] [小売・EC] [製造業] [サービス業] [SaaS]  │
│  分析タイプ: [すべて] [売上分析] [コスト分析] [利益分析] │
├────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 📈       │ │ 🛒       │ │ 🔄       │ │ 🏭       │  │
│  │ 売上分解 │ │ EC売上   │ │ SaaS MRR │ │ 製造コスト│  │
│  │ モデル   │ │ モデル   │ │ 分解     │ │ 構造     │  │
│  │ ノード:8 │ │ ノード:12│ │ ノード:15│ │ ノード:18│  │
│  │ 利用:150+│ │ 利用:80+ │ │ 利用:45+ │ │ 利用:35+ │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                        │
│  ┌──────────┐                                          │
│  │ ➕       │                                          │
│  │ 空の     │                                          │
│  │ ツリー   │                                          │
│  └──────────┘                                          │
└────────────────────────────────────────────────────────┘
```

---

## 2. 画面詳細設計

### 2.1 テンプレート選択画面（tree-new内）

| 画面項目 | 表示/入力形式 | APIエンドポイント | フィールド | 変換処理 |
|---------|-------------|------------------|-----------|---------|
| 業種フィルター | チップ選択 | GET /driver-tree/template | query: category | - |
| テンプレートカード | カードグリッド | GET /driver-tree/template | templates[] | - |
| テンプレート名 | テキスト | GET /driver-tree/template | templates[].name | - |
| テンプレートアイコン | アイコン | - | - | カテゴリ→アイコン変換 |
| ノード数 | テキスト | GET /driver-tree/template | templates[].nodeCount | "ノード: n" |
| 利用実績 | テキスト | GET /driver-tree/template | templates[].usageCount | "利用実績: n+" |
| 人気バッジ | バッジ | GET /driver-tree/template | templates[].usageCount | >100で表示 |

### 2.2 テンプレート作成モーダル

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| テンプレート名 | テキスト | ○ | POST /driver-tree/template | name | 1-255文字 |
| 説明 | テキストエリア | - | POST /driver-tree/template | description | 任意 |
| カテゴリ | セレクト | - | POST /driver-tree/template | category | 業種選択 |
| 公開設定 | トグル | - | POST /driver-tree/template | isPublic | true/false |
| 元ツリー | 非表示 | ○ | POST /driver-tree/template | sourceTreeId | 現在のツリーID |

### 2.3 テンプレート一覧画面

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| テンプレート名 | テキスト | GET /template | templates[].name | - |
| 説明 | テキスト | GET /template | templates[].description | - |
| タイプ | バッジ | GET /template | templates[].templateType | session/tree |
| 公開状態 | アイコン | GET /template | templates[].isPublic | 公開/非公開アイコン |
| 使用回数 | 数値 | GET /template | templates[].usageCount | - |
| 作成者 | テキスト | GET /template | templates[].createdByName | - |
| 作成日時 | 日時 | GET /template | templates[].createdAt | YYYY/MM/DD形式 |
| 削除ボタン | ボタン | DELETE /template/{id} | - | 確認ダイアログ |

---

## 3. 画面項目・APIマッピング

### 3.1 テンプレート一覧取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| カテゴリフィルタ | セレクト | - | `GET /driver-tree/template` | `category` | 業種選択 |
| スキップ | 数値 | - | 同上 | `skip` | ≥0 |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト20、最大100 |

### 3.2 テンプレート作成

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| テンプレート名 | テキスト | ✓ | `POST /driver-tree/template` | `name` | 1-255文字 |
| 説明 | テキストエリア | - | 同上 | `description` | 任意 |
| カテゴリ | セレクト | - | 同上 | `category` | 業種選択 |
| 公開設定 | トグル | - | 同上 | `isPublic` | true/false |
| 元ツリーID | 非表示 | ✓ | 同上 | `sourceTreeId` | UUID |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| テンプレート一覧ページ表示 | `GET /template` | 初期ロード |
| ツリー作成画面表示 | `GET /driver-tree/template` | テンプレート選択用 |
| カテゴリフィルタ変更 | `GET /driver-tree/template?category=` | 再取得 |
| テンプレート作成ボタン | `POST /driver-tree/template` | モーダル送信時 |
| テンプレート選択 | `POST /driver-tree/tree/import` | テンプレート適用 |
| テンプレート削除 | `DELETE /template/{id}` | 確認後 |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス権限がありませんメッセージ表示 |
| 404 Not Found | テンプレートが見つかりませんメッセージ表示 |
| 409 Conflict | 同名のテンプレートが存在しますメッセージ表示 |
| 422 Validation Error | フォームエラー表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 一覧取得 | ページネーションで件数制限（デフォルト20件） |
| テンプレートカード | useMemo でフィルタ結果を最適化 |
| キャッシュ | React Query でテンプレート一覧を5分間キャッシュ |
| プレビュー | 遅延ロードでテンプレート詳細を取得 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| TM-001 | テンプレート一覧表示 | `GET /template` | templates, tree-new | 設計済 |
| TM-002 | テンプレート作成（セッションから） | `POST /analysis/template` | session-detail | 設計済 |
| TM-003 | テンプレート作成（ツリーから） | `POST /driver-tree/template` | tree-edit | 設計済 |
| TM-004 | テンプレート適用 | `POST /session`, `POST /tree/import` | session-new, tree-new | 設計済 |
| TM-005 | テンプレート削除 | `DELETE /template/{id}` | templates | 設計済 |

---

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| TemplateCard | Default | テンプレートカード表示 | 通常、人気、説明付き、ローディング |
| TemplateTable | Default | テンプレート一覧テーブル | 通常、空、ローディング |
| TemplateFilters | Default | テンプレートフィルター | 初期状態、選択状態 |
| TemplateSelector | Default | テンプレート選択UI | 通常、フィルタ適用、空 |
| CreateTemplateModal | Default | テンプレート作成モーダル | 通常、バリデーションエラー、送信中 |

### 8.2 ストーリー実装例

```tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { TemplateCard } from "./template-card";
import type { Template } from "../../types";

const mockTemplate: Template = {
  id: "1",
  name: "売上分解モデル",
  category: "retail",
  nodeCount: 8,
  usageCount: 45,
};

const meta = {
  title: "features/templates/components/template-card",
  component: TemplateCard,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: "テンプレートカードコンポーネント。テンプレート選択UIで使用。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onSelect: fn(),
  },
  argTypes: {
    isPopular: { control: "boolean" },
    isLoading: { control: "boolean" },
  },
} satisfies Meta<typeof TemplateCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    template: mockTemplate,
  },
};

export const Popular: Story = {
  args: {
    template: {
      ...mockTemplate,
      id: "2",
      name: "EC売上モデル",
      category: "ec",
      nodeCount: 12,
      usageCount: 150,
    },
    isPopular: true,
  },
};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| コンポーネント | ユニットテスト | 80%以上 | Props表示、イベント、状態変化 |
| カスタムフック | ユニットテスト | 90%以上 | データ変換、状態管理、API呼び出し |
| 統合 | コンポーネントテスト | 70%以上 | コンポーネント間連携、フィルタ動作 |
| E2E | E2Eテスト | 主要フロー | テンプレート選択・作成・削除 |

### 9.2 ユニットテスト例

```typescript
import { describe, it, expect } from "vitest";
import { getCategoryIcon, formatUsageCount } from "./template-utils";

describe("getCategoryIcon", () => {
  it("小売カテゴリに正しいアイコンを返す", () => {
    expect(getCategoryIcon("retail")).toBe("📈");
  });

  it("ECカテゴリに正しいアイコンを返す", () => {
    expect(getCategoryIcon("ec")).toBe("🛒");
  });

  it("不明なカテゴリにデフォルトアイコンを返す", () => {
    expect(getCategoryIcon("unknown")).toBe("📁");
  });
});

describe("formatUsageCount", () => {
  it("100未満の場合そのまま表示", () => {
    expect(formatUsageCount(45)).toBe("45");
  });

  it("100以上の場合+付きで表示", () => {
    expect(formatUsageCount(150)).toBe("150+");
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { TemplateCard } from "./template-card";
import type { Template } from "../../types";

describe("TemplateCard", () => {
  const mockTemplate: Template = {
    id: "1",
    name: "売上分解モデル",
    category: "retail",
    nodeCount: 8,
    usageCount: 45,
  };

  it("テンプレート情報を表示する", () => {
    render(<TemplateCard template={mockTemplate} />);

    expect(screen.getByText("売上分解モデル")).toBeInTheDocument();
    expect(screen.getByText("ノード: 8")).toBeInTheDocument();
    expect(screen.getByText("利用実績: 45+")).toBeInTheDocument();
  });

  it("人気テンプレートに人気バッジを表示する", () => {
    render(<TemplateCard template={mockTemplate} isPopular />);

    expect(screen.getByText("人気")).toBeInTheDocument();
  });

  it("カード選択イベントを発火する", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<TemplateCard template={mockTemplate} onSelect={onSelect} />);

    await user.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledWith("1");
  });

  it("ローディング状態でスケルトンを表示する", () => {
    render(<TemplateCard isLoading />);

    expect(screen.getByTestId("template-card-skeleton")).toBeInTheDocument();
  });
});
```

### 9.4 E2Eテスト例

```typescript
import { test, expect } from "@playwright/test";

test.describe("テンプレート機能", () => {
  test("テンプレートからツリーを作成できる", async ({ page }) => {
    await page.goto("/projects/1/trees/new");

    // テンプレート選択
    await page.getByRole("button", { name: "売上分解モデル" }).click();

    // 確認ダイアログ
    await expect(page.getByText("このテンプレートを使用しますか？")).toBeVisible();
    await page.getByRole("button", { name: "使用する" }).click();

    // ツリー編集画面に遷移
    await expect(page).toHaveURL(/\/projects\/1\/trees\/[^/]+\/edit/);
    await expect(page.getByTestId("tree-canvas")).toBeVisible();
  });

  test("カテゴリフィルタでテンプレートを絞り込める", async ({ page }) => {
    await page.goto("/projects/1/trees/new");

    // フィルタ適用
    await page.getByRole("button", { name: "業種" }).click();
    await page.getByRole("option", { name: "小売・EC" }).click();

    // フィルタ結果を確認
    const cards = page.getByTestId("template-card");
    await expect(cards).toHaveCount(2);
  });

  test("テンプレートを作成できる", async ({ page }) => {
    await page.goto("/projects/1/trees/1/edit");

    // テンプレート作成モーダルを開く
    await page.getByRole("button", { name: "テンプレートとして保存" }).click();

    // フォーム入力
    await page.getByLabel("テンプレート名").fill("カスタム売上モデル");
    await page.getByLabel("説明").fill("カスタマイズした売上分析用テンプレート");
    await page.getByLabel("カテゴリ").selectOption("retail");

    // 作成
    await page.getByRole("button", { name: "作成" }).click();

    // 成功メッセージ
    await expect(page.getByText("テンプレートを作成しました")).toBeVisible();
  });

  test("テンプレートを削除できる", async ({ page }) => {
    await page.goto("/projects/1/templates");

    // 削除ボタンクリック
    await page.getByTestId("template-row-1").getByRole("button", { name: "削除" }).click();

    // 確認ダイアログ
    await expect(page.getByText("このテンプレートを削除しますか？")).toBeVisible();
    await page.getByRole("button", { name: "削除" }).click();

    // 成功メッセージ
    await expect(page.getByText("テンプレートを削除しました")).toBeVisible();
  });
});
```

### 9.5 モックデータ

```typescript
// src/testing/mocks/handlers/template.ts
import { http, HttpResponse } from "msw";

export const templateHandlers = [
  http.get("/api/driver-tree/template", ({ request }) => {
    const url = new URL(request.url);
    const category = url.searchParams.get("category");

    const templates = [
      {
        id: "1",
        name: "売上分解モデル",
        category: "retail",
        nodeCount: 8,
        usageCount: 150,
      },
      {
        id: "2",
        name: "EC売上モデル",
        category: "ec",
        nodeCount: 12,
        usageCount: 80,
      },
      {
        id: "3",
        name: "SaaS MRR分解",
        category: "saas",
        nodeCount: 15,
        usageCount: 45,
      },
    ];

    const filtered = category
      ? templates.filter((t) => t.category === category)
      : templates;

    return HttpResponse.json({ templates: filtered, total: filtered.length });
  }),

  http.post("/api/driver-tree/template", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: "new-template-id",
      ...body,
      createdAt: new Date().toISOString(),
    });
  }),

  http.delete("/api/template/:id", () => {
    return HttpResponse.json({ success: true });
  }),
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計書**: [01-template-design.md](./01-template-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | TM-FRONTEND-001 |
| 対象ユースケース | TM-001〜TM-005 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `app/projects/[id]/templates/` |
