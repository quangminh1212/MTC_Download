@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cls

echo ========================================
echo TỰ ĐỘNG TÌM APP_KEY
echo ========================================
echo.

REM Lấy IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

set "ADB=C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
set "DEVICE=127.0.0.1:5555"
set "APP=com.novelfever.app.android"

echo IP: %IP%
echo.

REM Cấu hình proxy
echo [1/3] Cấu hình proxy...
"%ADB%" -s %DEVICE% shell settings put global http_proxy %IP%:8080 >nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ Proxy OK
) else (
    echo ⚠️  Proxy có thể chưa set được
)
echo.

REM Mở app
echo [2/3] Mở app...
"%ADB%" -s %DEVICE% shell monkey -p %APP% 1 >nul 2>&1
echo ✓ Đã mở app
echo.

REM Khởi động mitmproxy
echo [3/3] Khởi động mitmproxy...
start "mitmproxy" cmd /c "mitmweb --listen-host 0.0.0.0 --listen-port 8080 --web-host 127.0.0.1 --web-port 8081"
timeout /t 3 >nul
start http://127.0.0.1:8081
echo ✓ mitmproxy: http://127.0.0.1:8081
echo.

echo ========================================
echo SẴN SÀNG!
echo ========================================
echo.
echo 📋 Bây giờ:
echo    1. Trong BlueStacks, đọc một chương
echo    2. Script sẽ tự động tìm APP_KEY
echo.
echo Nhấn Ctrl+C để dừng
echo ========================================
echo.

REM Chạy auto finder
python auto_find_key.py

REM Kiểm tra kết quả
echo.
if exist APP_KEY.txt (
    echo ✅ THÀNH CÔNG! Đã tìm thấy APP_KEY
    type APP_KEY.txt
) else if exist decrypted_sample.txt (
    echo ✅ THÀNH CÔNG! Nội dung đã giải mã
) else (
    echo ⚠️  Chưa tìm thấy. Thử đọc thêm chương.
)
echo.

pause
exit /b 0
