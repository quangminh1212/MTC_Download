@echo off
chcp 65001 >nul
title MeTruyenCV Downloader - Demo

echo.
echo ========================================
echo    📚 MeTruyenCV Downloader - DEMO
echo ========================================
echo.
echo 🚨 ĐÂY LÀ PHIÊN BẢN DEMO
echo 📝 Chỉ có dữ liệu mẫu để test giao diện
echo 🌐 Không cần kết nối internet
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

echo 📚 Dữ liệu mẫu có sẵn:
echo   - Nô Lệ Bóng Tối (3 chương)
echo   - Ta Có Một Tòa Thành Phố Ngày Tận Thế (3 chương)
echo.

echo 🚀 Đang khởi động demo...
echo.
echo 🌐 Demo sẽ chạy tại: http://localhost:5001
echo 📱 Trình duyệt sẽ tự động mở
echo.
echo ⚠️  Để dừng demo, nhấn Ctrl+C
echo.

REM Chờ 3 giây rồi mở trình duyệt
timeout /t 3 /nobreak >nul
start http://localhost:5001

REM Chạy demo
python demo_offline.py

pause
