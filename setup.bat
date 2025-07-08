@echo off
echo ========================================
echo MeTruyenCV Downloader - Setup Script
echo ========================================
echo.

echo [1/4] Cài đặt Python packages...
pip install httpx beautifulsoup4 ebooklib tqdm backoff playwright pytesseract Pillow appdirs async-lru lxml flask

echo.
echo [2/4] Cài đặt Playwright browsers...
playwright install firefox

echo.
echo [3/4] Kiểm tra Tesseract-OCR...
if not exist "Tesseract-OCR\tesseract.exe" (
    echo CẢNH BÁO: Tesseract-OCR chưa được cài đặt!
    echo Vui lòng tải và cài đặt Tesseract-OCR từ:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo Sau đó copy thư mục Tesseract-OCR vào thư mục dự án này.
    echo.
) else (
    echo Tesseract-OCR đã được tìm thấy!
)

echo.
echo [4/4] Kiểm tra cài đặt...
python -c "import httpx, bs4, ebooklib, tqdm, backoff, playwright, pytesseract, PIL, appdirs, async_lru; print('✓ Tất cả packages đã được cài đặt thành công!')"

echo.
echo ========================================
echo Setup hoàn tất!
echo ========================================
echo.
echo Để chạy ứng dụng:
echo - Chạy main.py: python main.py (phiên bản console)
echo - Chạy fast.py: python fast.py (phiên bản nhanh hơn)
echo.
pause
