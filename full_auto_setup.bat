@echo off
chcp 65001 >nul
cls
echo ========================================
echo TỰ ĐỘNG HOÀN TOÀN - TÌM APP_KEY
echo ========================================
echo.
echo Script này sẽ tự động:
echo 1. Cấu hình BlueStacks proxy
echo 2. Cài certificate
echo 3. Khởi động mitmproxy
echo 4. Mở app MTC
echo 5. Tìm APP_KEY tự động
echo.
echo ⚠️  Yêu cầu:
echo    - BlueStacks đang chạy
echo    - App MTC đã cài trong BlueStacks
echo.
pause
cls

echo.
echo [BƯỚC 1/3] Cấu hình BlueStacks...
echo ========================================
call auto_config_bluestacks.bat
echo.

echo.
echo [BƯỚC 2/3] Khởi động mitmproxy...
echo ========================================
start "mitmproxy" cmd /c "mitmweb --listen-host 0.0.0.0 --listen-port 8080 --web-host 127.0.0.1 --web-port 8081"
timeout /t 5 >nul
start http://127.0.0.1:8081
echo ✓ mitmproxy đã khởi động
echo ✓ Web interface: http://127.0.0.1:8081
echo.

echo.
echo [BƯỚC 3/3] Tự động tìm APP_KEY...
echo ========================================
echo.
echo 📋 Hướng dẫn:
echo    1. Trong BlueStacks, mở app MTC (nếu chưa mở)
echo    2. Đọc BẤT KỲ chương nào
echo    3. Script sẽ TỰ ĐỘNG phát hiện APP_KEY
echo.
echo ⏳ Đang chờ traffic từ app...
echo.

python auto_find_key.py

echo.
echo ========================================
echo HOÀN TẤT!
echo ========================================
echo.
if exist APP_KEY.txt (
    echo ✅ ĐÃ TÌM THẤY APP_KEY!
    echo.
    type APP_KEY.txt
    echo.
    echo 📋 Bước tiếp theo:
    echo    1. Test với: python test_decrypt_with_key.py
    echo    2. Cập nhật vào mtc/api.py
) else if exist decrypted_sample.txt (
    echo ✅ ĐÃ TÌM THẤY NỘI DUNG ĐÃ GIẢI MÃ!
    echo.
    echo 💡 App tự giải mã nội dung!
    echo    Không cần APP_KEY, có thể tải trực tiếp.
) else (
    echo ⚠️  Chưa tìm thấy APP_KEY
    echo.
    echo 📋 Thử lại:
    echo    1. Đảm bảo đã đọc chương trong app
    echo    2. Kiểm tra mitmproxy web: http://127.0.0.1:8081
    echo    3. Chạy lại: python auto_find_key.py
)
echo.
pause
