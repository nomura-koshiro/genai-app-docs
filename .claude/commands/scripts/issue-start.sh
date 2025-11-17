#!/bin/bash
# Claude Code カスタムコマンド: Issue作業開始
# @description Issue作業開始 - worktreeで独立した作業環境を作成、または開発サーバー起動
# @arg issue_number required "Issue番号" number
# @arg branch_name optional "カスタムブランチ名" string

set -e

# エラーハンドリング関数
handle_error() {
    local line_no=$1
    local error_code=$2
    echo "❌ エラーが発生しました (行: $line_no, コード: $error_code)"
    echo "🔧 問題の詳細を確認してください"

    # クリーンアップが必要な場合
    if [ -n "$WORKTREE_DIR" ] && [ -d "$WORKTREE_DIR" ]; then
        echo "🧹 作業ディレクトリをクリーンアップしています..."
        cd "$PROJECT_ROOT" 2>/dev/null || true
        git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true
        rm -rf "$WORKTREE_DIR" 2>/dev/null || true
    fi

    exit $error_code
}

# エラートラップの設定
trap 'handle_error ${LINENO} $?' ERR

# dev-issue.shとして実行された場合は開発サーバー起動モード
if [[ "$(basename $0)" == "dev-issue.sh" ]]; then
    # .env.localから環境変数を読み込み
    if [ -f ".env.local" ]; then
        export $(grep -v '^#' .env.local | xargs)
    fi

    echo "🚀 Issue専用開発サーバーを起動します..."
    echo "Frontend: http://localhost:${FRONTEND_PORT}"
    echo "Backend:  http://localhost:${BACKEND_PORT}"
    echo "Storybook: http://localhost:${STORYBOOK_PORT}"
    echo ""

    # 並列でサービスを起動
    trap 'kill $(jobs -p)' EXIT

    # フロントエンド
    cd apps/frontend
    pnpm dev -p ${FRONTEND_PORT} &

    # バックエンド (存在する場合)
    if [ -d "../backend" ]; then
        cd ../backend
        if command -v uv >/dev/null 2>&1; then
            uv run uvicorn app.main:app --reload --port ${BACKEND_PORT} &
        else
            uvicorn app.main:app --reload --port ${BACKEND_PORT} &
        fi
        cd ..
    fi

    # 待機
    wait
    exit 0
fi

