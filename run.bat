@echo off
setlocal enabledelayedexpansion

REM Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment is not set up.
    echo Please run setup.bat first to set up the environment.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate

REM Check input parameters
set "mode=%1"
if "%mode%"=="" set "mode=web"

if "%mode%"=="web" (
    echo ===== STARTING WEB APPLICATION =====
    echo Access the application at http://localhost:3000
    python -m mtc_downloader.cli web
) else if "%mode%"=="gui" (
    echo ===== STARTING GUI APPLICATION =====
    python -m mtc_downloader.cli gui
) else if "%mode%"=="cli" (
    echo ===== STARTING COMMAND LINE APPLICATION =====
    echo Usage instructions:
    mtc-download --help
    echo.
    echo Examples:
    echo mtc-download https://metruyencv.com/truyen/ten-truyen/chuong-XX
    echo mtc-extract -i file.html
    echo.
    cmd /k
) else (
    echo [ERROR] Invalid parameter: %mode%
    echo Valid parameters: web, gui, cli
    pause
    exit /b 1
)

REM Exit virtual environment if not in CLI mode
if not "%mode%"=="cli" (
    call venv\Scripts\deactivate
) 
