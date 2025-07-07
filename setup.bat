@echo off
echo ===== MTC DOWNLOADER ENVIRONMENT SETUP =====

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found on the system.
    echo Please install Python (version 3.6 or higher) from https://www.python.org/downloads/
    echo and make sure to add Python to the PATH environment variable.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate

REM Update pip
echo [INFO] Updating pip...
python -m pip install --upgrade pip

REM Install dependencies
echo [INFO] Installing MTC Downloader and its dependencies...
pip install -e .

REM Create necessary directories
if not exist "downloads" mkdir downloads
if not exist "logs" mkdir logs

echo ===== SETUP COMPLETE =====
echo.
echo To run the application, use one of the following commands:
echo - run.bat web    : Start the web application
echo - run.bat gui    : Start the GUI application
echo - run.bat cli    : Start the command-line application

echo.
pause 
