---
command: issue-dev
description: GitHub Issue開発作業の統合コマンド - フロントエンド・バックエンド・フルスタック対応
args:
  issue_number:
    required: true
    type: number
    description: Issue番号
  type:
    required: false
    type: string
    choices: [frontend, backend, fullstack, auto]
    default: auto
    description: 開発タイプ（autoは自動判定）
  action:
    required: false
    type: string
    choices: [start, develop, finish]
    default: develop
    description: 実行アクション
---

GitHub Issue #{issue_number} の開発作業を効率的に進める統合コマンドです。

## 自動判定機能

`type: auto`（デフォルト）の場合、Issueのラベル・内容から開発タイプを自動判定：

- **frontend**: `label:frontend`, `label:ui`, `label:component` など
- **backend**: `label:backend`, `label:api`, `label:database` など
- **fullstack**: `label:fullstack`, `label:feature` または両方が必要な場合

## アクション詳細

### 🚀 Start (`/issue-dev 123 --action=start`)

Issue作業環境の準備と開始

**共通処理**:

- Worktree作成・ブランチ作成
- 依存関係インストール
- 環境設定

**開発タイプ別処理**:

- **Frontend**: React開発環境準備、Storybook設定
- **Backend**: FastAPI環境準備、DB接続確認
- **Fullstack**: 両方の環境準備、API連携確認

### 💻 Develop (`/issue-dev 123` または `/issue-dev 123 frontend`)

メイン開発作業（デフォルトアクション）

#### Frontend開発 (`/issue-dev 123 frontend`)

@frontend-issue-developer

**実行フロー**:

1. **Issue分析・要件理解**

   ```bash
   gh issue view {issue_number} --json title,body,labels,assignees
   ```

2. **技術調査・影響範囲確認**
   - 既存コンポーネント・features調査
   - API連携要件の確認
   - 状態管理への影響分析

3. **Features-based実装**

   ```text
   src/features/{feature-name}/
   ├── api/           # TanStack Query hooks
   ├── components/    # React components
   ├── hooks/         # Custom hooks
   ├── types/         # TypeScript types
   └── index.ts       # Exports
   ```

4. **品質保証**
   - Unit tests (Vitest)
   - E2E tests (Playwright)
   - Accessibility checks
   - Performance optimization

#### Backend開発 (`/issue-dev 123 backend`)

@backend-issue-developer

**実行フロー**:

1. **Issue分析・API設計**
   - データモデル設計
   - エンドポイント仕様策定
   - セキュリティ要件確認

2. **Clean Architecture実装**

   ```text
   app/features/{feature}/
   ├── models.py      # SQLAlchemy models
   ├── schemas.py     # Pydantic schemas
   ├── repositories.py # Data access
   ├── services.py    # Business logic
   └── routes.py      # API endpoints
   ```

3. **データベース設計**
   - Migration作成
   - Index最適化
   - 制約・リレーション設定

4. **テスト・セキュリティ**
   - Unit tests (pytest)
   - Integration tests
   - Security validation
   - Performance optimization

#### フルスタック開発 (`/issue-dev 123 fullstack`)

@frontend-issue-developer @backend-issue-developer

**統合開発フロー**:

1. **要件分析・アーキテクチャ設計**
   - エンドツーエンド要件分析
   - API仕様策定
   - データフロー設計

2. **並行開発戦略**
   - Backend API先行開発
   - Frontend Mock開発
   - 段階的統合

3. **統合テスト**
   - API統合テスト
   - E2Eワークフローテスト
   - パフォーマンス最適化

### ✅ Finish (`/issue-dev 123 --action=finish`)

開発完了・品質確認・コミット

**共通処理**:

1. **品質チェック**

   ```bash
   # Frontend
   pnpm lint && pnpm type-check && pnpm test && pnpm build

   # Backend
   ruff check . && mypy . && pytest --cov=app
   ```

2. **統合確認**
   - E2Eテスト実行
   - パフォーマンス確認
   - セキュリティチェック

3. **コミット・PR準備**
   - 適切なコミットメッセージ生成
   - PR テンプレート作成
   - レビュー準備

## 使用例

```bash
# 基本使用（自動判定）
/issue-dev 123

# 明示的にフロントエンド開発
/issue-dev 123 frontend

# バックエンド開発
/issue-dev 123 backend

# フルスタック開発
/issue-dev 123 fullstack

# 作業開始のみ
/issue-dev 123 --action=start

# 作業完了処理
/issue-dev 123 --action=finish
```

## 高度な機能

### 🔄 継続作業モード

既存のworktreeがある場合、継続作業として開始

### 🎯 自動品質チェック

- TypeScript型チェック
- ESLint/Prettier
- テストカバレッジ
- パフォーマンス監視

### 📊 進捗追跡

- 開発フェーズ表示
- 完了チェックリスト
- 品質メトリクス

### 🚀 自動最適化

- バンドルサイズ最適化
- データベースクエリ最適化
- キャッシュ戦略適用

## 連携コマンド

- `/issue start` - 基本的なworktree作成
- `/issue list` - 作業状況確認
- `/issue finish` - 基本的な作業完了
- `/issue clean` - 環境クリーンアップ

## 設定

### 自動判定ルール設定

```json
// .claude/config/issue-dev.json
{
  "auto_detection": {
    "frontend_labels": ["frontend", "ui", "component", "styling"],
    "backend_labels": ["backend", "api", "database", "server"],
    "fullstack_labels": ["fullstack", "feature", "integration"]
  },
  "quality_gates": {
    "test_coverage": 80,
    "performance_budget": 100,
    "bundle_size_limit": 500
  }
}
```

このコマンドにより、Issue開発作業を効率的かつ高品質で進められます。
