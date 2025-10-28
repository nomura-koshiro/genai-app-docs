# Windows環境セットアップスクリプト
# PowerShell 5.1以降が必要

param(
    [switch]$Clean,
    [switch]$Help
)

# 色定義
$GREEN = "Green"
$BLUE = "Cyan"
$RED = "Red"
$YELLOW = "Yellow"

# ヘルプメッセージ
function Show-Help {
    Write-Host @"
Windows開発環境セットアップスクリプト

使用方法:
    .\setup-windows.ps1 [オプション]

オプション:
    -Clean      既存の仮想環境を削除してから再構築
    -Help       このヘルプメッセージを表示

例:
    .\setup-windows.ps1              # 通常のセットアップ
    .\setup-windows.ps1 -Clean       # 環境を削除してから再構築
"@
    exit 0
}

# クリーンアップ機能
function Invoke-Cleanup {
    Write-Host "=========================================" -ForegroundColor $RED
    Write-Host "既存環境のクリーンアップ" -ForegroundColor $RED
    Write-Host "=========================================" -ForegroundColor $RED
    Write-Host ""

    Write-Host "[1/2] 仮想環境を削除..." -ForegroundColor $BLUE
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force .venv
        Write-Host "✓ 仮想環境を削除しました" -ForegroundColor $GREEN
    } else {
        Write-Host "仮想環境が存在しません" -ForegroundColor $YELLOW
    }

    Write-Host "[2/2] キャッシュを削除..." -ForegroundColor $BLUE
    if (Test-Path ".pytest_cache") {
        Remove-Item -Recurse -Force .pytest_cache
    }
    if (Test-Path "__pycache__") {
        Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    }
    Write-Host "✓ キャッシュを削除しました" -ForegroundColor $GREEN

    Write-Host ""
    Write-Host "クリーンアップ完了" -ForegroundColor $GREEN
    Write-Host ""
}

# ヘルプ表示
if ($Help) {
    Show-Help
}

# クリーンモードの場合、環境を削除
if ($Clean) {
    Invoke-Cleanup
}

Write-Host "=========================================" -ForegroundColor $BLUE
Write-Host "Windows開発環境セットアップ" -ForegroundColor $BLUE
Write-Host "=========================================" -ForegroundColor $BLUE
Write-Host ""

# ステップ1: PostgreSQLの確認
Write-Host "[1/6] PostgreSQLの確認..." -ForegroundColor $BLUE
$pgCommand = Get-Command psql -ErrorAction SilentlyContinue
if ($pgCommand) {
    Write-Host "✓ PostgreSQLがインストールされています" -ForegroundColor $GREEN
    Write-Host "  バージョン: $(psql --version)" -ForegroundColor $GREEN
} else {
    Write-Host "⚠ PostgreSQLがインストールされていません" -ForegroundColor $YELLOW
    Write-Host ""
    Write-Host "PostgreSQLをインストールしてください：" -ForegroundColor $YELLOW
    Write-Host "  1. https://www.postgresql.org/download/windows/ からダウンロード" -ForegroundColor $YELLOW
    Write-Host "  2. または: scoop install postgresql" -ForegroundColor $YELLOW
    Write-Host ""
    $continue = Read-Host "インストール後、Enterキーを押して続行..."
}
Write-Host ""

# ステップ2: PostgreSQLサービスの確認
Write-Host "[2/6] PostgreSQLサービスの確認..." -ForegroundColor $BLUE
$pgService = Get-Service postgresql* -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' }
if ($pgService) {
    Write-Host "✓ PostgreSQLサービスが起動しています" -ForegroundColor $GREEN
} else {
    Write-Host "⚠ PostgreSQLサービスが起動していません" -ForegroundColor $YELLOW
    Write-Host "サービスを手動で起動してください" -ForegroundColor $YELLOW
}
Write-Host ""

