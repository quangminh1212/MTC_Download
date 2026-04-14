@echo off
chcp 65001 >nul 2>&1
cls
echo ========================================
echo TỰ ĐỘNG TÌM APP_KEY - KHÔNG CẦN NHẤN PHÍM
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

echo ========================================
echo BƯỚC 1: CẤU HÌNH BLUESTACKS
echo ========================================
echo.
echo [1/5] Cấu hình proxy: %IP%:8080
"%ADB%" -s %DEVICE% shell settings put global http_proxy %IP%:8080 2>nul || echo ⚠️  Lỗi set proxy nhưng tiếp tục...
echo ✓ Đã set proxy
echo.

echo [2/5] Tải certificate...
python -c "import urllib.request; urllib.request.urlretrieve('http://mitm.it/cert/cer', 'mitmproxy-ca-cert.cer')" 2>nul || echo ⚠️  Không tải được từ mitm.it
if exist mitmproxy-ca-cert.cer (
    echo ✓ Đã tải certificate
) else (
    echo ⚠️  Chưa tải được certificate, bỏ qua...
)
echo.

echo [3/5] Push certificate vào BlueStacks...
if exist mitmproxy-ca-cert.cer (
    "%ADB%" -s %DEVICE% push mitmproxy-ca-cert.cer /sdcard/Download/mitmproxy-ca-cert.cer 2>nul || echo ⚠️  Không push được, bỏ qua...
    echo ✓ Đã push certificate vào /sdcard/Download/
    echo.
    echo ℹ️  Cài certificate thủ công trong BlueStacks:
    echo    Settings → Security → Install from storage
    echo    Chọn: Download/mitmproxy-ca-cert.cer
) else (
    echo ⚠️  Không có certificate để push, bỏ qua...
)
echo.

echo [4/5] Khởi động app NovelFever...
"%ADB%" -s %DEVICE% shell monkey -p %APP_PACKAGE% -c android.intent.category.LAUNCHER 1 2>nul || echo ⚠️  Không mở được app, bỏ qua...
echo ✓ Đã mở app
echo.

echo [5/5] Restart app để áp dụng proxy...
"%ADB%" -s %DEVICE% shell am force-stop %APP_PACKAGE% 2>nul || echo ⚠️  Không stop được app
timeout /t 2 >nul
"%ADB%" -s %DEVICE% shell monkey -p %APP_PACKAGE% -c android.intent.category.LAUNCHER 1 2>nul || echo ⚠️  Không restart được app
echo ✓ Đã restart app
echo.

echo ========================================
echo BƯỚC 2: KHỞI ĐỘNG MITMPROXY
echo ========================================
echo.
start "mitmproxy" cmd /c "mitmweb --listen-host 0.0.0.0 --listen-port 8080 --web-host 127.0.0.1 --web-port 8081"
echo ⏳ Đang khởi động mitmproxy...
timeout /t 5 >nul
echo ✓ mitmproxy đã khởi động
echo ✓ Web interface: http://127.0.0.1:8081
start http://127.0.0.1:8081
echo.

echo ========================================
echo BƯỚC 3: TỰ ĐỘNG TÌM APP_KEY
echo ========================================
echo.
echo 📋 QUAN TRỌNG:
echo    1. App NovelFever đã mở trong BlueStacks
echo    2. HÃY ĐỌC MỘT CHƯƠNG BẤT KỲ NGAY BÂY GIỜ
echo    3. Script sẽ tự động phát hiện APP_KEY
echo.
echo ⏳ Đang chờ traffic từ app...
echo    (Nhấn Ctrl+C để dừng)
echo ========================================
echo.

python auto_find_key.py

echo.
echo ========================================
echo KẾT QUẢ
echo ========================================
echo.
if exist APP_KEY.txt (
    echo.
    echo ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
    echo ✅                                    ✅
    echo ✅     ĐÃ TÌM THẤY APP_KEY!          ✅
    echo ✅                                    ✅
    echo ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
    echo.
    type APP_KEY.txt
    echo.
    echo ========================================
    echo 📋 BƯỚC TIẾP THEO:
    echo ========================================
    echo.
    echo 1. Test giải mã:
    echo    python test_decrypt_with_key.py
    echo.
    echo 2. Tải truyện:
    echo    python download_to_extract.py
    echo.
    echo ========================================
) else if exist decrypted_sample.txt (
    echo.
    echo ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
    echo ✅                                    ✅
    echo ✅  NỘI DUNG ĐÃ ĐƯỢC GIẢI MÃ!       ✅
    echo ✅                                    ✅
    echo ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
    echo.
    echo 💡 App tự giải mã, không cần APP_KEY!
    echo.
) else (
    echo.
    echo ⚠️⚠️⚠️ CHƯA TÌM THẤY APP_KEY ⚠️⚠️⚠️
    echo.
    echo 📋 Hãy thử:
    echo    1. Đọc thêm vài chương trong app
    echo    2. Kiểm tra mitmproxy: http://127.0.0.1:8081
    echo    3. Chạy lại: python auto_find_key.py
    echo.
)
echo.
echo ========================================
echo Script đã hoàn tất!
echo ========================================
echo.
pause
exit /b 0
