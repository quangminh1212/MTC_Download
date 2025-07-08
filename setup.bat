@echo off
chcp 65001 >nul
title MeTruyenCV Downloader Setup

echo.
echo ========================================
echo   MeTruyenCV Downloader Setup
echo   Auto install complete system
echo ========================================
echo.

REM Check admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Dang chay voi quyen Administrator
) else (
    echo Khuyen nghi chay voi quyen Administrator de tranh loi
    echo.
)

REM Check if Python is installed
echo Kiem tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python khong duoc tim thay!
    echo.
    echo Dang tai Python installer...
    
    REM Download Python installer
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'python_installer.exe'}"
    
    if exist python_installer.exe (
        echo Dang cai dat Python...
        python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        
        echo Python da duoc cai dat
        del python_installer.exe
        
        REM Refresh PATH
        call refreshenv.cmd >nul 2>&1
    ) else (
        echo Khong the tai Python installer
        echo Vui long cai dat Python thu cong tu: https://python.org
        pause
        exit /b 1
    )
) else (
    for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo Python da duoc cai dat
)

REM Create virtual environment
echo.
echo Tao virtual environment...
if exist "venv" (
    echo Virtual environment da ton tai, dang xoa...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo Khong the tao virtual environment!
    pause
    exit /b 1
)

echo Virtual environment da duoc tao

REM Activate virtual environment
echo Kich hoat virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Khong the kich hoat virtual environment!
    pause
    exit /b 1
)

REM Upgrade pip
echo Nang cap pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Khong the nang cap pip, tiep tuc...
)

echo.
echo Step 1: Installing main Python packages...
echo Cai dat packages chinh...
pip install httpx beautifulsoup4 ebooklib tqdm backoff playwright pytesseract Pillow appdirs async-lru lxml selenium webdriver-manager configparser
if errorlevel 1 (
    echo Loi cai dat packages chinh!
    pause
    exit /b 1
)

echo.
echo Step 2: Installing web dependencies...
echo Cai dat web dependencies...
if exist "requirements_web.txt" (
    pip install -r requirements_web.txt
    if errorlevel 1 (
        echo Loi cai dat web dependencies!
        echo Thu cai dat thu cong: pip install Flask Flask-SocketIO eventlet
        pause
        exit /b 1
    )
) else (
    echo Khong tim thay requirements_web.txt, cai dat dependencies co ban...
    pip install Flask==3.0.0 Flask-SocketIO==5.3.6 eventlet==0.33.3
)

echo Web dependencies da duoc cai dat

echo.
echo Step 3: Installing Playwright browsers...
python -m playwright install firefox
if errorlevel 1 (
    echo Loi cai dat Playwright browsers, tiep tuc...
)

echo.
echo Step 4: Checking Tesseract-OCR...
if not exist "Tesseract-OCR\tesseract.exe" (
    echo WARNING: Tesseract-OCR not installed!
    echo Please download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Copy installation folder to this project as "Tesseract-OCR"
) else (
    echo Tesseract-OCR found!
)

REM Create config file if not exists
echo.
echo Tao file cau hinh...
if not exist "config.txt" (
    python -c "from config_manager import ConfigManager; ConfigManager().create_default_config()" 2>nul
    if errorlevel 1 (
        echo Khong the tao config tu dong, se tao khi chay lan dau
    ) else (
        echo File config.txt da duoc tao
    )
) else (
    echo File config.txt da ton tai
)

REM Create desktop shortcut
echo Creating desktop shortcut...
set CURRENT_DIR=%CD%
set WEB_SHORTCUT=%USERPROFILE%\Desktop\MeTruyenCV Web.lnk

REM Web shortcut
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%WEB_SHORTCUT%'); $Shortcut.TargetPath = '%CURRENT_DIR%\run.bat'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Description = 'MeTruyenCV Web Interface'; $Shortcut.Save()}" 2>nul

if exist "%WEB_SHORTCUT%" (
    echo Web shortcut created on Desktop
) else (
    echo Cannot create web shortcut
)

echo.
echo Step 5: Testing installation...
echo Test cai dat...
python -c "import httpx, bs4, ebooklib, tqdm, backoff, playwright, pytesseract, PIL, appdirs, async_lru, selenium, flask, flask_socketio; print('All packages OK!')" 2>nul
if errorlevel 1 (
    echo Mot so packages chua duoc cai dat dung
    echo Hay chay lai script hoac cai dat thu cong
) else (
    echo Test thanh cong!
)

REM Deactivate virtual environment
deactivate

echo.
echo ========================================
echo           SETUP COMPLETED!
echo ========================================
echo.
echo MeTruyenCV Downloader has been installed successfully!
echo.
echo How to use:
echo    1. Run: run.bat
echo    2. Web Interface will start automatically
echo.
echo Web Interface:
echo    - Open browser: http://localhost:5000
echo    - Configuration: http://localhost:5000/config
echo    - Download: http://localhost:5000/download
echo    - View logs: http://localhost:5000/logs
echo.
echo Desktop shortcut:
echo    - MeTruyenCV Web.lnk (Web interface)
echo.

REM Ask to run immediately
set /p RUN_NOW="Do you want to run the application now? (y/n): "
if /i "%RUN_NOW%"=="y" (
    echo.
    echo Starting MeTruyenCV Web Interface...
    call run.bat
) else (
    echo.
    echo Setup completed. Run run.bat when you want to use it.
    pause
)
