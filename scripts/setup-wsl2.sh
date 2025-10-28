#!/bin/bash
# WSL2完結型開発環境セットアップスクリプト

set -e

# 色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ヘルプメッセージ
show_help() {
    cat << EOF
WSL2完結型開発環境セットアップスクリプト

使用方法:
    bash setup-wsl2.sh [オプション]

オプション:
    --clean     既存環境を削除してから再構築
    --help      このヘルプメッセージを表示

例:
    bash setup-wsl2.sh              # 通常のセットアップ
    bash setup-wsl2.sh --clean      # 環境を削除してから再構築
EOF
    exit 0
}

# クリーンアップ機能
cleanup_environment() {
    echo "========================================="
    echo -e "${RED}既存環境のクリーンアップ${NC}"
    echo "========================================="
    echo ""

    # Dockerコンテナとボリュームの削除
    if [ -d ~/projects/genai-app-docs ]; then
        echo -e "${BLUE}[1/3] Dockerコンテナとボリュームを削除...${NC}"
        cd ~/projects/genai-app-docs
        docker compose down -v 2>/dev/null || true
        echo -e "${GREEN}✓ Dockerコンテナとボリュームを削除しました${NC}"
    else
        echo -e "${YELLOW}プロジェクトディレクトリが存在しません${NC}"
    fi

    # プロジェクトディレクトリの削除
    echo -e "${BLUE}[2/3] プロジェクトディレクトリを削除...${NC}"
    rm -rf ~/projects/genai-app-docs
    echo -e "${GREEN}✓ プロジェクトディレクトリを削除しました${NC}"

    # PATH設定のクリーンアップ（重複削除）
    echo -e "${BLUE}[3/3] PATH設定の重複を削除...${NC}"
    if [ -f ~/.bashrc ]; then
        # 重複したPATH設定を1つだけ残す
        if grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc; then
            # 一旦すべて削除
            sed -i '/export PATH="\$HOME\/.local\/bin:\$PATH"/d' ~/.bashrc
            # 1つだけ追加
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            echo -e "${GREEN}✓ PATH設定をクリーンアップしました${NC}"
        fi
    fi

    echo ""
    echo -e "${GREEN}クリーンアップ完了${NC}"
    echo ""
}

# コマンドライン引数の解析
CLEAN_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_MODE=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo -e "${RED}エラー: 不明なオプション '$1'${NC}"
            echo "ヘルプを表示するには: bash setup-wsl2.sh --help"
            exit 1
            ;;
    esac
done

# クリーンモードの場合、環境を削除
if [ "$CLEAN_MODE" = true ]; then
    cleanup_environment
fi

echo "========================================="
echo "WSL2完結型開発環境セットアップ"
echo "========================================="
echo ""

# ステップ1: Dockerのインストール確認
echo -e "${BLUE}[1/7] Dockerのインストール確認...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Dockerをインストールします..."
    sudo apt update
    sudo apt install -y docker.io
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✓ Dockerをインストールしました${NC}"
else
    echo -e "${GREEN}✓ Dockerは既にインストールされています${NC}"
fi
echo ""

# ステップ2: Dockerサービスの起動
echo -e "${BLUE}[2/7] Dockerサービスの起動...${NC}"
if ! sudo service docker status > /dev/null 2>&1; then
    sudo service docker start
    echo -e "${GREEN}✓ Dockerサービスを起動しました${NC}"
else
    echo -e "${GREEN}✓ Dockerサービスは既に起動しています${NC}"
fi
echo ""

# ステップ3: プロジェクトディレクトリの作成
echo -e "${BLUE}[3/7] プロジェクトディレクトリの準備...${NC}"
mkdir -p ~/projects
cd ~/projects

if [ ! -d "genai-app-docs" ]; then
    echo "Windowsからプロジェクトをコピーします（.venvと.pytest_cacheは除外）..."
    if [ -d "/mnt/c/developments/genai-app-docs" ]; then
        rsync -av --exclude='.venv' --exclude='.pytest_cache' --exclude='__pycache__' --exclude='*.pyc' /mnt/c/developments/genai-app-docs ./
        echo -e "${GREEN}✓ プロジェクトをコピーしました${NC}"
    else
        echo -e "${RED}エラー: /mnt/c/developments/genai-app-docs が見つかりません${NC}"
        echo "手動でプロジェクトをコピーしてください"
        exit 1
    fi
else
    echo -e "${GREEN}✓ プロジェクトディレクトリは既に存在します${NC}"
fi

cd ~/projects/genai-app-docs
echo ""

# ステップ4: uvのインストール
echo -e "${BLUE}[4/7] uvのインストール確認...${NC}"
if ! command -v uv &> /dev/null; then
    echo "uvをインストールします..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    # PATHを永続化
    if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo "✓ PATHを~/.bashrcに追加しました"
    fi
    echo -e "${GREEN}✓ uvをインストールしました${NC}"
else
    echo -e "${GREEN}✓ uvは既にインストールされています${NC}"
fi
echo ""

# ステップ5: 依存関係のインストール
echo -e "${BLUE}[5/7] Python依存関係のインストール...${NC}"
export PATH="$HOME/.local/bin:$PATH"
uv sync
echo -e "${GREEN}✓ 依存関係をインストールしました${NC}"
echo ""

# ステップ6: 環境変数ファイルの作成
echo -e "${BLUE}[6/7] 環境変数ファイルの作成...${NC}"
if [ ! -f ".env.local" ]; then
    cp .env.local.example .env.local
    echo -e "${GREEN}✓ .env.localを作成しました${NC}"
else
    echo -e "${GREEN}✓ .env.localは既に存在します${NC}"
fi
echo ""

# ステップ7: PostgreSQLの起動
echo -e "${BLUE}[7/7] PostgreSQLコンテナの起動...${NC}"
docker compose up -d postgres
sleep 5
echo -e "${GREEN}✓ PostgreSQLを起動しました${NC}"
echo ""

# 完了メッセージ
echo "========================================="
echo -e "${GREEN}✅ セットアップ完了！${NC}"
echo "========================================="
echo ""
echo "次のステップ:"
echo "1. テストを実行:"
echo "   uv run pytest tests/test_services.py -v"
echo ""
echo "2. アプリケーションを起動:"
echo "   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. VSCodeで開く:"
echo "   code ."
echo ""
echo "4. ブラウザでアクセス:"
echo "   http://localhost:8000/docs"
echo ""
echo "========================================="
echo ""
