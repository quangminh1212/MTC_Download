@echo off
chcp 65001 >nul
cls
echo ================================================
echo           MeTruyenCV Downloader
echo ================================================
echo.
echo Dang tu dong cai dat va chay...
echo.

echo [1/2] Cai dat dependencies...
pip install requests beautifulsoup4 lxml --quiet
echo.

echo [2/2] Chay downloader (khong can ChromeDriver)...
python ultra_simple.py
echo.

echo ================================================
echo           HOAN THANH!
echo ================================================
pause
