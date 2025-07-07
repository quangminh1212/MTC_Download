# MTC Downloader Environment Setup
Write-Host "===== MTC DOWNLOADER ENVIRONMENT SETUP =====" -ForegroundColor Green

# Check if Python is installed
Write-Host "Checking if Python is installed..."
try {
    $pythonVersion = python --version
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found on the system." -ForegroundColor Red
    Write-Host "Please install Python (version 3.6 or higher) from https://www.python.org/downloads/"
    Write-Host "and make sure to add Python to the PATH environment variable."
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path -Path "venv")) {
    Write-Host "[INFO] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& "./venv/Scripts/Activate.ps1"

# Update pip
Write-Host "[INFO] Updating pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install the package
Write-Host "[INFO] Installing MTC Downloader and its dependencies..." -ForegroundColor Yellow
pip install -e .

# Create necessary directories
Write-Host "[INFO] Creating necessary directories..." -ForegroundColor Yellow
if (-not (Test-Path -Path "downloads")) { New-Item -ItemType Directory -Path "downloads" | Out-Null }
if (-not (Test-Path -Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }

Write-Host "===== SETUP COMPLETE =====" -ForegroundColor Green
Write-Host ""
Write-Host "To run the application, use one of the following commands:"
Write-Host "- run.bat web    : Start the web application"
Write-Host "- run.bat gui    : Start the GUI application"
Write-Host "- run.bat cli    : Start the command-line application"

Read-Host "Press Enter to exit" 