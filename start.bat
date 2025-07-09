@echo off
chcp 65001 >nul
cls
echo ================================================
echo        MeTruyenCV Downloader - Khoi dong
echo ================================================
echo.
echo Dang khoi dong chuong trinh tai truyen...
echo.

echo [1/2] Cai dat dependencies...
pip install requests beautifulsoup4 lxml pycryptodome selenium --quiet --disable-pip-version-check 2>nul
echo.

echo [2/2] Doc config va bat dau download...
echo.
echo - Doc thong tin tu config.json
echo - Tu dong dang nhap va download theo cau hinh
echo - Nhan Ctrl+C de dung qua trinh
echo.

timeout /t 2 /nobreak >nul

python metruyencv_downloader.py

echo.
echo Nhan phim bat ky de dong cua so...
pause >nul
