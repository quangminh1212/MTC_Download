@echo off
chcp 65001 >nul
cls
echo ================================================
echo           MeTruyenCV Downloader
echo ================================================
echo.
echo Dang tu dong cai dat va chay...
echo.

echo [1/3] Cai dat dependencies...
python simple_install.py
echo.

echo [2/3] Tai ChromeDriver thu cong...
python manual_chrome_setup.py
echo.

echo [3/3] Chay downloader...
python simple_downloader.py
echo.

echo ================================================
echo           HOAN THANH!
echo ================================================
pause
