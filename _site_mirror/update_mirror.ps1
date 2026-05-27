<#
.SYNOPSIS
    Update or serve the project-skyscraper.com complete mirror.
.DESCRIPTION
    Fetches every scrap of content from project-skyscraper.com:
    HTML pages, REST API, media, theme/plugin assets, discovery docs,
    WordPress extras, CDN assets, and external references.
    Re-runnable - only fetches changed content and stores diffs.
.PARAMETER Serve
    Start the local mirror server instead of updating.
.PARAMETER Port
    Port for the local server (default: 8080).
.EXAMPLE
    .\update_mirror.ps1
    .\update_mirror.ps1 -Serve
    .\update_mirror.ps1 -Serve -Port 3000
#>

param(
    [switch]$Serve,
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $PSCommandPath

# Check Python availability
$pythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    $ver = & $cmd --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pythonCmd = $cmd
        break
    }
}

if (-not $pythonCmd) {
    Write-Error "Python 3 is required but not found in PATH."
    Write-Host "Install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

if ($Serve) {
    $servePath = Join-Path $ScriptDir "serve_mirror.py"
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  project-skyscraper.com - Local Mirror Server" -ForegroundColor Cyan
    Write-Host "  Port: $Port" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    & $pythonCmd $servePath $Port
    exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  project-skyscraper.com - Mirror Update" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Using: $(& $pythonCmd --version)" -ForegroundColor Gray
Write-Host ""

# Run the update script
$scriptPath = Join-Path $ScriptDir "update_mirror.py"
& $pythonCmd $scriptPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  MIRROR UPDATE COMPLETE" -ForegroundColor Green
    Write-Host "  Mirror location: $ScriptDir" -ForegroundColor Green
    Write-Host "  See MIRROR_MANIFEST.md for contents" -ForegroundColor Green
    Write-Host "  Run: .\update_mirror.ps1 -Serve" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  MIRROR UPDATE FAILED (exit code: $LASTEXITCODE)" -ForegroundColor Red
    Write-Host "  Check output above for errors." -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
}

# Pause so the window stays open if double-clicked
if ($Host.Name -eq "ConsoleHost") {
    Write-Host ""
    Write-Host "Press any key to continue..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
