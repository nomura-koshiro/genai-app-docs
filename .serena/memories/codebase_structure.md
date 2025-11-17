# Training Tracker - コードベース構造

## 全体構造
```
training-tracker/
├── apps/                    # アプリケーション層
│   ├── frontend/           # Next.js フロントエンド
│   └── backend/            # FastAPI バックエンド
├── packages/               # 共有パッケージ
│   └── infrastructure/    # AWS CDK インフラ
├── docs/                   # プロジェクト設計書類
├── .claude/                # Claude Code 設定
│   ├── agents/            # カスタムエージェント
│   ├── commands/          # コマンド定義
│   │   ├── backend/       # バックエンド専用
│   │   ├── frontend/      # フロントエンド専用
│   │   └── shared/        # 共通コマンド
│   └── docs/              # プロジェクト文書
└── pnpm-workspace.yaml    # pnpm ワークスペース設定
```

## フロントエンド構造 (apps/frontend/src)
```
src/
├── app/                    # App Router (Next.js 13+)
│   ├── layout.tsx         # ルートレイアウト
│   └── page.tsx           # ホームページ
├── components/            # UI コンポーネント
│   ├── ui/               # 汎用UIコンポーネント
│   ├── layout/           # レイアウト関連
│   └── form/             # フォーム関連
├── features/             # 機能別モジュール（bulletproof-react）
│   └── [feature-name]/   # 各機能モジュール
│       ├── api/          # API関連
│       ├── components/   # 機能固有コンポーネント
│       ├── hooks/        # カスタムフック
│       ├── types/        # 型定義
│       └── index.ts      # エクスポート
├── lib/                  # ユーティリティライブラリ
│   ├── api-client.ts     # API クライント設定
│   ├── auth.tsx          # 認証関連
│   └── react-query.tsx   # TanStack Query設定
├── stores/               # 状態管理（Zustand）
├── hooks/                # 共通カスタムフック
├── types/                # 型定義
├── utils/                # ユーティリティ関数
├── providers/            # コンテキストプロバイダー
└── config/               # 設定ファイル
```

## バックエンド構造 (apps/backend/app)
```
app/
├── main.py              # FastAPI アプリケーションエントリーポイント
├── api/                 # API層
│   ├── health.py        # ヘルスチェック
│   ├── users.py         # ユーザー関連
│   └── training.py      # トレーニング関連
├── core/                # コア設定
│   └── config.py        # 環境設定
├── models/              # SQLAlchemy モデル
├── schemas/             # Pydantic スキーマ
│   ├── user.py         # ユーザースキーマ
│   └── training.py     # トレーニングスキーマ
├── services/           # ビジネスロジック層
└── db/                 # データベース関連
```

## 設計パターン

### フロントエンド
- **アーキテクチャ**: Bulletproof React (features-based)
- **状態管理**: TanStack Query + Zustand
- **スタイリング**: Tailwind CSS + CVA
- **フォーム**: React Hook Form + Zod

### バックエンド
- **アーキテクチャ**: 層分離アーキテクチャ
- **API**: FastAPI + Pydantic
- **データベース**: SQLAlchemy + Alembic
- **認証**: JWT + OAuth2

## 依存関係の方向性

### フロントエンド
```
App Router -> Features -> Components -> UI Components
Features -> API/Hooks -> Lib -> Utils
```

### バックエンド
```
API -> Services -> Models -> Database
API -> Schemas (Pydantic)
```

## ファイル命名規則
- **フロントエンド**: kebab-case (user-profile.tsx)
- **バックエンド**: snake_case (user_profile.py)
- **型定義**: PascalCase (UserProfile)
- **インターフェース**: PascalCase + Interface suffix
