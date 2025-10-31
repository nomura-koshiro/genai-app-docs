# 環境リセットスクリプト
# Python仮想環境のクリーンアップと再構築

$ErrorActionPreference = 'Continue'

# 共通関数をインポート
. "$PSScriptRoot\lib\common.ps1"

<#
.SYNOPSIS
    開発環境をリセット
#>
function Reset-Environment {
    Show-SectionHeader "環境リセット"

    # ステップ1: 仮想環境の削除
    Show-Step 1 3 "仮想環境を削除中..."
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force .venv
        Show-Success "仮想環境を削除しました"
    } else {
        Show-Skip "仮想環境は存在しません"
    }
    Write-Host ""

    # ステップ2: キャッシュの削除
    Show-Step 2 3 "キャッシュを削除中..."
    $cachesRemoved = $false

    if (Test-Path ".pytest_cache") {
        Remove-Item -Recurse -Force .pytest_cache
        $cachesRemoved = $true
    }

    $pycacheDirs = Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
    if ($pycacheDirs) {
        $pycacheDirs | Remove-Item -Recurse -Force
        $cachesRemoved = $true
    }

    if ($cachesRemoved) {
        Show-Success "キャッシュを削除しました"
    } else {
        Show-Skip "キャッシュが見つかりません"
    }
    Write-Host ""

    # ステップ3: 依存関係の再インストール
    Show-Step 3 3 "Python依存関係を再インストール中..."
    if (-not (Test-UvInstalled)) {
        Show-Error "uvがインストールされていません"
        Write-Host ""
        Write-Host "uvをインストールしてください:" -ForegroundColor $YELLOW
        Write-Host "  powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor $YELLOW
        Write-Host ""
        exit 1
    }

    try {
        uv sync
        Show-Success "依存関係をインストールしました"
    } catch {
        Show-Error "依存関係のインストールに失敗しました: $_"
        exit 1
    }
    Write-Host ""

    # .env.localの存在確認
    if (-not (Test-Path ".env.local")) {
        Show-Warning ".env.localが存在しません"
        Write-Host ""
        Write-Host "テンプレートから.env.localを作成してください:" -ForegroundColor $YELLOW
        Write-Host "  Copy-Item .env.local.example .env.local" -ForegroundColor $YELLOW
        Write-Host ""
    }

    # 完了メッセージ
    Show-SectionHeader "環境リセット完了！"
    Write-Host "仮想環境が最新の依存関係で再構築されました。" -ForegroundColor $GREEN
    Write-Host ""
    Write-Host "次のステップ:" -ForegroundColor $BLUE
    Write-Host "  1. .env.localの設定を確認" -ForegroundColor $BLUE
    Write-Host "  2. 必要に応じてデータベースをリセット: .\scripts\reset-database.ps1" -ForegroundColor $BLUE
    Write-Host "  3. テストを実行: uv run pytest -v" -ForegroundColor $BLUE
    Write-Host ""
}

# メイン実行
Reset-Environment
