@echo off
chcp 65001 >nul 2>&1
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV=%SCRIPT_DIR%venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"

:: Check venv exists, create if missing
if not exist "%PYTHON%" (
    echo [setup] Creating virtual environment...
    python -m venv "%VENV%"
    echo [setup] Installing dependencies...
    "%PIP%" install requests pycryptodome tqdm -q
    echo [setup] Done.
)

:: Check & install missing packages
"%PYTHON%" -c "import requests, Crypto, tqdm" 2>nul
if errorlevel 1 (
    echo [setup] Installing missing packages...
    "%PIP%" install requests pycryptodome tqdm -q
)

:: Run the downloader with all provided args
"%PYTHON%" "%SCRIPT_DIR%downloader.py" %*
