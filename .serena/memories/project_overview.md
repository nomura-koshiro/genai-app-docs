# Training Tracker - プロジェクト概要

## プロジェクト目的
トレーニングの記録、管理、可視化を効率的に行えるWebアプリケーション（MVP）

## 技術スタック

### フロントエンド
- **フレームワーク**: Next.js 15.5.2
- **言語**: TypeScript 5.5+
- **スタイリング**: Tailwind CSS + CVA (Class Variance Authority)
- **状態管理**:
  - TanStack Query (サーバー状態)
  - Zustand (ローカル状態)
- **フォーム**: React Hook Form + Zod バリデーション
- **テスト**: Vitest + Testing Library + Playwright
- **開発支援**: Storybook, ESLint, Prettier

### バックエンド
- **フレームワーク**: FastAPI
- **言語**: Python 3.11+
- **データベース**: PostgreSQL (SQLAlchemy + Alembic)
- **認証**: python-jose + passlib
- **テスト**: pytest + pytest-asyncio
- **コード品質**: black, ruff, mypy

### インフラ
- **クラウド**: AWS
- **IaC**: AWS CDK
- **コンテナ**: Docker
- **パッケージ管理**: pnpm (Frontend), uv (Backend)

## プロジェクト構成
```
training-tracker/
├── apps/
│   ├── frontend/      # Next.js フロントエンド
│   └── backend/       # FastAPI バックエンド
├── packages/
│   └── infrastructure/ # AWS CDK インフラ
├── docs/              # プロジェクト設計書類
└── .claude/           # Claude Code 設定
```

## 開発環境セットアップ
```bash
# 依存関係のインストール
pnpm install
cd apps/backend && uv sync

# 開発サーバー起動
pnpm dev  # 全サービス
```

## 主要コマンド
- `pnpm dev` - 開発サーバー起動
- `pnpm build` - ビルド実行
- `pnpm test` - テスト実行
- `pnpm lint` - リント実行
- `pnpm format` - フォーマット実行

## アーキテクチャパターン
- **フロントエンド**: Bulletproof React features-based architecture
- **バックエンド**: FastAPI標準的な層分離アーキテクチャ
