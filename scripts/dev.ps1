# Development Helper Script
# Usage:
#   .\scripts\dev.ps1 setup [-Clean]   - Setup environment
#   .\scripts\dev.ps1 reset-db         - Reset database
#   .\scripts\dev.ps1 start-postgres   - Start PostgreSQL

param(
    [Parameter(Position=0)]
    [ValidateSet('setup', 'reset-db', 'start-postgres', 'help')]
    [string]$Command = 'help',

    [switch]$Clean
)

$ErrorActionPreference = 'Continue'

# Colors
$GREEN = "Green"
$BLUE = "Cyan"
$RED = "Red"
$YELLOW = "Yellow"

function Show-Help {
    Write-Host @"
Development Helper Script

Usage:
    .\scripts\dev.ps1 <command> [options]

Commands:
    setup              Setup development environment
    setup -Clean       Clean and rebuild environment
    reset-db           Reset database (drop, create, migrate)
    start-postgres     Start PostgreSQL if not running
    help               Show this help message

Examples:
    .\scripts\dev.ps1 setup
    .\scripts\dev.ps1 setup -Clean
    .\scripts\dev.ps1 reset-db
    .\scripts\dev.ps1 start-postgres
"@
}

function Start-PostgreSQL {
    Write-Host "=========================================" -ForegroundColor $BLUE
    Write-Host "PostgreSQL Startup" -ForegroundColor $BLUE
    Write-Host "=========================================" -ForegroundColor $BLUE
    Write-Host ""

    $PGDATA = "$env:USERPROFILE\scoop\apps\postgresql\current\data"
    $LOGFILE = "$env:USERPROFILE\scoop\apps\postgresql\current\logfile"

    $status = pg_ctl -D $PGDATA status 2>&1 | Out-String

    if ($status -match 'no server running') {
        Write-Host "PostgreSQL is not running. Starting..." -ForegroundColor $YELLOW
        Start-Process -FilePath "pg_ctl" -ArgumentList "-D", $PGDATA, "-l", $LOGFILE, "-w", "start" -NoNewWindow -Wait

        $retries = 10
        $connected = $false
        for ($i = 0; $i -lt $retries; $i++) {
            Start-Sleep -Milliseconds 500
            $testStatus = pg_ctl -D $PGDATA status 2>&1 | Out-String
            if ($testStatus -match 'server is running') {
                $connected = $true
                break
            }
        }

        if ($connected) {
            Write-Host "[OK] PostgreSQL started successfully." -ForegroundColor $GREEN
        } else {
            Write-Host "[WARN] PostgreSQL may still be starting. Check logs if connection fails." -ForegroundColor $YELLOW
        }
    } else {
        Write-Host "[OK] PostgreSQL is already running." -ForegroundColor $GREEN
    }
    Write-Host ""
}

function Reset-Database {
    Write-Host "=========================================" -ForegroundColor $BLUE
    Write-Host "Database Reset" -ForegroundColor $BLUE
    Write-Host "=========================================" -ForegroundColor $BLUE
    Write-Host ""

    Write-Host "[1/3] Drop and recreate database..." -ForegroundColor $BLUE
    psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db;" | Out-Null
    Write-Host "[OK] Dropped camp_backend_db" -ForegroundColor $GREEN
    psql -U postgres -c "CREATE DATABASE camp_backend_db;" | Out-Null
    Write-Host "[OK] Created camp_backend_db" -ForegroundColor $GREEN
    Write-Host ""

    Write-Host "[2/3] Drop and recreate test database..." -ForegroundColor $BLUE
    psql -U postgres -c "DROP DATABASE IF EXISTS camp_backend_db_test;" | Out-Null
    Write-Host "[OK] Dropped camp_backend_db_test" -ForegroundColor $GREEN
    psql -U postgres -c "CREATE DATABASE camp_backend_db_test;" | Out-Null
    Write-Host "[OK] Created camp_backend_db_test" -ForegroundColor $GREEN
    Write-Host ""

    Write-Host "[3/3] Run migrations..." -ForegroundColor $BLUE
    Push-Location src
    uv run alembic upgrade head
    Pop-Location
    Write-Host "[OK] Migrations completed" -ForegroundColor $GREEN
    Write-Host ""

    Write-Host "=========================================" -ForegroundColor $GREEN
    Write-Host "Database Reset Complete!" -ForegroundColor $GREEN
    Write-Host "=========================================" -ForegroundColor $GREEN
    Write-Host ""
}

