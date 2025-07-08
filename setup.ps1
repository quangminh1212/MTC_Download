# MeTruyenCV Downloader Setup Script
Write-Host "========================================" -ForegroundColor Green
Write-Host "MeTruyenCV Downloader Setup Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Step 1: Installing Python packages..." -ForegroundColor Yellow
pip install httpx beautifulsoup4 ebooklib tqdm backoff playwright pytesseract Pillow appdirs async-lru lxml flask

Write-Host ""
Write-Host "Step 2: Installing Playwright browsers..." -ForegroundColor Yellow
python -m playwright install firefox

Write-Host ""
Write-Host "Step 3: Checking Tesseract-OCR..." -ForegroundColor Yellow
if (-not (Test-Path "Tesseract-OCR\tesseract.exe")) {
    Write-Host "WARNING: Tesseract-OCR not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download and install Tesseract-OCR manually:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://github.com/UB-Mannheim/tesseract/wiki"
    Write-Host "2. Download the Windows installer"
    Write-Host "3. Install it to any location"
    Write-Host "4. Copy the installation folder to this project directory"
    Write-Host "5. Rename the copied folder to 'Tesseract-OCR'"
    Write-Host ""
} else {
    Write-Host "Tesseract-OCR found!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 4: Testing installation..." -ForegroundColor Yellow
try {
    python -c "import httpx, bs4, ebooklib, tqdm, backoff, playwright, pytesseract, PIL, appdirs, async_lru; print('All Python packages imported successfully!')"
    Write-Host "Python packages: OK" -ForegroundColor Green
} catch {
    Write-Host "Python packages: ERROR" -ForegroundColor Red
}

Write-Host ""
Write-Host "Testing user-agent module..." -ForegroundColor Yellow
try {
    python -c "from user_agent import get; print('User-agent module works!')"
    Write-Host "User-agent module: OK" -ForegroundColor Green
} catch {
    Write-Host "User-agent module: ERROR" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To run the application:" -ForegroundColor Cyan
Write-Host "- Basic version: python main.py"
Write-Host "- Fast version: python fast.py"
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
