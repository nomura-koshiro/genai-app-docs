# データベースリセットスクリプト
# データベースの削除、再作成、マイグレーション実行

$ErrorActionPreference = 'Continue'

# 共通関数をインポート
. "$PSScriptRoot\lib\common.ps1"

<#
.SYNOPSIS
    データベースを初期状態にリセット
#>
function Reset-Database {
    Show-SectionHeader "データベースリセット"

    # ステップ1: 開発用データベースの削除と再作成
    Show-Step 1 3 "データベースを削除・再作成中..."
    try {
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
    Show-Step 2 3 "テストデータベースを削除・再作成中..."
    try {
        psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db_test;" 2>$null | Out-Null
        Show-Success "camp_backend_db_testを削除しました"

        psql -U postgres -c "CREATE DATABASE camp_backend_db_test;" 2>$null | Out-Null
        Show-Success "camp_backend_db_testを作成しました"
    } catch {
        Show-Error "テストデータベースのリセットに失敗しました: $_"
        exit 1
    }
    Write-Host ""

    # ステップ3: マイグレーション実行
    Show-Step 3 3 "マイグレーションを実行中..."
    try {
        Push-Location src
        uv run alembic upgrade head
        Pop-Location
        Show-Success "マイグレーションが完了しました"
    } catch {
        Pop-Location
        Show-Error "マイグレーションの実行に失敗しました: $_"
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
