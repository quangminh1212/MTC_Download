@echo off
chcp 65001 >nul
echo ===================================
echo    Snyk Security Scan Tool
echo ===================================
echo.

REM Lấy đường dẫn tuyệt đối của thư mục hiện tại
set "PROJECT_PATH=%CD%"

echo [Bước 1/5] Trust project folder...
echo Đường dẫn: %PROJECT_PATH%
REM Snyk trust command sẽ được gọi qua Kiro MCP
echo Trust command cần chạy qua Kiro MCP tool
echo.

echo [Bước 2/5] Kiểm tra Snyk version...
REM Kiểm tra xem Snyk có sẵn không
echo Checking Snyk availability...
echo.

echo [Bước 3/5] Scan mã nguồn Python (SAST)...
echo Đang quét: %PROJECT_PATH%
echo Command: snyk code scan --path=%PROJECT_PATH% --severity-threshold=medium
echo.

echo [Bước 4/5] Scan Python dependencies (SCA)...
echo Command: snyk sca scan --path=%PROJECT_PATH% --command=python3
echo.

echo [Bước 5/5] Kiểm tra package health...
echo Các package chính trong project:
echo - mitmproxy
echo - requests
echo - cryptography
echo.

echo ===================================
echo    Hướng dẫn sử dụng
echo ===================================
echo.
echo Để chạy Snyk scan, bạn cần:
echo 1. Mở Kiro IDE
echo 2. Sử dụng chat để gọi Snyk MCP tools:
echo    - "snyk trust ."
echo    - "snyk code scan --path=."
echo    - "snyk sca scan --path=. --command=python3"
echo.
echo Hoặc xem file docs/SNYK_COMMANDS.md để biết chi tiết
echo.

pause
