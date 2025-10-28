#!/bin/bash
# Claude Code カスタムコマンド: Issue作業環境クリーンアップ
# @description Issue作業環境クリーンアップ - worktreeとブランチの削除
# @arg issue_number required "Issue番号" number

set -e

# 引数チェック
if [ $# -lt 1 ]; then
    echo "Usage: $0 <issue_number>"
    echo "Example: $0 123"
    exit 1
fi

# プロジェクトルートに移動
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
cd "$PROJECT_ROOT"

ISSUE_NUMBER=$1
WORKTREE_DIR="../training-tracker-issue-${ISSUE_NUMBER}"
BRANCH_NAME="training-tracker-issue-${ISSUE_NUMBER}"

echo "🧹 Issue #${ISSUE_NUMBER} の作業環境をクリーンアップします..."

# worktreeディレクトリの存在確認
if [ ! -d "${WORKTREE_DIR}" ]; then
    echo "ℹ️  作業ディレクトリが見つかりません: ${WORKTREE_DIR}"
    echo "既にクリーンアップ済みの可能性があります。"
else
    echo "📂 作業ディレクトリを確認中: ${WORKTREE_DIR}"
    
    # 未コミットの変更があるかチェック（worktreeが有効な場合のみ）
    if git worktree list | grep -q "${WORKTREE_DIR}"; then
        if ! git -C "${WORKTREE_DIR}" diff --quiet || ! git -C "${WORKTREE_DIR}" diff --cached --quiet; then
            echo "⚠️  未コミットの変更があります！"
            git -C "${WORKTREE_DIR}" status
            echo ""
            read -p "変更を破棄してクリーンアップを続行しますか？ (y/N): " confirm
            if [[ ! $confirm =~ ^[Yy]$ ]]; then
                echo "❌ クリーンアップを中止しました"
                echo "変更をコミットしてから再実行してください"
                exit 1
            fi
        fi
    else
        echo "⚠️  worktreeが既にGitから削除されています。ディレクトリのクリーンアップを続行します。"
    fi
    
    # worktreeを削除（存在する場合のみ）
    if git worktree list | grep -q "${WORKTREE_DIR}"; then
        echo "🗑️  worktreeを削除中..."
        git worktree remove "${WORKTREE_DIR}" --force 2>/dev/null || {
            echo "⚠️  worktree削除でエラーが発生しましたが続行します"
        }
    else
        echo "ℹ️  worktreeは既にGitから削除されています"
    fi
    
    # 物理ディレクトリが残っている場合は強制削除
    if [ -d "${WORKTREE_DIR}" ]; then
        echo "⚠️  ディレクトリが残っています。強制削除を実行中..."
        
        # Windows環境でnode_modules削除の問題に対処
        if [ -d "${WORKTREE_DIR}/node_modules" ]; then
            echo "    node_modules を削除中（時間がかかる場合があります）..."
            
            # MINGW/Git Bashの場合はWindowsのrmdir使用
            if [[ "$OSTYPE" == "msys" ]]; then
                cmd //c "rmdir /s /q $(cygpath -w "${WORKTREE_DIR}/node_modules")" 2>/dev/null || {
                    echo "    node_modules削除に失敗しましたが続行します"
                }
            else
                rm -rf "${WORKTREE_DIR}/node_modules" 2>/dev/null || {
                    echo "    node_modules削除に失敗しましたが続行します"
                }
            fi
        fi
        
        # 残りのファイルを削除（Windows/Unix対応）
        if [[ "$OSTYPE" == "msys" ]]; then
            # Windows環境ではrmdirを使用（より強力）
            echo "    残りのファイルを削除中（Windows rmdirを使用）..."
            cmd //c "rmdir /s /q $(cygpath -w "${WORKTREE_DIR}")" 2>/dev/null || {
                echo "    ⚠️  Windows rmdirでも削除できませんでした"
                echo "    手動で削除してください: ${WORKTREE_DIR}"
            }
        else
            # Unix/Linux環境では通常のrm -rf
            rm -rf "${WORKTREE_DIR}" 2>/dev/null || {
                echo "    ⚠️  一部のファイルが削除できませんでした"
                echo "    手動で削除してください: ${WORKTREE_DIR}"
            }
        fi
    fi
    
    if [ ! -d "${WORKTREE_DIR}" ]; then
        echo "✅ worktreeディレクトリを削除しました: ${WORKTREE_DIR}"
    else
        echo "⚠️  worktreeディレクトリの一部が残っています: ${WORKTREE_DIR}"
    fi
fi

# ローカルブランチの削除確認
if git show-ref --quiet refs/heads/${BRANCH_NAME}; then
    echo ""
    echo "🌿 ローカルブランチが残っています: ${BRANCH_NAME}"
    read -p "ローカルブランチを削除しますか？ (y/N): " branch_confirm
    if [[ $branch_confirm =~ ^[Yy]$ ]]; then
        git branch -D "${BRANCH_NAME}" 2>/dev/null || git branch -d "${BRANCH_NAME}"
        echo "✅ ローカルブランチを削除しました: ${BRANCH_NAME}"
    else
        echo "ℹ️  ローカルブランチは保持されます: ${BRANCH_NAME}"
    fi
fi

# リモートブランチの削除確認
if git ls-remote --exit-code --heads origin ${BRANCH_NAME} >/dev/null 2>&1; then
    echo ""
    echo "🌐 リモートブランチが存在します: origin/${BRANCH_NAME}"
    read -p "リモートブランチを削除しますか？ (通常はGitHub上でPRマージ時に自動削除) (y/N): " remote_confirm
    if [[ $remote_confirm =~ ^[Yy]$ ]]; then
        git push origin --delete "${BRANCH_NAME}"
        echo "✅ リモートブランチを削除しました: origin/${BRANCH_NAME}"
    else
        echo "ℹ️  リモートブランチは保持されます: origin/${BRANCH_NAME}"
    fi
fi

# mainブランチに戻る
echo ""
echo "🔄 mainブランチに戻ります..."
git checkout main 2>/dev/null || git checkout master 2>/dev/null
git pull origin main 2>/dev/null || git pull origin master 2>/dev/null

# worktreeリストをクリーンアップ
echo "🧹 worktreeリストをクリーンアップ中..."
git worktree prune

echo ""
echo "✅ Issue #${ISSUE_NUMBER} のクリーンアップが完了しました！"
echo ""
echo "現在の状態："
echo "📂 作業ディレクトリ: $(pwd)"
echo "🌿 現在のブランチ: $(git branch --show-current)"
echo ""
echo "新しいissueで作業を開始するには："
echo "  /issue-start <issue_number>"
echo ""

# worktreeの一覧表示
if [ "$(git worktree list | wc -l)" -gt 1 ]; then
    echo "アクティブなworktree："
    git worktree list
fi