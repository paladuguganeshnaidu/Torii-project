# Start Torii-Project (Windows PowerShell)
# - Creates .venv if missing
# - Installs Backend requirements
# - Runs the Flask app
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venv = Join-Path $root '.venv'
$python = Join-Path $venv 'Scripts\python.exe'

if (-not (Test-Path $python)) {
  Write-Host 'Creating virtual environment in .venv ...'
  py -m venv $venv
}

if (-not (Test-Path $python)) {
  Write-Error "Could not find venv python at $python"
  exit 1
}

Write-Host 'Upgrading pip and installing requirements...'
& $python -m pip install --upgrade pip
& $python -m pip install -r 'Backend\requirements.txt'

Write-Host 'Starting Flask app...'
& $python 'run.py'
