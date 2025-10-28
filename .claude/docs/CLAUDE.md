# Training Tracker - プロジェクト設定・メモリ

## プロジェクト概要

Training Tracker は、個人やチームのトレーニング記録を管理するフルスタックWebアプリケーションです。bulletproof-react アーキテクチャとSOLID原則に基づいて設計されています。

## 重要な設計原則

### アーキテクチャ
- **Features-based Architecture**: 機能別モジュール分割 (`src/features/`)
- **SOLID原則**: 単一責任、開放閉鎖、依存性逆転
- **DRY/KISS**: コード重複排除・シンプル設計

### 状態管理戦略
- **グローバル状態**: Zustand (認証、UI設定)
- **サーバー状態**: TanStack Query (APIデータ、キャッシュ)
- **ローカル状態**: React State (コンポーネント固有)

### コンポーネント設計
- **UI Components** (`components/ui/`): CVAによるバリアント、forwardRef、型安全なProps
- **Feature Components** (`features/*/components/`): ビジネスロジック統合
- **Layout Components** (`components/layout/`): ページ構造

## 技術スタック

### Frontend (apps/frontend/)
- Next.js 15 (App Router)
- React 19 (Hooks, Suspense)
- TypeScript (厳密な型安全性)
- Tailwind CSS + CVA (スタイリング)
- Zustand (グローバル状態)
- TanStack Query (サーバー状態)
- React Hook Form + Zod (フォーム・バリデーション)

### 品質管理ツール
- ESLint + Prettier (コード品質)
- Vitest (ユニット・統合テスト)
- Playwright (E2Eテスト)
- Storybook (コンポーネント開発)

## 重要な規約

### 命名規則
- **ファイル・フォルダ**: kebab-case (`user-profile/`, `use-local-storage.ts`)
- **コンポーネント**: PascalCase (`UserProfile.tsx`)
- **変数・関数**: camelCase (`userName`, `handleSubmit`)
- **定数**: UPPER_SNAKE_CASE (`API_ENDPOINTS`)

### コンポーネント作成時のチェック
- [ ] 単一責任の原則を満たしているか
- [ ] Props インターフェースが明確で最小限か
- [ ] forwardRef を適切に使用しているか
- [ ] アクセシビリティ要件を満たしているか
- [ ] 適切なJSDocコメントがあるか

### 型安全性
- `any` の使用を避ける
- 厳密な型定義 (interfaces, types)
- API レスポンスの型定義 (`src/types/api.ts`)
- Zod スキーマでのランタイムバリデーション

## 開発コマンド

### よく使用するコマンド
```bash
# 開発サーバー起動
cd apps/frontend && pnpm dev

# コード品質チェック
pnpm lint && pnpm format

# テスト実行
pnpm test
pnpm test:e2e

# コード生成
pnpm generate component Button ui
pnpm generate feature user-management
```

## 現在の状況

### 完成済み
- ✅ プロジェクト構造とモノレポ設定
- ✅ ESLint/Prettier/TypeScript設定
- ✅ 基本UIコンポーネント (Button, Label, Spinner)
- ✅ 状態管理設定 (Zustand, TanStack Query)
- ✅ 認証・認可システム設計
- ✅ Claude Code Agent設定

### 開発中・次のタスク
- 🔄 ユーザー管理機能の実装
- 🔄 トレーニングセッション機能
- 🔄 ダッシュボード画面
- 🔄 レスポンシブデザイン対応

## トラブルシューティング

### よくある問題
- **ESLintエラー**: `pnpm lint:fix` で自動修正
- **型エラー**: 厳密な型定義の確認、`src/types/api.ts` の活用
- **ビルドエラー**: `.next` フォルダ削除後再ビルド
- **依存関係エラー**: `pnpm install` で再インストール

### パフォーマンス最適化
- React.memo は重いコンポーネントにのみ使用
- useMemo/useCallback は適切な依存配列で
- 不要な再レンダリングをReact DevToolsで確認

## Agent活用ガイド

### @frontend-developer
新機能開発、リファクタリング、技術的実装に使用

### @frontend-code-reviewer  
コード品質チェック、SOLID原則確認、パフォーマンス最適化に使用

## 重要なファイル・ディレクトリ

```
apps/frontend/
├── docs/                     # プロジェクトドキュメント
├── src/
│   ├── features/            # ビジネス機能モジュール
│   ├── components/ui/       # 再利用可能UIコンポーネント
│   ├── lib/                # 共通ライブラリ・設定
│   ├── stores/             # Zustand状態管理
│   ├── types/              # 型定義
│   └── utils/              # ユーティリティ関数
├── package.json
├── tsconfig.json
├── next.config.js
└── tailwind.config.ts
```

このメモリ情報により、Claude は常にプロジェクトのコンテキスト、設計原則、技術選択を理解して開発支援を行います。