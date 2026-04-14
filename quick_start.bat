@echo off
cls
echo ========================================
echo MTC Novel Downloader - Quick Start
echo ========================================
echo.
echo This will help you find the APP_KEY to decrypt novels
echo.
echo Prerequisites:
echo - BlueStacks installed and running
echo - NovelFever app installed in BlueStacks
echo.
pause
echo.

echo [Step 1/4] Installing mitmproxy...
pip install mitmproxy
if errorlevel 1 (
    echo [ERROR] Failed to install mitmproxy
    pause
    exit /b 1
)

echo.
echo [Step 2/4] Getting your IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%
echo Your IP: %IP%

echo.
echo [Step 3/4] Instructions for BlueStacks:
echo.
echo 1. Open BlueStacks Settings (gear icon)
echo 2. Go to Network
echo 3. Set Manual Proxy:
echo    - Host: %IP%
echo    - Port: 8080
echo 4. Save and Restart BlueStacks
echo.
echo 5. In BlueStacks browser, go to: http://mitm.it
echo 6. Download and install Android certificate
echo.
pause

echo.
echo [Step 4/4] Starting mitmproxy...
echo.
echo Open browser: http://127.0.0.1:8081
echo.
start http://127.0.0.1:8081
echo.
echo Now:
echo 1. Open NovelFever app in BlueStacks
echo 2. Read any chapter
echo 3. Check mitmproxy web interface for APP_KEY
echo.
echo Press Ctrl+C to stop when done
echo.

mitmweb --listen-host 0.0.0.0 --listen-port 8080 --web-host 127.0.0.1 --web-port 8081
