---
title: Create UI Component
description: bulletproof-reactガイドラインに従った新しいUIコンポーネントを作成
tools: [Write, Edit, MultiEdit, Bash]
---

@frontend-developer

新しいUIコンポーネント「$ARGUMENTS」を作成してください。

## 要件

- **ディレクトリ**: `src/components/sample-ui/$ARGUMENTS/` (基本UI) または `src/components/ui/$ARGUMENTS/` (ユーティリティ)
- **アーキテクチャ**: bulletproof-react features-based architecture に従う
- **設計原則**: SOLID、DRY、KISS原則を適用

## 作成ファイル

1. **メインコンポーネント** (`index.tsx`)
   - CVAを使ったバリアント対応
   - forwardRef実装
   - 厳密なTypeScript型定義
   - 適切なJSDoc

2. **Storybookストーリー** (`$ARGUMENTS.stories.tsx`)
   - 全バリアントの例示
   - インタラクティブな操作例

3. **ユニットテスト** (`$ARGUMENTS.test.tsx`)
   - レンダリングテスト
   - プロパティテスト
   - イベントハンドリングテスト

## 技術仕様

- **スタイリング**: Tailwind CSS + CVA
- **アクセシビリティ**: WCAG 2.1準拠
- **テスト**: Vitest + Testing Library
- **型安全性**: 厳密なProps型定義

## プロジェクトガイドラインの確認

**必ず以下のドキュメントを読んでから実装してください：**

- `.claude/skills/frontend/component-guidelines.md` - コンポーネント設計・命名規則
- `.claude/skills/frontend/architecture.md` - bulletproof-react アーキテクチャ
- `.claude/skills/frontend/testing.md` - テスト方針

完了後、コンポーネントのインポート・エクスポートも含めて設定してください。
