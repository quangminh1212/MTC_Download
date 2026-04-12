@echo off
chcp 65001 >nul 2>&1
setlocal

set "DIR=%~dp0"
set "PYTHON=%DIR%venv\Scripts\python.exe"
set "PIP=%DIR%venv\Scripts\pip.exe"

:: Create venv if missing
if not exist "%PYTHON%" (
    echo [setup] Creating virtual environment...
    python -m venv "%DIR%venv"
    echo [setup] Installing packages...
    "%PIP%" install requests pycryptodome -q
    echo [setup] Done.
)

:: Install missing packages silently
"%PYTHON%" -c "import requests, Crypto" 2>nul || (
    "%PIP%" install requests pycryptodome -q
)

:: "run.bat cli ..." → CLI mode
if /i "%1"=="cli" (
    shift
    "%PYTHON%" "%DIR%downloader.py" %1 %2 %3 %4 %5 %6 %7 %8 %9
) else (
    :: Default → GUI
    "%PYTHON%" "%DIR%gui.py" %*
)
