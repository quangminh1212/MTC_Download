@echo off
chcp 65001 >nul
echo ============================================================
echo MTC DOWNLOADER - SETUP
echo ============================================================
echo.

echo [1/3] Kiểm tra Python...
python --version
if errorlevel 1 (
    echo ❌ Python chưa được cài đặt!
    echo Vui lòng cài Python từ: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python OK
echo.

echo [2/3] Cài đặt dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Cài đặt thất bại!
    pause
    exit /b 1
)
echo ✅ Dependencies OK
echo.

echo [3/3] Kiểm tra scripts...
if exist mtc_downloader.py (
    echo ✅ mtc_downloader.py
) else (
    echo ❌ Thiếu mtc_downloader.py
)

if exist download_by_ids.py (
    echo ✅ download_by_ids.py
) else (
    echo ❌ Thiếu download_by_ids.py
)

if exist batch_download.py (
    echo ✅ batch_download.py
) else (
    echo ❌ Thiếu batch_download.py
)

echo.
echo ============================================================
echo ✅ CÀI ĐẶT HOÀN TẤT!
echo ============================================================
echo.
echo Sử dụng:
echo   1. Tải theo ID:        python download_by_ids.py
echo   2. Tải tự động:        python batch_download.py
echo   3. Test truyện ngắn:   python demo_test.py
echo   4. Tải + Export TXT:   python advanced_downloader.py
echo.
pause
