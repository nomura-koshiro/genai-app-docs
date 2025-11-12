---
title: Fix Issues
description: プロジェクト内のTypeScript、ESLint、またはビルド問題を修正
tools: [Read, Edit, MultiEdit, Bash, Grep]
---

@frontend-developer

プロジェクトの問題を修正してください。

## 対象の問題

$ARGUMENTS

## 修正手順

### 1. 問題の分析

まず、問題の詳細を調査してください：

```bash
# TypeScript エラーの場合
cd apps/frontend && pnpm type-check

# ESLint エラーの場合
cd apps/frontend && pnpm lint

# ビルドエラーの場合
cd apps/frontend && pnpm build
```

### 2. 修正方針の決定

以下の優先順位で修正を検討：

#### TypeScript エラー

- [ ] 厳密な型定義の追加
- [ ] `src/types/api.ts` の型活用
- [ ] ジェネリクスの適切な使用
- [ ] `any` の排除

#### ESLint エラー

- [ ] プロジェクトのコーディング規約に従う修正
- [ ] 不使用変数・インポートの削除
- [ ] Hook依存配列の修正
- [ ] アクセシビリティ要件の修正

#### パフォーマンス問題

- [ ] 不要な再レンダリングの防止
- [ ] メモ化の適切な使用
- [ ] バンドルサイズの最適化

### 3. プロジェクト固有の考慮事項

- **アーキテクチャ**: bulletproof-react features-based architecture
- **状態管理**: Zustand (グローバル), TanStack Query (サーバー), React State (ローカル)
- **スタイリング**: Tailwind CSS + CVA
- **フォーム**: React Hook Form + Zod

### 4. 修正後の検証

修正完了後、以下のコマンドで検証してください：

```bash
# 型チェック
cd apps/frontend && pnpm type-check

# リント・フォーマット
cd apps/frontend && pnpm lint && pnpm format

# テスト実行
cd apps/frontend && pnpm test

# ビルド確認
cd apps/frontend && pnpm build
```

## 品質基準

- **型安全性**: `any` を使用せず、厳密な型定義
- **パフォーマンス**: 不要な再レンダリングなし
- **アクセシビリティ**: WCAG 2.1 準拠
- **テスタビリティ**: 適切なテストが書きやすい設計

## プロジェクトガイドライン参照

修正時に以下のドキュメントを参照してください：

- `apps/frontend/docs/DEVELOPMENT_GUIDE.md` - 開発ガイド
- `apps/frontend/docs/COMPONENT_GUIDELINES.md` - コンポーネント設計
- `apps/frontend/docs/ARCHITECTURE.md` - アーキテクチャ設計

修正内容と理由を明確に説明してください。
