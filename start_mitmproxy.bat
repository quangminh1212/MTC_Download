@echo off
echo ========================================
echo Starting mitmproxy Web Interface
echo ========================================
echo.
echo Instructions:
echo 1. Open browser: http://127.0.0.1:8081
echo 2. Configure BlueStacks proxy (see BLUESTACKS_SETUP.md)
echo 3. Open app and read a chapter
echo 4. Check this interface for traffic
echo.
echo Looking for:
echo - Requests to: api.lonoapp.net
echo - Headers: X-App-Key, Authorization
echo - Response: Plain text or encrypted
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

mitmweb --listen-host 0.0.0.0 --listen-port 8080 --web-host 127.0.0.1 --web-port 8081
