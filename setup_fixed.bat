@echo off
chcp 65001 >nul
echo ========================================
echo MeTruyenCV Downloader - Setup Script
echo ========================================
echo.

echo [1/5] Installing Python packages...
pip install httpx beautifulsoup4 ebooklib tqdm backoff playwright pytesseract Pillow appdirs async-lru lxml flask

echo.
echo [2/5] Installing Playwright browsers...
echo Trying different methods to install Playwright browsers...
python -m playwright install firefox
if errorlevel 1 (
    echo Trying alternative method...
    python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().firefox.launch()"
)

echo.
echo [3/5] Checking Tesseract-OCR...
if not exist "Tesseract-OCR\tesseract.exe" (
    echo WARNING: Tesseract-OCR not installed!
    echo.
    echo Please follow these steps:
    echo 1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Install it to any location
    echo 3. Copy the installation folder and rename it to "Tesseract-OCR"
    echo 4. Place the "Tesseract-OCR" folder in this project directory
    echo.
    echo The structure should be:
    echo %CD%\Tesseract-OCR\tesseract.exe
    echo.
) else (
    echo Tesseract-OCR found at: %CD%\Tesseract-OCR\tesseract.exe
)

echo.
echo [4/5] Testing imports...
python -c "import httpx, bs4, ebooklib, tqdm, backoff, playwright, pytesseract, PIL, appdirs, async_lru; print('✓ All packages imported successfully!')"

echo.
echo [5/5] Testing user-agent module...
python -c "from user_agent import get; print('✓ User-agent module works:', get()[:50] + '...')"

echo.
echo ========================================
echo Setup Status Check
echo ========================================
echo.
echo Running dependency checker...
python check_dependencies.py

echo.
echo ========================================
echo Setup completed!
echo ========================================
echo.
echo To run the application:
echo - Basic version: python main.py
echo - Fast version: python fast.py
echo - Or use: run.bat
echo.
echo To check dependencies: python check_dependencies.py
echo.
pause
