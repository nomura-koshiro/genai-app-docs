#!/bin/bash
# Claude Code カスタムコマンド: Issue作業状況一覧
# @description Issue作業状況一覧 - アクティブなworktreeとブランチの表示

set -e

# プロジェクトルートに移動
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
cd "$PROJECT_ROOT"

echo "🔍 Training Tracker - Issue作業状況一覧"
echo "========================================"
echo ""

# 現在のブランチ
current_branch=$(git branch --show-current)
echo "📍 現在のブランチ: ${current_branch}"
echo ""

# アクティブなworktreeの一覧
echo "🌿 アクティブなworktree:"
worktree_count=$(git worktree list | wc -l)
if [ "$worktree_count" -gt 1 ]; then
    git worktree list | while read line; do
        # worktree情報をパース
        path=$(echo "$line" | awk '{print $1}')
        commit=$(echo "$line" | awk '{print $2}')
        branch=$(echo "$line" | awk '{print $3}' | sed 's/\[//;s/\]//')
        
        if [[ "$path" == *"training-tracker-issue-"* ]]; then
            issue_num=$(basename "$path" | sed 's/training-tracker-issue-//')
            frontend_port=$((3000 + ${issue_num} % 100))
            backend_port=$((8000 + ${issue_num} % 100))
            storybook_port=$((6000 + ${issue_num} % 100))
            echo "  🔧 Issue #${issue_num}: ${path} (${branch})"
            echo "     🌐 Ports: Frontend:${frontend_port}, Backend:${backend_port}, Storybook:${storybook_port}"
        else
            echo "  📂 Main: ${path} (${branch})"
            echo "     🌐 Default ports: Frontend:3000, Backend:8000, Storybook:6006"
        fi
    done
else
    echo "  📂 Main worktreeのみ"
    echo "     🌐 Default ports: Frontend:3000, Backend:8000, Storybook:6006"
fi

echo ""

# Issue関連ブランチの一覧
echo "🌲 Issue関連ブランチ:"
issue_branches=$(git branch | grep "training-tracker-issue-" | sed 's/^[* ] //' || true)
if [ -n "$issue_branches" ]; then
    echo "$issue_branches" | while read branch; do
        if [[ "$branch" == training-tracker-issue-* ]]; then
            issue_num=$(echo "$branch" | sed 's/training-tracker-issue-//')
            if [ "$branch" = "$current_branch" ]; then
                echo "  ✅ ${branch} (Issue #${issue_num}) - 現在のブランチ"
            else
                echo "  📋 ${branch} (Issue #${issue_num})"
            fi
        fi
    done
else
    echo "  📝 Issue関連ブランチはありません"
fi

echo ""

# 利用可能なコマンド
echo "📋 利用可能なコマンド:"
echo "  /issue-start <issue_number> [branch_name] - Issue作業開始"
echo "  /issue-finish <issue_number> [message]    - Issue作業完了"
echo "  /issue-clean <issue_number>               - 作業環境クリーンアップ"
echo "  /issue-list                               - この一覧表示"
echo ""