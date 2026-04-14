@echo off
chcp 65001 >nul
cls
echo ========================================
echo TÌM APP_KEY TỰ ĐỘNG - MTC Novel
echo ========================================
echo.

REM Lấy IP máy tính
echo [1/5] Đang lấy địa chỉ IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%
echo ✓ IP của bạn: %IP%
echo.

REM Tạo file hướng dẫn cấu hình
echo [2/5] Tạo file hướng dẫn...
echo ======================================== > HUONG_DAN_CAU_HINH.txt
echo HƯỚNG DẪN CẤU HÌNH BLUESTACKS >> HUONG_DAN_CAU_HINH.txt
echo ======================================== >> HUONG_DAN_CAU_HINH.txt
echo. >> HUONG_DAN_CAU_HINH.txt
echo 1. Mở BlueStacks Settings (biểu tượng bánh răng) >> HUONG_DAN_CAU_HINH.txt
echo 2. Vào Network hoặc Advanced >> HUONG_DAN_CAU_HINH.txt
echo 3. Chọn Manual Proxy Configuration >> HUONG_DAN_CAU_HINH.txt
echo 4. Nhập: >> HUONG_DAN_CAU_HINH.txt
echo    - Host: %IP% >> HUONG_DAN_CAU_HINH.txt
echo    - Port: 8080 >> HUONG_DAN_CAU_HINH.txt
echo 5. Save và Restart BlueStacks >> HUONG_DAN_CAU_HINH.txt
echo. >> HUONG_DAN_CAU_HINH.txt
echo 6. Trong BlueStacks, mở Browser >> HUONG_DAN_CAU_HINH.txt
echo 7. Truy cập: http://mitm.it >> HUONG_DAN_CAU_HINH.txt
echo 8. Tải và cài Android certificate >> HUONG_DAN_CAU_HINH.txt
echo. >> HUONG_DAN_CAU_HINH.txt
echo 9. Mở app MTC và đọc bất kỳ chương nào >> HUONG_DAN_CAU_HINH.txt
echo 10. Script sẽ tự động tìm APP_KEY >> HUONG_DAN_CAU_HINH.txt
echo ======================================== >> HUONG_DAN_CAU_HINH.txt

echo ✓ Đã tạo file HUONG_DAN_CAU_HINH.txt
echo.

REM Hiển thị hướng dẫn
echo [3/5] HƯỚNG DẪN CẤU HÌNH BLUESTACKS:
echo.
echo 1. Mở BlueStacks Settings (biểu tượng bánh răng)
echo 2. Vào Network hoặc Advanced
echo 3. Chọn Manual Proxy Configuration
echo 4. Nhập:
echo    - Host: %IP%
echo    - Port: 8080
echo 5. Save và Restart BlueStacks
echo.
echo 6. Trong BlueStacks, mở Browser
echo 7. Truy cập: http://mitm.it
echo 8. Tải và cài Android certificate
echo.
echo 9. Mở app MTC và đọc bất kỳ chương nào
echo.
echo ========================================
echo.
echo Nhấn phím bất kỳ sau khi đã cấu hình xong...
pause >nul

echo.
echo [4/5] Khởi động mitmproxy...
start "mitmproxy" cmd /c "mitmweb --listen-host 0.0.0.0 --listen-port 8080 --web-host 127.0.0.1 --web-port 8081"
timeout /t 3 >nul

echo ✓ mitmproxy đã khởi động
echo ✓ Web interface: http://127.0.0.1:8081
echo.

REM Mở web interface
start http://127.0.0.1:8081

echo [5/5] Khởi động auto finder...
echo.
echo ========================================
echo ĐANG TỰ ĐỘNG TÌM APP_KEY...
echo ========================================
echo.
echo Hướng dẫn:
echo 1. Mở app MTC trong BlueStacks
echo 2. Đọc bất kỳ chương truyện nào
echo 3. Script sẽ tự động phát hiện APP_KEY
echo.
echo Nhấn Ctrl+C để dừng
echo ========================================
echo.

python auto_find_key.py

echo.
echo ========================================
echo HOÀN TẤT!
echo ========================================
pause
