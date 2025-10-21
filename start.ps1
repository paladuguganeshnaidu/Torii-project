# Start Torii-Project (Windows PowerShell)
# - Creates .venv if missing
# - Installs Backend requirements
# - Runs the Flask app
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$dotenv = Join-Path $root '.env'
if (Test-Path $dotenv) {
  Write-Host 'Loading environment variables from .env'
  Get-Content $dotenv | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith('#')) { return }
    $idx = $line.IndexOf('=')
    if ($idx -gt 0) {
      $key = $line.Substring(0, $idx).Trim()
      $val = $line.Substring($idx + 1).Trim()
      # Remove surrounding quotes if any
      if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
        $val = $val.Substring(1, $val.Length - 2)
      }
      $env:$key = $val
    }
  }
}

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
