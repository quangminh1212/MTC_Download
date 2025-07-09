@echo off
chcp 65001 >nul
cls
echo ================================================
echo        MeTruyenCV Downloader - Web Interface
echo ================================================
echo.
echo Dang tu dong cai dat va khoi dong web server...
echo.

echo [1/2] Cai dat dependencies...
pip install flask requests beautifulsoup4 lxml pycryptodome --quiet --disable-pip-version-check 2>nul
echo.

echo [2/2] Khoi dong web server...
echo.
echo - Web server se chay tai: http://localhost:3000
echo - Trinh duyet se tu dong mo trong vai giay...
echo - Nhan Ctrl+C de dung server
echo.

timeout /t 3 /nobreak >nul
start http://localhost:3000

python app.py
