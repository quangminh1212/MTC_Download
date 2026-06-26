@echo off
chcp 65001 >nul
echo ========================================
echo   VTRUYEN NON-COMPLETED DOWNLOAD
echo   8203 books - 12 threads - Fast mode
echo ========================================
echo.

cd /d "C:\Dev\MTC_Download"

echo [INFO] Checking Python...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

echo [INFO] Starting download...
echo [INFO] Progress will be shown every 60 seconds
echo.

python "C:\Dev\MTC_Download\tmp\download_vtruyen_fast.py"

echo.
echo [INFO] Download finished or stopped.
echo [INFO] Check logs in: C:\Dev\MTC_Download\logs\
echo.
pause
