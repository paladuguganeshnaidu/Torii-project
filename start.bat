@echo off
REM Start Torii-Project (Windows cmd)
setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0
set VENV=%SCRIPT_DIR%.venv
set PY=%VENV%\Scripts\python.exe

if not exist "%PY%" (
  echo Creating virtual environment in .venv ...
  py -m venv "%VENV%"
)

if not exist "%PY%" (
  echo ERROR: Could not find venv python at %PY%
  exit /b 1
)

echo Installing requirements...
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r Backend\requirements.txt

echo Starting Flask app...
"%PY%" run.py
