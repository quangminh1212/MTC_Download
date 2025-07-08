@echo off
chcp 65001 >nul
title MeTruyenCV Downloader - Khởi động dự án

echo.
echo ========================================
echo    📚 MeTruyenCV Downloader
echo    🚀 Khởi động dự án
echo ========================================
echo.

REM Kiểm tra Python
echo 🔍 Đang kiểm tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python chưa được cài đặt!
    echo.
    echo 📥 Vui lòng tải và cài đặt Python từ:
    echo    https://python.org/downloads/
    echo.
    echo 💡 Lưu ý: Nhớ tick "Add Python to PATH" khi cài đặt
    echo.
    pause
    exit /b 1
)

python --version
echo ✅ Python đã được cài đặt
echo.

REM Kiểm tra pip
echo 🔍 Đang kiểm tra pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip chưa được cài đặt!
    echo 💡 pip thường đi kèm với Python, hãy cài đặt lại Python
    pause
    exit /b 1
)

echo ✅ pip đã sẵn sàng
echo.

REM Kiểm tra file requirements.txt
if not exist "requirements.txt" (
    echo ❌ Không tìm thấy file requirements.txt
    echo 💡 Hãy chắc chắn bạn đang chạy trong thư mục dự án
    pause
    exit /b 1
)

REM Cài đặt dependencies
echo 📦 Đang cài đặt các thư viện cần thiết...
echo    Quá trình này có thể mất vài phút...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ Lỗi khi cài đặt thư viện!
    echo.
    echo 💡 Có thể thử:
    echo    1. Chạy Command Prompt với quyền Administrator
    echo    2. Kiểm tra kết nối internet
    echo    3. Thử lệnh: pip install --upgrade pip
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Đã cài đặt thành công tất cả thư viện
echo.

REM Tạo thư mục downloads nếu chưa có
if not exist "downloads" (
    mkdir downloads
    echo 📁 Đã tạo thư mục downloads
)

echo 🚀 Đang khởi động MeTruyenCV Downloader...
echo.
echo 🌐 Ứng dụng sẽ chạy tại: http://localhost:5000
echo 📱 Trình duyệt sẽ tự động mở sau 3 giây
echo.
echo ⚠️  Để dừng ứng dụng, nhấn Ctrl+C
echo.

REM Chờ 3 giây rồi mở trình duyệt
timeout /t 3 /nobreak >nul
start http://localhost:5000

REM Chạy ứng dụng
python app.py

echo.
echo 🎉 Cảm ơn bạn đã sử dụng MeTruyenCV Downloader!
echo.
pause
