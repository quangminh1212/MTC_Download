@echo off
title MeTruyenCV Downloader

echo.
echo ========================================
echo        MeTruyenCV Downloader
echo ========================================
echo.

REM Check if argument is provided (for shortcuts)
if "%1"=="1" goto console_mode
if "%1"=="2" goto web_mode

echo Chon che do chay:
echo.
echo [1] Console Mode
echo [2] Web Interface  
echo [3] Thoat
echo.

set /p choice="Nhap lua chon (1-3): "

if "%choice%"=="1" goto console_mode
if "%choice%"=="2" goto web_mode
if "%choice%"=="3" goto exit
echo Lua chon khong hop le!
pause
goto :eof

:console_mode
echo.
echo ========================================
echo Console Mode - MeTruyenCV Downloader
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment khong ton tai!
    echo Chay setup.bat de cai dat day du
    pause
    goto :eof
)

REM Activate virtual environment
echo Kich hoat virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Khong the kich hoat virtual environment!
    pause
    goto :eof
)

echo Running MeTruyenCV Downloader...
echo.
python main_config.py

REM Deactivate virtual environment
deactivate 2>nul

pause
goto :eof

:web_mode
echo.
echo ========================================
echo Web Interface - MeTruyenCV Downloader
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python khong duoc tim thay!
    echo Vui long cai dat Python tu: https://python.org
    pause
    goto :eof
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Tao virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Khong the tao virtual environment!
        pause
        goto :eof
    )
)

REM Activate virtual environment
echo Kich hoat virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Khong the kich hoat virtual environment!
    pause
    goto :eof
)

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\flask" (
    echo Cai dat dependencies...
    pip install -r requirements.txt
    pip install -r requirements_web.txt
    if errorlevel 1 (
        echo Loi cai dat dependencies!
        pause
        goto :eof
    )
)

REM Check if config exists
if not exist "config.txt" (
    echo Tao file cau hinh mac dinh...
    python -c "from config_manager import ConfigManager; ConfigManager().create_default_config()" 2>nul
)

REM Start web server
echo.
echo Khoi dong web server...
echo Truy cap: http://localhost:5000
echo.
echo Nhan Ctrl+C de dung server
echo ===============================================
echo.

REM Run the web application
python app.py

REM Cleanup on exit
echo.
echo Dang don dep...
deactivate 2>nul

echo.
echo Web server da dung
pause
goto :eof

:exit
echo.
echo Tam biet!
timeout /t 2 >nul
