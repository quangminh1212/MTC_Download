@echo off
chcp 65001 >nul
title MeTruyenCV Web Interface Setup

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  MeTruyenCV Web Setup                        ║
echo ║              Cài đặt tự động web interface                  ║
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

:: Check if Git is installed (optional)
echo 🔍 Kiểm tra Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Git không được tìm thấy (tùy chọn)
) else (
    echo ✅ Git đã được cài đặt
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

:: Install main dependencies
echo 📦 Cài đặt dependencies chính...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Lỗi cài đặt dependencies chính!
        echo 💡 Thử cài đặt thủ công: pip install selenium beautifulsoup4 lxml httpx ebooklib
        pause
        exit /b 1
    )
    echo ✅ Dependencies chính đã được cài đặt
) else (
    echo ⚠️  Không tìm thấy requirements.txt, cài đặt dependencies cơ bản...
    pip install selenium beautifulsoup4 lxml httpx ebooklib configparser
)

:: Install web dependencies
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

:: Setup ChromeDriver
echo 🌐 Cài đặt ChromeDriver...
pip install webdriver-manager
if errorlevel 1 (
    echo ⚠️  Không thể cài đặt webdriver-manager
)

:: Create config file if not exists
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

:: Create desktop shortcut
echo 🖥️  Tạo shortcut...
set CURRENT_DIR=%CD%
set SHORTCUT_PATH=%USERPROFILE%\Desktop\MeTruyenCV Web.lnk

powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%CURRENT_DIR%\run_web.bat'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.IconLocation = '%CURRENT_DIR%\static\img\favicon.ico'; $Shortcut.Description = 'MeTruyenCV Web Interface'; $Shortcut.Save()}" 2>nul

if exist "%SHORTCUT_PATH%" (
    echo ✅ Shortcut đã được tạo trên Desktop
) else (
    echo ⚠️  Không thể tạo shortcut
)

:: Test installation
echo.
echo 🧪 Test cài đặt...
python -c "import flask, flask_socketio, selenium, bs4; print('✅ Tất cả modules đã được cài đặt thành công')" 2>nul
if errorlevel 1 (
    echo ❌ Một số modules chưa được cài đặt đúng
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
echo 🎉 Web interface đã được cài đặt thành công!
echo.
echo 📋 Cách sử dụng:
echo    1. Chạy: run_web.bat
echo    2. Mở browser: http://localhost:5000
echo    3. Cấu hình tại: http://localhost:5000/config
echo.
echo 🔗 Shortcuts:
echo    - Desktop: MeTruyenCV Web.lnk
echo    - Command: run_web.bat
echo.
echo 📁 Files quan trọng:
echo    - app.py: Web server chính
echo    - config.txt: File cấu hình
echo    - templates/: Giao diện web
echo    - static/: Assets (CSS, JS, images)
echo.
echo 💡 Lưu ý:
echo    - Lần đầu chạy cần cấu hình email/password
echo    - Web interface chạy trên port 5000
echo    - Logs được lưu trong web_app.log
echo.

:: Ask to run immediately
set /p RUN_NOW="🚀 Bạn có muốn chạy web interface ngay bây giờ? (y/n): "
if /i "%RUN_NOW%"=="y" (
    echo.
    echo 🌐 Đang khởi động web interface...
    call run_web.bat
) else (
    echo.
    echo ✅ Setup hoàn tất. Chạy run_web.bat khi cần sử dụng.
    pause
)
