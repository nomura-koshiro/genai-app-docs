# Training Tracker - Pages & Components Architecture

## 📁 Feature-based Architecture Structure

Based on bulletproof-react principles and TypeScript types defined:

```
src/
├── features/
│   ├── auth/           # 認証機能
│   ├── dashboard/      # ダッシュボード
│   ├── training/       # トレーニング記録
│   ├── menu/          # メニュー管理
│   ├── history/       # 履歴閲覧
│   ├── stats/         # 統計・分析
│   └── settings/      # 設定
├── components/        # 共通UIコンポーネント
├── types/            # 型定義（既に作成済み）
├── hooks/            # 共通フック
├── utils/            # ユーティリティ
└── stores/           # Zustand状態管理
```

## 🎯 MVPコンポーネント優先度

### Phase 1 (最優先 - 基本機能)
- 認証システム
- ダッシュボード
- 基本的なトレーニング記録
- 共通UIコンポーネント

### Phase 2 (中優先 - 核心機能)
- メニュー管理
- 履歴表示
- 基本統計

### Phase 3 (低優先 - 拡張機能)
- 高度な統計・グラフ
- 外部連携
- エクスポート機能

## 🔧 使用技術スタック
- Next.js 15 (App Router)
- TypeScript (strict mode)
- Tailwind CSS + CVA
- Zustand + TanStack Query
- React Hook Form + Zod
- shadcn/ui components
