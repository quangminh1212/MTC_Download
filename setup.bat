@echo off
chcp 65001 >nul
echo ========================================
echo MeTruyenCV Downloader - Setup Script
echo ========================================
echo.

echo [1/6] Installing Python packages...
pip install httpx beautifulsoup4 ebooklib tqdm backoff playwright pytesseract Pillow appdirs async-lru lxml flask

echo.
echo [2/6] Installing Playwright browsers...
echo Installing Firefox browser for Playwright...
python -m playwright install firefox
if errorlevel 1 (
    echo Warning: Playwright browser installation may have failed
    echo You can try running this manually later: python -m playwright install firefox
)

echo.
echo [3/6] Checking Tesseract-OCR...
if not exist "Tesseract-OCR\tesseract.exe" (
    echo WARNING: Tesseract-OCR not installed!
    echo.
    echo Auto-downloading Tesseract-OCR installer...
    echo Please follow the installation wizard when it opens.

    REM Try to download Tesseract installer
    powershell -Command "try { Invoke-WebRequest -Uri 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe' -OutFile 'tesseract-installer.exe'; echo 'Download completed!' } catch { echo 'Download failed. Please download manually.' }"

    if exist "tesseract-installer.exe" (
        echo.
        echo Starting Tesseract installer...
        echo IMPORTANT: During installation, note the installation path!
        echo After installation, you need to copy the installation folder to this project.
        echo.
        pause
        start /wait tesseract-installer.exe

        echo.
        echo Installation completed. Now copying Tesseract to project folder...
        echo Please enter the Tesseract installation path
        echo (usually C:\Program Files\Tesseract-OCR or C:\Users\%USERNAME%\AppData\Local\Programs\Tesseract-OCR):
        set /p tesseract_source="Installation path: "

        if exist "%tesseract_source%\tesseract.exe" (
            echo Copying Tesseract to project folder...
            xcopy "%tesseract_source%" "Tesseract-OCR\" /E /I /Y
            echo Tesseract copied successfully!
        ) else (
            echo Could not find tesseract.exe at specified path.
            echo Please manually copy the Tesseract installation folder to this project
            echo and rename it to "Tesseract-OCR"
        )

        REM Clean up installer
        del tesseract-installer.exe
    ) else (
        echo Download failed. Please download Tesseract manually from:
        echo https://github.com/UB-Mannheim/tesseract/wiki
        echo Then copy the installation folder to this project as "Tesseract-OCR"
    )
) else (
    echo Tesseract-OCR found at: %CD%\Tesseract-OCR\tesseract.exe
)

echo.
echo [4/6] Testing Python imports...
python -c "import httpx, bs4, ebooklib, tqdm, backoff, playwright, pytesseract, PIL, appdirs, async_lru; print('✓ All Python packages imported successfully!')"

echo.
echo [5/6] Testing user-agent module...
python -c "from user_agent import get; print('✓ User-agent module works:', get()[:50] + '...')"

echo.
echo [6/6] Final verification...
python -c "
import os
print('=== FINAL STATUS ===')
# Check Python packages
try:
    import httpx, bs4, ebooklib, tqdm, backoff, playwright, pytesseract, PIL, appdirs, async_lru
    from user_agent import get
    print('✓ All Python packages: OK')
except ImportError as e:
    print('✗ Python packages:', e)

# Check Tesseract
tesseract_path = os.path.join(os.getcwd(), 'Tesseract-OCR', 'tesseract.exe')
if os.path.exists(tesseract_path):
    print('✓ Tesseract-OCR: OK')
else:
    print('✗ Tesseract-OCR: Missing')

# Check Playwright
try:
    from playwright.sync_api import sync_playwright
    print('✓ Playwright: OK')
except Exception:
    print('✗ Playwright browsers: May need manual installation')

print('===================')
"

echo.
echo ========================================
echo Setup completed!
echo ========================================
echo.
echo To run the application:
echo - Basic version: python main.py
echo - Fast version: python fast.py
echo.
echo If you encounter issues:
echo - For Playwright: python -m playwright install firefox
echo - For Tesseract: Download from https://github.com/UB-Mannheim/tesseract/wiki
echo.
pause
