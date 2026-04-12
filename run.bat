@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

set DIR=%~dp0
set PYTHON=%DIR%venv\Scripts\python.exe
set PIP=%DIR%venv\Scripts\pip.exe

if not exist "%PYTHON%" (
    echo [setup] Creating virtual environment...
    python -m venv "%DIR%venv"
    echo [setup] Installing packages...
    "%PIP%" install requests -q
    echo [setup] Done.
)

"%PYTHON%" -c "import requests" 2>nul || (
    "%PIP%" install requests -q
)

"%PYTHON%" "%DIR%gui.py" %*
