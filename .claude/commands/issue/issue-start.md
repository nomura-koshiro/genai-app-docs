---
command: issue-start
description: GitHub Issue作業開始 - worktreeで独立した作業環境を作成
args:
  issue_number:
    required: true
    type: number
    description: Issue番号
  branch_name:
    required: false
    type: string
    description: カスタムブランチ名（デフォルト: training-tracker-issue-{issue_number}）
---

GitHub Issue #{issue_number} の作業を開始し、独立したworktree環境を作成します。

## 実行内容

1. **最新コードの取得**
   - mainブランチを最新に更新

2. **独立した作業環境の作成**
   - worktreeで専用ディレクトリを作成: `../training-tracker-issue-{issue_number}`
   - 新しいブランチを作成: `{branch_name}` または `training-tracker-issue-{issue_number}`

3. **専用ポート設定**
   - Frontend: 3000 + (issue_number % 100)
   - Backend: 8000 + (issue_number % 100)
   - Storybook: 6000 + (issue_number % 100)

4. **開発環境の準備**
   - 依存関係のインストール（pnpm install）
   - Python環境のセットアップ（uv sync）
   - 専用.env.localファイルの作成
   - 開発サーバーの自動起動（フロントエンド + バックエンド）

## 使用例

```bash
# Issue #123の作業を開始
/issue-start 123

# カスタムブランチ名で作業開始
/issue-start 123 feature/new-auth-system
```

## 次のステップ

作業開始後は以下のようになります：

- **自動的にworktreeディレクトリに移動**
- **開発サーバーが自動起動**：
  - Frontend: http://localhost:300X (Xはissue番号の下2桁)
  - Backend: http://localhost:800X (uvicorn + uv環境で起動)
- **VS Codeで新しいワークスペースが開く**

手動で開発サーバーを起動したい場合：

```bash
cd ../training-tracker-issue-123
./dev-issue.sh
```

## 関連コマンド

- `/issue-list` - アクティブなissue作業の一覧表示
- `/issue-finish` - 作業完了とコミット
- `/issue-clean` - 作業環境のクリーンアップ

## 技術的な改善点

### Python環境の自動セットアップ
- `uv`コマンドが利用可能な場合、自動的に`uv sync`を実行
- uvicornは`uv run`経由で起動し、依存関係の問題を解決
- 従来のvenvベースの環境にもフォールバック対応

### 自動化された作業フロー
- worktree作成後、自動的に作業ディレクトリに移動
- 開発サーバーの起動状況を明確に表示
- エラーハンドリングとクリーンアップ機能

## スクリプト実行

```bash
bash .claude/commands/scripts/issue-start.sh {issue_number} {branch_name}
```
