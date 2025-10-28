# Issue Management Commands

GitHub Issue作業を効率的に管理するためのコマンド群です。

## 🎯 推奨ワークフロー

### 基本的な作業管理
```bash
/issue start 123          # 作業環境作成（worktree）
/issue list               # 作業状況確認
/issue finish 123         # 作業完了・コミット・プッシュ
/issue clean 123          # 環境クリーンアップ
```

### 本格的な開発作業
```bash
/issue-dev 123            # 自動判定で開発開始（推奨）
/issue-dev 123 frontend   # フロントエンド開発
/issue-dev 123 backend    # バックエンド開発
/issue-dev 123 fullstack  # フルスタック開発
```

## 📋 コマンド詳細

### 基本コマンド（軽量な作業管理）

| コマンド | 説明 | 例 |
|---------|------|-----|
| `/issue start` | Worktree作成・ブランチ作成・環境準備 | `/issue start 123` |
| `/issue list` | アクティブな作業環境一覧表示 | `/issue list` |
| `/issue finish` | 品質チェック・コミット・プッシュ | `/issue finish 123` |
| `/issue clean` | 作業環境の完全削除 | `/issue clean 123` |

### 開発コマンド（本格的な開発支援）

| コマンド | 説明 | 特徴 |
|---------|------|------|
| `/issue-dev` | 統合開発コマンド | 自動判定・品質チェック・最適化 |

#### 開発タイプ

- **`auto`** (デフォルト): Issueラベル・内容から自動判定
- **`frontend`**: React/Next.js フロントエンド開発
- **`backend`**: FastAPI/Python バックエンド開発  
- **`fullstack`**: フロントエンド・バックエンド統合開発

#### アクション

- **`develop`** (デフォルト): メイン開発作業
- **`start`**: 開発環境準備のみ
- **`finish`**: 開発完了・品質確認

## 🚀 自動判定機能

`/issue-dev 123` で自動判定される開発タイプ：

### Frontend判定条件
- ラベル: `frontend`, `ui`, `component`, `styling`
- 内容: React, UI, コンポーネント関連

### Backend判定条件  
- ラベル: `backend`, `api`, `database`, `server`
- 内容: API, データベース, サーバー関連

### Fullstack判定条件
- ラベル: `fullstack`, `feature`, `integration`
- 内容: 両方の要素が必要

## 🔧 高度な機能

### 品質ゲート
- TypeScript型チェック
- ESLint/Prettier
- テストカバレッジ確認
- パフォーマンス監視

### 自動最適化
- バンドルサイズ最適化
- データベースクエリ最適化
- キャッシュ戦略適用

### 継続作業対応
既存のworktreeがある場合、自動的に継続作業として認識

## 📊 ポート自動割り当て

Issue番号に基づく専用ポート設定：

- **Frontend**: 3000 + (issue_number % 100)
- **Backend**: 8000 + (issue_number % 100)  
- **Storybook**: 6000 + (issue_number % 100)

例: Issue #123
- Frontend: http://localhost:3023
- Backend: http://localhost:8023
- Storybook: http://localhost:6023

## 🎯 使用例

### 典型的なワークフロー
```bash
# 1. 自動判定で開発開始
/issue-dev 123

# 2. 開発作業実施（自動で品質チェック付き）
# - フロントエンド: React/Next.js開発
# - バックエンド: FastAPI/Python開発
# - テスト実装・実行
# - パフォーマンス最適化

# 3. 作業完了・PR準備
/issue-dev 123 --action=finish

# 4. 環境クリーンアップ
/issue clean 123
```

### 明示的なタイプ指定
```bash
# フロントエンド特化
/issue-dev 456 frontend

# バックエンド特化  
/issue-dev 789 backend

# フルスタック統合
/issue-dev 101 fullstack
```

## 🔄 移行ガイド

### 旧コマンドからの移行

| 旧コマンド | 新コマンド | 備考 |
|-----------|-----------|------|
| `/issue-frontend 123` | `/issue-dev 123 frontend` | 統合済み |
| `/issue-backend 123` | `/issue-dev 123 backend` | 統合済み |
| `/issue-fullstack 123` | `/issue-dev 123 fullstack` | 統合済み |

### 自動判定の活用

旧コマンドの代わりに自動判定を使用（推奨）：
```bash
# 推奨: 自動判定
/issue-dev 123

# 必要に応じて明示的指定
/issue-dev 123 frontend
```

## 📁 ファイル構成

```
.claude/commands/issue/
├── issue.md              # 基本作業管理
├── issue-dev.md          # 開発作業統合
├── issue-start.md        # 個別: 作業開始
├── issue-list.md         # 個別: 一覧表示
├── issue-finish.md       # 個別: 作業完了
├── issue-clean.md        # 個別: クリーンアップ
├── CONSOLIDATION_PLAN.md # 統合計画書
└── README.md             # このファイル
```

## ⚡ パフォーマンス最適化

統合コマンドにより以下が自動実行：

### フロントエンド
- コンポーネント最適化
- バンドル分析・最適化
- 画像最適化
- キャッシュ戦略

### バックエンド
- クエリ最適化
- インデックス分析
- レスポンス時間監視
- メモリ使用量最適化

統合により、Issue作業の効率性と品質が大幅に向上しました。