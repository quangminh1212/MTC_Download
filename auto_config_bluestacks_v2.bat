@echo off
chcp 65001 >nul
cls
echo ========================================
echo Tự ĐỘNG CẤU HÌNH BLUESTACKS
echo ========================================
echo.

set "ADB=C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
set "DEVICE=127.0.0.1:5555"
set "APP_PACKAGE=com.novelfever.app.android"

REM Lấy IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

echo ✓ ADB: %ADB%
echo ✓ Device: %DEVICE%
echo ✓ App: %APP_PACKAGE%
echo ✓ IP: %IP%
echo.

echo [1/5] Cấu hình proxy...
"%ADB%" -s %DEVICE% shell settings put global http_proxy %IP%:8080
echo ✓ Proxy: %IP%:8080
echo.

echo [2/5] Tải certificate...
python -c "import urllib.request; urllib.request.urlretrieve('http://mitm.it/cert/cer', 'mitmproxy-ca-cert.cer')" 2>nul
if not exist mitmproxy-ca-cert.cer (
    echo ⚠️  Không tải được, thử cách khác...
    curl -o mitmproxy-ca-cert.cer http://mitm.it/cert/cer 2>nul
)
if exist mitmproxy-ca-cert.cer (
    echo ✓ Đã tải certificate
) else (
    echo ⚠️  Không tải được certificate
)
echo.

echo [3/5] Push certificate vào BlueStacks...
if exist mitmproxy-ca-cert.cer (
    "%ADB%" -s %DEVICE% push mitmproxy-ca-cert.cer /sdcard/Download/mitmproxy-ca-cert.cer
    echo ✓ Đã push certificate
    echo.
    
    echo [4/5] Mở màn hình cài certificate...
    "%ADB%" -s %DEVICE% shell am start -a android.credentials.INSTALL
    echo.
    echo ⚠️  QUAN TRỌNG: Trong BlueStacks, làm theo:
    echo    1. Chọn "Install from storage" hoặc "Install certificate"
    echo    2. Tìm file: Download/mitmproxy-ca-cert.cer
    echo    3. Đặt tên: mitmproxy
    echo    4. Chọn "VPN and apps"
    echo.
    echo Nhấn phím bất kỳ sau khi đã cài xong...
    pause >nul
) else (
    echo ⚠️  Bỏ qua bước cài certificate
)
echo.

echo [5/5] Khởi động app NovelFever...
"%ADB%" -s %DEVICE% shell am start -n %APP_PACKAGE%/com.novelfever.app.android.MainActivity
if errorlevel 1 (
    echo ⚠️  Thử cách khác...
    "%ADB%" -s %DEVICE% shell monkey -p %APP_PACKAGE% -c android.intent.category.LAUNCHER 1
)
echo ✓ Đã mở app
echo.

echo ========================================
echo HOÀN TẤT CẤU HÌNH!
echo ========================================
echo.
echo ✅ Đã cấu hình:
echo    - Proxy: %IP%:8080
echo    - Certificate: Đã push (cần cài thủ công)
echo    - App: Đã mở
echo.
echo 📋 Bước tiếp theo:
echo    1. Trong app, đọc BẤT KỲ chương nào
echo    2. Script auto_find_key.py sẽ tự động tìm APP_KEY
echo.
