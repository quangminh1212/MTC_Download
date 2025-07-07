@echo off
echo ===== THIẾT LẬP MÔI TRƯỜNG CHO MTC DOWNLOADER =====

REM Kiểm tra Python đã được cài đặt chưa
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [LỖI] Python không được tìm thấy trên hệ thống.
    echo Vui lòng cài đặt Python (phiên bản 3.6 trở lên) từ https://www.python.org/downloads/
    echo và đảm bảo đã thêm Python vào biến môi trường PATH.
    pause
    exit /b 1
)

echo [OK] Đã tìm thấy Python:
python --version

REM Tạo thư mục venv nếu chưa tồn tại
if not exist "venv" (
    echo [INFO] Đang tạo môi trường ảo Python...
    python -m venv venv
)

REM Kích hoạt môi trường ảo
echo [INFO] Kích hoạt môi trường ảo...
call venv\Scripts\activate

REM Cập nhật pip
echo [INFO] Đang cập nhật pip...
python -m pip install --upgrade pip

REM Cài đặt các phụ thuộc
echo [INFO] Đang cài đặt MTC Downloader và các phụ thuộc...
pip install -e .

REM Tạo các thư mục cần thiết
if not exist "downloads" mkdir downloads
if not exist "logs" mkdir logs

echo ===== CÀI ĐẶT HOÀN TẤT =====
echo.
echo Để khởi chạy ứng dụng, sử dụng một trong các lệnh sau:
echo - run.bat web    : Khởi chạy ứng dụng web
echo - run.bat gui    : Khởi chạy ứng dụng giao diện đồ họa
echo - run.bat cli    : Khởi chạy ứng dụng dòng lệnh

echo.
pause 