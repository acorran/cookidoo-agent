#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Interactive test runner for cookidoo-agent.

.DESCRIPTION
    Presents a menu of test suites so you don't have to remember
    pytest commands and markers.  Activates the venv automatically.

.EXAMPLE
    .\run_tests.ps1          # interactive menu
    .\run_tests.ps1 1        # run option 1 directly
#>

param(
    [Parameter(Position = 0)]
    [string]$Choice
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Activate venv ────────────────────────────────────────────────────
$venvActivate = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Host "ERROR: venv not found at $venvActivate" -ForegroundColor Red
    Write-Host "Run setup.ps1 first to create the virtual environment."
    exit 1
}
. $venvActivate

# ── Menu options ─────────────────────────────────────────────────────
$options = @(
    @{ Key = "1"; Label = "Unit tests only";                   Cmd = "pytest tests/test_api_endpoints.py tests/test_recipe_service.py -v" }
    @{ Key = "2"; Label = "All e2e tests (full suite)";        Cmd = "pytest -m e2e -v -s" }
    @{ Key = "3"; Label = "E2e read-only (safe, no writes)";   Cmd = "pytest -m e2e -v -s -k 'TestGetRecipe or TestShoppingList'" }
    @{ Key = "4"; Label = "E2e create new recipe";             Cmd = "pytest -m e2e -v -s -k 'test_create_new'" }
    @{ Key = "5"; Label = "E2e copy + tweak existing recipe";  Cmd = "pytest -m e2e -v -s -k 'test_copy or test_tweak or test_read_back_tweak'" }
    @{ Key = "6"; Label = "E2e full CRUD cycle";               Cmd = "pytest -m e2e -v -s -k TestCustomRecipeCRUD" }
    @{ Key = "7"; Label = "E2e WITHOUT cleanup (keep recipes)";Cmd = "pytest -m 'e2e and not e2e_cleanup' -v -s" }
    @{ Key = "8"; Label = "Cleanup only (delete test recipes)";Cmd = "pytest -m e2e_cleanup -v -s" }
    @{ Key = "9";  Label = "ALL tests (unit + e2e)";            Cmd = "pytest -v -s" }
    @{ Key = "10"; Label = "E2e image upload test";              Cmd = "__image_upload__" }
)

function Show-Menu {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║       cookidoo-agent  Test Runner            ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    foreach ($opt in $options) {
        $label = $opt.Label
        $key   = $opt.Key
        Write-Host "  [$key] $label" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "  [q] Quit" -ForegroundColor DarkGray
    Write-Host ""
}

# ── Resolve choice ───────────────────────────────────────────────────
if (-not $Choice) {
    Show-Menu
    $Choice = Read-Host "Select an option"
}

if ($Choice -eq "q") { exit 0 }

$selected = $options | Where-Object { $_.Key -eq $Choice }

if (-not $selected) {
    Write-Host "Invalid option: $Choice" -ForegroundColor Red
    exit 1
}

# ── Run ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Running: $($selected.Label)" -ForegroundColor Green

# Special handling for image upload test — prompt for optional image path
if ($selected.Cmd -eq "__image_upload__") {
    $imagePath = Read-Host "Path to image file (Enter to use generated test image)"
    $imagePath = $imagePath.Trim('"', "'", ' ')
    if ($imagePath) {
        if (-not (Test-Path $imagePath)) {
            Write-Host "File not found: $imagePath" -ForegroundColor Red
            exit 1
        }
        $env:TEST_IMAGE_PATH = (Resolve-Path $imagePath).Path
        Write-Host "Using image: $($env:TEST_IMAGE_PATH)" -ForegroundColor Cyan
    } else {
        $env:TEST_IMAGE_PATH = ""
        Write-Host "Using generated test image" -ForegroundColor Cyan
    }
    $actualCmd = "pytest -m e2e -v -s -k test_upload_image_standalone"
    Write-Host "Command: $actualCmd" -ForegroundColor DarkGray
    Write-Host ("-" * 60)
    Invoke-Expression $actualCmd
} else {
    Write-Host "Command: $($selected.Cmd)" -ForegroundColor DarkGray
    Write-Host ("-" * 60)
    Invoke-Expression $selected.Cmd
}
