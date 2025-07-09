@echo off
chcp 65001 >nul
echo ================================================
echo           MeTruyenCV Downloader
echo ================================================
echo.
echo Chọn chức năng:
echo 1. Cài đặt lần đầu
echo 2. Chạy downloader (tương tác)
echo 3. Test XPath selectors
echo 4. Thoát
echo.
set /p choice="Nhập lựa chọn (1-4): "

if "%choice%"=="1" (
    echo.
    echo Đang cài đặt...
    python setup.py
    pause
    goto :start
)

if "%choice%"=="2" (
    echo.
    echo Đang khởi động downloader...
    python run_downloader.py
    pause
    goto :start
)

if "%choice%"=="3" (
    echo.
    echo Đang test XPath selectors...
    python test_selectors.py
    pause
    goto :start
)

if "%choice%"=="4" (
    echo Tạm biệt!
    exit
)

echo Lựa chọn không hợp lệ!
pause
:start
cls
goto :start