# 引数チェック（issue-start.shとして実行された場合）
if [ $# -lt 1 ]; then
    echo "Usage: $0 <issue_number> [branch_name]"
    echo "Example: $0 123"
    echo "Example: $0 123 feature/custom-branch-name"
    exit 1
fi

# プロジェクトルートに移動
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
cd "$PROJECT_ROOT"

ISSUE_NUMBER=$1
BRANCH_NAME=${2:-"training-tracker-issue-${ISSUE_NUMBER}"}
WORKTREE_DIR="../training-tracker-issue-${ISSUE_NUMBER}"

echo "🚀 GitHub Issue #${ISSUE_NUMBER} の作業を開始します..."
echo "ブランチ名: ${BRANCH_NAME}"
echo "作業ディレクトリ: ${WORKTREE_DIR}"

# mainブランチが最新であることを確認
echo "📥 mainブランチを最新に更新中..."
if ! git fetch origin; then
    echo "❌ リモートリポジトリからのフェッチに失敗しました"
    echo "🔧 ネットワーク接続を確認してください"
    exit 1
fi

# mainまたはmasterブランチにチェックアウト
if ! git checkout main 2>/dev/null && ! git checkout master 2>/dev/null; then
    echo "❌ mainまたはmasterブランチが見つかりません"
    echo "🔧 リポジトリの構成を確認してください"
    exit 1
fi

# 最新の変更をpull
if ! git pull origin main 2>/dev/null && ! git pull origin master 2>/dev/null; then
    echo "⚠️  リモートからのpullに失敗しました。ローカルで作業を続行します"
fi

# worktreeディレクトリが既に存在する場合の処理
if [ -d "${WORKTREE_DIR}" ]; then
    echo "⚠️  作業ディレクトリが既に存在します: ${WORKTREE_DIR}"
    read -p "削除して再作成しますか？ (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        git worktree remove "${WORKTREE_DIR}" --force 2>/dev/null || true
        rm -rf "${WORKTREE_DIR}" 2>/dev/null || true
        echo "🗑️  既存のworktreeを削除しました"
    else
        echo "❌ 作業を中止しました"
        exit 1
    fi
fi

# 新しいブランチでworktreeを作成
echo "🌿 新しいブランチ '${BRANCH_NAME}' でworktreeを作成中..."
if ! git worktree add "${WORKTREE_DIR}" -b "${BRANCH_NAME}"; then
    echo "❌ worktreeの作成に失敗しました"
    echo "🔧 ブランチ名 '${BRANCH_NAME}' が既に存在する可能性があります"
    echo "既存のブランチを確認してください: git branch -a | grep ${BRANCH_NAME}"
    exit 1
fi

# 作業ディレクトリに移動
cd "${WORKTREE_DIR}"

# 依存関係のインストール（package.jsonがある場合）
if [ -f "package.json" ]; then
    echo "📦 依存関係をインストール中..."
    if ! command -v pnpm >/dev/null 2>&1; then
        echo "❌ pnpmが見つかりません。インストールしてください："
        echo "  npm install -g pnpm"
        exit 1
    fi

    if ! pnpm install --frozen-lockfile; then
        echo "⚠️  lockfileでのインストールに失敗しました。通常のインストールを試行中..."
        if ! pnpm install; then
            echo "❌ 依存関係のインストールに失敗しました"
            exit 1
        fi
    fi
    echo "✅ 依存関係のインストールが完了しました"
fi

# ポート計算（Issue番号ベース）
FRONTEND_PORT=$((3000 + ${ISSUE_NUMBER} % 100))  # 3000-3099の範囲
BACKEND_PORT=$((8000 + ${ISSUE_NUMBER} % 100))   # 8000-8099の範囲
STORYBOOK_PORT=$((6000 + ${ISSUE_NUMBER} % 100)) # 6000-6099の範囲

# worktree用の.envファイルを作成
cat > .env.local << EOF
# Issue #${ISSUE_NUMBER} 専用ポート設定
NEXT_PUBLIC_API_URL=http://localhost:${BACKEND_PORT}
PORT=${FRONTEND_PORT}
FRONTEND_PORT=${FRONTEND_PORT}
BACKEND_PORT=${BACKEND_PORT}
STORYBOOK_PORT=${STORYBOOK_PORT}
EOF


# 開発サーバー起動オプションの確認
echo ""
echo "✅ Issue #${ISSUE_NUMBER} の作業環境が準備完了！"
echo ""
echo "📂 作業ディレクトリ: ${WORKTREE_DIR}"
echo "🌿 ブランチ: ${BRANCH_NAME}"
echo "🌐 専用ポート: Frontend:${FRONTEND_PORT}, Backend:${BACKEND_PORT}, Storybook:${STORYBOOK_PORT}"
echo ""

# VS Codeで開く（利用可能な場合）
if command -v code >/dev/null 2>&1; then
    echo "💻 VS Codeでworktreeを開きます..."
    code "${WORKTREE_DIR}"
fi

# 開発サーバー起動
echo "🚀 開発サーバーを起動中..."
echo "Frontend: http://localhost:${FRONTEND_PORT}"
if [ -d "apps/backend" ]; then
    echo "Backend:  http://localhost:${BACKEND_PORT}"
fi
echo ""

# 並列でサービスを起動
trap 'echo "🛑 開発サーバーを停止します..."; kill $(jobs -p) 2>/dev/null; exit 0' EXIT INT TERM

# フロントエンドの起動確認
if [ -d "apps/frontend" ]; then
    echo "▶️  フロントエンドを起動中..."
    cd apps/frontend
    pnpm dev -p ${FRONTEND_PORT} &
    FRONTEND_PID=$!
    cd ../..
else
    echo "⚠️  フロントエンドディレクトリが見つかりません"
fi

# バックエンドの起動確認
if [ -d "apps/backend" ]; then
    echo "▶️  バックエンドを起動中..."
    cd apps/backend

    # uvがある場合はuv syncで環境を整備
    if command -v uv >/dev/null 2>&1; then
        echo "🐍 Python環境をuv syncで同期中..."
        if ! uv sync --quiet; then
            echo "⚠️  uv syncに失敗しました。手動で確認してください"
        fi
        uv run uvicorn app.main:app --reload --port ${BACKEND_PORT} &
        BACKEND_PID=$!
    elif command -v uvicorn >/dev/null 2>&1; then
        uvicorn app.main:app --reload --port ${BACKEND_PORT} &
        BACKEND_PID=$!
    else
        echo "⚠️  uvもuvicornも見つかりません。Pythonの仮想環境を確認してください"
        echo "🔧 uvのインストール: pip install uv"
    fi
    cd ../..
fi

# プロセス待機
echo "🎯 開発サーバーが起動しました。Ctrl+C で停止できます"
wait

echo ""
echo "📁 現在のディレクトリをworktreeに変更します"
cd "${WORKTREE_DIR}"
echo "✅ 作業ディレクトリ: $(pwd)"
echo ""
echo "作業完了時は以下のコマンドを実行してください："
echo "  /issue-finish ${ISSUE_NUMBER}"
echo ""
