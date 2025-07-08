@echo off
echo ========================================
echo MeTruyenCV Downloader
echo ========================================
echo.
echo Chọn phiên bản để chạy:
echo 1. Main version (main.py) - Phiên bản cơ bản
echo 2. Fast version (fast.py) - Phiên bản nhanh hơn
echo.
set /p choice="Nhập lựa chọn (1 hoặc 2): "

if "%choice%"=="1" (
    echo Đang chạy main.py...
    python main.py
) else if "%choice%"=="2" (
    echo Đang chạy fast.py...
    python fast.py
) else (
    echo Lựa chọn không hợp lệ!
    pause
    goto :eof
)

pause
