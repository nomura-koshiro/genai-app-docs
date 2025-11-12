---
title: Create Feature Module
description: bulletproof-reactアーキテクチャに従った新しい機能を作成
tools: [Write, Edit, MultiEdit, Bash, Glob]
---

@frontend-developer

新しいfeature「$ARGUMENTS」を作成してください。

## アーキテクチャ

bulletproof-react の features-based architecture に従って以下の構造で実装：

```
src/features/$ARGUMENTS/
├── api/
│   └── index.ts          # API関連の関数とフック
├── components/
│   └── index.tsx         # feature固有のコンポーネント
├── hooks/
│   └── index.ts          # カスタムフック
├── types/
│   └── index.ts          # feature固有の型定義
└── index.ts              # エクスポート
```

## 実装要件

### 1. API層 (`api/index.ts`)

- TanStack Query を使用したAPIフック
- 型安全なAPI関数
- エラーハンドリング
- キャッシュ戦略

### 2. コンポーネント (`components/index.tsx`)

- ビジネスロジックを含むコンポーネント
- ローディング・エラー・空状態の処理
- UI コンポーネントとの適切な分離

### 3. カスタムフック (`hooks/index.ts`)

- ロジックの抽象化
- 再利用可能な状態管理
- テスタブルな設計

### 4. 型定義 (`types/index.ts`)

- feature固有の型とインターフェース
- API レスポンス型
- Props型

## 技術仕様

- **状態管理**: TanStack Query (サーバー状態) + React State (ローカル状態)
- **フォーム**: React Hook Form + Zod バリデーション
- **型安全性**: 厳密なTypeScript型定義
- **エラーハンドリング**: api-client での統一処理

## 設計原則

- **単一責任の原則**: 各ファイルは明確な責任を持つ
- **依存性逆転**: カスタムフックによる抽象化
- **テスタビリティ**: 副作用の分離

## プロジェクトガイドラインの確認

以下のドキュメントを参照してください：

- `apps/frontend/docs/ARCHITECTURE.md`
- `apps/frontend/docs/STATE_MANAGEMENT.md`
- `apps/frontend/docs/DEVELOPMENT_GUIDE.md`

完了後、`src/features/index.ts` でのエクスポートも設定してください。
