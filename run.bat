@echo off
chcp 65001 >nul
cls
echo ================================================
echo           MeTruyenCV Downloader
echo ================================================
echo.
echo Dang tu dong cai dat va chay...
echo.

echo [1/4] Kiem tra va cai dat dependencies...
python install.py
echo.

echo [2/4] Sua loi ChromeDriver (neu co)...
python fix_chrome.py
echo.

echo [3/4] Tai ChromeDriver thu cong...
python manual_chrome_setup.py
echo.

echo [4/4] Chay downloader...
python simple_downloader.py
echo.

echo ================================================
echo           HOAN THANH!
echo ================================================
pause
