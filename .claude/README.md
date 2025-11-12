# Claude Code Project Configuration

Training Tracker プロジェクトの Claude Code 設定とエージェント構成

## 📁 ディレクトリ構成

```
.claude/
├── agents/                    # 専門エージェント
│   ├── frontend-developer.md      # フロントエンド開発専門
│   ├── frontend-code-reviewer.md  # フロントエンドコードレビュー
│   ├── backend-developer.md       # バックエンド開発専門
│   └── backend-code-reviewer.md   # バックエンドコードレビュー
├── commands/                 # カスタムコマンド
│   ├── backend/                   # バックエンド専用コマンド
│   │   ├── api.md                    # API エンドポイント作成
│   │   ├── fix-backend.md            # バックエンド修正
│   │   ├── model.md                  # モデル作成
│   │   ├── review-backend.md         # バックエンドレビュー
│   │   └── test-backend.md           # バックエンドテスト
│   ├── frontend/                  # フロントエンド専用コマンド
│   │   ├── component.md              # UI コンポーネント作成
│   │   └── feature.md                # 機能モジュール作成
│   └── shared/                    # 共通コマンド
│       ├── fix.md                    # 汎用修正
│       ├── optimize.md               # パフォーマンス最適化
│       ├── review.md                 # 汎用レビュー
│       ├── status.md                 # プロジェクト状況確認
│       └── test.md                   # 汎用テスト
├── docs/                     # プロジェクトドキュメント
│   └── CLAUDE.md                  # プロジェクト設定・メモリ
├── settings.local.json       # Claude Code 設定（メイン）
└── README.md                # このファイル
```

## 🤖 利用可能なエージェント

### フロントエンド開発

- **@frontend-developer**: Next.js、React、TypeScript の開発支援
  - Features-based アーキテクチャ
  - SOLID/DRY/KISS 原則
  - Zustand + TanStack Query 状態管理
  - CVA によるコンポーネント設計

- **@frontend-code-reviewer**: フロントエンドコード品質チェック
  - コード品質とパフォーマンス最適化
  - アクセシビリティとUX改善
  - TypeScript型安全性チェック

### バックエンド開発

- **@backend-developer**: FastAPI、Python の開発支援
  - Clean Architecture + Repository パターン
  - SOLID 原則の実装
  - セキュリティベストプラクティス
  - 非同期処理とデータベース最適化

- **@backend-code-reviewer**: バックエンドコード品質チェック
  - PEP8 準拠とセキュリティ監査
  - パフォーマンス問題の検出
  - SOLID 原則適用状況評価

## 📖 プロジェクト情報

詳細なプロジェクト情報は以下を参照：

- **プロジェクト設定**: `docs/CLAUDE.md`
- **技術スタック**: Next.js 15 + FastAPI + PostgreSQL
- **アーキテクチャ**: Features-based + Clean Architecture
- **開発原則**: SOLID/DRY/KISS + リーダブルコード

## 🛠️ カスタムコマンド

### バックエンドコマンド

- `@api` - FastAPI エンドポイント作成
- `@model` - SQLAlchemy モデル作成
- `@fix-backend` - バックエンド修正
- `@review-backend` - バックエンドレビュー
- `@test-backend` - バックエンドテスト

### フロントエンドコマンド

- `@component` - UI コンポーネント作成
- `@feature` - 機能モジュール作成

### 共通コマンド

- `@fix` - 汎用修正
- `@optimize` - パフォーマンス最適化
- `@review` - 汎用レビュー
- `@status` - プロジェクト状況確認
- `@test` - 汎用テスト

## 🚀 使用方法

### エージェント呼び出し

```
@frontend-developer ユーザー管理機能のコンポーネントを作成してください
@backend-code-reviewer この認証コードをレビューしてください
```

### コマンド使用

```
@component Button - 新しいButtonコンポーネントを作成
@api users - ユーザー管理API作成
@feature authentication - 認証機能モジュール作成
```

## ⚙️ 設定ファイル

- **settings.local.json**: メイン設定（権限、フック、環境設定）
- **hooks**: TypeScript ファイル編集時の自動フォーマット・リント
- **permissions**: セキュリティ設定
