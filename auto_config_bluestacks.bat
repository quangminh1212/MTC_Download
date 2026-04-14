@echo off
chcp 65001 >nul
cls
echo ========================================
echo TỰ ĐỘNG CẤU HÌNH BLUESTACKS
echo ========================================
echo.

REM Tìm BlueStacks ADB
set "BLUESTACKS_ADB=C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
if not exist "%BLUESTACKS_ADB%" (
    set "BLUESTACKS_ADB=C:\Program Files\BlueStacks\HD-Adb.exe"
)
if not exist "%BLUESTACKS_ADB%" (
    set "BLUESTACKS_ADB=C:\Program Files (x86)\BlueStacks_nxt\HD-Adb.exe"
)
if not exist "%BLUESTACKS_ADB%" (
    set "BLUESTACKS_ADB=C:\Program Files (x86)\BlueStacks\HD-Adb.exe"
)

if not exist "%BLUESTACKS_ADB%" (
    echo ❌ Không tìm thấy BlueStacks ADB
    echo Đang thử dùng ADB từ system...
    set "BLUESTACKS_ADB=adb"
)

echo ✓ Sử dụng ADB: %BLUESTACKS_ADB%
echo.

REM Lấy IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%
echo ✓ IP máy tính: %IP%
echo.

echo [1/6] Kết nối với BlueStacks...
"%BLUESTACKS_ADB%" kill-server 2>nul
"%BLUESTACKS_ADB%" start-server
timeout /t 2 >nul
"%BLUESTACKS_ADB%" connect 127.0.0.1:5555
if errorlevel 1 (
    echo ⚠️  Thử port khác...
    "%BLUESTACKS_ADB%" connect 127.0.0.1:5556
    if errorlevel 1 (
        "%BLUESTACKS_ADB%" connect 127.0.0.1:5557
    )
)
timeout /t 2 >nul
echo.

echo [2/6] Cấu hình proxy...
"%BLUESTACKS_ADB%" shell settings put global http_proxy %IP%:8080
if errorlevel 1 (
    echo ⚠️  Thử cách khác...
    "%BLUESTACKS_ADB%" shell "settings put global http_proxy %IP%:8080"
)
echo ✓ Đã set proxy: %IP%:8080
echo.

echo [3/6] Tải certificate từ mitmproxy...
echo ✓ Đang tải certificate...
curl -o mitmproxy-ca-cert.cer http://mitm.it/cert/cer 2>nul
if not exist mitmproxy-ca-cert.cer (
    echo ⚠️  Không tải được từ mitm.it, thử cách khác...
    REM Tạo script Python để lấy cert
    echo import mitmproxy.certs > get_cert.py
    echo import pathlib >> get_cert.py
    echo cert_path = pathlib.Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.cer" >> get_cert.py
    echo if cert_path.exists(): >> get_cert.py
    echo     import shutil >> get_cert.py
    echo     shutil.copy(cert_path, "mitmproxy-ca-cert.cer") >> get_cert.py
    echo     print("OK") >> get_cert.py
    python get_cert.py 2>nul
    del get_cert.py 2>nul
)
echo.

echo [4/6] Push certificate vào BlueStacks...
if exist mitmproxy-ca-cert.cer (
    "%BLUESTACKS_ADB%" push mitmproxy-ca-cert.cer /sdcard/Download/
    echo ✓ Đã copy certificate vào /sdcard/Download/
    echo.
    
    echo [5/6] Cài đặt certificate...
    echo ℹ️  Đang mở màn hình cài đặt certificate...
    "%BLUESTACKS_ADB%" shell am start -a android.intent.action.VIEW -d file:///sdcard/Download/mitmproxy-ca-cert.cer -t application/x-x509-ca-cert
    timeout /t 2 >nul
    
    REM Thử cách khác
    "%BLUESTACKS_ADB%" shell am start -a android.credentials.INSTALL
    echo.
    echo ⚠️  LƯU Ý: Bạn cần thao tác thủ công trong BlueStacks:
    echo    1. Chọn file mitmproxy-ca-cert.cer
    echo    2. Đặt tên: mitmproxy
    echo    3. Chọn "VPN and apps"
    echo.
) else (
    echo ⚠️  Không tìm thấy certificate
    echo.
)

echo [6/6] Mở app MTC...
echo ℹ️  Đang tìm package name của app MTC...

REM Tìm package name
"%BLUESTACKS_ADB%" shell pm list packages | findstr -i "mtc novel lono" > packages.txt
if exist packages.txt (
    for /f "tokens=2 delims=:" %%p in (packages.txt) do (
        echo ✓ Tìm thấy: %%p
        "%BLUESTACKS_ADB%" shell monkey -p %%p -c android.intent.category.LAUNCHER 1
        goto :app_opened
    )
    del packages.txt
)

REM Thử các package name phổ biến
echo ⚠️  Thử mở app với package name phổ biến...
"%BLUESTACKS_ADB%" shell monkey -p com.lonoapp.novelfever -c android.intent.category.LAUNCHER 1 2>nul
"%BLUESTACKS_ADB%" shell monkey -p com.mtc.novel -c android.intent.category.LAUNCHER 1 2>nul
"%BLUESTACKS_ADB%" shell monkey -p com.novel.mtc -c android.intent.category.LAUNCHER 1 2>nul

:app_opened
echo.
echo ========================================
echo HOÀN TẤT CẤU HÌNH!
echo ========================================
echo.
echo ✅ Đã cấu hình:
echo    - Proxy: %IP%:8080
echo    - Certificate: Đã push vào BlueStacks
echo.
echo 📋 Bước tiếp theo:
echo    1. Trong BlueStacks, cài certificate (nếu chưa tự động)
echo    2. Mở app MTC
echo    3. Đọc bất kỳ chương nào
echo    4. Script auto_find_key.py sẽ tự động tìm APP_KEY
echo.
echo ⚠️  Nếu app không mở được:
echo    - Mở thủ công app MTC trong BlueStacks
echo    - Đọc một chương bất kỳ
echo.
pause
