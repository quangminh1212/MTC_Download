@echo off
echo ========================================
echo MTC Novel Downloader - mitmproxy Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Installing mitmproxy...
pip install mitmproxy
if errorlevel 1 (
    echo [ERROR] Failed to install mitmproxy
    pause
    exit /b 1
)

echo.
echo [2/5] Checking for ADB...
where adb >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ADB not found in PATH
    echo.
    echo Please install ADB:
    echo 1. Download Platform Tools from: https://developer.android.com/studio/releases/platform-tools
    echo 2. Extract to C:\platform-tools
    echo 3. Add C:\platform-tools to PATH
    echo.
    echo OR use BlueStacks built-in ADB:
    echo - Usually at: C:\Program Files\BlueStacks_nxt\HD-Adb.exe
    echo.
) else (
    echo [OK] ADB found
)

echo.
echo [3/5] Getting your computer's IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%a
    set IP=!IP:~1!
    echo Your IP: !IP!
    goto :found_ip
)
:found_ip

echo.
echo [4/5] Creating mitmproxy start script...
echo @echo off > start_mitmproxy.bat
echo echo Starting mitmproxy web interface... >> start_mitmproxy.bat
echo echo. >> start_mitmproxy.bat
echo echo Open browser and go to: http://127.0.0.1:8081 >> start_mitmproxy.bat
echo echo. >> start_mitmproxy.bat
echo mitmweb --listen-host 0.0.0.0 --listen-port 8080 --web-host 127.0.0.1 --web-port 8081 >> start_mitmproxy.bat

echo.
echo [5/5] Creating analysis script...
echo Done!

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run: start_mitmproxy.bat
echo 2. Configure BlueStacks proxy (see instructions below)
echo 3. Install certificate in BlueStacks
echo 4. Open app and read a chapter
echo 5. Check mitmproxy for APP_KEY
echo.
pause
