@echo off
chcp 65001 >nul
cls
echo ================================================
echo           MeTruyenCV Downloader
echo ================================================
echo.
echo Chon chuc nang:
echo 1. Cai dat lan dau
echo 2. Chay downloader
echo 3. Sua loi ChromeDriver
echo 4. Tai ChromeDriver thu cong
echo 5. Thoat
echo.
set /p choice="Nhap lua chon (1-5): "

if "%choice%"=="1" (
    echo.
    echo Dang cai dat...
    python install.py
    echo.
    pause
    goto start
)

if "%choice%"=="2" (
    echo.
    echo Dang chay downloader...
    python simple_downloader.py
    echo.
    pause
    goto start
)

if "%choice%"=="3" (
    echo.
    echo Dang sua loi ChromeDriver...
    python fix_chrome.py
    echo.
    pause
    goto start
)

if "%choice%"=="4" (
    echo.
    echo Dang tai ChromeDriver thu cong...
    python manual_chrome_setup.py
    echo.
    pause
    goto start
)

if "%choice%"=="5" (
    echo Tam biet!
    exit
)

echo Lua chon khong hop le!
pause

:start
cls
goto start
