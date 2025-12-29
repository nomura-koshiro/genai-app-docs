---
command: issue-list
description: GitHub Issue作業状況一覧 - アクティブなworktreeとブランチの表示
---

現在アクティブなGitHub Issue作業環境の一覧を表示します。

## 表示内容

- **現在のブランチ**: 現在チェックアウトしているブランチ
- **アクティブなworktree**: 作業中のissue環境とそのポート設定
- **Issue関連ブランチ**: issueブランチの一覧
- **利用可能なコマンド**: issue関連コマンドのヘルプ

## 出力例

```text
🔍 Training Tracker - Issue作業状況一覧
========================================

📍 現在のブランチ: main

🌿 アクティブなworktree:
  📂 Main: /c/developments/training-tracker (main)
     🌐 Default ports: Frontend:3000, Backend:8000, Storybook:6006
  🔧 Issue #123: ../training-tracker-issue-123 (training-tracker-issue-123)
     🌐 Ports: Frontend:3023, Backend:8023, Storybook:6023
  🔧 Issue #456: ../training-tracker-issue-456 (training-tracker-issue-456)
     🌐 Ports: Frontend:3056, Backend:8056, Storybook:6056

🌲 Issue関連ブランチ:
  📋 training-tracker-issue-123 (Issue #123)
  ✅ training-tracker-issue-456 (Issue #456) - 現在のブランチ
  📋 training-tracker-issue-789 (Issue #789)
```

## 使用例

```bash
# Issue作業状況を確認
/issue-list
```

## 関連コマンド

- `/issue-start` - 新しいissue作業を開始
- `/issue-finish` - 作業完了とコミット
- `/issue-clean` - 作業環境のクリーンアップ

## スクリプト実行

```bash
bash .claude/commands/scripts/issue-list.sh
```
