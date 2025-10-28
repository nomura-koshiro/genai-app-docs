---
command: issue-finish
description: GitHub Issue作業完了 - コード品質チェック、コミット、プッシュ
args:
  issue_number:
    required: true
    type: number
    description: Issue番号
  commit_message:
    required: false
    type: string
    description: コミットメッセージ（デフォルト: "Fix issue #{issue_number}"）
---

GitHub Issue #{issue_number} の作業を完了し、品質チェック後にコミット・プッシュします。

## 実行内容

1. **作業ディレクトリの確認**
   - worktreeディレクトリの存在確認
   - 正しいブランチにいることを確認

2. **コード品質チェック**
   - ESLintによるコード検証
   - Prettierによるフォーマット確認
   - TypeScriptの型チェック

3. **変更のコミット**
   - 変更内容の確認表示
   - ステージングとコミット
   - コミットメッセージの適用

4. **リモートへのプッシュ**
   - originへのプッシュ（確認付き）
   - upstreamブランチの設定

## 使用例

```bash
# Issue #123の作業を完了（デフォルトメッセージ）
/issue-finish 123

# カスタムメッセージで完了
/issue-finish 123 "Add user authentication feature with OAuth support"
```

## 品質チェック項目

- ✅ ESLintエラー・警告のチェック
- ✅ Prettierフォーマット違反のチェック
- ✅ TypeScript型エラーのチェック
- ⚠️ 問題があっても続行可能（警告表示）

## 完了後の次のステップ

1. **Pull Requestの作成**
   - GitHub Web UIでPRを作成
   - `training-tracker-issue-{issue_number}` → `main`

2. **作業環境のクリーンアップ**
   ```bash
   /issue-clean 123
   ```

3. **新しいissueで作業継続**
   ```bash
   /issue-start 456
   ```

## 関連コマンド

- `/issue-start` - issue作業を開始
- `/issue-list` - アクティブなissue一覧
- `/issue-clean` - 作業環境のクリーンアップ

## スクリプト実行

```bash
bash .claude/commands/scripts/issue-finish.sh {issue_number} "{commit_message}"
```