Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendRoot = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $BackendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $BackendRoot)) {
    throw "Backend directory was not found: $BackendRoot"
}

$Python = if (Test-Path -LiteralPath $VenvPython) {
    $VenvPython
}
else {
    "python"
}

function Invoke-CheckedStep {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Action

    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

Push-Location $BackendRoot
try {
    Invoke-CheckedStep "Ruff format check" {
        & $Python -m ruff format --check app tests migrations scripts
    }

    Invoke-CheckedStep "Ruff lint" {
        & $Python -m ruff check app tests migrations scripts
    }

    Invoke-CheckedStep "MyPy" {
        & $Python -m mypy app tests scripts
    }

    Invoke-CheckedStep "Alembic heads" {
        & $Python -m alembic heads
    }

    Invoke-CheckedStep "Alembic current" {
        & $Python -m alembic current
    }

    Invoke-CheckedStep "Alembic synchronization" {
        & $Python -m alembic check
    }

    Invoke-CheckedStep "Backend tests and coverage" {
        & $Python -m pytest
    }

    Invoke-CheckedStep "Phase 1 repository audit" {
        & $Python scripts\phase1_audit.py
    }
}
finally {
    Pop-Location
}

Push-Location $ProjectRoot
try {
    Invoke-CheckedStep "Git whitespace check" {
        & git diff --check
    }

    Write-Host ""
    Write-Host "==> Git status"
    & git status --short
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Phase 1 verification completed successfully."
