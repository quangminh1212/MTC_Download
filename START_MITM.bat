@echo off
echo ========================================
echo MTC Encryption Key Capture - Quick Start
echo ========================================
echo.

REM Check if mitmproxy is installed
where mitmweb >/dev/null 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] mitmproxy not installed
    echo.
    echo Installing mitmproxy...
    pip install mitmproxy
    echo.
)

REM Create capture script if not exists
if not exist capture_key.py (
    echo Creating capture script...
    python -c "from setup_mitm_capture import create_mitm_script; create_mitm_script()"
)

echo [OK] Starting mitmproxy...
echo.
echo Web interface: http://127.0.0.1:8081
echo.
echo NEXT STEPS:
echo 1. Configure BlueStacks proxy: 127.0.0.1:8080
echo 2. Install cert from http://mitm.it
echo 3. Run MTC app and read a chapter
echo 4. Check captured_keys.txt for encryption key
echo.

mitmweb -s capture_key.py --listen-port 8080
