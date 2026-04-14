@echo off
chcp 65001 >nul
echo ===================================
echo    Snyk Quick Scan Helper
echo ===================================
echo.

set "PROJECT_PATH=%CD%"

echo Project: %PROJECT_PATH%
echo.

echo ===================================
echo    HƯỚNG DẪN SỬ DỤNG TRONG KIRO
echo ===================================
echo.

echo Bước 1: Trust project
echo ----------------------
echo Trong Kiro chat, gõ:
echo   "snyk trust %PROJECT_PATH%"
echo.

echo Bước 2: Authenticate (nếu chưa đăng nhập)
echo ------------------------------------------
echo Trong Kiro chat, gõ:
echo   "snyk auth"
echo.

echo Bước 3: Scan mã nguồn Python
echo -----------------------------
echo Trong Kiro chat, gõ:
echo   "snyk code scan --path=%PROJECT_PATH%"
echo.
echo Hoặc scan với severity cao:
echo   "snyk code scan --path=%PROJECT_PATH% --severity-threshold=high"
echo.

echo Bước 4: Scan dependencies
echo --------------------------
echo Trong Kiro chat, gõ:
echo   "snyk sca scan --path=%PROJECT_PATH% --command=python3"
echo.

echo Bước 5: Kiểm tra package health
echo --------------------------------
echo Ví dụ kiểm tra package mitmproxy:
echo   "snyk package health check --package-name=mitmproxy --ecosystem=pypi"
echo.

echo ===================================
echo    QUICK COMMANDS (Copy & Paste)
echo ===================================
echo.

echo # Trust và scan nhanh
echo snyk trust %PROJECT_PATH%
echo snyk code scan --path=%PROJECT_PATH% --severity-threshold=medium
echo.

echo # Scan chi tiết
echo snyk code scan --path=%PROJECT_PATH% --include-ignores
echo snyk sca scan --path=%PROJECT_PATH% --command=python3 --print-deps
echo.

echo ===================================
echo    FILES CREATED
echo ===================================
echo.
echo - docs\SNYK_COMMANDS.md : Hướng dẫn chi tiết
echo - snyk_trust_all.bat    : Trust tất cả folders
echo - snyk_scan_all.bat     : Scan tổng thể
echo - snyk_quick_scan.bat   : File này (quick reference)
echo.

pause
