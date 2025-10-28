---
command: issue
description: GitHub Issue作業管理の統合コマンド - start/list/finish/cleanを一元管理
args:
  action:
    required: true
    type: string
    choices: [start, list, finish, clean]
    description: 実行するアクション
  issue_number:
    required: false
    type: number
    description: Issue番号（list以外で必須）
  option:
    required: false
    type: string
    description: ブランチ名（start）またはコミットメッセージ（finish）
---

GitHub Issue作業を効率的に管理するための統合コマンドです。

## アクション一覧

### 📋 `/issue start {issue_number} [branch_name]`
新しいissue作業を開始し、独立したworktree環境を作成

### 🔍 `/issue list`
アクティブなissue作業環境の一覧を表示

### ✅ `/issue finish {issue_number} [commit_message]`
作業を完了し、品質チェック後にコミット・プッシュ

### 🧹 `/issue clean {issue_number}`
作業環境を完全にクリーンアップ

## 使用例

```bash
# Issue #123の作業を開始
/issue start 123

# カスタムブランチ名で開始
/issue start 123 feature/new-auth

# 作業状況を確認
/issue list

# 作業を完了してコミット
/issue finish 123 "Add authentication feature"

# 作業環境をクリーンアップ
/issue clean 123
```

## ワークフロー例

```bash
# 1. Issue作業を開始
/issue start 456

# 2. 開発作業を実施
cd ../training-tracker-issue-456
./dev-issue.sh  # 開発サーバー起動

# 3. 作業状況を確認
/issue list

# 4. 作業を完了
/issue finish 456 "Implement user profile page"

# 5. PR作成後、環境をクリーンアップ
/issue clean 456

# 6. 次のissueへ
/issue start 789
```

## 特徴

### 🚀 独立した作業環境
- Issue毎に独立したworktreeディレクトリ
- 専用ポート設定で複数issue同時作業可能
- 他のissue作業に影響を与えない

### 🔒 安全な作業管理
- 未コミット変更の警告
- 削除前の確認プロンプト
- Windows環境対応の特別処理

### 📊 ポート自動割り当て
- Frontend: 3000 + (issue_number % 100)
- Backend: 8000 + (issue_number % 100)
- Storybook: 6000 + (issue_number % 100)

## 個別コマンドへのアクセス

統合コマンドの代わりに、個別コマンドも使用可能：
- `/issue-start` - 作業開始
- `/issue-list` - 一覧表示
- `/issue-finish` - 作業完了
- `/issue-clean` - クリーンアップ

## スクリプト実行

内部的には以下のスクリプトを実行：

```bash
# start
bash .claude/commands/scripts/issue-start.sh {issue_number} {branch_name}

# list
bash .claude/commands/scripts/issue-list.sh

# finish
bash .claude/commands/scripts/issue-finish.sh {issue_number} "{commit_message}"

# clean
bash .claude/commands/scripts/issue-clean.sh {issue_number}
```