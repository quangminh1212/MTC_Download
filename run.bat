@echo off
title MeTruyenCV Downloader

echo.
echo ========================================
echo    MeTruyenCV Downloader
echo    Khoi dong du an
echo ========================================
echo.

REM Kiem tra Python
echo Dang kiem tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python chua duoc cai dat!
    echo.
    echo Vui long tai va cai dat Python tu:
    echo    https://python.org/downloads/
    echo.
    echo Luu y: Nho tick "Add Python to PATH" khi cai dat
    echo.
    pause
    exit /b 1
)

python --version
echo Python da duoc cai dat
echo.

REM Kiem tra pip
echo Dang kiem tra pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo pip chua duoc cai dat!
    echo pip thuong di kem voi Python, hay cai dat lai Python
    pause
    exit /b 1
)

echo pip da san sang
echo.

REM Kiem tra file requirements.txt
if not exist "requirements.txt" (
    echo Khong tim thay file requirements.txt
    echo Hay chac chan ban dang chay trong thu muc du an
    pause
    exit /b 1
)

REM Cai dat dependencies
echo Dang cai dat cac thu vien can thiet...
echo Qua trinh nay co the mat vai phut...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Loi khi cai dat thu vien!
    echo.
    echo Co the thu:
    echo    1. Chay Command Prompt voi quyen Administrator
    echo    2. Kiem tra ket noi internet
    echo    3. Thu lenh: pip install --upgrade pip
    echo.
    pause
    exit /b 1
)

echo.
echo Da cai dat thanh cong tat ca thu vien
echo.

REM Tao thu muc downloads neu chua co
if not exist "downloads" (
    mkdir downloads
    echo Da tao thu muc downloads
)

echo Dang khoi dong MeTruyenCV Downloader...
echo.
echo Ung dung se chay tai: http://localhost:5000
echo Trinh duyet se tu dong mo sau 3 giay
echo.
echo De dung ung dung, nhan Ctrl+C
echo.

REM Cho 3 giay roi mo trinh duyet
timeout /t 3 /nobreak >nul
start http://localhost:5000

REM Chay ung dung
python app.py

echo.
echo Cam on ban da su dung MeTruyenCV Downloader!
echo.
pause
