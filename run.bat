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
echo 3. Thoat
echo.
set /p choice="Nhap lua chon (1-3): "

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
    echo Tam biet!
    exit
)

echo Lua chon khong hop le!
pause

:start
cls
goto start
