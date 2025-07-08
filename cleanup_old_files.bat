@echo off
chcp 65001 >nul
title Cleanup Old Files

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Cleanup Old Files                         ║
echo ║              Dọn dẹp các file cũ không cần thiết            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🧹 Đang dọn dẹp các file cũ...
echo.

:: Remove old individual setup files
if exist "setup_web.bat" (
    echo 🗑️  Xóa setup_web.bat (đã tích hợp vào setup.bat)
    del "setup_web.bat"
)

if exist "setup_web.sh" (
    echo 🗑️  Xóa setup_web.sh (không cần thiết)
    del "setup_web.sh"
)

:: Remove old individual run files
if exist "run_web.bat" (
    echo 🗑️  Xóa run_web.bat (đã tích hợp vào run.bat)
    del "run_web.bat"
)

:: Remove old commit files
if exist "commit_web_interface.bat" (
    echo 🗑️  Xóa commit_web_interface.bat (không cần thiết)
    del "commit_web_interface.bat"
)

:: Remove old uninstall files
if exist "uninstall_web.bat" (
    echo 🗑️  Xóa uninstall_web.bat (không cần thiết)
    del "uninstall_web.bat"
)

:: Remove old update files
if exist "update_web.bat" (
    echo 🗑️  Xóa update_web.bat (không cần thiết)
    del "update_web.bat"
)

:: Clean up Python cache
if exist "__pycache__" (
    echo 🗑️  Xóa Python cache
    rmdir /s /q "__pycache__"
)

if exist "user_agent\__pycache__" (
    echo 🗑️  Xóa user_agent cache
    rmdir /s /q "user_agent\__pycache__"
)

:: Clean up old log files (optional)
set /p CLEAN_LOGS="🗑️  Bạn có muốn xóa log files cũ? (y/n): "
if /i "%CLEAN_LOGS%"=="y" (
    if exist "download.log" (
        echo 🗑️  Xóa download.log
        del "download.log"
    )
    if exist "web_app.log" (
        echo 🗑️  Xóa web_app.log
        del "web_app.log"
    )
)

:: Clean up old virtual environment (optional)
set /p CLEAN_VENV="🗑️  Bạn có muốn xóa virtual environment cũ? (y/n): "
if /i "%CLEAN_VENV%"=="y" (
    if exist "venv" (
        echo 🗑️  Xóa virtual environment cũ
        rmdir /s /q "venv"
        echo 💡 Chạy setup.bat để tạo lại virtual environment
    )
)

echo.
echo ✅ Dọn dẹp hoàn tất!
echo.
echo 📋 Các file còn lại quan trọng:
echo    - run.bat (file chạy chính)
echo    - setup.bat (file setup tích hợp)
echo    - main_config.py (console downloader)
echo    - app.py (web server)
echo    - config.txt (cấu hình)
echo    - templates/ (web templates)
echo    - static/ (web assets)
echo.
echo 💡 Để sử dụng hệ thống mới:
echo    1. Chạy: setup.bat
echo    2. Chạy: run.bat
echo.
pause
