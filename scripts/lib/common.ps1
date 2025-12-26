# 共通関数ライブラリ
# すべてのPowerShellスクリプトで使用される共有ユーティリティ関数

# 出力の色定義（一貫性のあるフォーマットのため）
$script:GREEN = "Green"
$script:BLUE = "Cyan"
$script:RED = "Red"
$script:YELLOW = "Yellow"

<#
.SYNOPSIS
    セクションヘッダーを表示
.PARAMETER Title
    表示するタイトル
#>
function Show-SectionHeader {
    param([string]$Title)

    Write-Host "=========================================" -ForegroundColor $BLUE
    Write-Host $Title -ForegroundColor $BLUE
    Write-Host "=========================================" -ForegroundColor $BLUE
    Write-Host ""
}

<#
.SYNOPSIS
    ステップメッセージを進捗インジケーター付きで表示
.PARAMETER StepNumber
    現在のステップ番号
.PARAMETER TotalSteps
    全ステップ数
.PARAMETER Message
    ステップの説明メッセージ
#>
function Show-Step {
    param(
        [int]$StepNumber,
        [int]$TotalSteps,
        [string]$Message
    )

    Write-Host "[$StepNumber/$TotalSteps] $Message" -ForegroundColor $BLUE
}

<#
.SYNOPSIS
    成功メッセージを表示
.PARAMETER Message
    表示するメッセージ
#>
function Show-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor $GREEN
}

<#
.SYNOPSIS
    警告メッセージを表示
.PARAMETER Message
    表示するメッセージ
#>
function Show-Warning {
    param([string]$Message)
    Write-Host "[警告] $Message" -ForegroundColor $YELLOW
}

<#
.SYNOPSIS
    エラーメッセージを表示
.PARAMETER Message
    表示するメッセージ
#>
function Show-Error {
    param([string]$Message)
    Write-Host "[エラー] $Message" -ForegroundColor $RED
}

<#
.SYNOPSIS
    スキップメッセージを表示
.PARAMETER Message
    表示するメッセージ
#>
function Show-Skip {
    param([string]$Message)
    Write-Host "[スキップ] $Message" -ForegroundColor $YELLOW
}

<#
.SYNOPSIS
    PostgreSQLがインストールされているかチェック
.OUTPUTS
    Boolean - インストールされている場合True、それ以外False
#>
function Test-PostgreSQLInstalled {
    $pgCommand = Get-Command psql -ErrorAction SilentlyContinue
    return $null -ne $pgCommand
}

<#
.SYNOPSIS
    PostgreSQLが現在実行中かチェック
.OUTPUTS
    Boolean - 実行中の場合True、それ以外False
#>
function Test-PostgreSQLRunning {
    # 接続テストが最も確実（プロセスが起動していても接続を受け付けていない場合がある）
    $null = psql -U postgres -c "SELECT 1;" 2>&1
    return $LASTEXITCODE -eq 0
}

<#
.SYNOPSIS
    uvがインストールされているかチェック
.OUTPUTS
    Boolean - インストールされている場合True、それ以外False
#>
function Test-UvInstalled {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    return $null -ne $uvCommand
}

<#
.SYNOPSIS
    PostgreSQLが起動していない場合は起動
.DESCRIPTION
    PostgreSQLを起動し、接続可能になるまで待機
.OUTPUTS
    Boolean - この関数実行後にPostgreSQLが実行中の場合True、それ以外False
#>
function Start-PostgreSQLIfNeeded {
    if (Test-PostgreSQLRunning) {
        Show-Success "PostgreSQLは既に起動しています"
        return $true
    }

    $PGDATA = "$env:USERPROFILE\scoop\apps\postgresql\current\data"

    if (Test-Path $PGDATA) {
        # Scoop版PostgreSQL
        $LOGFILE = "$env:USERPROFILE\scoop\apps\postgresql\current\logfile"

        Write-Host "PostgreSQLが起動していません。起動中..." -ForegroundColor $YELLOW
        # pg_ctlをバックグラウンドで起動（-wなしで即座に戻る）
        Start-Process -FilePath "pg_ctl" -ArgumentList "-D", $PGDATA, "-l", $LOGFILE, "start" -NoNewWindow

        # 起動確認（リトライ）
        $retries = 20
        $connected = $false
        for ($i = 0; $i -lt $retries; $i++) {
            Start-Sleep -Milliseconds 500
            if (Test-PostgreSQLRunning) {
                $connected = $true
                break
            }
        }

        if ($connected) {
            Show-Success "PostgreSQLが正常に起動しました"
            return $true
        } else {
            Show-Warning "PostgreSQLの起動に失敗しました。ログを確認してください: $LOGFILE"
            return $false
        }
    } else {
        # 公式インストーラー版PostgreSQL
        $pgService = Get-Service postgresql* -ErrorAction SilentlyContinue | Select-Object -First 1

        if ($null -eq $pgService) {
            Show-Error "PostgreSQLサービスが見つかりません"
            return $false
        }

        if ($pgService.Status -ne 'Running') {
            Write-Host "PostgreSQLサービスを起動中..." -ForegroundColor $YELLOW
            Start-Service $pgService.Name
            Start-Sleep -Seconds 2
        }

        if (Test-PostgreSQLRunning) {
            Show-Success "PostgreSQLサービスが正常に起動しました"
            return $true
        } else {
            Show-Error "PostgreSQLサービスの起動に失敗しました"
            return $false
        }
    }
}

# 関数と変数はドットソース時に自動的に利用可能
# .ps1ファイルではExport-ModuleMemberは不要