# ステップ3: uvのインストール確認
Write-Host "[3/6] uvのインストール確認..." -ForegroundColor $BLUE
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCommand) {
    Write-Host "✓ uvは既にインストールされています" -ForegroundColor $GREEN
} else {
    Write-Host "uvをインストールします..." -ForegroundColor $BLUE
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        Write-Host "✓ uvをインストールしました" -ForegroundColor $GREEN
        Write-Host ""
        Write-Host "⚠ PATHを更新するため、新しいPowerShellセッションを開いて再実行してください" -ForegroundColor $YELLOW
        exit 0
    } catch {
        Write-Host "✗ uvのインストールに失敗しました: $_" -ForegroundColor $RED
        exit 1
    }
}
Write-Host ""

# ステップ4: Python依存関係のインストール
Write-Host "[4/6] Python依存関係のインストール..." -ForegroundColor $BLUE
try {
    uv sync
    Write-Host "✓ 依存関係をインストールしました" -ForegroundColor $GREEN
} catch {
    Write-Host "✗ 依存関係のインストールに失敗しました: $_" -ForegroundColor $RED
    exit 1
}
Write-Host ""

# ステップ5: 環境変数ファイルの作成
Write-Host "[5/6] 環境変数ファイルの作成..." -ForegroundColor $BLUE
if (-not (Test-Path ".env.local")) {
    Copy-Item ".env.local.example" ".env.local"
    Write-Host "✓ .env.localを作成しました" -ForegroundColor $GREEN
    Write-Host ""
    Write-Host "⚠ .env.localを編集してデータベース接続情報を設定してください：" -ForegroundColor $YELLOW
    Write-Host "  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/camp_backend_db" -ForegroundColor $YELLOW
    Write-Host "  SECRET_KEY=your-secret-key-here-min-32-characters-long" -ForegroundColor $YELLOW
} else {
    Write-Host "✓ .env.localは既に存在します" -ForegroundColor $GREEN
}
Write-Host ""

# ステップ6: データベースの確認
Write-Host "[6/6] データベースの確認..." -ForegroundColor $BLUE
Write-Host "データベース 'camp_backend_db' が作成されているか確認してください" -ForegroundColor $YELLOW
Write-Host ""
Write-Host "作成されていない場合、以下のコマンドで作成してください：" -ForegroundColor $YELLOW
Write-Host "  psql -U postgres -c `"CREATE DATABASE camp_backend_db;`"" -ForegroundColor $YELLOW
Write-Host ""

# 完了メッセージ
Write-Host "=========================================" -ForegroundColor $GREEN
Write-Host "✅ セットアップ完了！" -ForegroundColor $GREEN
Write-Host "=========================================" -ForegroundColor $GREEN
Write-Host ""
Write-Host "次のステップ:" -ForegroundColor $BLUE
Write-Host "1. データベースを作成（まだの場合）:" -ForegroundColor $BLUE
Write-Host "   psql -U postgres -c `"CREATE DATABASE camp_backend_db;`"" -ForegroundColor $BLUE
Write-Host ""
Write-Host "2. .env.localを編集してデータベース接続情報を設定" -ForegroundColor $BLUE
Write-Host ""
Write-Host "3. データベースマイグレーションを実行:" -ForegroundColor $BLUE
Write-Host "   cd src" -ForegroundColor $BLUE
Write-Host "   uv run alembic upgrade head" -ForegroundColor $BLUE
Write-Host "   cd .." -ForegroundColor $BLUE
Write-Host ""
Write-Host "4. テストを実行:" -ForegroundColor $BLUE
Write-Host "   uv run pytest tests/ -v" -ForegroundColor $BLUE
Write-Host ""
Write-Host "5. アプリケーションを起動:" -ForegroundColor $BLUE
Write-Host "   uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor $BLUE
Write-Host ""
Write-Host "6. ブラウザでアクセス:" -ForegroundColor $BLUE
Write-Host "   http://localhost:8000/docs" -ForegroundColor $BLUE
Write-Host ""
Write-Host "=========================================" -ForegroundColor $GREEN
Write-Host ""
