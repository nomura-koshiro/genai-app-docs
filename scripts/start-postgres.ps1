# PostgreSQL起動スクリプト
# PostgreSQLの状態を確認し、起動していない場合は起動

$ErrorActionPreference = 'Continue'

# 共通関数をインポート
. "$PSScriptRoot\lib\common.ps1"

<#
.SYNOPSIS
    PostgreSQL起動のメイン実行関数
#>
function Start-PostgreSQL {
    Show-SectionHeader "PostgreSQL起動"

    if (-not (Test-PostgreSQLInstalled)) {
        Show-Error "PostgreSQLがインストールされていません"
        Write-Host ""
        Write-Host "PostgreSQLをインストールしてください:" -ForegroundColor $YELLOW
        Write-Host "  方法1（推奨）: scoop install postgresql" -ForegroundColor $YELLOW
        Write-Host "  方法2: https://www.postgresql.org/download/windows/" -ForegroundColor $YELLOW
        Write-Host ""
        exit 1
    }

    $result = Start-PostgreSQLIfNeeded

    if (-not $result) {
        Show-Warning "PostgreSQLの起動に問題がある可能性があります。ログを確認してください。"
        Write-Host ""
        Write-Host "トラブルシューティング:" -ForegroundColor $YELLOW
        Write-Host "  Scoop版: ~\scoop\apps\postgresql\current\logfile のログを確認" -ForegroundColor $YELLOW
        Write-Host "  インストーラー版: WindowsサービスでPostgreSQLの状態を確認" -ForegroundColor $YELLOW
        Write-Host ""
        exit 1
    }

    Write-Host ""
}

# メイン実行
Start-PostgreSQL
