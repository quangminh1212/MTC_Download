@echo off
chcp 65001 >nul
title MeTruyenCV Downloader

echo.
echo ========================================
echo    📚 MeTruyenCV Downloader
echo ========================================
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python chưa được cài đặt!
    echo 📥 Vui lòng tải Python từ: https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python đã được cài đặt
echo.

REM Kiểm tra pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip chưa được cài đặt!
    pause
    exit /b 1
)

echo ✅ pip đã được cài đặt
echo.

REM Cài đặt dependencies
echo 📦 Đang cài đặt thư viện cần thiết...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Lỗi khi cài đặt thư viện!
    pause
    exit /b 1
)

echo ✅ Đã cài đặt thành công các thư viện
echo.

REM Tạo thư mục downloads
if not exist "downloads" mkdir downloads

echo 🚀 Đang khởi động ứng dụng...
echo.
echo 🌐 Ứng dụng sẽ chạy tại: http://localhost:5000
echo 📱 Trình duyệt sẽ tự động mở
echo.
echo ⚠️  Để dừng ứng dụng, nhấn Ctrl+C
echo.

REM Chờ 3 giây rồi mở trình duyệt
timeout /t 3 /nobreak >nul
start http://localhost:5000

REM Chạy ứng dụng
python app.py

pause
