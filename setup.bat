@echo off
chcp 65001 >nul
title MeTruyenCV Downloader Setup

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  MeTruyenCV Downloader Setup                 ║
echo ║              Cài đặt tự động toàn bộ hệ thống               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Đang chạy với quyền Administrator
) else (
    echo ⚠️  Khuyến nghị chạy với quyền Administrator để tránh lỗi
    echo.
)

:: Check if Python is installed
echo 🔍 Kiểm tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không được tìm thấy!
    echo.
    echo 📥 Đang tải Python installer...

    :: Download Python installer
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'python_installer.exe'}"

    if exist python_installer.exe (
        echo ⚙️  Đang cài đặt Python...
        python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

        echo ✅ Python đã được cài đặt
        del python_installer.exe

        :: Refresh PATH
        call refreshenv.cmd >nul 2>&1
    ) else (
        echo ❌ Không thể tải Python installer
        echo 📥 Vui lòng cài đặt Python thủ công từ: https://python.org
        pause
        exit /b 1
    )
) else (
    for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo ✅ Python !PYTHON_VERSION! đã được cài đặt
)

:: Create virtual environment
echo.
echo 🔧 Tạo virtual environment...
if exist "venv" (
    echo ⚠️  Virtual environment đã tồn tại, đang xóa...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ❌ Không thể tạo virtual environment!
    pause
    exit /b 1
)

echo ✅ Virtual environment đã được tạo

:: Activate virtual environment
echo 🔄 Kích hoạt virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Không thể kích hoạt virtual environment!
    pause
    exit /b 1
)

:: Upgrade pip
echo 📦 Nâng cấp pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ⚠️  Không thể nâng cấp pip, tiếp tục...
)

echo.
echo Step 1: Installing main Python packages...
echo 📦 Cài đặt packages chính...
pip install httpx beautifulsoup4 ebooklib tqdm backoff playwright pytesseract Pillow appdirs async-lru lxml selenium webdriver-manager configparser
if errorlevel 1 (
    echo ❌ Lỗi cài đặt packages chính!
    pause
    exit /b 1
)

echo.
echo Step 2: Installing web dependencies...
echo 📦 Cài đặt web dependencies...
if exist "requirements_web.txt" (
    pip install -r requirements_web.txt
    if errorlevel 1 (
        echo ❌ Lỗi cài đặt web dependencies!
        echo 💡 Thử cài đặt thủ công: pip install Flask Flask-SocketIO eventlet
        pause
        exit /b 1
    )
) else (
    echo ⚠️  Không tìm thấy requirements_web.txt, cài đặt dependencies cơ bản...
    pip install Flask==3.0.0 Flask-SocketIO==5.3.6 eventlet==0.33.3
)

echo ✅ Web dependencies đã được cài đặt

echo.
echo Step 3: Installing Playwright browsers...
python -m playwright install firefox
if errorlevel 1 (
    echo ⚠️  Lỗi cài đặt Playwright browsers, tiếp tục...
)

echo.
echo Step 4: Checking Tesseract-OCR...
if not exist "Tesseract-OCR\tesseract.exe" (
    echo ⚠️  WARNING: Tesseract-OCR not installed!
    echo 📥 Please download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 📁 Copy installation folder to this project as "Tesseract-OCR"
) else (
    echo ✅ Tesseract-OCR found!
)

:: Create config file if not exists
echo.
echo 📝 Tạo file cấu hình...
if not exist "config.txt" (
    python -c "from config_manager import ConfigManager; ConfigManager().create_default_config()" 2>nul
    if errorlevel 1 (
        echo ⚠️  Không thể tạo config tự động, sẽ tạo khi chạy lần đầu
    ) else (
        echo ✅ File config.txt đã được tạo
    )
) else (
    echo ✅ File config.txt đã tồn tại
)

:: Create desktop shortcut for console mode
echo 🖥️  Tạo shortcuts...
set CURRENT_DIR=%CD%
set CONSOLE_SHORTCUT=%USERPROFILE%\Desktop\MeTruyenCV Console.lnk
set WEB_SHORTCUT=%USERPROFILE%\Desktop\MeTruyenCV Web.lnk

:: Console shortcut
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%CONSOLE_SHORTCUT%'); $Shortcut.TargetPath = '%CURRENT_DIR%\run.bat'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Arguments = '1'; $Shortcut.Description = 'MeTruyenCV Console Mode'; $Shortcut.Save()}" 2>nul

:: Web shortcut
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%WEB_SHORTCUT%'); $Shortcut.TargetPath = '%CURRENT_DIR%\run.bat'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Arguments = '2'; $Shortcut.IconLocation = '%CURRENT_DIR%\static\img\favicon.ico'; $Shortcut.Description = 'MeTruyenCV Web Interface'; $Shortcut.Save()}" 2>nul

if exist "%CONSOLE_SHORTCUT%" (
    echo ✅ Console shortcut đã được tạo trên Desktop
) else (
    echo ⚠️  Không thể tạo console shortcut
)

if exist "%WEB_SHORTCUT%" (
    echo ✅ Web shortcut đã được tạo trên Desktop
) else (
    echo ⚠️  Không thể tạo web shortcut
)

echo.
echo Step 5: Testing installation...
echo 🧪 Test cài đặt...
python -c "import httpx, bs4, ebooklib, tqdm, backoff, playwright, pytesseract, PIL, appdirs, async_lru, selenium, flask, flask_socketio; print('✅ All packages OK!')" 2>nul
if errorlevel 1 (
    echo ❌ Một số packages chưa được cài đặt đúng
    echo 💡 Hãy chạy lại script hoặc cài đặt thủ công
) else (
    echo ✅ Test thành công!
)

:: Deactivate virtual environment
deactivate

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    CÀI ĐẶT HOÀN TẤT!                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 MeTruyenCV Downloader đã được cài đặt thành công!
echo.
echo 📋 Cách sử dụng:
echo    1. Chạy: run.bat
echo    2. Chọn Console Mode hoặc Web Interface
echo.
echo 🖥️  Console Mode:
echo    - Chạy trực tiếp trong command line
echo    - Sử dụng file config.txt
echo.
echo 🌐 Web Interface:
echo    - Mở browser: http://localhost:5000
echo    - Cấu hình tại: http://localhost:5000/config
echo    - Download tại: http://localhost:5000/download
echo    - Xem logs tại: http://localhost:5000/logs
echo.
echo 🔗 Shortcuts trên Desktop:
echo    - MeTruyenCV Console.lnk (Console mode)
echo    - MeTruyenCV Web.lnk (Web interface)
echo.
echo 📁 Files quan trọng:
echo    - run.bat: File chạy chính (chọn mode)
echo    - main_config.py: Console downloader
echo    - app.py: Web server
echo    - config.txt: File cấu hình
echo    - templates/: Giao diện web
echo    - static/: Assets (CSS, JS, images)
echo.
echo 💡 Lưu ý:
echo    - Lần đầu chạy cần cấu hình email/password
echo    - Web interface chạy trên port 5000
echo    - Logs được lưu trong download.log và web_app.log
echo.

:: Ask to run immediately
set /p RUN_NOW="🚀 Bạn có muốn chạy ứng dụng ngay bây giờ? (y/n): "
if /i "%RUN_NOW%"=="y" (
    echo.
    echo 🌐 Đang khởi động MeTruyenCV Downloader...
    call run.bat
) else (
    echo.
    echo ✅ Setup hoàn tất. Chạy run.bat khi cần sử dụng.
    pause
)
