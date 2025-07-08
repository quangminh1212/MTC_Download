@echo off
echo Starting MeTruyenCV Downloader Setup...
echo.
echo Step 1: Installing Python packages...
pip install httpx beautifulsoup4 ebooklib tqdm backoff playwright pytesseract Pillow appdirs async-lru lxml flask

echo.
echo Step 2: Installing Playwright browsers...
python -m playwright install firefox

echo.
echo Step 3: Checking Tesseract-OCR...
if not exist "Tesseract-OCR\tesseract.exe" (
    echo WARNING: Tesseract-OCR not installed!
    echo Please download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Copy installation folder to this project as "Tesseract-OCR"
) else (
    echo Tesseract-OCR found!
)

echo.
echo Step 4: Testing installation...
python -c "import httpx, bs4, ebooklib, tqdm, backoff, playwright, pytesseract, PIL, appdirs, async_lru; print('All packages OK!')"

echo.
echo Setup completed!
echo To run: python main.py or python fast.py
echo.
pause
