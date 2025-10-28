---
command: issue-clean
description: GitHub Issue作業環境クリーンアップ - worktreeとブランチの削除
args:
  issue_number:
    required: true
    type: number
    description: Issue番号
---

GitHub Issue #{issue_number} の作業環境を完全にクリーンアップします。

## 実行内容

1. **未コミット変更の確認**
   - 変更がある場合は警告表示
   - 破棄確認（ユーザー確認付き）

2. **Worktreeの削除**
   - Git worktreeから削除
   - 物理ディレクトリの削除
   - node_modulesの特別処理（Windows対応）

3. **ブランチの削除**
   - ローカルブランチの削除（確認付き）
   - リモートブランチの削除（確認付き）

4. **環境のリセット**
   - mainブランチへのチェックアウト
   - 最新コードの取得
   - worktreeリストのクリーンアップ

## 使用例

```bash
# Issue #123の作業環境をクリーンアップ
/issue-clean 123
```

## Windows環境での特別処理

Windows環境では、以下の特別処理を実行：
- `node_modules`の強制削除（rmdirコマンド使用）
- ファイルロック対策
- 長いパス名の処理

## 確認プロンプト

以下の場合にユーザー確認を求めます：
- ⚠️ 未コミットの変更がある場合
- 🌿 ローカルブランチの削除
- 🌐 リモートブランチの削除

## クリーンアップ後の状態

- 作業ディレクトリ: メインプロジェクトディレクトリ
- 現在のブランチ: main（最新状態）
- worktree: 該当issueのworktreeは削除済み

## 関連コマンド

- `/issue-start` - 新しいissue作業を開始
- `/issue-list` - アクティブなissue一覧
- `/issue-finish` - 作業完了とコミット

## スクリプト実行

```bash
bash .claude/commands/scripts/issue-clean.sh {issue_number}
```