@echo off
chcp 65001 >nul
title MeTruyenCV Downloader

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    MeTruyenCV Downloader                     ║
echo ║                  Chọn chế độ chạy ứng dụng                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check if argument is provided (for shortcuts)
if "%1"=="1" goto console_mode
if "%1"=="2" goto web_mode

echo 📋 Chọn chế độ chạy:
echo.
echo [1] 🖥️  Console Mode (Chế độ dòng lệnh)
echo [2] 🌐 Web Interface (Giao diện web)
echo [3] ❌ Thoát
echo.

set /p choice="👉 Nhập lựa chọn của bạn (1-3): "

if "%choice%"=="1" goto console_mode
if "%choice%"=="2" goto web_mode
if "%choice%"=="3" goto exit
echo ❌ Lựa chọn không hợp lệ!
pause
goto :eof

:console_mode
echo.
echo ========================================
echo Console Mode - MeTruyenCV Downloader
echo ========================================
echo.
echo Running MeTruyenCV Downloader with Config Management...
echo.
python main_config.py
pause
goto :eof

:web_mode
echo.
echo ========================================
echo Web Interface - MeTruyenCV Downloader
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không được tìm thấy!
    echo 📥 Vui lòng cài đặt Python từ: https://python.org
    pause
    goto :eof
)

:: Check if virtual environment exists
if not exist "venv" (
    echo 🔧 Tạo virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Không thể tạo virtual environment!
        pause
        goto :eof
    )
)

:: Activate virtual environment
echo 🔄 Kích hoạt virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Không thể kích hoạt virtual environment!
    pause
    goto :eof
)

:: Install main dependencies if needed
if not exist "venv\Lib\site-packages\selenium" (
    echo 📦 Cài đặt dependencies chính...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Lỗi cài đặt dependencies chính!
        pause
        goto :eof
    )
)

:: Install web dependencies
echo 📦 Cài đặt web dependencies...
pip install -r requirements_web.txt
if errorlevel 1 (
    echo ❌ Lỗi cài đặt web dependencies!
    echo 💡 Thử chạy: pip install Flask Flask-SocketIO eventlet
    pause
    goto :eof
)

:: Run system check
echo 🔍 Kiểm tra hệ thống...
python check_system.py
if errorlevel 1 (
    echo ❌ Hệ thống chưa sẵn sàng!
    echo 💡 Chạy setup.bat để cài đặt đầy đủ
    pause
    goto :eof
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
goto :eof

:exit
echo.
echo 👋 Tạm biệt!
timeout /t 2 >nul
