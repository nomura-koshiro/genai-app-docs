#!/bin/bash
# Claude Code カスタムコマンド: Issue作業完了
# @description Issue作業完了 - コード品質チェック、コミット、プッシュ
# @arg issue_number required "Issue番号" number
# @arg commit_message optional "コミットメッセージ" string

set -e

# 引数チェック
if [ $# -lt 1 ]; then
    echo "Usage: $0 <issue_number> [commit_message]"
    echo "Example: $0 123"
    echo "Example: $0 123 'Add user authentication feature'"
    exit 1
fi

# プロジェクトルートに移動
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
cd "$PROJECT_ROOT"

ISSUE_NUMBER=$1
COMMIT_MESSAGE=${2:-"Fix issue #${ISSUE_NUMBER}"}
WORKTREE_DIR="../training-tracker-issue-${ISSUE_NUMBER}"
BRANCH_NAME="training-tracker-issue-${ISSUE_NUMBER}"

echo "🏁 Issue #${ISSUE_NUMBER} の作業を完了します..."

# worktreeディレクトリが存在するかチェック
if [ ! -d "${WORKTREE_DIR}" ]; then
    echo "❌ 作業ディレクトリが見つかりません: ${WORKTREE_DIR}"
    echo "先に /issue-start ${ISSUE_NUMBER} を実行してください"
    exit 1
fi

# 作業ディレクトリに移動
cd "${WORKTREE_DIR}"

# 現在のブランチを確認
current_branch=$(git branch --show-current)
if [ "${current_branch}" != "${BRANCH_NAME}" ]; then
    echo "⚠️  想定外のブランチにいます: ${current_branch}"
    echo "期待されるブランチ: ${BRANCH_NAME}"
    read -p "続行しますか？ (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "❌ 作業を中止しました"
        exit 1
    fi
fi

# 変更があるかチェック
if git diff --quiet && git diff --cached --quiet; then
    echo "📝 変更がありません。そのまま完了処理を続行します。"
else
    echo "📝 変更を確認中..."
    git status
    echo ""
    
    # コード品質チェック
    echo "🔍 コード品質をチェック中..."
    
    # フロントエンドのlintとformat
    if [ -d "apps/frontend" ]; then
        echo "  - フロントエンドのlint/formatをチェック..."
        cd apps/frontend
        pnpm lint 2>/dev/null || echo "    ⚠️ lint警告があります"
        pnpm format 2>/dev/null || echo "    ⚠️ format警告があります"
        cd ../..
    fi
    
    # TypeScriptの型チェック
    if [ -f "apps/frontend/tsconfig.json" ]; then
        echo "  - TypeScriptの型チェック..."
        cd apps/frontend
        npx tsc --noEmit 2>/dev/null || echo "    ⚠️ 型エラーがあります"
        cd ../..
    fi
    
    echo ""
    
    # コミット確認
    read -p "変更をコミットしますか？ (Y/n): " confirm
    if [[ ! $confirm =~ ^[Nn]$ ]]; then
        # ステージング
        git add .
        
        # コミット
        echo "💾 変更をコミット中..."
        git commit -m "${COMMIT_MESSAGE}"
        
        # リモートにプッシュ
        read -p "リモートにプッシュしますか？ (Y/n): " push_confirm
        if [[ ! $push_confirm =~ ^[Nn]$ ]]; then
            echo "🚀 リモートにプッシュ中..."
            git push origin "${current_branch}" --set-upstream
        fi
    fi
fi

# mainディレクトリに戻る
cd ..

# Pull Requestの作成確認
echo ""
echo "✅ Issue #${ISSUE_NUMBER} の作業が完了しました！"
echo ""
echo "📂 作業ディレクトリ: ${WORKTREE_DIR}"
echo "🌿 ブランチ: ${current_branch}"
echo ""
echo "次のステップ："
echo "1. Pull Requestを作成"
echo "   GitHub Web UIで ${current_branch} → main のPRを作成してください"
echo ""
echo "2. レビュー完了後、以下のコマンドでクリーンアップ："
echo "   /issue-clean ${ISSUE_NUMBER}"
echo ""
echo "3. 他のissueで作業を継続する場合："
echo "   /issue-start <new_issue_number>"
echo ""