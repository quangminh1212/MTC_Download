@echo off
chcp 65001 >nul
echo ===================================
echo    Snyk Trust All Folders
echo ===================================
echo.

REM Lấy đường dẫn tuyệt đối
set "PROJECT_PATH=%CD%"

echo Đường dẫn project: %PROJECT_PATH%
echo.

echo ===================================
echo LƯU Ý QUAN TRỌNG:
echo ===================================
echo.
echo Snyk trust command chỉ có thể chạy qua Kiro MCP tool.
echo Không thể chạy trực tiếp từ command line.
echo.
echo Để trust các folder, hãy:
echo 1. Mở Kiro IDE
echo 2. Mở chat và gõ lệnh sau:
echo.
echo ===================================
echo    Các lệnh cần chạy trong Kiro:
echo ===================================
echo.

echo Trust thư mục gốc:
echo   snyk trust %PROJECT_PATH%
echo.

echo Trust thư mục download:
echo   snyk trust %PROJECT_PATH%\download
echo.

echo Trust thư mục extract:
echo   snyk trust %PROJECT_PATH%\extract
echo.

echo Trust thư mục docs:
echo   snyk trust %PROJECT_PATH%\docs
echo.

echo Trust thư mục data:
echo   snyk trust %PROJECT_PATH%\data
echo.

echo ===================================
echo    Hoặc trust tất cả cùng lúc:
echo ===================================
echo.
echo Trong Kiro chat, gõ:
echo "Trust tất cả các folder trong project này để scan Snyk"
echo.

echo Xem thêm chi tiết tại: docs\SNYK_COMMANDS.md
echo.

pause
