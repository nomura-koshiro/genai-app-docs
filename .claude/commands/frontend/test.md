---
title: Create Tests
description: コンポーネントまたは機能の包括的なテストを作成
tools: [Write, Edit, MultiEdit, Read, Bash]
---

@frontend-developer

「$ARGUMENTS」のテストを作成してください。

## テスト戦略

### 1. ユニットテスト (Vitest + Testing Library)

#### コンポーネントテスト

- [ ] レンダリング確認
- [ ] Props による表示変化
- [ ] イベントハンドリング
- [ ] 条件分岐（ローディング、エラー、空状態）
- [ ] アクセシビリティ属性

#### カスタムフックテスト

- [ ] 初期状態の確認
- [ ] 状態更新の確認
- [ ] 副作用の確認
- [ ] エラーハンドリング

#### ユーティリティ関数テスト

- [ ] 入力・出力のテスト
- [ ] エッジケースの確認
- [ ] エラーハンドリング

### 2. 統合テスト

- [ ] API統合の確認
- [ ] フォーム操作の確認
- [ ] 状態管理統合

### 3. E2E テスト (Playwright)

- [ ] ユーザーシナリオテスト
- [ ] ページ遷移テスト
- [ ] フォーム送信フロー

## テスト実装ガイドライン

### 命名規則

```typescript
// ✅ 良い例
describe("UserCard", () => {
  it("should display user information correctly", () => {});
  it("should call onEdit when edit button is clicked", () => {});
  it("should show loading state while updating", () => {});
});

// ❌ 悪い例
describe("test", () => {
  it("works", () => {});
});
```

### テストデータ

```typescript
// モックデータの作成
const mockUser: User = {
  id: "1",
  name: "John Doe",
  email: "john@example.com",
  // 必要な他のプロパティ...
};
```

### MSW（Mock Service Worker）の活用

API呼び出しのモックを適切に設定してください。

### アクセシビリティテスト

```typescript
// screen.getByRole を使用したテスト
expect(screen.getByRole("button", { name: "送信" })).toBeInTheDocument();
expect(screen.getByLabelText("ユーザー名")).toBeInTheDocument();
```

## カバレッジ目標

- **ライン カバレッジ**: 80% 以上
- **ブランチ カバレッジ**: 75% 以上
- **重要な機能**: 100% カバレッジ

## テスト実行コマンド

```bash
# 全テスト実行
cd apps/frontend && pnpm test

# 特定ファイルのテスト
cd apps/frontend && pnpm test UserCard

# カバレッジ測定
cd apps/frontend && pnpm test:coverage

# ウォッチモード
cd apps/frontend && pnpm test --watch

# E2E テスト
cd apps/frontend && pnpm test:e2e
```

## 品質基準

- **読みやすさ**: テストケース名が明確
- **保守性**: DRYな設計、再利用可能なヘルパー関数
- **信頼性**: 非決定的テストの排除
- **速度**: 高速実行（モック活用）

## プロジェクト固有の考慮事項

- **状態管理**: Zustand/TanStack Query のモック
- **ルーティング**: Next.js App Router のテスト
- **コンポーネント**: CVA バリアントのテスト

## プロジェクトガイドライン参照

**必ず以下のドキュメントを読んでからテストを作成してください：**

- `.claude/skills/frontend/testing.md` - テスト方針・ベストプラクティス
- `.claude/skills/frontend/component-guidelines.md` - コンポーネント設計

テスト作成完了後、実行して全て成功することを確認してください。
