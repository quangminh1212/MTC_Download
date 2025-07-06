@echo off
title MeTruyenCV Downloader - Setup and Run
color 0A
cls

echo ==============================================
echo     MeTruyenCV Downloader - Setup and Run
echo ==============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.6 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

:: Run the setup script
python setup.py

:: End of script
exit /b 