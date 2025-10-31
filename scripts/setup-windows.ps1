# Windows環境セットアップスクリプト
# camp_backend開発環境の初期セットアップ

param(
    [switch]$Clean,
    [switch]$Help
)

$ErrorActionPreference = 'Continue'

# 共通関数をインポート
. "$PSScriptRoot\lib\common.ps1"

<#
.SYNOPSIS
    ヘルプメッセージを表示
#>
function Show-Help {
    Write-Host @"
Windows開発環境セットアップ

使用法:
    .\scripts\setup-windows.ps1 [オプション]

オプション:
    -Clean      既存の仮想環境を削除してからセットアップ
    -Help       このヘルプメッセージを表示

例:
    .\scripts\setup-windows.ps1              # 通常のセットアップ
    .\scripts\setup-windows.ps1 -Clean       # クリーンビルド

ドキュメント:
    詳細は docs/01-getting-started/02-windows-setup.md を参照
"@
    exit 0
}

<#
.SYNOPSIS
    既存の環境をクリーンアップ
#>
function Invoke-Cleanup {
    Show-SectionHeader "環境クリーンアップ"

    Show-Step 1 2 "仮想環境を削除中..."
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force .venv
        Show-Success "仮想環境を削除しました"
    } else {
        Show-Skip "仮想環境は存在しません"
    }

    Show-Step 2 2 "キャッシュを削除中..."
    if (Test-Path ".pytest_cache") {
        Remove-Item -Recurse -Force .pytest_cache
    }
    if (Test-Path "__pycache__") {
        Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    }
    Show-Success "キャッシュを削除しました"
    Write-Host ""
}

<#
.SYNOPSIS
    メインセットアップ関数
#>
function Invoke-Setup {
    Show-SectionHeader "Windows開発環境セットアップ"

    # ステップ1: PostgreSQLの確認
    Show-Step 1 5 "PostgreSQLを確認中..."
    if (Test-PostgreSQLInstalled) {
        Show-Success "PostgreSQLがインストールされています"
    } else {
        Show-Error "PostgreSQLがインストールされていません"
        Write-Host ""
        Write-Host "PostgreSQLをインストールしてください:" -ForegroundColor $YELLOW
        Write-Host "  方法1（推奨）: scoop install postgresql" -ForegroundColor $YELLOW
        Write-Host "  方法2: https://www.postgresql.org/download/windows/" -ForegroundColor $YELLOW
        Write-Host ""
        exit 1
    }
    Write-Host ""

    # ステップ2: uvの確認
    Show-Step 2 5 "uvを確認中..."
    if (Test-UvInstalled) {
        Show-Success "uvは既にインストールされています"
    } else {
        Show-Error "uvがインストールされていません"
        Write-Host ""
        Write-Host "uvをインストールしてください:" -ForegroundColor $YELLOW
        Write-Host "  powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor $YELLOW
        Write-Host ""
        Write-Host "インストール後、新しいPowerShellセッションを開いてこのスクリプトを再実行してください。" -ForegroundColor $YELLOW
        exit 1
    }
    Write-Host ""

    # ステップ3: Python依存関係のインストール
    Show-Step 3 5 "Python依存関係をインストール中..."
    try {
        uv sync
        Show-Success "依存関係をインストールしました"
    } catch {
        Show-Error "依存関係のインストールに失敗しました: $_"
        exit 1
    }
    Write-Host ""

    # ステップ4: 環境設定ファイルの作成
    Show-Step 4 5 "環境設定ファイルを作成中..."
    if (-not (Test-Path ".env.local")) {
        Copy-Item ".env.local.example" ".env.local"
        Show-Success ".env.localを作成しました"
        Write-Host ""
        Write-Host ".env.localを編集して以下を設定してください:" -ForegroundColor $YELLOW
        Write-Host "  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/camp_backend_db" -ForegroundColor $YELLOW
        Write-Host "  SECRET_KEY=your-secret-key-here-min-32-characters-long" -ForegroundColor $YELLOW
    } else {
        Show-Skip ".env.localは既に存在します"
    }
    Write-Host ""

    # ステップ5: データベースの作成
    Show-Step 5 5 "データベースを作成中..."

    # 開発用データベース
    $dbExists = psql -U postgres -lqt 2>$null | Select-String -Pattern "camp_backend_db"
    if (-not $dbExists) {
        try {
            psql -U postgres -c "CREATE DATABASE camp_backend_db;" 2>$null | Out-Null
            Show-Success "camp_backend_dbを作成しました"
        } catch {
            Show-Warning "camp_backend_dbの作成に失敗しました"
            Write-Host "  手動で作成: psql -U postgres -c `"CREATE DATABASE camp_backend_db;`"" -ForegroundColor $YELLOW
        }
    } else {
        Show-Skip "データベースcamp_backend_dbは既に存在します"
    }

    # テスト用データベース
    $testDbExists = psql -U postgres -lqt 2>$null | Select-String -Pattern "camp_backend_db_test"
    if (-not $testDbExists) {
        try {
            psql -U postgres -c "CREATE DATABASE camp_backend_db_test;" 2>$null | Out-Null
            Show-Success "camp_backend_db_testを作成しました"
        } catch {
            Show-Warning "camp_backend_db_testの作成に失敗しました"
            Write-Host "  手動で作成: psql -U postgres -c `"CREATE DATABASE camp_backend_db_test;`"" -ForegroundColor $YELLOW
        }
    } else {
        Show-Skip "テストデータベースcamp_backend_db_testは既に存在します"
    }
    Write-Host ""

    # 完了メッセージ
    Show-SectionHeader "セットアップ完了！"
    Write-Host "次のステップ:" -ForegroundColor $BLUE
    Write-Host "  1. 必要に応じて.env.localを編集（データベース認証情報、シークレットキー）" -ForegroundColor $BLUE
    Write-Host "  2. マイグレーション実行: .\scripts\reset-database.ps1" -ForegroundColor $BLUE
    Write-Host "  3. サーバー起動: VS CodeでF5キーを押す" -ForegroundColor $BLUE
    Write-Host ""
}

# Main execution
if ($Help) {
    Show-Help
}

if ($Clean) {
    Invoke-Cleanup
}

Invoke-Setup
