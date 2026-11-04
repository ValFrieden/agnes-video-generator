# PowerShell launcher for Begi Clip Pipeline
param(
    [string]$stage = "all",
    [int]$scene = -1,
    [string]$model = "",
    [string]$provider = "agnes"
)

$ErrorActionPreference = "Stop"
$root = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Begi Za Solntsem - Variant A (Yellow Umbrella) Pipeline" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Ensure venv site-packages are visible to python
$venvSite = "$root\.venv\Lib\site-packages"
if (Test-Path $venvSite) {
    $env:PYTHONPATH = $venvSite
}

# Determine python command - prioritize virtual environment (.venv)
if (Test-Path "$root\.venv\Scripts\python.exe") {
    $py = "$root\.venv\Scripts\python.exe"
    $pyCmdArgs = @("$root\begi_clip_pipeline.py", "--stage", $stage)
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $py = "py"
    $pyCmdArgs = @("-3", "$root\begi_clip_pipeline.py", "--stage", $stage)
} else {
    $py = "python"
    $pyCmdArgs = @("$root\begi_clip_pipeline.py", "--stage", $stage)
}

if ($scene -ge 0) {
    $pyCmdArgs += @("--scene", $scene.ToString())
}
if ($model -ne "") {
    $pyCmdArgs += @("--model", $model)
}
if ($provider -ne "") {
    $pyCmdArgs += @("--provider", $provider)
}

Write-Host "Starting pipeline with $py (Stage: $stage, Provider: $provider)..." -ForegroundColor Green
& $py $pyCmdArgs
