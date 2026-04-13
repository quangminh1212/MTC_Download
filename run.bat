@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

set DIR=%~dp0
set PYTHON=%DIR%.venv\Scripts\python.exe

if not exist "%PYTHON%" (
    echo [setup] Creating virtual environment...
    python -m venv "%DIR%.venv"
    echo [setup] Virtual environment ready.
)

echo.
echo  ========================================
echo   MTC Novel Downloader - Hot Reload Mode
echo   Luu file .py = tu dong restart app
echo   Ctrl+C = thoat hoan toan
echo  ========================================
echo.

set MTC_HOT_RELOAD=1

:loop
echo [%time%] Starting gui.py...
"%PYTHON%" "%DIR%gui.py"
set EC=%errorlevel%

if "%EC%"=="42" (
    echo [%time%] File changed - reloading...
    timeout /t 1 /nobreak >nul
    goto loop
)

echo [%time%] Exited (code: %EC%).
pause
