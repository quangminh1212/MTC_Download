@echo off
title MeTruyenCV Downloader

echo.
echo ========================================
echo    MeTruyenCV Downloader
echo    Starting Project
echo ========================================
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo.
    echo Please download and install Python from:
    echo    https://python.org/downloads/
    echo.
    echo Note: Remember to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

python --version
echo Python is installed
echo.

REM Check pip
echo Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo pip is not installed!
    echo pip usually comes with Python, please reinstall Python
    pause
    exit /b 1
)

echo pip is ready
echo.

REM Check requirements.txt
if not exist "requirements.txt" (
    echo requirements.txt not found
    echo Make sure you are running in the project directory
    pause
    exit /b 1
)

REM Install dependencies
echo Installing required libraries...
echo This process may take a few minutes...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Error installing libraries!
    echo.
    echo You can try:
    echo    1. Run Command Prompt as Administrator
    echo    2. Check internet connection
    echo    3. Try command: pip install --upgrade pip
    echo.
    pause
    exit /b 1
)

echo.
echo Successfully installed all libraries
echo.

REM Create downloads folder if not exists
if not exist "downloads" (
    mkdir downloads
    echo Created downloads folder
)

echo Starting MeTruyenCV Downloader...
echo.
echo Application will run at: http://localhost:5000
echo Browser will open automatically in 3 seconds
echo.
echo To stop the application, press Ctrl+C
echo.

REM Wait 3 seconds then open browser
timeout /t 3 /nobreak >nul
start http://localhost:5000

REM Run application
python app.py

echo.
echo Thank you for using MeTruyenCV Downloader!
echo.
pause
