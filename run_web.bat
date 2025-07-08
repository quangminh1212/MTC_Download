@echo off
chcp 65001 >nul
title MeTruyenCV Web Interface

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    MeTruyenCV Web Interface                  ║
echo ║                     Giao diện web downloader                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không được tìm thấy!
    echo 📥 Vui lòng cài đặt Python từ: https://python.org
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist "venv" (
    echo 🔧 Tạo virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Không thể tạo virtual environment!
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo 🔄 Kích hoạt virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Không thể kích hoạt virtual environment!
    pause
    exit /b 1
)

:: Install main dependencies if needed
if not exist "venv\Lib\site-packages\selenium" (
    echo 📦 Cài đặt dependencies chính...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Lỗi cài đặt dependencies chính!
        pause
        exit /b 1
    )
)

:: Install web dependencies
echo 📦 Cài đặt web dependencies...
pip install -r requirements_web.txt
if errorlevel 1 (
    echo ❌ Lỗi cài đặt web dependencies!
    echo 💡 Thử chạy: pip install Flask Flask-SocketIO eventlet
    pause
    exit /b 1
)

:: Run system check
echo 🔍 Kiểm tra hệ thống...
python check_system.py
if errorlevel 1 (
    echo ❌ Hệ thống chưa sẵn sàng!
    echo 💡 Chạy setup_web.bat để cài đặt đầy đủ
    pause
    exit /b 1
)

:: Check if config exists
if not exist "config.txt" (
    echo 📝 Tạo file cấu hình mặc định...
    python -c "from config_manager import ConfigManager; ConfigManager().create_default_config()"
)

:: Start web server
echo.
echo 🌐 Khởi động web server...
echo 📱 Truy cập: http://localhost:5000
echo 🔧 Cấu hình: http://localhost:5000/config  
echo 📥 Download: http://localhost:5000/download
echo 📋 Logs: http://localhost:5000/logs
echo.
echo ⏹️  Nhấn Ctrl+C để dừng server
echo ═══════════════════════════════════════════════════════════════
echo.

:: Run the web application
python app.py

:: Cleanup on exit
echo.
echo 🔄 Đang dọn dẹp...
deactivate

echo.
echo ✅ Web server đã dừng
pause
