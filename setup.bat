@echo off
chcp 65001 >nul
echo ========================================
echo MeTruyenCV Downloader - Setup Script
echo ========================================
echo.

echo [1/4] Installing Python packages...
pip install httpx beautifulsoup4 ebooklib tqdm backoff playwright pytesseract Pillow appdirs async-lru lxml flask

echo.
echo [2/4] Installing Playwright browsers...
python -m playwright install firefox

echo.
echo [3/4] Checking Tesseract-OCR...
if not exist "Tesseract-OCR\tesseract.exe" (
    echo WARNING: Tesseract-OCR not installed!
    echo Please download and install Tesseract-OCR from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo Then copy Tesseract-OCR folder to this project directory.
    echo.
) else (
    echo Tesseract-OCR found!
)

echo.
echo [4/4] Checking installation...
python -c "import httpx, bs4, ebooklib, tqdm, backoff, playwright, pytesseract, PIL, appdirs, async_lru; print('All packages installed successfully!')"

echo.
echo ========================================
echo Setup completed!
echo ========================================
echo.
echo To run the application:
echo - Run main.py: python main.py (basic version)
echo - Run fast.py: python fast.py (faster version)
echo.
pause
