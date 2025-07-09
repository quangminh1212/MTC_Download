@echo off
chcp 65001 >nul
title MeTruyenCV Web Interface

echo.
echo ========================================
echo     MeTruyenCV Web Interface
echo ========================================
echo.
REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found!
    echo Please install Python from: https://python.org
    pause
    goto :eof
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Cannot create virtual environment!
        pause
        goto :eof
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Cannot activate virtual environment!
    pause
    goto :eof
)

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\flask" (
    echo Installing dependencies...
    pip install -r requirements.txt
    pip install -r requirements_web.txt
    if errorlevel 1 (
        echo Error installing dependencies!
        pause
        goto :eof
    )
)

REM Check if config exists
if not exist "config.txt" (
    echo Creating default config file...
    python -c "from config_manager import ConfigManager; ConfigManager().create_default_config()" 2>nul
)

REM Start web server
echo.
echo Starting web server...
echo The application will automatically find an available port
echo.
echo Press Ctrl+C to stop server
echo ===============================================
echo.

REM Run the web application
python app.py

REM Cleanup on exit
echo.
echo Cleaning up...
deactivate 2>nul

echo.
echo Web server stopped
pause