function Invoke-Cleanup {
    Write-Host "=========================================" -ForegroundColor $RED
    Write-Host "Environment Cleanup" -ForegroundColor $RED
    Write-Host "=========================================" -ForegroundColor $RED
    Write-Host ""

    Write-Host "[1/2] Remove virtual environment..." -ForegroundColor $BLUE
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force .venv
        Write-Host "[OK] Virtual environment removed" -ForegroundColor $GREEN
    } else {
        Write-Host "[SKIP] Virtual environment does not exist" -ForegroundColor $YELLOW
    }

    Write-Host "[2/2] Remove caches..." -ForegroundColor $BLUE
    if (Test-Path ".pytest_cache") {
        Remove-Item -Recurse -Force .pytest_cache
    }
    if (Test-Path "__pycache__") {
        Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    }
    Write-Host "[OK] Caches removed" -ForegroundColor $GREEN
    Write-Host ""
}

function Setup-Environment {
    if ($Clean) {
        Invoke-Cleanup
    }

    Write-Host "=========================================" -ForegroundColor $BLUE
    Write-Host "Windows Development Setup" -ForegroundColor $BLUE
    Write-Host "=========================================" -ForegroundColor $BLUE
    Write-Host ""

    Write-Host "[1/5] Check PostgreSQL..." -ForegroundColor $BLUE
    $pgCommand = Get-Command psql -ErrorAction SilentlyContinue
    if ($pgCommand) {
        Write-Host "[OK] PostgreSQL is installed" -ForegroundColor $GREEN
    } else {
        Write-Host "[ERROR] PostgreSQL is not installed" -ForegroundColor $RED
        Write-Host "Install PostgreSQL: https://www.postgresql.org/download/windows/" -ForegroundColor $YELLOW
        exit 1
    }
    Write-Host ""

    Write-Host "[2/5] Check uv..." -ForegroundColor $BLUE
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCommand) {
        Write-Host "[OK] uv is already installed" -ForegroundColor $GREEN
    } else {
        Write-Host "[ERROR] uv is not installed" -ForegroundColor $RED
        Write-Host "Install uv: https://docs.astral.sh/uv/" -ForegroundColor $YELLOW
        exit 1
    }
    Write-Host ""

    Write-Host "[3/5] Install Python dependencies..." -ForegroundColor $BLUE
    uv sync
    Write-Host "[OK] Dependencies installed" -ForegroundColor $GREEN
    Write-Host ""

    Write-Host "[4/5] Create environment file..." -ForegroundColor $BLUE
    if (-not (Test-Path ".env.local")) {
        Copy-Item ".env.local.example" ".env.local"
        Write-Host "[OK] Created .env.local" -ForegroundColor $GREEN
    } else {
        Write-Host "[SKIP] .env.local already exists" -ForegroundColor $GREEN
    }
    Write-Host ""

    Write-Host "[5/5] Create databases..." -ForegroundColor $BLUE
    $dbExists = psql -U postgres -lqt 2>$null | Select-String -Pattern "camp_backend_db"
    if (-not $dbExists) {
        psql -U postgres -c "CREATE DATABASE camp_backend_db;" 2>$null | Out-Null
        Write-Host "[OK] Created camp_backend_db" -ForegroundColor $GREEN
    } else {
        Write-Host "[SKIP] Database camp_backend_db already exists" -ForegroundColor $GREEN
    }

    $testDbExists = psql -U postgres -lqt 2>$null | Select-String -Pattern "camp_backend_db_test"
    if (-not $testDbExists) {
        psql -U postgres -c "CREATE DATABASE camp_backend_db_test;" 2>$null | Out-Null
        Write-Host "[OK] Created camp_backend_db_test" -ForegroundColor $GREEN
    } else {
        Write-Host "[SKIP] Test database camp_backend_db_test already exists" -ForegroundColor $GREEN
    }
    Write-Host ""

    Write-Host "=========================================" -ForegroundColor $GREEN
    Write-Host "Setup Complete!" -ForegroundColor $GREEN
    Write-Host "=========================================" -ForegroundColor $GREEN
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor $BLUE
    Write-Host "  1. Run migrations: .\scripts\dev.ps1 reset-db" -ForegroundColor $BLUE
    Write-Host "  2. Start server: Press F5 in VS Code" -ForegroundColor $BLUE
    Write-Host ""
}

# Execute command
switch ($Command) {
    'setup' {
        Setup-Environment
    }
    'reset-db' {
        Reset-Database
    }
    'start-postgres' {
        Start-PostgreSQL
    }
    'help' {
        Show-Help
    }
    default {
        Show-Help
    }
}
