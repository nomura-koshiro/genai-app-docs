# データベースリセットスクリプト
# データベースの削除と再作成

$ErrorActionPreference = 'Continue'

# 共通関数をインポート
. "$PSScriptRoot\lib\common.ps1"

<#
.SYNOPSIS
    データベースを初期状態にリセット
#>
function Reset-Database {
    Show-SectionHeader "データベースリセット"

    # ステップ0: PostgreSQLが起動しているか確認し、必要なら起動
    if (-not (Start-PostgreSQLIfNeeded)) {
        Show-Error "PostgreSQLを起動できませんでした。手動で起動してから再実行してください。"
        exit 1
    }
    Write-Host ""

    # ステップ1: 開発用データベースの削除と再作成
    Show-Step 1 2 "データベースを削除・再作成中..."
    try {
        # 既存の接続を強制切断
        psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'camp_backend_db' AND pid <> pg_backend_pid();" 2>$null | Out-Null
        psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db;" 2>$null | Out-Null
        Show-Success "camp_backend_dbを削除しました"

        psql -U postgres -c "CREATE DATABASE camp_backend_db;" 2>$null | Out-Null
        Show-Success "camp_backend_dbを作成しました"
    } catch {
        Show-Error "開発用データベースのリセットに失敗しました: $_"
        exit 1
    }
    Write-Host ""

    # ステップ2: テスト用データベースの削除と再作成
    Show-Step 2 2 "テストデータベースを削除・再作成中..."
    try {
        # 既存の接続を強制切断
        psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'camp_backend_db_test' AND pid <> pg_backend_pid();" 2>$null | Out-Null
        psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db_test;" 2>$null | Out-Null
        Show-Success "camp_backend_db_testを削除しました"

        psql -U postgres -c "CREATE DATABASE camp_backend_db_test;" 2>$null | Out-Null
        Show-Success "camp_backend_db_testを作成しました"
    } catch {
        Show-Error "テストデータベースのリセットに失敗しました: $_"
        exit 1
    }
    Write-Host ""

    # 完了メッセージ
    Show-SectionHeader "データベースリセット完了！"
    Write-Host "開発用とテスト用の両方のデータベースがリセットされました。" -ForegroundColor $GREEN
    Write-Host ""
}

# メイン実行
Reset-Database
