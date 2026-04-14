@echo off
chcp 65001 >nul
cls
echo ========================================
echo TỰ ĐỘNG TÌM APP_KEY - MTC NOVEL
echo ========================================
echo.
echo Script này sẽ TỰ ĐỘNG:
echo   ✓ Cấu hình proxy cho BlueStacks
echo   ✓ Cài certificate (bán tự động)
echo   ✓ Mở app NovelFever
echo   ✓ Khởi động mitmproxy
echo   ✓ Tìm APP_KEY tự động
echo.
echo ⚠️  Yêu cầu:
echo    - BlueStacks đang chạy
echo    - App NovelFever đã cài (com.novelfever.app.android)
echo.
echo Nhấn phím bất kỳ để bắt đầu...
pause >nul
cls

echo.
echo ========================================
echo BƯỚC 1: CẤU HÌNH BLUESTACKS
echo ========================================
call auto_config_bluestacks_v2.bat

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

echo.
echo ========================================
echo BƯỚC 3: TỰ ĐỘNG TÌM APP_KEY
echo ========================================
echo.
echo 📋 Hướng dẫn:
echo    1. Trong BlueStacks, app NovelFever đã mở
echo    2. Đọc BẤT KỲ chương nào
echo    3. Script sẽ TỰ ĐỘNG phát hiện APP_KEY
echo.
echo ⏳ Đang chờ traffic từ app...
echo    (Hãy đọc một chương trong app ngay bây giờ)
echo.
echo Nhấn Ctrl+C để dừng
echo ========================================
echo.

python auto_find_key.py

echo.
echo ========================================
echo KẾT QUẢ
echo ========================================
echo.
if exist APP_KEY.txt (
    echo ✅ ✅ ✅ ĐÃ TÌM THẤY APP_KEY! ✅ ✅ ✅
    echo.
    type APP_KEY.txt
    echo.
    echo ========================================
    echo 📋 BƯỚC TIẾP THEO:
    echo ========================================
    echo 1. Test giải mã:
    echo    python test_decrypt_with_key.py
    echo.
    echo 2. Cập nhật vào code:
    echo    Mở file mtc/api.py
    echo    Thêm APP_KEY vào đầu file
    echo.
    echo 3. Tải truyện:
    echo    python download_to_extract.py
    echo ========================================
) else if exist decrypted_sample.txt (
    echo ✅ ✅ ✅ TÌM THẤY NỘI DUNG ĐÃ GIẢI MÃ! ✅ ✅ ✅
    echo.
    echo 💡 App tự giải mã nội dung trước khi hiển thị!
    echo    Không cần APP_KEY, có thể tải trực tiếp từ API.
    echo.
    echo ========================================
    echo 📋 BƯỚC TIẾP THEO:
    echo ========================================
    echo 1. Kiểm tra file: decrypted_sample.txt
    echo 2. Cập nhật mtc/api.py để bỏ qua bước giải mã
    echo 3. Tải truyện trực tiếp
    echo ========================================
) else (
    echo ⚠️  CHƯA TÌM THẤY APP_KEY
    echo.
    echo 📋 Khắc phục:
    echo    1. Đảm bảo đã ĐỌC chương trong app
    echo    2. Kiểm tra mitmproxy: http://127.0.0.1:8081
    echo    3. Kiểm tra proxy trong BlueStacks Settings
    echo    4. Thử chạy lại: python auto_find_key.py
    echo.
    echo 💡 Hoặc xem hướng dẫn chi tiết:
    echo    CAU_HINH_BLUESTACKS_CHI_TIET.md
)
echo.
pause
