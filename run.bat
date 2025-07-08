@echo off
chcp 65001 >nul
echo ========================================
echo MeTruyenCV Downloader
echo ========================================
echo.
echo Choose version to run:
echo 1. Main version (main.py) - Basic version
echo 2. Fast version (fast.py) - Faster version
echo.
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    echo Running main.py...
    python main.py
) else if "%choice%"=="2" (
    echo Running fast.py...
    python fast.py
) else (
    echo Invalid choice!
    pause
    goto :eof
)

pause
